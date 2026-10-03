#!/usr/bin/env python3
"""
features_master.py  -  FEATURES bâtiment Valais/Suisse -> un CSV master hebdomadaire.

  * ne télécharge QUE des features (aucune cible : pas de BESTA, pas de Job Tracker)
  * agrège tout au pas hebdomadaire (semaine ISO, date = lundi)
  * écrit  data/master_weekly.csv            (données seules)
           data/master_dictionary.csv        (explication de chaque colonne + couverture)
           data/master_weekly_documented.xlsx (même master, explications sous l'en-tête)

Usage
  pip install requests pandas openpyxl
  python features_master.py               # fetch + build
  python features_master.py --build-only  # reconstruit le master depuis data/*.csv déjà téléchargés
  python features_master.py --fetch-only

Anti-fuite (leakage) : une ligne = une semaine W (lun-dim). Pour les indicateurs lents
(mensuels, trimestriels, annuels) on n'affiche que la dernière valeur DÉJÀ PUBLIÉE à la fin
de W (date de publication estimée = période + délai, voir LAGS). Les semaines futures
n'ont que des features de calendrier (jours fériés, vacances, fermeture de chantiers).
"""
import argparse
import io
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ============================== CONFIG ==============================
START = "2020-01-01"      # début du master (jours fériés OpenHolidays dispo dès 2020)
FUTURE_WEEKS = 13         # semaines futures ajoutées (features de calendrier uniquement)
OUT = Path("data")
STATIONS = {"sio": "Sion"}   # stations MeteoSwiss (abréviations minuscules)
CANTONS = ["VS"]                # calendriers fériés / vacances
HEAVY_RAIN_MM = 10.0      # seuil "forte pluie" (mm/jour)
FROST_C = 0.0             # gel si Tmin < FROST_C
# Fermetures officielles de chantiers en Valais (AVE-WBV). 2026 : circulaire 2026. A compléter.
CLOSURES_VS = [("2026-08-03", "2026-08-10")]
# Permis de construire Genève (optionnel) : URL WFS + nom de couche depuis https://sitg.ge.ch/donnees/sit-autor-dossier
SITG_WFS = ""
SITG_TYPENAME = ""

# Délais de publication estimés (hypothèses de l'inventaire) -> date de disponibilité
LAGS = {
    "kof_barometer": "fin du mois de référence",
    "kof_emp": 35,          # jours après le début du trimestre (Q3 publié ~3 août)
    "seco_wea": 16,         # jours après le lundi de la semaine (semaine 37 publiée le 23 sept)
    "snb_mortgage": 31,     # jours après la fin du mois
    "snb_fx": 1,            # jours après la fin du mois
    "annual_months": 20,    # mois après le 31 décembre (STATENT, BFS investissements)
}

S = requests.Session()
S.headers["User-Agent"] = "flexsis-features/0.2 (research; contact: you@example.com)"
LOG = []


def log(msg):
    print(msg)
    LOG.append(msg)


# ============================== FETCH (features seulement) ==============================
def save_bytes(name, content):
    (OUT / name).write_bytes(content)
    log(f"OK   {name} ({len(content)/1024:.0f} Ko)")


def get(url, name, **kw):
    try:
        r = S.get(url, timeout=60, **kw)
        r.raise_for_status()
        save_bytes(name, r.content)
        return r
    except Exception as e:
        log(f"FAIL {name}: {e}")


PX = "https://www.pxweb.bfs.admin.ch/api/v1/de/{t}/{t}.px"
PX_TABLES = {  # uniquement du contexte structurel (poids cantonaux, volume de construction)
    "statent_canton_noga": ("px-x-0602010000_101",
                            {"kanton|canton": r"Wallis|Valais|Waadt|Vaud|Genf|Genève|Schweiz"}),
    "bfs_construction_invest": ("px-x-0904010000_203",
                                {"kanton|canton|gemeinde": r"Wallis|Valais|Schweiz"}),
}


def px_fetch(table, filters, chunk=8):
    url = PX.format(t=table)
    meta = S.get(url, timeout=60).json()
    selections, time_idx = [], None
    for i, v in enumerate(meta["variables"]):
        codes, texts = v["values"], v["valueTexts"]
        for var_re, val_re in filters.items():
            if re.search(var_re, v["code"] + " " + v["text"], re.I):
                keep = [c for c, t in zip(codes, texts) if re.search(val_re, t, re.I)]
                if keep:
                    codes = keep
        selections.append((v["code"], codes))
        if v.get("time"):
            time_idx = i

    def post(sel):
        q = {"query": [{"code": c, "selection": {"filter": "item", "values": vals}} for c, vals in sel],
             "response": {"format": "csv"}}
        r = S.post(url, json=q, timeout=120)
        r.raise_for_status()
        try:
            txt = r.content.decode("utf-8-sig")
        except UnicodeDecodeError:
            txt = r.content.decode("cp1252")
        return pd.read_csv(io.StringIO(txt))

    try:
        return post(selections)
    except requests.HTTPError:
        if time_idx is None:
            raise
    code, vals = selections[time_idx]
    frames = []

    def run(sub):
        sel = list(selections)
        sel[time_idx] = (code, sub)
        try:
            frames.append(post(sel))
            time.sleep(0.3)
        except requests.HTTPError:
            if len(sub) == 1:
                raise
            mid = len(sub) // 2
            run(sub[:mid])
            run(sub[mid:])

    for k in range(0, len(vals), chunk):
        run(vals[k:k + chunk])
    return pd.concat(frames, ignore_index=True)


def fetch_all():
    OUT.mkdir(exist_ok=True)
    # BFS (contexte)
    for name, (table, flt) in PX_TABLES.items():
        try:
            df = px_fetch(table, flt)
            df.to_csv(OUT / f"{name}.csv", index=False)
            log(f"OK   {name}.csv ({len(df)} lignes)")
        except Exception as e:
            log(f"FAIL {name}: {e}")
    # KOF : indicateur emploi (intentions d'embauche) + baromètre conjoncturel
    get("https://tsdb-api.kof.ethz.ch/v2/ts?keys=ch.kof.ie.retro.ch_total.ind.d11,"
        "ch.kof.ie.retro.ch_total.ass.d11,ch.kof.ie.retro.ch_total.exp.d11&mime=csv&access_type=public",
        "kof_employment_indicator.csv")
    for key in ("ch.kof.barometer", "kofbarometer"):
        if get(f"https://tsdb-api.kof.ethz.ch/v2/ts?keys={key}&mime=csv&access_type=public",
               "kof_barometer.csv"):
            break
    # SNB (taux hypothécaires, change) et SECO (activité hebdo)
    for cube in ("zikrepro", "devkum"):
        get(f"https://data.snb.ch/api/cube/{cube}/data/csv/en", f"snb_{cube}.csv")
    get("https://scheduler.swissdatas.ch/scheduled/wwa.csv", "seco_wwa.csv")
    # MeteoSwiss (STAC) : fichiers journaliers des stations
    for st in STATIONS:
        try:
            item = S.get("https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn/"
                         f"items/{st}", timeout=60).json()
            for key, asset in item.get("assets", {}).items():
                if "_d_" in key and key.endswith(".csv"):
                    get(asset["href"], f"meteo_{key}")
        except Exception as e:
            log(f"FAIL meteo {st}: {e}")
    # OpenHolidays (fenêtres d'un an)
    for sub in (f"CH-{c}" for c in CANTONS):
        for kind in ("PublicHolidays", "SchoolHolidays"):
            rows = []
            try:
                for year in range(2020, 2028):
                    r = S.get(f"https://openholidaysapi.org/{kind}", timeout=60, params={
                        "countryIsoCode": "CH", "subdivisionCode": sub,
                        "validFrom": f"{year}-01-01", "validTo": f"{year}-12-31", "languageIsoCode": "FR"})
                    if r.status_code != 200:
                        raise RuntimeError(f"{r.status_code} {r.text[:200]}")
                    for h in r.json():
                        rows.append({"start": h["startDate"], "end": h["endDate"], "type": h.get("type"),
                                     "name": (h.get("name") or [{}])[0].get("text"),
                                     "nationwide": h.get("nationwide")})
                pd.DataFrame(rows).drop_duplicates().to_csv(OUT / f"holidays_{kind}_{sub}.csv", index=False)
                log(f"OK   holidays_{kind}_{sub}.csv ({len(rows)} lignes)")
            except Exception as e:
                log(f"FAIL holidays {kind} {sub}: {e}")
    # SITG Genève (optionnel)
    if SITG_WFS and SITG_TYPENAME:
        try:
            r = S.get(SITG_WFS, timeout=120, params={
                "service": "WFS", "version": "2.0.0", "request": "GetFeature",
                "typeNames": SITG_TYPENAME, "outputFormat": "geojson", "count": 100000})
            r.raise_for_status()
            df = pd.json_normalize([f["properties"] for f in r.json()["features"]])
            df.to_csv(OUT / "sitg_permis_ge.csv", index=False)
            log(f"OK   sitg_permis_ge.csv ({len(df)} lignes)")
        except Exception as e:
            log(f"FAIL sitg: {e}")
    else:
        log("SKIP sitg_permis_ge (renseigner SITG_WFS / SITG_TYPENAME)")


# ============================== BUILD ==============================
DOCS = []
OBSERVED = []   # colonnes mesurées (masquées sur les semaines futures)
M = None        # master (index = lundi de la semaine)


def doc(col, group, desc, source, freq, avail, unit="", observed=True):
    DOCS.append(dict(column=col, group=group, description=desc, source=source,
                     native_frequency=freq, availability=avail, unit=unit))
    if observed:
        OBSERVED.append(col)


def put(col, series, group, desc, source, freq, avail, unit="", observed=True):
    M[col] = pd.Series(series).reindex(M.index).astype(float).to_numpy()
    doc(col, group, desc, source, freq, avail, unit, observed)


def week_start_idx(idx):
    idx = pd.DatetimeIndex(idx)
    return (idx - pd.to_timedelta(idx.dayofweek, unit="D")).normalize()


def asof(obs, cols):
    """Dernière valeur publiée à la fin de chaque semaine (obs doit avoir une colonne 'avail')."""
    o = obs.dropna(subset=["avail"]).copy()
    o["avail"] = pd.to_datetime(o["avail"]).astype("datetime64[ns]")
    o = o.sort_values("avail")
    sp = pd.DataFrame({"week_end": (M.index + pd.Timedelta(days=6)).astype("datetime64[ns]")})
    out = pd.merge_asof(sp, o[["avail"] + cols], left_on="week_end", right_on="avail", direction="backward")
    out.index = M.index
    return out[cols]


def month_end(s):
    return pd.to_datetime(s) + pd.offsets.MonthEnd(0)


def expand_days(df):
    days = [pd.date_range(r.start, r.end) for r in df.itertuples()]
    return pd.DatetimeIndex(np.concatenate([d.values for d in days])).drop_duplicates() if days else pd.DatetimeIndex([])


def weekly_count(days, wd_only=True):
    days = pd.DatetimeIndex(days)
    if wd_only:
        days = days[days.dayofweek < 5]
    return pd.Series(1.0, index=week_start_idx(days)).groupby(level=0).sum()


def build_spine():
    global M
    first = pd.Timestamp(START)
    if first.dayofweek:                      # premier lundi >= START
        first += pd.Timedelta(days=7 - first.dayofweek)
    today = pd.Timestamp.today().normalize()
    last_complete = today - pd.Timedelta(days=today.dayofweek) - pd.Timedelta(weeks=1)
    idx = pd.date_range(first, last_complete + pd.Timedelta(weeks=FUTURE_WEEKS), freq="7D")
    M = pd.DataFrame(index=pd.DatetimeIndex(idx, name="date"))
    M["is_future"] = (M.index > last_complete).astype(int)
    iso = M.index.isocalendar()
    M["iso_year"] = iso["year"].to_numpy()
    M["iso_week"] = iso["week"].to_numpy()
    mid = M.index + pd.Timedelta(days=3)   # jeudi = mois de référence ISO
    M["month"] = mid.month
    M["quarter"] = mid.quarter
    doc("is_future", "calendrier", "1 = semaine incomplète ou à venir : seules les features de calendrier sont remplies", "calculé", "hebdo", "-", "0/1", False)
    doc("iso_year", "calendrier", "Année ISO de la semaine", "calculé", "hebdo", "-", "année", False)
    doc("iso_week", "calendrier", "Numéro de semaine ISO (1-53) : saisonnalité hebdomadaire du chantier", "calculé", "hebdo", "-", "semaine", False)
    doc("month", "calendrier", "Mois civil du jeudi de la semaine (saisonnalité mensuelle)", "calculé", "hebdo", "-", "1-12", False)
    doc("quarter", "calendrier", "Trimestre civil du jeudi de la semaine", "calculé", "hebdo", "-", "1-4", False)
    return last_complete


def sec_holidays():
    for cc in CANTONS:
        c = cc.lower()
        pub = pd.read_csv(OUT / f"holidays_PublicHolidays_CH-{cc}.csv", parse_dates=["start", "end"])
        sch = pd.read_csv(OUT / f"holidays_SchoolHolidays_CH-{cc}.csv", parse_dates=["start", "end"])
        ph = weekly_count(expand_days(pub)).reindex(M.index).fillna(0)
        sh = weekly_count(expand_days(sch)).reindex(M.index).fillna(0)
        cov = (M.index >= "2020-01-01") & (M.index <= "2027-12-31")   # couverture OpenHolidays
        ph[~cov], sh[~cov] = np.nan, np.nan
        put(f"{c}_public_holidays_weekdays", ph, "jours_feries_vacances",
            f"Nombre de jours fériés tombant un jour ouvrable (lun-ven) dans la semaine, canton {cc} (inclut les fériés cantonaux, ex. Saint-Joseph, Fête-Dieu en VS)",
            "OpenHolidays API", "calendrier", "connu à l'avance", "jours", False)
        put(f"{c}_working_days", 5 - ph, "jours_feries_vacances",
            f"Jours ouvrables de la semaine = 5 - jours fériés ouvrables, canton {cc}", "OpenHolidays API (calculé)",
            "calendrier", "connu à l'avance", "jours", False)
        put(f"{c}_school_holiday_weekdays", sh, "jours_feries_vacances",
            f"Nombre de jours ouvrables (lun-ven) en vacances scolaires dans la semaine, canton {cc} (union des régions/écoles). Proxy de baisse de disponibilité des travailleurs et de la demande",
            "OpenHolidays API", "calendrier", "connu à l'avance", "jours", False)
    clos = [pd.date_range(a, b) for a, b in CLOSURES_VS]
    cl = weekly_count(pd.DatetimeIndex(np.concatenate([d.values for d in clos]))) if clos else pd.Series(dtype=float)
    cl = cl.reindex(M.index).fillna(0)
    put("vs_site_closure_weekdays", cl, "jours_feries_vacances",
        "Jours ouvrables de fermeture officielle des chantiers valaisans (AVE-WBV, CLOSURES_VS ; seulement les années renseignées dans la config)",
        "AVE-WBV circulaire 2026", "annuel", "connu à l'avance", "jours", False)
    put("vs_construction_working_days", M["vs_working_days"] - cl, "jours_feries_vacances",
        "Jours réellement travaillables sur un chantier valaisan = jours ouvrables VS - fermeture officielle",
        "calculé", "calendrier", "connu à l'avance", "jours", False)


def sec_weather():
    for st, label in STATIONS.items():
        files = sorted(OUT.glob(f"meteo_ogd-smn_{st}_d_*.csv"))
        if not files:
            raise FileNotFoundError(f"pas de fichier météo pour {st}")
        d = pd.concat([pd.read_csv(f, sep=";", dtype=str) for f in files])
        d["day"] = pd.to_datetime(d["reference_timestamp"], format="%d.%m.%Y %H:%M").dt.normalize()
        d = d.drop_duplicates("day", keep="last").set_index("day").sort_index()
        num = lambda c: pd.to_numeric(d[c], errors="coerce")
        tmean, tmin, tmax, rain, sun = num("tre200d0"), num("tre200dn"), num("tre200dx"), num("rre150d0"), num("sre000d0")
        weekday = d.index.dayofweek < 5
        f = pd.DataFrame({
            "tmean": tmean, "tmin": tmin, "precip": rain, "sun_h": sun / 60,
            "frost": (tmin < FROST_C).astype(float).where(tmin.notna()),
            "heavy": (rain >= HEAVY_RAIN_MM).astype(float).where(rain.notna()),
            "bad": (((rain >= HEAVY_RAIN_MM) | (tmax < 0)) & weekday).astype(float).where(rain.notna() | tmax.notna()),
        })
        g = f.groupby(week_start_idx(f.index))
        a = pd.DataFrame({
            "tmean": g["tmean"].mean(), "tmin": g["tmin"].min(), "precip": g["precip"].sum(min_count=1),
            "frost": g["frost"].sum(min_count=1), "heavy": g["heavy"].sum(min_count=1),
            "bad": g["bad"].sum(min_count=1), "sun_h": g["sun_h"].sum(min_count=1)})
        a = a[g["tmean"].count() >= 5]   # semaines avec >= 5 jours de mesure
        src = f"MeteoSwiss SwissMetNet, station {label} ({st.upper()})"
        k = f"meteo_{st}_"
        kw = dict(group="meteo", source=src, freq="journalier", avail="même semaine (délai ~20 min)")
        put(k + "tmean_c", a["tmean"], desc=f"Température moyenne de la semaine à {label} (moyenne des moyennes journalières)", unit="°C", **kw)
        put(k + "tmin_c", a["tmin"], desc=f"Température minimale de la semaine à {label} (plus bas des minima journaliers)", unit="°C", **kw)
        put(k + "precip_mm", a["precip"], desc=f"Cumul de précipitations de la semaine à {label}", unit="mm", **kw)
        put(k + "frost_days", a["frost"], desc=f"Jours de gel dans la semaine à {label} (Tmin < {FROST_C} °C) : bétonnage et travaux extérieurs compromis", unit="jours (0-7)", **kw)
        put(k + "heavy_rain_days", a["heavy"], desc=f"Jours de forte pluie dans la semaine à {label} (>= {HEAVY_RAIN_MM} mm)", unit="jours (0-7)", **kw)
        put(k + "bad_workdays", a["bad"], desc=f"Jours ouvrables (lun-ven) à {label} avec >= {HEAVY_RAIN_MM} mm de pluie OU température max < 0 °C : proxy de jours de chantier perdus (rattrapage attendu 1-4 semaines après)", unit="jours (0-5)", **kw)
        put(k + "sun_hours", a["sun_h"], desc=f"Heures d'ensoleillement cumulées de la semaine à {label}", unit="heures", **kw)

def sec_sitg():
    p = OUT / "sitg_permis_ge.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    col = next(c for c in d.columns if c.upper() == "DATE_DEPOT")
    x = d[col]
    dt = pd.to_datetime(x, unit="ms") if pd.api.types.is_numeric_dtype(x) else pd.to_datetime(x, errors="coerce")
    cnt = pd.Series(1.0, index=week_start_idx(dt.dropna())).groupby(level=0).sum()
    s = cnt.reindex(M.index).fillna(0)
    s[M.index < cnt.index.min()] = np.nan
    put("ge_permits_filed_n", s, "appels_offres", "Dossiers de permis de construire déposés dans la semaine, canton de Genève (signal avancé 3-9 mois avant les chantiers)",
        "SITG Genève (WFS)", "événements (journalier)", "1 jour", "nombre")


def sec_kof():
    b = pd.read_csv(OUT / "kof_barometer.csv", parse_dates=["date"]).rename(columns={"ch.kof.barometer": "v"})
    b = b.sort_values("date")
    b["chg"] = b["v"] - b["v"].shift(3)
    b["avail"] = month_end(b["date"])
    o = asof(b, ["v", "chg"])
    kw = dict(group="conjoncture", source="KOF Swiss Economic Institute (ETH)", freq="mensuel", avail="fin du mois de référence")
    put("kof_barometer", o["v"], desc="Baromètre conjoncturel KOF : indicateur avancé de la croissance du PIB suisse (100 = moyenne long terme). Avance estimée 3-6 mois sur l'emploi", unit="indice", **kw)
    put("kof_barometer_chg_3m", o["chg"], desc="Variation du baromètre KOF sur 3 mois (points) : accélération ou ralentissement du cycle", unit="points", **kw)
    e = pd.read_csv(OUT / "kof_employment_indicator.csv", parse_dates=["date"])
    e.columns = ["date", "ind", "ass", "exp"]
    e["avail"] = e["date"] + pd.Timedelta(days=LAGS["kof_emp"])
    o = asof(e, ["ind", "ass", "exp"])
    kw = dict(group="conjoncture", source="KOF Swiss Economic Institute (ETH)", freq="trimestriel",
              avail=f"début du trimestre + ~{LAGS['kof_emp']} jours")
    put("kof_emp_indicator", o["ind"], desc="Indicateur KOF de l'emploi : solde des intentions d'embauche des entreprises pour les 3 prochains mois (série ch_total.ind)", unit="solde, points", **kw)
    put("kof_emp_assessment", o["ass"], desc="KOF emploi, composante 'appréciation' (série ch_total.ass) : jugement des entreprises sur leurs effectifs actuels", unit="solde, points", **kw)
    put("kof_emp_expectations", o["exp"], desc="KOF emploi, composante 'attentes' (série ch_total.exp) : effectifs attendus à 3 mois", unit="solde, points", **kw)


def sec_seco():
    w = pd.read_csv(OUT / "seco_wwa.csv", parse_dates=["date"])
    w = w[(w["structure"] == "seco_wwa") & (w["type"] == "index") & (w["seas_adj"] == "csa")].sort_values("date")
    w["m4"] = w["value"].rolling(4, min_periods=4).mean()
    w["avail"] = w["date"] + pd.Timedelta(days=LAGS["seco_wea"])
    o = asof(w, ["value", "m4"])
    kw = dict(group="conjoncture", source="SECO Weekly Economic Activity index", freq="hebdomadaire",
              avail=f"lundi de la semaine + {LAGS['seco_wea']} jours")
    put("seco_wea_index", o["value"], desc="Indice SECO d'activité économique hebdomadaire (WEA, corrigé), très corrélé à la croissance du PIB : nowcast du cycle", unit="indice", **kw)
    put("seco_wea_index_4w", o["m4"], desc="Moyenne mobile 4 semaines de l'indice SECO WEA (tendance)", unit="indice", **kw)


def read_snb(name):
    return pd.read_csv(OUT / name, sep=";", skiprows=3, encoding="utf-8-sig")


def sec_snb():
    z = read_snb("snb_zikrepro.csv")
    z = z[(z["D0"] == "M") & z["D1"].isin(["HYP_11", "HYP_15"])].dropna(subset=["Value"])
    p = z.pivot(index="Date", columns="D1", values="Value").sort_index()
    p.index = pd.to_datetime(p.index + "-01")
    p["spread"] = p["HYP_15"] - p["HYP_11"]
    p["chg6"] = p["HYP_11"] - p["HYP_11"].shift(6)
    p["avail"] = month_end(p.index.to_series()).to_numpy() + pd.Timedelta(days=LAGS["snb_mortgage"])
    o = asof(p.reset_index(drop=True), ["HYP_11", "HYP_15", "spread", "chg6"])
    kw = dict(group="taux_change", source="SNB data portal, cube zikrepro (D0=M moyenne mensuelle)", freq="mensuel",
              avail=f"fin du mois + ~{LAGS['snb_mortgage']} jours")
    put("snb_mortgage_hyp11_pct", o["HYP_11"], desc="Taux hypothécaire moyen, série SNB HYP_11 (hypothèque fixe, échéance présumée la plus courte). Hypothèse : avance de 6-12 mois sur les dépôts de permis. A vérifier dans le portail SNB", unit="% ", **kw)
    put("snb_mortgage_hyp15_pct", o["HYP_15"], desc="Taux hypothécaire moyen, série SNB HYP_15 (hypothèque fixe, échéance présumée la plus longue)", unit="%", **kw)
    put("snb_mortgage_term_spread_pp", o["spread"], desc="Écart HYP_15 - HYP_11 (pente de la courbe hypothécaire)", unit="points de %", **kw)
    put("snb_mortgage_hyp11_chg_6m_pp", o["chg6"], desc="Variation du taux HYP_11 sur 6 mois : choc de financement pour les projets de construction", unit="points de %", **kw)
    d = read_snb("snb_devkum.csv")
    d = d[(d["D0"] == "M0") & d["D1"].isin(["EUR1", "USD1"])].dropna(subset=["Value"])
    p = d.pivot(index="Date", columns="D1", values="Value").sort_index()
    p.index = pd.to_datetime(p.index + "-01")
    p["eur_chg3"] = p["EUR1"].pct_change(3) * 100
    p["avail"] = month_end(p.index.to_series()).to_numpy() + pd.Timedelta(days=LAGS["snb_fx"])
    o = asof(p.reset_index(drop=True), ["EUR1", "USD1", "eur_chg3"])
    kw = dict(group="taux_change", source="SNB data portal, cube devkum (D0=M0 moyenne mensuelle)", freq="mensuel",
              avail=f"fin du mois + {LAGS['snb_fx']} jour")
    put("snb_eurchf_avg", o["EUR1"], desc="Cours moyen mensuel: CHF pour 1 EUR (baisse = franc fort, pression sur l'industrie exportatrice et les marges)", unit="CHF", **kw)
    put("snb_usdchf_avg", o["USD1"], desc="Cours moyen mensuel: CHF pour 1 USD", unit="CHF", **kw)
    put("snb_eurchf_chg_3m_pct", o["eur_chg3"], desc="Variation du cours EUR/CHF sur 3 mois (%)", unit="%", **kw)


def sec_annual():
    lagm = LAGS["annual_months"]
    avail = lambda years: [pd.Timestamp(f"{int(y)}-12-31") + pd.DateOffset(months=lagm) for y in years]
    # STATENT : poids de la construction (NOGA 41-43) en Valais vs Suisse
    s = pd.read_csv(OUT / "statent_canton_noga.csv")
    s = s[s["Wirtschaftsabteilung"].str.match(r"^4[123]\b")]
    cols = ["Beschäftigte", "Vollzeitäquivalente", "Arbeitsstätten"]
    s[cols] = s[cols].apply(pd.to_numeric, errors="coerce")   # "X" = secret statistique -> NaN
    vs = s[s["Kanton"].str.contains("Valais|Wallis")].groupby("Jahr")[cols].sum()
    ch = s[s["Kanton"] == "Schweiz"].groupby("Jahr")[cols].sum()
    t = pd.DataFrame({"vs_emp": vs["Beschäftigte"], "vs_fte": vs["Vollzeitäquivalente"], "vs_est": vs["Arbeitsstätten"],
                      "ch_emp": ch["Beschäftigte"]})
    t["share"] = t["vs_emp"] / t["ch_emp"] * 100
    t["avail"] = avail(t.index)
    o = asof(t, ["vs_emp", "vs_fte", "vs_est", "ch_emp", "share"])
    kw = dict(group="annuel_structurel", source="BFS STATENT (NOGA 41 Hochbau + 42 Tiefbau + 43 second oeuvre)", freq="annuel",
              avail=f"31 décembre + {lagm} mois")
    put("vs_construction_employees", o["vs_emp"], desc="Personnes employées dans la construction (NOGA 41-43) en Valais, dernière année publiée (constante entre deux publications)", unit="personnes", **kw)
    put("vs_construction_fte", o["vs_fte"], desc="Équivalents plein temps de la construction (NOGA 41-43) en Valais", unit="EPT", **kw)
    put("vs_construction_workplaces", o["vs_est"], desc="Établissements de la construction (NOGA 41-43) en Valais", unit="établissements", **kw)
    put("ch_construction_employees", o["ch_emp"], desc="Personnes employées dans la construction (NOGA 41-43) en Suisse", unit="personnes", **kw)
    put("vs_share_ch_construction_emp_pct", o["share"], desc="Part du Valais dans l'emploi suisse de la construction : poids pour convertir un signal national en estimation valaisanne", unit="%", **kw)
    # BFS : volume de construction et carnet de commandes
    b = pd.read_csv(OUT / "bfs_construction_invest.csv")
    c0, c1, c2, c3 = b.columns[:4]
    b = b[b[c1].str.contains("Total") & b[c2].str.contains("Total") & b[c3].str.contains("Absolute")].copy()
    g = b[c0].str.strip()
    b["geo"] = np.where(g == "Schweiz", "ch", np.where(g == "- Wallis", "vs", ""))
    b = b[b["geo"] != ""]
    b["kind"] = np.where(b[c3].str.contains("Folgejahr"), "backlog", "invest")
    ycols = [c for c in b.columns[4:] if str(c).isdigit()]
    long = b.melt(id_vars=["geo", "kind"], value_vars=ycols, var_name="year", value_name="v")
    long["v"] = pd.to_numeric(long["v"], errors="coerce")
    long["year"] = long["year"].astype(int)
    w = long.pivot_table(index="year", columns=["geo", "kind"], values="v", aggfunc="first")
    w.columns = [f"{a}_{k}" for a, k in w.columns]
    w["vs_ratio"] = w["vs_backlog"] / w["vs_invest"]
    w["avail"] = avail(w.index)
    o = asof(w, ["vs_invest", "vs_backlog", "vs_ratio", "ch_invest", "ch_backlog"])
    kw = dict(group="annuel_structurel", source="BFS statistique de la construction (px-x-0904010000_203)", freq="annuel",
              avail=f"31 décembre + {lagm} mois")
    put("vs_construction_invest_kchf", o["vs_invest"], desc="Investissements de construction réalisés en Valais l'année de référence (tous maîtres d'ouvrage et ouvrages)", unit="milliers de CHF", **kw)
    put("vs_construction_backlog_kchf", o["vs_backlog"], desc="Carnet de commandes (Arbeitsvorrat) valaisan pour l'année suivante : volume de travaux déjà engagé", unit="milliers de CHF", **kw)
    put("vs_backlog_to_invest_ratio", o["vs_ratio"], desc="Carnet de commandes / investissements de l'année, Valais (>1 = reprise attendue, <1 = repli)", unit="ratio", **kw)
    put("ch_construction_invest_kchf", o["ch_invest"], desc="Investissements de construction réalisés en Suisse", unit="milliers de CHF", **kw)
    put("ch_construction_backlog_kchf", o["ch_backlog"], desc="Carnet de commandes suisse pour l'année suivante", unit="milliers de CHF", **kw)

def update_frequency(col, group, source, native):
    """Fréquence à laquelle la SOURCE publie une nouvelle donnée (≠ pas des données du fichier)."""
    if group == "calendrier":
        return "n/a (colonne calculée)"
    if "AVE-WBV" in source:
        return "annuelle"
    if "OpenHolidays" in source or col == "vs_construction_working_days":
        return "annuelle ou moins (calendrier publié à l'avance)"
    if "MeteoSwiss" in source:
        return "quotidienne (source : toutes les 10 min)"
    if "simap" in source or "SITG" in source:
        return "quotidienne (au fil des événements)"
    if col.startswith("kof_barometer"):
        return "mensuelle"
    if col.startswith("kof_emp"):
        return "trimestrielle"
    if col.startswith("seco_wea"):
        return "hebdomadaire"
    if "SNB" in source:
        return "mensuelle"
    if "BFS" in source:
        return "annuelle"
    return native or "à définir"   # filet de sécurité si une nouvelle source est ajoutée

def build_master():
    OUT.mkdir(exist_ok=True)
    build_spine()
    for fn in (sec_holidays, sec_weather, sec_sitg, sec_kof, sec_seco, sec_snb, sec_annual):
        try:
            fn()
            log(f"BUILD OK   {fn.__name__}")
        except Exception as e:
            log(f"BUILD FAIL {fn.__name__}: {type(e).__name__}: {e}")
    # semaines futures : on ne garde que le calendrier (le forward-fill des indicateurs n'est pas une observation)
    # semaines futures ou incomplètes : exclues du master
    out = M[M["is_future"] == 0].drop(columns="is_future").reset_index()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    # dictionnaire + couverture
    dd = pd.DataFrame([dict(column="date", group="calendrier", description="Lundi de la semaine ISO (début de semaine). Les features décrivent la semaine lun-dim, ou la dernière valeur publiée à la fin de celle-ci",
                            source="calculé", native_frequency="hebdo", availability="-", unit="date")] + DOCS)
    dd = dd[dd["column"].isin(out.columns)].copy()
    dd.insert(dd.columns.get_loc("availability") + 1, "update_frequency",
        [update_frequency(r.column, r.group, r.source, r.native_frequency) for r in dd.itertuples()])
    hist = M[M["is_future"] == 0]
    cov = {}
    for c in dd["column"]:
        if c == "date":
            continue
        v = hist[c].dropna()
        cov[c] = (v.index.min().strftime("%Y-%m-%d") if len(v) else "", v.index.max().strftime("%Y-%m-%d") if len(v) else "",
                  round(100 * hist[c].isna().mean(), 1))
    dd["first_valid_week"] = dd["column"].map(lambda c: cov.get(c, ("", "", ""))[0])
    dd["last_valid_week"] = dd["column"].map(lambda c: cov.get(c, ("", "", ""))[1])
    dd["pct_missing_past_weeks"] = dd["column"].map(lambda c: cov.get(c, ("", "", ""))[2])
    out = out[list(dd["column"])]
    out.to_csv(OUT / "master_weekly.csv", index=False, float_format="%.5g")
    dd.to_csv(OUT / "master_dictionary.csv", index=False)
    log(f"MASTER master_weekly.csv  {out.shape[0]} semaines x {out.shape[1]} colonnes")
    try:
        from openpyxl.styles import Alignment, Font
        desc = dict(zip(dd["column"], dd["description"]))
        with pd.ExcelWriter(OUT / "master_weekly_documented.xlsx", engine="openpyxl") as xw:
            out.to_excel(xw, sheet_name="master", index=False)
            dd.to_excel(xw, sheet_name="dictionnaire", index=False)
            ws = xw.sheets["master"]
            ws.insert_rows(2)
            for j, c in enumerate(out.columns, start=1):
                cell = ws.cell(row=2, column=j, value=desc[c])
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                cell.font = Font(italic=True, size=9)
                ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = 26
                ws.cell(row=1, column=j).font = Font(bold=True)
            ws.row_dimensions[2].height = 150
            ws.freeze_panes = "B3"
            wd = xw.sheets["dictionnaire"]
            for col, wdt in zip("ABCDEFGHIJKL", (32, 20, 90, 40, 18, 34, 38, 14, 14, 14, 12, 12)):
                wd.column_dimensions[col].width = wdt
            for row in wd.iter_rows(min_row=2, min_col=3, max_col=3):
                row[0].alignment = Alignment(wrap_text=True, vertical="top")
        log("MASTER master_weekly_documented.xlsx")
    except ImportError:
        log("SKIP xlsx (pip install openpyxl)")
    (OUT / "_log_master.txt").write_text("\n".join(LOG), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--fetch-only", action="store_true")
    a = ap.parse_args()
    if not a.build_only:
        fetch_all()
    if not a.fetch_only:
        build_master()