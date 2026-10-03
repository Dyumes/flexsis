#!/usr/bin/env python3
"""
Swiss Job Tracker (KOF ETH / x28) downloader.

Usage:
    python jobtracker.py keys                       # list available series keys (saved to data/jobtracker_keys.csv)
    python jobtracker.py keys --grep vs             # filter the key list (case-insensitive substring)
    python jobtracker.py fetch                      # download the national total index
    python jobtracker.py fetch --grep canton        # download every key matching a pattern
    python jobtracker.py fetch --keys K1 K2 ...     # download specific keys
    python jobtracker.py fetch --raw                # also dump the raw API answer, for debugging
    python jobtracker.py probe                      # discover canton/occupation/sector keys by trial
                                                    # (use when 'keys' fails; saves data/jobtracker_keys.csv)

Output: data/jobtracker_long.csv (key, date, value) and data/jobtracker_wide.csv (date x key).
Needs: pip install requests pandas
"""
import argparse
import io
import json
import sys
from pathlib import Path

import pandas as pd
import requests

TS_URL = "https://tsdb-api.kof.ethz.ch/v2/ts"
# Metadata endpoint found via search on the older KOF Datenservice API.
META_URLS = [
    "https://datenservice.kof.ethz.ch/api/v1/public/metadata/collections/ch.kof.jobtracker?mime=csv",
    "https://datenservice.kof.ethz.ch/api/v1/public/collections/ch.kof.jobtracker?mime=csv",
]
TOTAL_KEY = "ch.kof.jobtracker.total.total.clean.idx"  # documented on the KOF page
OUT = Path(__file__).resolve().parent / "data"
CHUNK = 20  # keys per request, keeps URLs short


def get(url, params=None):
    r = requests.get(url, params=params, timeout=60, headers={"User-Agent": "flexsis-hackathon/0.1"})
    r.raise_for_status()
    return r


# ---------------------------------------------------------------- probe
CANTONS = ["ag", "ai", "ar", "be", "bl", "bs", "fr", "ge", "gl", "gr", "ju", "lu", "ne", "nw",
           "ow", "sg", "sh", "so", "sz", "tg", "ti", "ur", "vd", "vs", "zg", "zh"]
ISCO = [str(i) for i in range(10)]
NOGA = list("abcdefghijklmnopqrstu")
# Dimension names to try for each family. The total key is ch.kof.jobtracker.total.total.clean.idx,
# so a key is assumed to be ch.kof.jobtracker.<slot1>.<slot2>.clean.idx
DIMS = {
    "canton": (["canton", "kanton", "ct", "region"], CANTONS),
    "occupation": (["isco", "occupation", "occ", "beruf"], ISCO + ["isco" + i for i in ISCO]),
    "sector": (["noga", "sector", "sec", "branche", "industry"], NOGA),
}


def candidates():
    seen = set()
    for fam, (names, values) in DIMS.items():
        for v in values:
            for v2 in {v, v.upper()}:
                pairs = [(v2, "total"), ("total", v2)] + [(n, v2) for n in names]
                for a, b in pairs:
                    k = f"ch.kof.jobtracker.{a}.{b}.clean.idx"
                    if k not in seen:
                        seen.add(k)
                        yield fam, k


def key_exists(key):
    try:
        r = requests.get(TS_URL, params={"keys": key, "mime": "json", "access_type": "public"},
                         timeout=30, headers={"User-Agent": "flexsis-hackathon/0.1"})
        if r.status_code != 200:
            return False
        df = parse_json(r.json(), [key])
        return _valid(df) and df["value"].notna().any()
    except Exception:
        return False


def probe(workers=8):
    from concurrent.futures import ThreadPoolExecutor
    cands = list(candidates())
    print(f"Probing {len(cands)} candidate keys against {TS_URL} ...")
    if not key_exists(TOTAL_KEY):
        sys.exit("Even the documented total key returned nothing: run 'fetch --raw' and check data/raw_0.json.")
    with ThreadPoolExecutor(workers) as ex:
        ok = list(ex.map(lambda c: key_exists(c[1]), cands))
    found = pd.DataFrame([c for c, good in zip(cands, ok) if good], columns=["family", "key"])
    OUT.mkdir(exist_ok=True)
    found.to_csv(OUT / "jobtracker_keys.csv", index=False)
    return found


# ---------------------------------------------------------------- keys
def list_keys(grep=None):
    last_err = None
    for url in META_URLS:
        try:
            r = get(url)
            df = pd.read_csv(io.StringIO(r.text))
            break
        except Exception as e:  # try next endpoint
            last_err = e
    else:
        sys.exit(f"Could not read the key list ({last_err}).\n"
                 f"Fallback: run 'fetch' with the documented total key {TOTAL_KEY}, "
                 "or look up keys in the dashboard https://swissjobtracker.ch")

    # Find the column that holds the series keys
    keycol = next((c for c in df.columns if c.lower() in ("ts_key", "key", "keys")), None)
    if keycol is None:
        keycol = next(c for c in df.columns
                      if df[c].astype(str).str.startswith("ch.kof.jobtracker").any())
    df = df.rename(columns={keycol: "key"})
    if grep:
        df = df[df["key"].str.contains(grep, case=False, na=False)]
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "jobtracker_keys.csv", index=False)
    return df


# ---------------------------------------------------------------- fetch
import re

DATE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?")
DATE_NAMES = ("date", "dates", "time", "period", "periods", "index", "x")
VALUE_NAMES = ("value", "values", "y", "obs", "observations")


def _is_date(s):
    return isinstance(s, str) and bool(DATE_RE.match(s))


def _series_in(obj):
    """Return a list of (dates, values) pairs found directly in obj, or None."""
    if isinstance(obj, dict):
        dk = next((k for k in obj if k.lower() in DATE_NAMES and isinstance(obj[k], list)), None)
        vk = next((k for k in obj if k.lower() in VALUE_NAMES and isinstance(obj[k], list)), None)
        if dk and vk and len(obj[dk]) == len(obj[vk]):                 # {date: [...], value: [...]}
            return list(obj[dk]), list(obj[vk])
        if obj and all(_is_date(k) for k in obj):                        # {"2020-01-06": 100, ...}
            return list(obj.keys()), list(obj.values())
    if isinstance(obj, list) and obj:
        if all(isinstance(p, dict) for p in obj):                        # [{date, value}, ...]
            dk = next((k for k in obj[0] if k.lower() in DATE_NAMES), None)
            vk = next((k for k in obj[0] if k.lower() in VALUE_NAMES), None)
            if dk and vk and not isinstance(obj[0][dk], (list, dict)):
                return [p.get(dk) for p in obj], [p.get(vk) for p in obj]
        if all(isinstance(p, (list, tuple)) and len(p) == 2 and _is_date(p[0]) for p in obj):
            return [p[0] for p in obj], [p[1] for p in obj]              # [[date, value], ...]
    return None


def _key_in(obj):
    """Find a string that looks like a KOF series key inside obj (shallow)."""
    if isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, str) and v.startswith("ch.kof."):
                return v
    return None


def parse_json(payload, requested=()):
    """Walk any JSON shape and collect every (key, date, value) series it contains."""
    rows = []

    def walk(obj, key):
        key = _key_in(obj) or key
        found = _series_in(obj)
        if found:
            rows.extend((key, d, v) for d, v in zip(*found))
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, k if isinstance(k, str) and k.startswith("ch.kof.") else key)
        elif isinstance(obj, list):
            for v in obj:
                walk(v, key)

    walk(payload, requested[0] if len(requested) == 1 else None)
    return pd.DataFrame(rows, columns=["key", "date", "value"])


def _skeleton(obj, depth=0):
    """Short description of a JSON structure, printed when parsing fails."""
    pad = "  " * depth
    if depth > 3:
        return pad + "..."
    if isinstance(obj, dict):
        lines = [f"{pad}dict with {len(obj)} keys"]
        for k in list(obj)[:6]:
            lines.append(f"{pad}  {k!r}:")
            lines.append(_skeleton(obj[k], depth + 2))
        return "\n".join(lines)
    if isinstance(obj, list):
        return f"{pad}list of {len(obj)}" + ("\n" + _skeleton(obj[0], depth + 1) if obj else "")
    return f"{pad}{type(obj).__name__}: {str(obj)[:60]!r}"


def _valid(df):
    if df.empty:
        return False
    d = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    return d.notna().mean() > 0.9


def fetch(keys, raw=False):
    frames = []
    OUT.mkdir(exist_ok=True)
    for i in range(0, len(keys), CHUNK):
        chunk = keys[i:i + CHUNK]
        params = {"keys": ",".join(chunk), "mime": "json", "access_type": "public"}
        r = get(TS_URL, params)
        raw_path = OUT / f"raw_{i // CHUNK}.json"
        if raw:
            raw_path.write_bytes(r.content)
        try:
            payload = r.json()
            df = parse_json(payload, chunk)
        except ValueError:
            payload, df = None, pd.DataFrame()
        if not _valid(df):  # fall back to CSV
            rc = get(TS_URL, {**params, "mime": "csv"})
            try:
                c = pd.read_csv(io.StringIO(rc.text))
                if {"key", "date", "value"} <= set(c.columns):
                    df = c[["key", "date", "value"]]
                else:
                    c = c.rename(columns={c.columns[0]: "date"})
                    df = c.melt(id_vars="date", var_name="key", value_name="value")
            except Exception:
                df = pd.DataFrame(columns=["key", "date", "value"])
        if not _valid(df):
            raw_path.write_bytes(r.content)
            (OUT / f"raw_{i // CHUNK}.csv").write_text(rc.text)
            print(f"  Could not parse the answer for {chunk[:3]}... Saved {raw_path.name} and raw_{i // CHUNK}.csv")
            if payload is not None:
                print(_skeleton(payload))
            continue
        frames.append(df)
        print(f"  got {df['key'].nunique()} series, {len(df)} rows")
    if not frames:
        sys.exit("Nothing parsed. Send the structure printed above (or the first lines of the raw files).")
    long = pd.concat(frames, ignore_index=True)
    long["date"] = pd.to_datetime(long["date"], errors="coerce", format="mixed")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["date"]).sort_values(["key", "date"])
    long.to_csv(OUT / "jobtracker_long.csv", index=False)
    long.pivot_table(index="date", columns="key", values="value").to_csv(OUT / "jobtracker_wide.csv")
    return long


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("keys");  k.add_argument("--grep")
    f = sub.add_parser("fetch"); f.add_argument("--keys", nargs="+"); f.add_argument("--grep")
    f.add_argument("--raw", action="store_true")
    sub.add_parser("probe")
    a = ap.parse_args()

    if a.cmd == "probe":
        found = probe()
        if found.empty:
            print("No key pattern matched. Get real keys from the dashboard: open https://swissjobtracker.ch, "
                  "press F12 > Network, filter on 'tsdb-api', pick a canton or occupation, and copy the "
                  "'keys=' value of the request. Then run: fetch --keys <key>")
        else:
            print(found.groupby("family").size().to_string())
            print(found.head(20).to_string(index=False))
            print(f"\n{len(found)} keys saved to {OUT / 'jobtracker_keys.csv'}; "
                  "now run: fetch --grep <pattern> (reads that file)")
        return

    if a.cmd == "keys":
        df = list_keys(a.grep)
        print(df.head(50).to_string(index=False))
        print(f"\n{len(df)} keys, saved to {OUT / 'jobtracker_keys.csv'}")
        return

    if a.keys:
        keys = a.keys
    elif a.grep:
        kf = OUT / "jobtracker_keys.csv"  # written by 'probe' or 'keys'
        kdf = pd.read_csv(kf) if kf.exists() else list_keys()
        keys = kdf[kdf["key"].str.contains(a.grep, case=False, na=False)]["key"].tolist()
        if not keys:
            sys.exit(f"No key matches '{a.grep}' in {kf}")
    else:
        keys = [TOTAL_KEY]
    print(f"Fetching {len(keys)} series...")
    long = fetch(keys, a.raw)
    summary = long.groupby("key")["date"].agg(["min", "max", "count"])
    print(summary.to_string())
    print(f"\nSaved {OUT / 'jobtracker_long.csv'} and {OUT / 'jobtracker_wide.csv'}")


if __name__ == "__main__":
    main()
