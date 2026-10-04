#!/usr/bin/env python3
"""
predict_et.py - fetch last week's data and predict with the ExtraTrees (ET) models.

Pipeline (same logic as main.ipynb, ET only)
  1. fetch fresh data + rebuild data/master_weekly.csv   (features_extract.py)
  2. build the features of the last COMPLETE week (Mon-Sun)
       - base features from the master
       - seasonal harmonics (3 sin/cos pairs on ISO week)
       - calendar features of the target week  (<cal>__t{h} = calendar h weeks ahead)
  3. predict y_vs_chg_{2,4,8,13,26}w with one ET per horizon
  4. print + append to predictions/et_predictions.csv

Usage (run from the project root, next to features_extract.py)
  python predict_et.py --train        # once (and whenever you want to refresh the models)
  python predict_et.py                # weekly: fetch + predict
  python predict_et.py --no-fetch     # skip downloads, reuse data/*.csv already on disk

Files
  data/master_weekly.csv, data/master_dictionary.csv   written by features_extract.py
  data_seb/labels_valais_weekly.csv                    labels (needed by --train only)
  models/et_bundle.pkl                              trained ETs + their column lists
  predictions/et_predictions.csv                       prediction log (one row per run/horizon)
"""
import argparse
import pickle
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_absolute_error, r2_score

warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================================
# CONFIG (copied from the notebook)
# ============================================================================
DATA_DIR = Path("data")
MASTER_CSV = DATA_DIR / "master_weekly.csv"
DICT_CSV = DATA_DIR / "master_dictionary.csv"
LABELS_CSV = Path("data_seb/labels_valais_weekly.csv")
MODEL_PATH = Path("models/et_bundle.pkl")
PRED_PATH = Path("predictions/et_predictions.csv")

MAX_FEAT_CORR = 0.95
MIN_TARGET_CORR = 0.05
N_PRED, N_TEST, N_VAL = 26, 52, 52
DATE_COLS = ["month", "quarter"]
N_HARM = 3
MAX_STALE_WEEKS = 4          # a missing base feature may be carried forward at most this long

horizons = {
    "2w":  {"y": "y_vs_chg_2w",  "freqs": ["hebdo", "journalier", "calendrier"]},
    "4w":  {"y": "y_vs_chg_4w",  "freqs": ["hebdo", "journalier", "calendrier"]},
    "8w":  {"y": "y_vs_chg_8w",  "freqs": ["hebdo", "journalier", "calendrier", "mensuel"]},
    "13w": {"y": "y_vs_chg_13w", "freqs": ["hebdo", "journalier", "calendrier", "mensuel"]},
}
TARGET_COLS = [c["y"] for c in horizons.values()]

# Best ET hyper-parameters found in the notebook (validation grid search)
ET_PARAMS = {
    "2w":  dict(n_estimators=300, max_depth=None, min_samples_leaf=10, max_features=0.3),
    "4w":  dict(n_estimators=300, max_depth=None, min_samples_leaf=5,  max_features=1.0),
    "8w":  dict(n_estimators=300, max_depth=None, min_samples_leaf=5,  max_features=0.6),
    "13w": dict(n_estimators=300, max_depth=None, min_samples_leaf=5,  max_features=1.0),
}


# ============================================================================
# HELPERS
# ============================================================================
def week_index(s):
    """Any date -> Monday of its week (same as the notebook)."""
    s = pd.to_datetime(pd.Series(s).astype(str).str[:10])
    return pd.DatetimeIndex(s.dt.to_period("W-SUN").dt.start_time, name="date")


def directional_accuracy(y_true, y_pred, tol=0.0):
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    mask = np.abs(y_true) > tol
    return float(np.mean(np.sign(y_true[mask]) == np.sign(y_pred[mask]))) if mask.any() else np.nan


def last_complete_monday(today=None):
    today = pd.Timestamp(today or pd.Timestamp.today()).normalize()
    return today - pd.Timedelta(days=today.dayofweek) - pd.Timedelta(weeks=1)


def load_master(path=MASTER_CSV):
    m = pd.read_csv(path)
    m.index = week_index(m["date"])
    m = m.drop(columns="date")
    m = m[~m.index.duplicated()].sort_index()
    return m.reindex(pd.date_range(m.index.min(), m.index.max(), freq="W-MON", name="date"))


def calendar_columns(feat, df_dict):
    cols = [c for c in df_dict.loc[df_dict["native_frequency"] == "calendrier", "column"]
            if c in feat.columns and c not in DATE_COLS and c not in ("iso_year", "iso_week")]
    if not cols:
        cols = [c for c in feat.columns if any(k in c for k in ("holiday", "working_days", "closure"))]
    return cols


def build_features(master, df_dict, future_calendar=None):
    """Master -> feature frame with harmonics and target-week calendar features.

    future_calendar : optional frame (Monday index) holding the calendar columns for
                      weeks after the master's last week; needed for prediction because
                      <cal>__t{h} looks h weeks ahead.
    """
    feat = master.copy()
    cal_cols = calendar_columns(feat, df_dict)
    if future_calendar is not None:
        fut = future_calendar.loc[future_calendar.index > feat.index.max(), cal_cols]
        feat = pd.concat([feat, fut])
        feat.index.name = "date"

    woy = feat.index.isocalendar().week.astype(float).values
    harm_cols = []
    for k in range(1, N_HARM + 1):
        feat[f"harm_sin{k}"] = np.sin(2 * np.pi * k * woy / 52.18)
        feat[f"harm_cos{k}"] = np.cos(2 * np.pi * k * woy / 52.18)
        harm_cols += [f"harm_sin{k}", f"harm_cos{k}"]

    tw_cols = {}
    for name in horizons:
        h = int(name[:-1])
        tw_cols[name] = []
        for c in cal_cols:
            col = f"{c}__t{h}"
            feat[col] = feat[c].shift(-h)
            tw_cols[name].append(col)
    return feat, cal_cols, harm_cols, tw_cols


# ============================================================================
# TRAIN
# ============================================================================
def train(labels_path, fit_on):
    master, df_dict = load_master(), pd.read_csv(DICT_CSV)
    labels = pd.read_csv(labels_path)
    labels.index = week_index(labels["date"])
    labels = labels.drop(columns="date")
    labels = labels[~labels.index.duplicated()]
    missing = [c for c in TARGET_COLS if c not in labels.columns]
    if missing:
        sys.exit(f"Labels file is missing columns: {missing}")

    feat, cal_cols, harm_cols, tw_cols = build_features(master, df_dict)
    data = feat.join(labels, how="inner")

    # same chronological split as the notebook
    n = len(data)
    i_val, i_test, i_fut = n - (N_PRED + N_TEST + N_VAL), n - (N_PRED + N_TEST), n - N_PRED
    tr_idx, va_idx, te_idx = data.index[:i_val], data.index[i_val:i_test], data.index[i_test:i_fut]
    print(f"rows: {n} | train {len(tr_idx)}  val {len(va_idx)}  test {len(te_idx)}  "
          f"| last labelled week {data.index.max().date()}")

    # correlation filter, computed on the train split only (as in the notebook)
    derived = set(harm_cols) | {c for v in tw_cols.values() for c in v}
    feature_cols = [c for c in feat.select_dtypes("number").columns
                    if c not in TARGET_COLS and c not in DATE_COLS
                    and c not in labels.columns and c not in derived]
    train_df = data.loc[tr_idx]
    relevance = (train_df[feature_cols + TARGET_COLS].corr().abs()
                 .loc[feature_cols, TARGET_COLS].mean(axis=1).sort_values(ascending=False))
    feat_corr = train_df[feature_cols].corr().abs()
    kept = []
    for col, rel in relevance.items():
        if np.isnan(rel) or rel < MIN_TARGET_CORR:
            continue
        if kept and feat_corr.loc[col, kept].max() > MAX_FEAT_CORR:
            continue
        kept.append(col)
    print(f"features: {len(feature_cols)} -> kept {len(kept)}")

    bundle = {"models": {}, "kept": kept, "fit_on": fit_on,
              "trained_at": datetime.now().isoformat(timespec="seconds"),
              "last_labelled_week": str(data.index.max().date())}
    report = []
    for name, cfg in horizons.items():
        y = cfg["y"]
        cols_x = [c for c in df_dict.loc[df_dict["native_frequency"].isin(cfg["freqs"]), "column"]
                  if c in kept] + harm_cols + tw_cols[name]
        sel = cols_x + [y]
        tr, va, te = (data.loc[i, sel].dropna() for i in (tr_idx, va_idx, te_idx))

        # sanity check = notebook protocol: fit on train+val, score on the test year
        chk = ExtraTreesRegressor(random_state=42, n_jobs=-1, **ET_PARAMS[name])
        tv = pd.concat([tr, va])
        chk.fit(tv[cols_x], tv[y])
        p = chk.predict(te[cols_x])
        report.append({"horizon": name, "test_R2": r2_score(te[y], p),
                       "test_MAE": mean_absolute_error(te[y], p),
                       "test_dir_acc": directional_accuracy(te[y], p), "n_features": len(cols_x)})

        fit_df = tv if fit_on == "train_val" else data[sel].dropna()
        model = ExtraTreesRegressor(random_state=42, n_jobs=-1, **ET_PARAMS[name])
        model.fit(fit_df[cols_x], fit_df[y])
        bundle["models"][name] = {"model": model, "cols_x": cols_x, "target": y,
                                  "n_fit": len(fit_df)}
        print(f"  {name:>3}: ET fitted on {len(fit_df)} rows ({fit_on})")

    print("\nTest-year check (notebook protocol; the notebook shows ET R2 ~ "
          "0.22 / 0.41 / 0.54 / 0.35 / -0.20):")
    print(pd.DataFrame(report).set_index("horizon").round(3).to_string())
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    print(f"\nSaved {MODEL_PATH}")


# ============================================================================
# PREDICT
# ============================================================================
def refresh_data(fetch):
    """Download (optional) and rebuild the master. Returns (calendar frame incl. future weeks, failures)."""
    try:
        import features_extract as fe
    except ImportError:
        sys.exit("features_extract.py must sit next to predict_et.py")
    fe.FUTURE_WEEKS = max(int(h[:-1]) for h in horizons) + 2   # calendar must cover the 26w horizon
    if fetch:
        fe.fetch_all()
    fe.build_master()          # writes data/master_weekly.csv + dictionary, leaves fe.M in memory
    fails = [l for l in fe.LOG if l.startswith(("FAIL", "BUILD FAIL"))]
    return fe.M.copy(), fails


def predict(fetch):
    if not MODEL_PATH.exists():
        sys.exit(f"{MODEL_PATH} not found - run:  python predict_et.py --train")
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    m_full, fails = refresh_data(fetch)
    master, df_dict = load_master(), pd.read_csv(DICT_CSV)
    feat, cal_cols, _, _ = build_features(master, df_dict, future_calendar=m_full)

    week = master.index.max()
    expected = last_complete_monday()
    print(f"\nFeature week: {week.date()} (Mon-Sun), expected last complete week: {expected.date()}")
    if week < expected:
        print("  WARNING: the master is older than the last complete week - check the FAIL lines below.")

    rows = []
    for name, spec in bundle["models"].items():
        h, cols_x, model = int(name[:-1]), spec["cols_x"], spec["model"]
        x = feat.loc[week, cols_x].astype(float).copy()

        # base features missing for that week (late publication): carry the last value, up to MAX_STALE_WEEKS
        for c in x.index[x.isna()]:
            if "__t" in c:
                continue
            hist = feat[c].loc[:week].dropna()
            if len(hist) and (week - hist.index[-1]) <= pd.Timedelta(weeks=MAX_STALE_WEEKS):
                x[c] = hist.iloc[-1]
                print(f"  note [{name}] {c}: missing for {week.date()}, using {hist.index[-1].date()}")
        if x.isna().any():
            print(f"  SKIP  [{name}] still missing: {list(x.index[x.isna()])}")
            continue

        X = x.to_numpy(dtype=np.float32).reshape(1, -1)
        rows.append({"run_at": datetime.now().isoformat(timespec="seconds"),
                     "feature_week": week.date(), "horizon": name,
                     "horizon_end_week": (week + pd.Timedelta(weeks=h)).date(),
                     "target": spec["target"], "prediction": float(model.predict(X)[0])})

    if not rows:
        sys.exit("No prediction could be made.")
    out = pd.DataFrame(rows)
    print("\nET predictions:")
    print(out.drop(columns="run_at").round(4).to_string(index=False))

    PRED_PATH.parent.mkdir(parents=True, exist_ok=True)
    if PRED_PATH.exists():
        old = pd.read_csv(PRED_PATH)
        old = old[~((old["feature_week"].astype(str) == str(week.date()))
                    & old["horizon"].isin(out["horizon"]))]
        out = pd.concat([old, out], ignore_index=True)
    out.to_csv(PRED_PATH, index=False)
    print(f"\nAppended to {PRED_PATH}")
    if fails:
        print("\nFetch/build problems (those features may be stale):")
        for l in fails:
            print("  ", l)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train", action="store_true", help="(re)train the ET models and save them")
    ap.add_argument("--no-fetch", action="store_true", help="do not download, rebuild from data/*.csv")
    ap.add_argument("--labels", default=str(LABELS_CSV), help="labels CSV (for --train)")
    ap.add_argument("--fit-on", choices=["all", "train_val"], default="all",
                    help="--train: 'all' = every labelled week (default, best for production); "
                         "'train_val' = same as the notebook (test year held out)")
    a = ap.parse_args()
    if a.train:
        train(a.labels, a.fit_on)
    else:
        predict(fetch=not a.no_fetch)