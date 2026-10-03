#!/usr/bin/env python3
"""
Collect public procurement projects from simap.ch (construction) and aggregate them per canton and week.

    uv run scripts/simap.py search                       # VS, VD, GE construction projects since 2018
    uv run scripts/simap.py search --cantons all         # all 26 cantons
    uv run scripts/simap.py search --from 2024-01-01     # shorter period
    uv run scripts/simap.py details                      # add award values (CHF) for awarded projects (slow, cached)
    uv run scripts/simap.py weekly                       # build data/simap_weekly.csv for the model

Outputs in scripts/data/:
  simap_projects.csv   one row per project (its newest publication): type, date, canton, city, title ...
  simap_awards.csv     award details per publication: award date, number of offers, vendors, price CHF, CPV
  simap_weekly.csv     week (Friday, aligned with the Job Tracker) x canton: counts of tenders / awards, CHF awarded

API endpoints come from the open source simap MCP server (github.com/Digilac/simap-mcp):
  GET https://www.simap.ch/api/publications/v2/project/project-search
  GET https://www.simap.ch/api/publications/v1/project/{projectId}/publication-details/{publicationId}
Public, read-only, no key. Rate limit kept at <= 1 request per second.
"""
import argparse
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

API = "https://www.simap.ch/api"
SEARCH = API + "/publications/v2/project/project-search"
DETAILS = API + "/publications/v1/project/{pid}/publication-details/{pubid}"
OUT = Path(__file__).resolve().parent / "data"
CACHE = OUT / "simap_cache"
ALL_CANTONS = ["AG", "AI", "AR", "BE", "BL", "BS", "FR", "GE", "GL", "GR", "JU", "LU", "NE", "NW",
               "OW", "SG", "SH", "SO", "SZ", "TG", "TI", "UR", "VD", "VS", "ZG", "ZH"]
AWARD_TYPES = {"award", "award_tender", "award_study_contract", "award_competition", "direct_award"}
TENDER_TYPES = {"tender", "advance_notice", "competition", "study_contract",
                "participant_selection", "selective_offering_phase"}
PAUSE = 1.05  # seconds between requests


# ------------------------------------------------------------------ http
class Client:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({
            "Accept": "application/json",
            "Accept-Language": "fr-CH,fr;q=0.9,de;q=0.8,en;q=0.7",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) flexsis-hackathon/0.1",
        })
        self.last = 0.0
        self.warmed = False

    def warm_up(self):
        """simap.ch shows a cookie check to clients without a session cookie: collect it once."""
        try:
            self.s.get("https://www.simap.ch/", headers={"Accept": "text/html"}, timeout=30)
        except requests.RequestException:
            pass
        self.warmed = True

    def get(self, url, params=None):
        for attempt in range(4):
            wait = PAUSE - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            r = self.s.get(url, params=params, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(5 * (attempt + 1))
                continue
            try:
                return r.json()
            except ValueError:
                # HTML answer = cookie wall: get the cookie and retry
                if not self.warmed or attempt == 0:
                    self.warm_up()
                    continue
                sys.exit(f"simap.ch did not return JSON (HTTP {r.status_code}). Start of answer:\n{r.text[:400]}")
        sys.exit(f"simap.ch kept failing for {url}")


def tr(x, lang=("fr", "de", "it", "en")):
    """Pick a translation from a {de, fr, it, en} dict."""
    if isinstance(x, dict):
        for l in lang:
            if x.get(l):
                return x[l]
        return None
    return x


# ------------------------------------------------------------------ search
def month_windows(start, end):
    d = start
    while d <= end:
        nxt = (d.replace(day=1) + timedelta(days=32)).replace(day=1)
        yield d, min(nxt - timedelta(days=1), end)
        d = nxt


def search(cli, cantons, start, end, subtypes):
    rows, seen = [], set()
    for a, b in month_windows(start, end):
        last_item, n_month = None, 0
        while True:
            params = [("newestPublicationFrom", a.isoformat()), ("newestPublicationUntil", b.isoformat())]
            params += [("orderAddressCantons", c) for c in cantons]
            params += [("projectSubTypes", t) for t in subtypes]
            if last_item:
                params.append(("lastItem", last_item))
            js = cli.get(SEARCH, params)
            projects = js.get("projects") or []
            for p in projects:
                if p["id"] in seen:
                    continue
                seen.add(p["id"])
                addr = p.get("orderAddress") or {}
                rows.append({
                    "project_id": p["id"],
                    "project_number": p.get("projectNumber"),
                    "title": tr(p.get("title")),
                    "project_type": p.get("projectType"),
                    "project_subtype": p.get("projectSubType"),
                    "process_type": p.get("processType"),
                    "pub_type": p.get("pubType"),
                    "publication_id": p.get("publicationId"),
                    "publication_date": p.get("publicationDate"),
                    "canton": addr.get("cantonId") or addr.get("canton"),
                    "city": tr(addr.get("city")),
                    "postal_code": addr.get("postalCode"),
                    "proc_office": tr(p.get("procOfficeName")),
                    "n_lots": len(p.get("lots") or []),
                    "lot_publications": json.dumps([l.get("publicationId") for l in (p.get("lots") or [])]),
                })
                n_month += 1
            nxt = (js.get("pagination") or {}).get("lastItem")
            if not projects or not nxt or nxt == last_item:
                break
            last_item = nxt
        print(f"  {a:%Y-%m}: {n_month} projects (total {len(rows)})")
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ details
def parse_details(js):
    dec = js.get("decision") or {}
    vendors = dec.get("vendors") or []
    prices = [((v.get("price") or {}).get("price")) for v in vendors]
    prices = [p for p in prices if isinstance(p, (int, float))]
    cpv = ((js.get("procurement") or {}).get("cpvCode") or (js.get("base") or {}).get("cpvCode") or {})
    return {
        "pub_type_detail": js.get("type"),
        "award_date": dec.get("awardDecisionDate"),
        "n_offers": dec.get("numberOfSubmissions"),
        "n_vendors": len(vendors),
        "vendors": "; ".join(v.get("vendorName") or "" for v in vendors),
        "price_chf": sum(prices) if prices else None,
        "cpv_code": cpv.get("code"),
        "cpv_label": tr(cpv.get("label")),
        "description": (tr((js.get("procurement") or {}).get("orderDescription")) or "")[:300],
    }


def details(cli, projects, only_awards=True):
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = projects[projects["pub_type"].isin(AWARD_TYPES)] if only_awards else projects
    rows = []
    print(f"Fetching details for {len(todo)} projects (cached in {CACHE.name}/, safe to stop and restart)")
    for i, p in enumerate(todo.itertuples(), 1):
        pubs = json.loads(p.lot_publications) if p.n_lots else []
        pubs = [x for x in pubs if x] or [p.publication_id]
        for pubid in pubs:
            f = CACHE / f"{p.project_id}_{pubid}.json"
            if f.exists():
                js = json.loads(f.read_text())
            else:
                js = cli.get(DETAILS.format(pid=p.project_id, pubid=pubid))
                f.write_text(json.dumps(js))
            rows.append({"project_id": p.project_id, "publication_id": pubid, **parse_details(js)})
        if i % 50 == 0:
            print(f"  {i}/{len(todo)}")
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ weekly aggregate
def weekly():
    pr = pd.read_csv(OUT / "simap_projects.csv")
    pr["date"] = pd.to_datetime(pr["publication_date"], errors="coerce", utc=True, format="mixed").dt.tz_localize(None)
    pr["kind"] = pr["pub_type"].map(lambda t: "award" if t in AWARD_TYPES else "tender" if t in TENDER_TYPES else "other")
    aw_path = OUT / "simap_awards.csv"
    if aw_path.exists() and aw_path.stat().st_size > 10:
        aw = pd.read_csv(aw_path).groupby("project_id")["price_chf"].sum(min_count=1)
        pr = pr.join(aw, on="project_id")
    else:
        pr["price_chf"] = None
    # week ending Friday, same convention as the Job Tracker dates
    pr["week"] = pr["date"].dt.to_period("W-FRI").dt.end_time.dt.normalize()
    pr["canton"] = pr["canton"].astype(str).str.lower()
    g = pr.groupby(["week", "canton", "kind"]).agg(n=("project_id", "count"), chf=("price_chf", "sum"))
    w = g.unstack("kind").fillna(0)
    w.columns = [f"simap_{k}_{m}" for m, k in w.columns]
    w = w.reset_index().rename(columns={"week": "date"})
    w.to_csv(OUT / "simap_weekly.csv", index=False)
    print(f"simap_weekly.csv: {len(w)} rows, {w['date'].min().date()} -> {w['date'].max().date()}")
    print(w.groupby("canton").sum(numeric_only=True).round(0).to_string())


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("--cantons", nargs="+", default=["VS", "VD", "GE"])
    s.add_argument("--from", dest="start", default="2018-01-01")
    s.add_argument("--until", dest="end", default=date.today().isoformat())
    s.add_argument("--subtypes", nargs="+", default=["construction"])
    d = sub.add_parser("details")
    d.add_argument("--all", action="store_true", help="also fetch details for non-award publications")
    sub.add_parser("weekly")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    if a.cmd == "search":
        cantons = ALL_CANTONS if a.cantons == ["all"] else [c.upper() for c in a.cantons]
        df = search(Client(), cantons, date.fromisoformat(a.start), date.fromisoformat(a.end), a.subtypes)
        df.to_csv(OUT / "simap_projects.csv", index=False)
        print(f"\nsimap_projects.csv: {len(df)} projects")
        if len(df):
            print(df["pub_type"].value_counts().to_string())
            print("first publication date:", df["publication_date"].min())
    elif a.cmd == "details":
        pr = pd.read_csv(OUT / "simap_projects.csv")
        df = details(Client(), pr, only_awards=not a.all)
        if df.empty:
            sys.exit("No award publications found in simap_projects.csv (check the pub_type values).")
        df.to_csv(OUT / "simap_awards.csv", index=False)
        print(f"simap_awards.csv: {len(df)} rows, {df['price_chf'].notna().sum()} with a price")
    else:
        weekly()


if __name__ == "__main__":
    main()
