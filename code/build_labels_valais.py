#!/usr/bin/env python3
"""
Valais-focused label table, aligned with data/master_weekly.csv (one row per ISO week, date = Monday).

    uv run code/build_labels_valais.py

Input : data_seb/jobtracker_long.csv  (Swiss Job Tracker, weekly, Friday dates, index Jan 2020 = 100)
Output: data/labels_valais_weekly.csv

Series kept (there is no "construction in Valais" series: each Job Tracker series splits by ONE dimension):
  vs    canton.vs  all job ads in Valais                  -> main regional label
  f     noga.f     construction, Switzerland
  c     noga.c     manufacturing, Switzerland
  h     noga.h     transport & storage, Switzerland
  isco7 isco.7     craft trades (masons, electricians, welders...), Switzerland
  isco8 isco.8     machine operators & drivers, Switzerland
  isco9 isco.9     elementary occupations (labourers, warehouse), Switzerland

Columns per series s:
  jt_<s>              index level
  jt_<s>_sa           index / average of the same ISO week in 2018-2023 (seasonal baseline,
                      built only on years before the test period) -> 1.10 = 10% above a normal week
  y_<s>_chg_<h>w      future % change of the index, h weeks ahead (TARGET, raw)
  y_<s>_sa_chg_<h>w   future change of the seasonally adjusted index (TARGET, "surprise" vs normal season)
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data_seb" / "jobtracker_long.csv"
OUT = ROOT / "data" / "labels_valais_weekly.csv"
SERIES = {"vs": "canton.vs", "f": "noga.f", "c": "noga.c", "h": "noga.h",
          "isco7": "isco.7", "isco8": "isco.8", "isco9": "isco.9"}
HORIZONS = [2, 4, 8, 13, 26]
BASELINE_END = "2023-12-31"

df = pd.read_csv(SRC, parse_dates=["date"])
df["series"] = df["key"].str.replace("ch.kof.jobtracker.", "", regex=False).str.replace(".clean.idx", "", regex=False)
df = df[df["series"].isin(SERIES.values())]
wide = df.pivot_table(index="date", columns="series", values="value")
wide = wide.interpolate(limit=4, limit_area="inside")           # fill short gaps only
wide.index = wide.index - pd.to_timedelta(wide.index.weekday, unit="D")  # Friday -> Monday of the ISO week
wide.index.name = "date"

out = pd.DataFrame(index=wide.index)
iso_week = wide.index.isocalendar().week.astype(int).values
for short, s in SERIES.items():
    x = wide[s]
    base = x[x.index <= BASELINE_END].groupby(iso_week[x.index <= BASELINE_END]).mean()
    sa = x / pd.Series(iso_week, index=x.index).map(base)
    out[f"jt_{short}"] = x
    out[f"jt_{short}_sa"] = sa
    for h in HORIZONS:
        out[f"y_{short}_chg_{h}w"] = x.shift(-h) / x - 1
        out[f"y_{short}_sa_chg_{h}w"] = sa.shift(-h) - sa

out = out.reset_index()
OUT.parent.mkdir(exist_ok=True)
out.round(5).to_csv(OUT, index=False)
print(f"{OUT.relative_to(ROOT)}: {out.shape[0]} weeks x {out.shape[1]} columns, "
      f"{out['date'].min().date()} -> {out['date'].max().date()}")
