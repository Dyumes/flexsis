#!/usr/bin/env python3
"""
Build ML labels from the downloaded data (no network needed).

    uv run scripts/build_labels.py

Inputs (in scripts/data/):
  jobtracker_long.csv          from jobtracker.py   (required)
  bfs_vacancies_division.csv   from bfs.py          (optional, enables vacancy counts)
  bfs_vacancies_region.csv     from bfs.py          (optional)
  bfs_employment_division.csv  from bfs.py          (optional)

Outputs (in scripts/data/):
  labels_weekly.csv     one row per (series, week): level, past changes and FUTURE targets
  labels_quarterly.csv  official quarterly counts (BESTA) + Job Tracker quarterly means, for validation
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
HORIZONS = [2, 4, 8, 13, 26]          # weeks ahead = 2 weeks to 6 months
CLASS_K = 0.5                         # up/down if future change beyond +-0.5 std of that series' changes
# Job Tracker sector -> BESTA division with official vacancy counts
NOGA_TO_BESTA = {"noga.c": "10-33", "noga.f": "41-43", "noga.h": "49-53"}
CANTON_TO_REGION = {
    "vd": "Region lémanique", "vs": "Region lémanique", "ge": "Region lémanique",
    "be": "Espace Mittelland", "fr": "Espace Mittelland", "so": "Espace Mittelland",
    "ne": "Espace Mittelland", "ju": "Espace Mittelland",
    "bs": "Nordwestschweiz", "bl": "Nordwestschweiz", "ag": "Nordwestschweiz",
    "zh": "Zürich",
    "gl": "Ostschweiz", "sh": "Ostschweiz", "ar": "Ostschweiz", "ai": "Ostschweiz",
    "sg": "Ostschweiz", "gr": "Ostschweiz", "tg": "Ostschweiz",
    "lu": "Zentralschweiz", "ur": "Zentralschweiz", "sz": "Zentralschweiz",
    "ow": "Zentralschweiz", "nw": "Zentralschweiz", "zg": "Zentralschweiz",
    "ti": "Ticino",
}
FOCUS = {"noga.c": "manufacturing", "noga.f": "construction", "noga.h": "transport & storage",
         "isco.7": "craft trades", "isco.8": "machine operators & drivers", "isco.9": "elementary occupations",
         "canton.vs": "Valais", "canton.vd": "Vaud", "canton.ge": "Geneva"}


# ------------------------------------------------------------------ weekly labels
def load_jobtracker():
    df = pd.read_csv(DATA / "jobtracker_long.csv", parse_dates=["date"])
    df["series"] = df["key"].str.replace("ch.kof.jobtracker.", "", regex=False).str.replace(".clean.idx", "", regex=False)
    df["family"] = df["series"].str.split(".").str[0].map({"canton": "canton", "isco": "occupation", "noga": "sector"})
    df["code"] = df["series"].str.split(".").str[1]
    df = df.sort_values(["series", "date"])
    # fill short gaps (max 4 weeks) and flag them
    df["imputed"] = df["value"].isna()
    df["index"] = df.groupby("series")["value"].transform(lambda s: s.interpolate(limit=4, limit_area="inside"))
    return df.drop(columns=["value", "key"])


def add_features_and_targets(df):
    g = df.groupby("series")["index"]
    # past information (usable as features or for "current state" dashboards)
    df["chg_4w"] = g.pct_change(4, fill_method=None)
    df["chg_13w"] = g.pct_change(13, fill_method=None)
    df["yoy"] = g.pct_change(52, fill_method=None)
    # seasonal deviation: index vs average of the same ISO week in the other years of that series
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    wk_mean = df.groupby(["series", "week"])["index"].transform("mean")
    df["seasonal_dev"] = df["index"] / wk_mean - 1
    # FUTURE targets: what the model has to predict
    for h in HORIZONS:
        fut = g.shift(-h)
        df[f"y_chg_{h}w"] = fut / df["index"] - 1
        sd = df.groupby("series")[f"y_chg_{h}w"].transform("std")
        df[f"y_class_{h}w"] = np.select(
            [df[f"y_chg_{h}w"] > CLASS_K * sd, df[f"y_chg_{h}w"] < -CLASS_K * sd],
            ["up", "down"], default="flat")
        df.loc[df[f"y_chg_{h}w"].isna(), f"y_class_{h}w"] = None
    return df


# ------------------------------------------------------------------ official counts (BESTA)
def load_bfs(name):
    p = DATA / f"{name}.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df["quarter"] = pd.PeriodIndex(df["Quartal"].str.replace("Q", "-Q"), freq="Q")
    return df


def calibrate_counts(weekly, vac_div):
    """Turn sector indices into estimated vacancy COUNTS using official quarterly BESTA counts.
    ratio(q) = BESTA vacancies(q) / mean Job Tracker index(q); interpolated weekly; last ratio carried forward."""
    weekly["est_vacancies"] = np.nan
    if vac_div is None:
        return weekly
    for series, div in NOGA_TO_BESTA.items():
        b = vac_div[vac_div["Wirtschaftsabteilung"] == div].set_index("quarter")["value"]
        m = weekly["series"] == series
        w = weekly.loc[m, ["date", "index"]].copy()
        w["quarter"] = w["date"].dt.to_period("Q")
        qmean = w.groupby("quarter")["index"].mean()
        ratio = (b / qmean).dropna()
        if ratio.empty:
            continue
        # place each quarterly ratio at the quarter midpoint, interpolate in between
        mid = ratio.index.to_timestamp(how="start") + pd.Timedelta(days=45)
        r = pd.Series(ratio.values, index=mid)
        r = r.reindex(r.index.union(w["date"])).interpolate(method="time").ffill().bfill()
        weekly.loc[m, "est_vacancies"] = w["index"].values * r.reindex(w["date"]).values
    return weekly


def quarterly_table(weekly, vac_div, vac_reg, emp):
    q = weekly.assign(quarter=weekly["date"].dt.to_period("Q")).groupby(["series", "quarter"])["index"].mean()
    q = q.unstack("series")
    q.columns = [f"jt_{c}" for c in q.columns]
    out = [q]
    if vac_div is not None:
        v = vac_div.pivot_table(index="quarter", columns="Wirtschaftsabteilung", values="value")
        out.append(v.add_prefix("besta_vacancies_"))
    if vac_reg is not None:
        v = vac_reg.pivot_table(index="quarter", columns="Grossregion_label", values="value")
        out.append(v.add_prefix("besta_vacancies_region_"))
    if emp is not None:
        e = emp[emp["Beschäftigungsgrad"] == "3"]  # seasonally adjusted total
        if e.empty:
            e = emp[emp["Beschäftigungsgrad"] == "TOT"]
        v = e.pivot_table(index="quarter", columns="Wirtschaftsabteilung", values="value")
        out.append(v.add_prefix("besta_employment_"))
    t = pd.concat(out, axis=1).sort_index()
    t.index = t.index.astype(str)
    return t


def main():
    weekly = add_features_and_targets(load_jobtracker())
    vac_div, vac_reg, emp = (load_bfs(n) for n in
                             ["bfs_vacancies_division", "bfs_vacancies_region", "bfs_employment_division"])
    weekly = calibrate_counts(weekly, vac_div)
    weekly["region"] = np.where(weekly["family"] == "canton", weekly["code"].map(CANTON_TO_REGION), None)
    weekly["focus"] = weekly["series"].map(FOCUS)

    cols = ["date", "series", "family", "code", "focus", "region", "index", "imputed", "est_vacancies",
            "chg_4w", "chg_13w", "yoy", "seasonal_dev"] + \
           [c for h in HORIZONS for c in (f"y_chg_{h}w", f"y_class_{h}w")]
    weekly[cols].to_csv(DATA / "labels_weekly.csv", index=False)

    quarterly = quarterly_table(weekly, vac_div, vac_reg, emp)
    quarterly.to_csv(DATA / "labels_quarterly.csv")

    # ---- report
    print(f"labels_weekly.csv: {len(weekly)} rows, {weekly['series'].nunique()} series, "
          f"{weekly['date'].min().date()} -> {weekly['date'].max().date()}")
    print(f"labels_quarterly.csv: {quarterly.shape[0]} quarters x {quarterly.shape[1]} columns")
    last = weekly[weekly["series"].isin(FOCUS)].groupby("series").tail(1)
    print("\nLatest week, focus series:")
    print(last[["series", "focus", "index", "yoy", "seasonal_dev", "est_vacancies"]].round(3).to_string(index=False))
    print("\nClass balance (13 weeks ahead):")
    print(weekly["y_class_13w"].value_counts(normalize=True).round(3).to_string())
    if vac_div is not None:
        print("\nValidation: correlation of Job Tracker quarterly mean vs official BESTA vacancies")
        for s, d in NOGA_TO_BESTA.items():
            a, b = f"jt_{s}", f"besta_vacancies_{d}"
            if a in quarterly and b in quarterly:
                c = quarterly[[a, b]].dropna()
                print(f"  {s} vs {d}: r = {c.corr().iloc[0, 1]:.2f} over {len(c)} quarters")
    else:
        print("\n(no BFS files yet: run scripts/bfs.py to add official vacancy counts)")


if __name__ == "__main__":
    main()
