#!/usr/bin/env python3
"""
Download official BFS/OFS BESTA tables (quarterly) through the PxWeb API.

    uv run scripts/bfs.py            # downloads the 3 tables below into scripts/data/
    uv run scripts/bfs.py --raw      # also keeps the raw json-stat answers

Tables (variable codes checked against the API metadata on 2026-10-03):
  px-x-0602000000_103  job vacancies (count) by NOGA division, 1992Q2 -> latest
  px-x-0602000000_104  job vacancies (count) by large region, 1997Q1 -> latest
  px-x-0602000000_101  employment by NOGA division incl. 78 (temp agencies), 1991Q3 -> latest
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

import pandas as pd
import requests

BASE = "https://www.pxweb.bfs.admin.ch/api/v1/de/{0}/{0}.px"
OUT = Path(__file__).resolve().parent / "data"
ALL = {"filter": "all", "values": ["*"]}


def item(code, values):
    return {"code": code, "selection": values if isinstance(values, dict) else {"filter": "item", "values": values}}


TABLES = {
    "bfs_vacancies_division": ("px-x-0602000000_103", [
        item("Offene Stellen", ["1"]),            # 1 = count ("Offene Stellen - Total")
        item("Wirtschaftsabteilung", ALL),
        item("Quartal", ALL),
    ]),
    "bfs_vacancies_region": ("px-x-0602000000_104", [
        item("Offene Stellen", ["1"]),
        item("Grossregion", ALL),
        item("Quartal", ALL),
    ]),
    "bfs_employment_division": ("px-x-0602000000_101", [
        item("Wirtschaftsabteilung", ["5-96", "10-33", "41-43", "41-42", "43", "49-53", "49", "52", "53", "78"]),
        item("Beschäftigungsgrad", ["TOT", "3"]),  # total, total seasonally adjusted
        item("Geschlecht", ["TOT"]),
        item("Quartal", ALL),
    ]),
}


def jsonstat_to_df(js):
    """Flatten a json-stat (v1 or v2) answer into a tidy DataFrame with code and label columns."""
    if "dataset" in js:                         # json-stat v1 wrapper
        js = js["dataset"]
        ids, sizes = js["dimension"]["id"], js["dimension"]["size"]
    else:
        ids, sizes = js["id"], js["size"]
    dims = js["dimension"]
    codes, labels = [], []
    for d in ids:
        cat = dims[d]["category"]
        idx = cat.get("index")
        if isinstance(idx, dict):
            order = sorted(idx, key=idx.get)
        elif isinstance(idx, list):
            order = idx
        else:
            order = list(cat["label"].keys())
        codes.append(order)
        labels.append([cat.get("label", {}).get(c, c) for c in order])
    assert [len(c) for c in codes] == list(sizes), "json-stat sizes do not match categories"

    vals = js["value"]
    n = 1
    for s in sizes:
        n *= s
    if isinstance(vals, dict):                  # sparse form {"position": value}
        vals = [vals.get(str(i)) for i in range(n)]

    rows = []
    for pos, combo in enumerate(itertools.product(*[range(s) for s in sizes])):
        row = {}
        for d, k, c, l in zip(ids, combo, codes, labels):
            row[d] = c[k]
            row[d + "_label"] = l[k]
        row["value"] = vals[pos]
        rows.append(row)
    return pd.DataFrame(rows)


def download(name, table, query, raw=False):
    url = BASE.format(table)
    r = requests.post(url, json={"query": query, "response": {"format": "json-stat2"}}, timeout=120)
    if r.status_code != 200:
        r = requests.post(url, json={"query": query, "response": {"format": "json-stat"}}, timeout=120)
    if r.status_code != 200:
        print(f"  {name}: HTTP {r.status_code}: {r.text[:300]}")
        return None
    js = r.json()
    if raw:
        (OUT / f"raw_{name}.json").write_text(json.dumps(js))
    df = jsonstat_to_df(js)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df.to_csv(OUT / f"{name}.csv", index=False)
    q = df["Quartal"]
    print(f"  {name}: {len(df)} rows, {q.min()} -> {q.max()}  -> data/{name}.csv")
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    ok = [download(n, t, q, a.raw) is not None for n, (t, q) in TABLES.items()]
    if not all(ok):
        sys.exit("Some tables failed; send me the HTTP message above.")


if __name__ == "__main__":
    main()
