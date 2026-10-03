# Data catalogue: early warning for staffing demand in construction, logistics and industry (Switzerland)

Hackathon Foire du Valais 2026, Flexsis challenge. Search done on 3 October 2026 in FR, DE, IT and EN. "Verified" means the page, file or API was opened during this search. Lead times are labelled as hypotheses unless a study is cited. Usability score: 5 = free, machine readable, monthly or finer, canton level, 5+ years; 3 = usable with effort; 1 = paid or too coarse.

Access notes for the team: bfs.admin.ch, swissstaffing.ch, vs.ch and parts of opendata.swiss refused our automated fetcher (robots.txt or 403), so several BFS items were verified through the BFS PxWeb API instead, and some are listed as unverified in section 7. These sites work normally in a browser.

## 1. Executive summary

- **Best target proxy:** the KOF / x28 **Swiss Job Tracker** (weekly online job postings since 2018, by canton, ISCO occupation and NOGA sector, free API, 0.96 correlation with official BESTA vacancies). ISCO 7, 8 and 9 cover masons, electricians, welders, machine operators, drivers and warehouse staff.
- **Official ground truth:** BFS **BESTA** vacancies and employment by NOGA division (quarterly, national, PxWeb API), including division 78 (temp agencies). **Swiss Staffingindex** temp hours is the closest concept to Flexsis demand, but there are only quarterly press releases.
- **Best construction signals:** building permit flows that are free and fresh in Romandie: **Geneva SITG permit files (daily, WFS)**, **Bulletin officiel du Valais** (weekly, by commune, scraping needed), **FAO Vaud** (free summary lists), plus **simap.ch** awards (public read-only API). The SBV backlog and Bauindex are quarterly confirmations.
- **Best industry signals:** **procure.ch PMI** and **Raiffeisen SME PMI** (monthly, with employment, backlog and delivery time subindices, PDF only), the **KOF Employment Indicator** (3-month hiring intentions), **BAZG exports** by goods, and **SNB** CHF rates (free API).
- **Best logistics signals:** the retail calendar (Black Friday 27 Nov 2026), **card spending incl. e-commerce** (HSG Monitoring Consumption), **ASTRA** monthly traffic count bulletins, the Rhine port bulletin, and Swiss Post peak figures.
- **Context:** MeteoSwiss station data (free STAC API, 10 minutes) and OpenHolidays (school and public holidays per canton, free API) are both score 5.
- **Valais coverage:** permits (Bulletin officiel), AMSTAT unemployment and vacancies, Job Tracker canton VS, STATENT, BFS construction investment, MeteoSwiss stations, OpenHolidays, and the Valais construction work calendar.
- **Biggest gaps:** no public temp hours series by sector or canton; no national open feed of permit applications (Baublatt/Docu Media is paid); no national open bad weather compensation series (only canton St. Gallen); short-time work data lags about 3 months; BESTA is quarterly and only regional; Indeed Hiring Lab does not cover Switzerland.

## 2. Target proxy catalogue

Sorted by usability score. Every row was opened during this search (see notes where only part of a source could be read).

| Name / link | Publisher | Subsector | Role | Measures | Geo | Time | History | Lag | Latest | Access / format | Licence | Cost | Lead time (hypothesis) | Score | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **[Swiss Job Tracker (weekly online job postings index)](https://kof.ethz.ch/en/forecasts-and-indicators/indicators/swiss-job-tracker.html)** | KOF ETH Zurich, University of Lausanne, data by x28 AG | cross-sector | target proxy | Weekly count of unique online job postings (job boards + company websites, duplicates and recruitment agency postings removed), indexed Jan 2020 = 100; split by ISCO-08 1-digit occupation, NOGA 1-digit sector and canton | canton (all 26), national | weekly | 2018-01 | about 1 week (hypothesis, weekly dashboard) | weekly, current (exact week not read) | free API (public tsdb-api endpoint); dashboard swissjobtracker.ch; XLSX/CSV/JSON via https://tsdb-api.kof.ethz.ch/v2/ts?keys=ch.kof.jobtracker.total.total.clean.idx&mime=xlsx&access_type=public | public data per KOF page; cite KOF/x28 | free | Target proxy. Methodology paper reports correlation 0.96 with BFS BESTA vacancies and release weeks before BESTA, so it can also nowcast BESTA by about 2 months | 4 | Best free target proxy. ISCO 7 (craft trades: masons, electricians, welders), ISCO 8 (machine operators, drivers) and ISCO 9 (labourers, warehouse helpers) map well to Flexsis temp roles; NOGA F, C, H map to the three subsectors. Agency postings are removed, so temp demand is seen only indirectly. Keys for canton/occupation series must be discovered (KOF metadata endpoint found via search, not opened). Valais, Vaud, Geneva covered. |
| **[SECO AMSTAT (unemployed, job seekers, registered vacancies, short-time work)](https://www.amstat.ch/v2/amstat_de.html)** | SECO | cross-sector | target proxy | Registered unemployed and job seekers by occupation and economic division, registered vacancies (Job-Room/RAV), allowance recipients, short-time work | canton, district (Bezirk), national | monthly | not verified in UI | about 1 week for unemployment (monthly report around the 6th-7th); about 3 months for short-time work | August 2026 (monthly report listed on arbeit.swiss) | free web application (JS app; no public REST API according to the seco-labor-mcp project); interactive tables; export options not verified | official statistics, attribution | free | Registered vacancies in construction occupations: target proxy. Falling unemployment of masons/drivers in a canton = tightening supply, hypothesis 0-1 month lead on temp rates | 4 | Canton and occupation detail including Valais, Vaud, Geneva. Vacancies are biased toward occupations under the job reporting obligation (threshold 5% unemployment), which includes many construction and logistics occupations. |
| **[Statistique Vaud: unemployment and job vacancies](https://www.vd.ch/etat-droit-finances/statistique/statistiques-par-domaine/03-vie-active-remuneration-du-travail/chomage-et-places-vacantes)** | Statistique Vaud (Canton de Vaud) | cross-sector | target proxy | Job seekers, unemployed and rates by district and month; vacancies by economic activity (annual averages); based on SECO data | canton VD, district, commune | monthly (vacancies by sector annual) | 1992 (unemployment), 2004 (vacancies) | about 1 month (hypothesis) | monthly, current (exact month not read) | free download; XLSX | official statistics, attribution | free | Target proxy for the Renens HQ region | 4 | French speaking canton; useful for Flexsis home market. |
| **[BESTA job vacancies by NOGA division](https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0602000000_103/px-x-0602000000_103.px)** | BFS / OFS (Federal Statistical Office) | cross-sector | target proxy | Number of open positions, index (Q2 2015=100) and vacancy rate, by selected NOGA divisions (incl. manufacturing subdivisions such as 28 machinery, and construction) | national | quarterly | 1992-Q2 | about 2 months after quarter end (hypothesis; Q2 2026 available on 3 Oct 2026) | 2026-Q2 | free API (PxWeb, POST JSON query to the URL) and STAT-TAB web UI; PX/JSON/CSV via PxWeb API | BFS open data terms (attribution) | free | Target variable (official). Quarterly and lagged, so use as ground truth to validate faster signals | 3 | Table id px-x-0602000000_103. Only 20 selected divisions; check whether 49-53 transport/storage is split. bfs.admin.ch pages were blocked to our fetcher by robots.txt, but the PxWeb API answered. |
| **[BESTA job vacancies by large region](https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0602000000_104/px-x-0602000000_104.px)** | BFS / OFS | cross-sector | target proxy | Open positions, index and vacancy rate by Grossregion (Region lemanique = VD, VS, GE; Espace Mittelland; NW CH; Zurich; East; Central; Ticino) | region (7 large regions) | quarterly | 1997-Q1 | about 2 months (hypothesis) | 2026-Q2 | free API (PxWeb); PX/JSON/CSV | BFS open data terms | free | Target variable at regional level | 3 | No sector split. Valais only inside Region lemanique. |
| **[BESTA employment by NOGA division (incl. division 78 employment activities)](https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0602000000_101/px-x-0602000000_101.px)** | BFS / OFS | cross-sector | target proxy | Employees by NOGA division (41-43, 41-42, 43; 10-33 subdivisions; 49, 52, 53; 78 personnel services = temp agencies), by employment level and sex | national | quarterly | 1991-Q3 | about 2 months (hypothesis) | 2026-Q2 | free API (PxWeb); PX/JSON/CSV | BFS open data terms | free | Division 78 employment is the closest official proxy for temp worker stock; hypothesis: it moves 1-2 quarters before employment in 10-33 and 41-43 | 3 | Table px-x-0602000000_102 gives the same by large region but only sectors II/III. |
| **[Die Lage auf dem Arbeitsmarkt (monthly labour market report)](https://www.seco.admin.ch/dam/de/sd-web/3dmYe3hl-IiX/2026-01_Die_Lage_auf_dem_Arbeitsmarkt_DE.pdf)** | SECO | cross-sector | target proxy | Unemployed by sector (e.g. construction 14,116 in Jan 2026, +4.1% m/m; industry sector II 35,694), registered vacancies (48,904 in Jan 2026), short-time work (affected workers, units) | national and canton tables | monthly | archive of monthly PDFs (2024+ seen) | about 1 week; short-time work refers to month t-3 (Oct 2025 in the Jan 2026 report) | August 2026 | free download; PDF | official publication | free | Construction unemployment has a strong winter seasonality, useful to calibrate the seasonal baseline | 3 | Index page: https://www.arbeit.swiss/en/information-centre/labour-market-statistics-switzerland |
| **[Short-time work and bad weather compensation statistics (canton St. Gallen)](https://www.sg.ch/ueber-den-kanton-st-gallen/statistik/themen/B03/kurzarbeit-schlechtwetterentschaedigung.html)** | Kanton St. Gallen, Fachstelle fuer Statistik | cross-sector | target proxy | Firms, employees, CHF paid and lost hours under short-time work and under bad weather compensation (Schlechtwetterentschaedigung), split industry / trades / services, with Swiss comparison | canton SG and electoral districts, CH comparison | monthly (annual totals 2015-2025) | 2016 (monthly) | updated 4 Aug 2026, includes advance registrations for Aug 2026 | August 2026 (advance registrations) | free download; XLS, PDF, OGD | OGD | free | Bad weather compensation is a direct, observable effect of weather on construction work; use it to calibrate weather rules for construction temp demand (same month) | 3 | Only canton SG publishes this cleanly; no national bad-weather series was found in open form. |
| **[Swiss Staffingindex (temp work hours and permanent placements)](https://www.organisator.ch/en/human-resources/hrm/2026-04-29/swiss-staffingindex-temporaermarkt-dreht-nach-drei-jahren-ins-plus/)** | swissstaffing (with Adecco Group commentary) | cross-sector | target proxy | Year-on-year change in hours worked by temp workers and in permanent placements by member staffing firms | national, with qualitative regional comments (e.g. Eastern Switzerland -2.2%, Mittelland +5.5% in Q1 2026) | quarterly (plus half-year summary) | not verified | about 1 month after quarter end (Q1 2026 released 29 Apr 2026) | 2026-Q2 / H1 2026 (temp hours +1.5% yoy) | press releases only; no downloadable series found; web text / press release | not stated | free (press releases) | Closest concept to Flexsis demand; use as the quarterly ground truth for the temp market | 2 | Q1 2026 was the first positive quarter after 12 declines (+1.3%), driven by industrial clusters (watches). No sector or canton series published. swissstaffing.ch pages were blocked to our fetcher; content read via press reprints (swiss-press.com, organisator.ch). |
| **[Adecco Group Swiss Job Market Index](https://www.adeccogroup.com/de-ch/zukunft-der-arbeit/job-index/job-index-q1-2026)** | Adecco Group Switzerland and Stellenmarkt-Monitor Schweiz (University of Zurich) | cross-sector | target proxy | Number of publicly advertised positions (press, company websites, job portals); quarterly change; occupational groups incl. construction and finishing trades, industrial and craft specialists | national; 6 regions on the UZH page | quarterly | 2008-03 | about 1 month (Q2 2026 release in July 2026) | 2026-Q2 | PDF study and press release; UZH page offers Excel index files; PDF; XLSX (UZH page) | not stated | free | Target proxy (job ads), slower than Swiss Job Tracker | 2 | UZH page https://www.stellenmarktmonitor.uzh.ch/de/indices/asjmi.html shows downloads but the visible latest release there was 2019, so the Excel may be stale; current figures only in Adecco PDFs (Q1 2026: +0.7% q/q). |
| **[x28 Jobradar](https://www.jobundkarriereblog.ch/jobradar-2-quartal-2026/)** | x28 AG | cross-sector | target proxy | Job ads crawled from employer websites: counts by canton, industry, top occupations; direct employer vs agency | canton | quarterly | not verified | about 1 month | 2026-Q2 (construction industry 12,852 postings, 2nd largest) | free basic report; Pro version paid; web article / report | proprietary | free basic, paid Pro | Target proxy; quarterly snapshots only in the free version | 2 | x28 is also the data provider behind Swiss Job Tracker; contact for raw data is a paid option. |
| **[jobs.ch / jobup.ch job boards (scraping only)](https://www.jobs.ch/robots.txt)** | JobCloud AG | cross-sector | target proxy | Live job ads by keyword and location | commune/region | daily | none (only current ads) | real time | live | scraping only; robots.txt disallows /api/ and job detail pages (/de/stellenangebote/detail/...) for all agents; terms of use not reviewed; HTML | proprietary | free to view | Real-time target proxy, but no history | 1 | Not recommended in 24 h: no history and legal risk. Prefer Swiss Job Tracker. |

## 3. Leading signal catalogue

### 3.1 Construction

| Name / link | Publisher | Subsector | Role | Measures | Geo | Time | History | Lag | Latest | Access / format | Licence | Cost | Lead time (hypothesis) | Score | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **[Building permit applications, Geneva (SITG 'Autorisation de construire - Dossier')](https://sitg.ge.ch/donnees/sit-autor-dossier)** | Canton de Geneve, SITG / Office des autorisations de construire | construction | leading signal | Each building permit file with location, operation type, filing date (DATE_DEPOT), status and last update | parcel / point (canton GE) | daily updates (event data) | dataset published 12 Jun 2025; depth of historical files not verified | 1 day | metadata updated 2026-10-03 | free API (WFS, ArcGIS REST, WMS); also on opendata.swiss; WFS/GeoJSON, ArcGIS REST | open access (SITG 'acces libre') | free | Hypothesis: filings lead site starts by 3-9 months (instruction + tender); main works hiring 3-6 months after filing, finishing trades 6-12 months | 4 | Best machine-readable permit source in Romandie. Aggregate weekly counts by operation type (new build vs transformation). |
| **[simap.ch public procurement API](https://github.com/Digilac/simap-mcp)** | Verein simap.ch (Confederation, cantons, communes) | construction | leading signal | Public tenders and awards, searchable by text, dates, tender type, canton, CPV code, BKP (construction cost code), NPK, OAG | canton / contracting authority | daily (event data) | not verified (new platform since 2024) | real time | live | free API, read-only, no key (per the open source MCP server README); JSON (REST); docs at https://www.simap.ch/api-doc/ (behind cookie wall for our fetcher) | not verified | free | Hypothesis: award notices for civil engineering and building works lead on-site staffing by 1-4 months; tender publication by 3-9 months | 4 | Filter CPV 45xxxxxx (construction work) and BKP codes; sum award values per canton per month. Covers Valais and Romandie. |
| **[Bulletin officiel du Valais: building permit applications](https://www.bulletinvalaiswallis.ch/fr/articles/annonces-officielles/)** | Canton du Valais / Bulletin officiel | construction | leading signal | Published building permit applications ('demande d'autorisation de construire') and other official notices | commune (filter by all Valais communes) | weekly edition, items dated | archive pages back to at least 2025 (about 4,700 items paginated) | same week | live | free web access; scraping needed (no API found); reuse terms not stated; HTML list (plus e-paper) | not stated | free | Same hypothesis as Geneva permits: 3-9 months to site start in Valais; strong spring seasonality in mountain communes | 3 | Only free Valais permit flow found. Check terms with publisher before automated collection; a polite low-frequency crawl of the list page is the minimum. |
| **[FAO Vaud: building permit enquiries ('permis de construire')](https://www.faovd.ch/permis-de-construire/district/lausanne/)** | Feuille des avis officiels du canton de Vaud | construction | leading signal | Building permit enquiries with date, commune, CAMAC number, nature of works (new, transformation, renovation), description | district / commune (VD) | edition-based (about 100 editions per year) | editions 2025-2026 seen | same day | 2026-10-02 entry seen | summary list free; full content for subscribers; scraping terms not stated; HTML | proprietary (subscription model) | summary free, full text paid | Lead 3-9 months to site start (hypothesis) | 3 | Count notices per district per week from the free list. Covers Flexsis HQ area (Renens, Lausanne). |
| **[SBV quarterly survey (Quartalserhebung): turnover, order intake, order backlog](https://baumeister.swiss/baumeister-5-0/konjunktur-statistiken/baukonjunktur/)** | Schweizerischer Baumeisterverband (SSE/SBV) | construction | leading signal | Main construction trade turnover, order intake, work backlog (Arbeitsvorrat), employment; Hochbau vs Tiefbau; regional and size breakdowns | national and regions | quarterly | not verified | about 8 weeks (Q2 2026 released 26 Aug 2026) | 2026-Q2 (turnover CHF 6.2 bn, +1.3%; H1 order intake +1.6%; backlog about 8 months) | press releases free; full tables possibly members only (not verified); web page / PDF | not stated | free summaries | Order intake and backlog lead main works employment by 1-3 quarters (hypothesis, backlog of 8 months implies long pipeline) | 3 | Main works (gros oeuvre) only; no second oeuvre. |
| **[SBV Bauindex](https://baumeister.swiss/baumeister-5-0/konjunktur-statistiken/bauindex/)** | Schweizerischer Baumeisterverband (with Credit Suisse until Q3 2023) | construction | leading signal | Forecast of seasonally adjusted main construction turnover for the next quarter and trend for the following three quarters | national | quarterly | re-based Q1 2023 = 100 (older CS series exists) | published at start of quarter | 2026-Q3 (+1.4% yoy) | web page; series download not found; web / PDF | not stated | free | Designed as a 1-quarter-ahead turnover forecast | 3 | Use as a sanity check, not a model input (structural break 2023). |
| **[BFS construction investment and work backlog by canton/commune](https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0904010000_203/px-x-0904010000_203.px)** | BFS / OFS | construction | leading signal | Construction investments and work backlog for the following year, by client type (public/private) and building category; companion table px-x-0904010000_201 adds maintenance and new vs renovation | large region, canton, commune | annual | 1994 | about 20 months | 2024 | free API (PxWeb); PX/JSON/CSV | BFS open data terms | free | Next-year backlog leads annual construction employment by about 1 year (hypothesis) | 2 | Annual only; useful for canton weights and long-run context (Valais public vs private split). |
| **[BFS building projects (Bauvorhaben) by canton/commune](https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0904010000_112/px-x-0904010000_112.px)** | BFS / OFS | construction | leading signal | Building projects by canton/commune, client category, building type and year (see also px-x-0904010000_111 with type of work) | canton, commune | annual | not verified | about 20 months (hypothesis) | not verified (likely 2024) | free API (PxWeb); PX/JSON/CSV | BFS open data terms | free | Annual pipeline indicator | 2 | Too slow for alerts; good for back-testing by canton. |

### 3.2 Industry

| Name / link | Publisher | Subsector | Role | Measures | Geo | Time | History | Lag | Latest | Access / format | Licence | Cost | Lead time (hypothesis) | Score | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **[BAZG foreign trade statistics (SwissImpex, open data, canton files)](https://www.bazg.admin.ch/de/schweizerische-aussenhandelsstatistik-aktuelle-daten)** | Federal Office for Customs and Border Security (BAZG/OFDF) | industry | leading signal | Exports and imports by goods (CPA, SITC, tariff numbers) and country; seasonally adjusted series; canton exports/imports annual Excel 2016-2025 | national (monthly), canton (annual) | monthly; canton annual | decades nationally; canton 2016 | about 3-4 weeks for monthly data (hypothesis) | monthly, current (exact month not read) | free: SwissImpex dashboard, opendata.swiss datasets, Excel; CSV/XLSX | OGD (attribution) | free | Exports of machinery, metals, watches lead production hiring by 1-3 months (hypothesis); imports of consumer goods lead warehouse volumes by 2-6 weeks (hypothesis) | 4 | Canton page: https://www.bazg.admin.ch/bazg/de/home/themen/schweizerische-aussenhandelsstatistik/daten/kantone.html ; price list exists for custom extractions. |
| **[procure.ch Purchasing Managers' Index (PMI) manufacturing](https://www.procure.ch/magazin)** | procure.ch (sponsored by UBS) | industry | leading signal | Manufacturing PMI with subindices (employment, delivery times, order backlog, production, purchase volume, inventories) | national | monthly | not verified | first working days of next month | September 2026 (55.3, -1.8 points) | free PDF reports; history not downloadable as a file (not found); PDF | not stated | free | Order backlog and employment subindices lead manufacturing hiring by 1-3 months (hypothesis) | 3 | Transcribe subindices from monthly PDFs for 3-5 years; tradingeconomics/investing.com carry the headline series. |
| **[Raiffeisen SME PMI (KMU PMI)](https://www.raiffeisen.ch/rch/de/wissen/unternehmensthemen/forschungs-und-werkplatz-schweiz/kmu-pmi-index/aktuelle-ausgabe.html)** | Raiffeisen Schweiz | industry | leading signal | PMI for industrial SMEs with subindices order backlog, production, employment, delivery times, inventories | national | monthly | not verified | first day of next month (Sept 2026 released 1 Oct 2026) | September 2026 (54.5) | free PDF; PDF | not stated | free | SME focus is closer to Flexsis clients; same lead hypothesis as PMI | 3 |  |
| **[Swissgrid energy overview (Swiss control block load)](https://www.swissgrid.ch/en/home/customers/topics/energy-data-ch.html)** | Swissgrid | industry | leading signal | Quarter-hourly consumption and production of the Swiss control block | national | 15 minutes (monthly files) | 2009 | about 15 working days after month end; final after 6 months | annual file 2025 (published 19 May 2026); 2026 monthly updates | free download; XLSX/CSV | not stated | free | Coincident activity proxy for industry, not a true lead | 3 | Weather-sensitive; weekday/working-hour load is a better industrial proxy. |
| **[Swissmem quarterly industry figures (tech / MEM industry)](https://www.aktuelle-technik.ch/swissmem-schweizer-tech-industrie-h1-2026-auftraege-umsatz-exporte-a-4ec38ffcdcc8da31dc2303ac689d6ab0/)** | Swissmem | industry | leading signal | Order intake, turnover, capacity utilisation (81.1% in Q2 2026 vs 85.6% long-run), exports of machinery, electrical and metal industry (about 250 reporting firms) | national | quarterly | not verified | about 2 months (H1 2026 released 3 Sep 2026) | 2026-Q2 | press releases free; web / PDF | not stated | free | Order intake leads MEM employment by 2-4 quarters (hypothesis); capacity utilisation below average signals no hiring | 2 | Statistics page https://www.swissmem.ch/de/produkte-dienstleistungen/beratung/branchenstatistiken.html (not opened). |

### 3.3 Logistics

| Name / link | Publisher | Subsector | Role | Measures | Geo | Time | History | Lag | Latest | Access / format | Licence | Cost | Lead time (hypothesis) | Score | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **[FEDRO/ASTRA Swiss automatic road traffic counts (SARTC) monthly results](https://www.astra.admin.ch/astra/en/home/documentation/data-and-information-products/traffic-data/data-and-publication/swiss-automatic-road-traffic-counts--sartc-/annual-and-monthly-results.html)** | Federal Roads Office (ASTRA/OFROU) | logistics | leading signal | Monthly results of automatic counting stations (traffic volumes; heavy vehicle split to be confirmed in the files) | station (national road network) | monthly (hourly values exist in the full census database) | annual archives 2021-2025 on the page | about 6 weeks (June 2026 published 11 Aug 2026) | 2026-06 | free download; XLSX (Bulletin_YYYY_MM_en.xlsx) | not stated | free | Heavy vehicle volumes are coincident to 1 month ahead of warehouse and driver demand (hypothesis) | 4 | Pick stations near logistics hubs (A1 Oensingen/Haerkingen, A9 Valais, A1 Lausanne-Geneva). |
| **[opentransportdata.swiss real-time road traffic (automatic counting stations)](https://opentransportdata.swiss/en/road-traffic/)** | FEDRO via Open Transport Data Switzerland | logistics | leading signal | Real-time traffic counts (1-minute updates), traffic situations | station | 1 minute | archive exists, details not verified | real time | live | free with registration (default 6 months, 260,000 calls per 6 months); API (DATEX II style, details in cookbook) | platform terms | free | Weekly heavy vehicle counts as a coincident logistics activity signal | 3 | Vehicle class split not confirmed. |
| **[Port of Switzerland monthly transshipment bulletin (Rhine ports)](https://port-of-switzerland.ch/umschlagsstatistik-bulletin-juni-2026/)** | Schweizerische Rheinhaefen | logistics | leading signal | Monthly cargo handled in Swiss Rhine ports (tonnage, containers; details in PDF) | port (Basel region) | monthly | monthly bulletins since at least 2025 seen | about 3 weeks (June 2026 published 23 Jul 2026) | 2026-06 | free download; PDF | not stated | free | Import container volumes lead distribution warehouse work by 2-6 weeks (hypothesis) | 3 | Relevant mainly for Northwestern Switzerland. |
| **[Monitoring Consumption Switzerland / Consumer Spending Index](https://monitoringconsumption.com/)** | University of St. Gallen (HSG), data by Worldline and others | logistics | leading signal | Payment card transactions by canton, merchant category, point of sale vs e-commerce; HSG Consumer Spending Index monthly by 7 regions and 6 categories | canton (transactions), 7 regions (index) | daily (transactions), monthly (index) | 2019-01-01 | days to 2 weeks | active; some datasets frozen on 2023-01-04 | free dashboards; data stated as freely available, download format not verified; dashboard / downloads (not verified) | not stated | free | E-commerce spending growth before Black Friday leads parcel and warehouse peaks by 1-4 weeks (hypothesis) | 3 | Consumer Spending Index: https://www.unisg.ch/en/research/research-in-focus/consumer-spending-in-switzerland/ |
| **[Alpine freight traffic semester reports](https://www.bav.admin.ch/de/newnsb/ViWq1MYAkV3B)** | Federal Office of Transport (BAV/OFT) | logistics | leading signal | Heavy goods vehicle trips across Swiss Alps and rail share (H1 2026: 511,000 lorry trips, +7%; rail share 68%) | national (by crossing in reports) | half-yearly | long series | about 2.5 months (H1 2026 published 10 Sep 2026) | H1 2026 | free; PDF | official | free | Too coarse for alerts; context for transit trucking | 2 |  |
| **[Zurich Airport monthly traffic figures (cargo tonnage)](https://aviation.direct/flughafen-zuerich-veroeffentlicht-verkehrszahlen-fuer-august-2026)** | Flughafen Zuerich AG (via press) | logistics | leading signal | Monthly air cargo tonnage (Aug 2026: 34,444 t, -0.4% yoy) | airport | monthly | not verified | about 2 weeks | 2026-08 | free press releases; web | not stated | free | Coincident for air freight forwarders, weak for temp demand | 2 | Official investor page not opened. |

### 3.4 Cross-sector macro and search signals (feed all three subsectors)

| Name / link | Publisher | Subsector | Role | Measures | Geo | Time | History | Lag | Latest | Access / format | Licence | Cost | Lead time (hypothesis) | Score | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **[SNB data portal API (interest rates, mortgage rates, exchange rates)](https://data.snb.ch/api/cube/zikrepro/data/csv/en)** | Swiss National Bank | cross-sector | leading signal | Data cubes by id, e.g. zikrepro (interest rates incl. historical mortgage series) and devkum (monthly FX rates); verify dimension codes per cube | national | monthly (some daily) | decades (devkum from 1916) | days | cube publishing date 2026-10-01 | free API, no key; CSV/JSON via https://data.snb.ch/api/cube/<id>/data/csv/en | SNB terms (attribution) | free | Mortgage rates lead permit filings by 6-12 months (hypothesis); CHF appreciation leads export-industry hiring declines by 3-6 months (hypothesis) | 4 | Pick cube ids in the portal; zikrepro dimension codes not decoded during this search. |
| **[KOF Economic Barometer](https://datenservice.kof.ethz.ch/)** | KOF Swiss Economic Institute, ETH Zurich | cross-sector | leading signal | Composite leading indicator of Swiss GDP growth | national | monthly | not verified | end of month (same month) | September 2026 (109.1 per secondary source) | free API (public endpoint, key 'kofbarometer'); JSON/CSV/XLSX via https://datenservice.kof.ethz.ch/api/v1/public/ts?keys=kofbarometer&mime=csv | KOF terms | free | General cycle signal, about 3-6 months ahead of employment (hypothesis) | 4 | API documented on the open docs page; the data URL itself was blocked to our fetcher by robots.txt, test locally. |
| **[SECO Weekly Economic Activity index (WEA / WWA)](https://www.seco.admin.ch/en/index-weekly-economic-activity)** | SECO | cross-sector | leading signal | Experimental weekly index of economic activity built from daily/weekly indicators, highly correlated with GDP growth | national | weekly | not verified | about 1-2 weeks (week 37 published 23 Sep 2026) | 2026-W37 | free download; CSV https://scheduler.swissdatas.ch/scheduled/wwa.csv ; XLSX per release | official statistics, attribution | free | Nowcast of the cycle; turning points visible 1-2 months before monthly data (hypothesis) | 4 | National only. |
| **[Google Trends via trendecon R package (consistent long daily series)](https://github.com/trendecon/trendecon)** | trendEcon (KOF, SECO, HSG, cynkra and others); data by Google | cross-sector | leading signal | Google search interest for keywords in Switzerland (geo='CH'), harmonised daily series from daily/weekly/monthly queries | national (Google also offers canton-level 'interest by region') | daily / weekly | 2004 (Google Trends) | 1-3 days | live | free (unofficial access via gtrendsR/pytrends, rate limited); R time series | Google Trends terms; package open source | free | Searches such as 'emploi temporaire', 'Temporärjob', 'cariste', 'Staplerfahrer', 'Kurzarbeit' lead registrations by 0-2 months (hypothesis; literature finds 1-12 month predictive power for employment) | 4 | Method published in Eichenauer et al. 2022 (Economic Inquiry). Expect 429 rate limits; cache results. |
| **[KOF Employment Indicator](https://kof.ethz.ch/prognosen-indikatoren/indikatoren/kof-beschaeftigungsindikator.html)** | KOF Swiss Economic Institute, ETH Zurich | cross-sector | leading signal | Balance of firms' employment expectations for the next 3 months (9 industries, about 85% of private employment) | national | quarterly | not verified (methodology 2017) | released in the first month of the quarter (Q3 2026 on 3 Aug 2026) | 2026-Q3 (2.1 points) | free API; XLSX via https://tsdb-api.kof.ethz.ch/v2/ts?keys=ch.kof.ie.retro.ch_total.ind.d11,ch.kof.ie.retro.ch_total.ass.d11,ch.kof.ie.retro.ch_total.exp.d11&mime=xlsx&access_type=public | open use with source (opendata.swiss listing) | free | Explicit 3-month hiring intention, so lead about 1 quarter | 3 | Sector series (construction, manufacturing) exist in KOF surveys but public keys not confirmed. API returned data, our fetcher could not parse it; test in Python. |
| **[SNB Business cycle signals (regional network)](https://www.snb.ch/en/publications/business-cycle-signals/2026/quartbul_2026_1_konj)** | Swiss National Bank | cross-sector | leading signal | Qualitative findings from SNB delegates' talks with companies across regions (staffing, capacity, outlook) | regions (qualitative) | quarterly | long archive | same quarter | 2026 issues 1-3 | free download; PDF | SNB terms | free | Qualitative, useful to justify alerts in a pitch | 2 | Content of the PDF not read. |

## 4. Context and calendar data

| Name / link | Publisher | Measures | Geo | Time | Latest | Access / format | Score | Notes |
|---|---|---|---|---|---|---|---|---|
| **[MeteoSwiss open data: automatic weather stations (SwissMetNet)](https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations)** | MeteoSwiss | Temperature, precipitation, wind, sunshine, humidity, radiation, pressure at about 160 stations | station | 10 min, hourly, daily, monthly, yearly | live | free API (STAC) and file download, no key; CSV via STAC https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn | 5 | Valais stations available (e.g. Sion, Visp). Forecast products are documented in other opendatadocs sections (not opened). |
| **[OpenHolidays API (school and public holidays by canton)](https://www.openholidaysapi.org/en/)** | OpenHolidays project (openpotato) | Public holidays and school holidays per Swiss canton (ISO 3166-2 subdivisions) | canton | daily calendar | future years available | free API, no key; JSON, e.g. /SchoolHolidays?countryIsoCode=CH&subdivisionCode=CH-VS | 5 | Cross-check with EDK lists. |
| **[STATENT business structure statistics (workplaces and employees by canton and NOGA division)](https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0602010000_101/px-x-0602010000_101.px)** | BFS / OFS | Workplaces, employees and FTE by canton and 96 NOGA divisions | canton (all 26); commune in other tables | annual | 2024 | free API (PxWeb); PX/JSON/CSV | 3 | Valais/Vaud/Geneva available. |
| **[EDK/CDIP school holiday lists](https://edk.ch/de/bildungssystem/kantonale-schulorganisation/Schulferien)** | EDK / CDIP | School holidays per canton (and some communes) | canton | annual lists | 2026 and 2027 confirmed, 2028 provisional | free download; PDF | 3 | Use for history before 2020 (OpenHolidays starts 2020). |
| **[Valais construction employers circular 2026 (work calendar, summer site closure)](https://www.ave-wbv.ch/files/CIRCULAIRE2026-FR.pdf)** | AVE-WBV (Association valaisanne des entrepreneurs) | Annual working time 2,112 h; official summer closure of sites 3-10 Aug 2026; holiday rules; switch to calendar-year planning from 1 Jan 2027 | canton VS | annual | 2026 | free download; PDF | 3 | National collective agreement CN 2026-2031 PDF exists at shop.baumeister.swiss (found via search, not opened). |
| **[Swiss Post peak season parcel figures](https://www.srf.ch/news/schweiz/black-friday-ansturm-post-liefert-7-9-millionen-pakete-und-bricht-damit-rekord)** | Swiss Post (via SRF) | Black Friday week 2025: 7.9 million parcels (about +400,000 yoy), about 500 temp workers added, sorting up to 22 h/day, 370 extra delivery rounds per day | national | event-based (annual) | Black Friday week 2025 | free press; web | 2 | Use for calendar calibration of logistics peaks. Black Friday 2026 is Friday 27 November. |
| **[GS1 Logistics Market Study Switzerland (Logistikmarktstudie)](https://handelsverband.swiss/news/logistikmarktstudie-schweiz-01-26-die-zukunft-der-schweizer-logistik-beginnt-jetzt/)** | GS1 Switzerland with University of St. Gallen | Logistics market size, top 100 logistics providers, thematic analyses | national | 3 editions per year | 01/2026 (5 Mar 2026) | free download at https://lms.gs1.ch/de; PDF | 1 | Good for pitch numbers on market size. |

Calendar facts worth hard-coding (verified): Valais construction summer site closure 3 to 10 Aug 2026; annual working time 2,112 h in Valais main construction; Black Friday 2026 = Friday 27 Nov; Swiss Post added about 500 temps for the 2025 peak. MeteoSwiss station data and OpenHolidays give the other calendar features.

## 5. Top 5 signal and target pairings for a 24 hour prototype

All lead times below are hypotheses to test by back-testing against the target proxy, except where a study is cited.

### 5.1 Permit pulse to construction hiring (Romandie and Valais)

- **Signal:** weekly count of new building permit applications from SITG Geneva (filing date), FAO Vaud (summary list) and Bulletin officiel du Valais, split into new build vs transformation, with simap.ch construction awards (CPV 45) as a second input.
- **Predicts:** construction job postings in Swiss Job Tracker (ISCO 7 and NOGA F, cantons GE, VD, VS), checked against quarterly BESTA vacancies for 41-43.
- **Lead time:** 3 to 6 months for main works (gros oeuvre), 6 to 12 months for finishing trades (second oeuvre). Strauss (2013) found permits lead state employment by up to 4 quarters in the US.
- **Alert rule:** 13-week rolling count of new-build applications per canton, as a z-score against the same weeks of earlier years. Above +1.5: "rising demand in 3 to 6 months". Below -1.5: "falling demand". Then fit a lagged regression (permits at t-12 to t-26 weeks on job postings at t) to show the best lag.
- **Action:** the Flexsis branch in that canton starts building a pool of masons, crane operators and construction workers before the peak, and contacts the contractors who win the matching simap awards.
- **Why a jury would believe it:** the chain is intuitive (no permit, no site), the data is public and comes from the host region, and the alert can be shown on a map of Valais communes.

### 5.2 Weather shock and catch-up (construction)

- **Signal:** MeteoSwiss forecast and observed daily minimum temperature, snow and precipitation at stations near the main sites (for example Sion, Visp, Geneva, Pully), combined with the work calendar (Valais summer closure 3 to 10 Aug 2026, Christmas break, school holidays from OpenHolidays).
- **Predicts:** short-term drops in construction temp hours, then a catch-up peak. The bad weather compensation series of canton St. Gallen (monthly since 2016) gives the observed effect to calibrate on.
- **Lead time:** 2 to 14 days for the drop, 1 to 4 weeks for the catch-up.
- **Alert rule:** a rule on forecast days, for example Tmin below -5 C, more than 20 mm of rain in a day, or fresh snow. Two or more such days in the next 7 days: "redeploy". A run of 5 or more lost days: "catch-up demand expected", with size roughly proportional to the lost days.
- **Action:** move temps to indoor finishing work, industry or logistics during the shock, then warn clients and pre-book capacity for the rebound.
- **Why a jury would believe it:** it is easy to validate, it is very local to Valais, and it gives a visible short-horizon win next to the slower signals.

### 5.3 Industrial order pipeline (industry)

- **Signal:** order backlog, employment and delivery time subindices of the procure.ch PMI and the Raiffeisen SME PMI (monthly), the KOF Employment Indicator (quarterly), and BAZG monthly exports of machinery, metals and watches.
- **Predicts:** manufacturing postings in Swiss Job Tracker (NOGA C, ISCO 8) and BESTA employment and vacancies in divisions 10-33. The Swiss Staffingindex (industry drove the Q1 2026 temp rebound) is the qualitative check.
- **Lead time:** 1 to 3 months.
- **Alert rule:** backlog subindex above 50 for 2 consecutive months together with lengthening delivery times: "hiring wave". Composite below 50 together with CHF appreciation above 3% in a month (SNB API): "risk of cuts".
- **Action:** pre-qualify production operators, machine operators, welders and polymechanics, and propose temp-to-perm to clients whose sector is accelerating.
- **Why a jury would believe it:** PMIs are standard leading indicators and Flexsis already knows the industrial sector well. The SME PMI matches Flexsis' client base.

### 5.4 Retail calendar to warehouse peak (logistics)

- **Signal:** a fixed calendar (Black Friday 27 Nov 2026, Christmas, January sales), year-on-year growth in e-commerce card spending (HSG Monitoring Consumption), BAZG imports of consumer goods, and ASTRA heavy vehicle counts near hubs.
- **Predicts:** warehouse operator, forklift driver and delivery driver demand (Job Tracker ISCO 8 and 9, NOGA H). Swiss Post's 2025 peak (7.9 million parcels in Black Friday week, about 500 extra temps) is the reference.
- **Lead time:** recruitment needs to start 6 to 8 weeks before the peak, which means early October for 2026.
- **Alert rule:** expected peak size = last year's peak multiplied by (1 + e-commerce spending growth over the last 8 weeks). Alert at T-8 weeks with the expected headcount gap per region.
- **Action:** the client gets a staffing plan for the peak, and Flexsis trains a forklift-certified pool in September and October.
- **Why a jury would believe it:** the timing is real (the event is 8 weeks after the hackathon), the value is clear, and the peak is measured.

### 5.5 Cycle turning points (all three sectors)

- **Signal:** the SECO Weekly Economic Activity index (CSV), the KOF Economic Barometer (API) and Google Trends for job-search terms in FR, DE and IT (for example "emploi temporaire", "Temporärjob", "lavoro temporaneo", "cariste", "Staplerfahrer"), plus SECO short-time work as a lagging confirmation.
- **Predicts:** turning points in total postings (Job Tracker) and BESTA vacancies.
- **Lead time:** 1 to 3 months. Borup and Montes Schuette found Google job-search data predicts US employment growth at 1 to 12 month horizons.
- **Alert rule:** a simple dynamic factor or the average z-score of the three; a change of sign held for 4 weeks.
- **Action:** Flexsis shifts recruiting budget between sectors, and clients get a heads-up for headcount planning.
- **Why a jury would believe it:** it is the macro layer that frames the sector alerts; on its own it is weaker for innovation.

## 6. Prior work

- **Swiss Job Tracker methodology** (Bannert, Klaeui, Kopp, Siegenthaler, Thoeni, Winkelmann; KOF / UNIL with x28): weekly postings index from 2018, correlation 0.96 with BESTA vacancies, available weeks before BESTA. [PDF](https://swissjobtracker.ch/Methodology%20Swiss%20Job%20Tracker.pdf)
- **Strauss (2013), Journal of Urban Economics 73(1)**: building permits lead US state employment and income growth, beat the leading index at 4 quarters ahead, and fell before every recession since 1970. [link](https://www.sciencedirect.com/science/article/abs/pii/S0094119012000575)
- **Borup and Montes Schuette (2019 working paper), "In search of a job: forecasting employment growth using Google Trends"**: 173 job-search terms; out-of-sample R2 of 26% to 59%, best at 12 months with random forests (US data). [PDF](https://scispace.com/pdf/in-search-of-a-job-forecasting-employment-growth-using-3ehs05bxkl.pdf)
- **trendEcon (KOF, SECO, HSG, cynkra and others, 2020)** and **Eichenauer et al. (2022), Economic Inquiry 60(2)**: a method and R package for consistent daily Google Trends series, applied to Switzerland. [KOF Bulletin](https://kof.ethz.ch/en/news-and-events/kof-bulletin/kof-bulletin/2020/05/trendecon-taegliche-wirtschaftsindikatoren-basierend-auf-schweizer-google-suchtrends.html), [GitHub](https://github.com/trendecon/trendecon)
- **Sacchi et al. (2008) and the Stellenmarkt-Monitor Schweiz publications (UZH)**: methodology of the Adecco Swiss Job Market Index as a job-ad based labour demand measure; later work on mismatch and tightness (Buchs and Sacchi 2017). [list](https://www.stellenmarktmonitor.uzh.ch/en/publications.html)
- **KOF Employment Indicator press releases**: they report sector differences and the use of the indicator as a 3-month employment outlook. [2026 release](https://kof.ethz.ch/en/news-and-events/media/press-releases/2026/05/kof-employment-indicator.html) (title from search, not opened)
- **Monitoring Consumption Switzerland (Swiss Journal of Economics and Statistics, 2023)**: describes the card-transaction data and its use cases. Title from search, paper not opened. [link](https://link.springer.com/article/10.1186/s41937-023-00108-9)
- **Schaupp and Meier (2026), Work, Employment and Society**: climate vulnerability and work organisation on Swiss construction sites. Title from search, not opened. [DOI](https://doi.org/10.1177/09500170251386757)
- **Liu and Hirsch, "Does winter weather decrease work?" / "Winter weather and work hours"** (Contemporary Economic Policy): winter weather reduces hours, with regional adaptation. Title from search, not opened. [link](https://onlinelibrary.wiley.com/doi/10.1111/coep.12516)
- No public study on forecasting Swiss temp staffing demand was found. The Swiss Staffingindex press releases describe temp hours as an early cycle indicator, but give no quantified lead.

## 7. Unverified leads and known gaps

### 7.1 Probably exists, could not be opened or confirmed

| Lead | Why unverified | Priority |
|---|---|---|
| BFS production, orders and turnover in the secondary sector, monthly series (opendata.swiss dataset "produktions-auftrags-und-umsatzstatistik-im-sekundaren-sektor-monatliche-zeitreihen") | opendata.swiss returned 403 to our fetcher; bfs.admin.ch blocked by robots.txt | High: probably the best official industry order signal by NOGA division |
| BFS retail trade turnover, monthly (Detailhandelsumsatzstatistik, DHU) | bfs.admin.ch blocked; PxWeb table 0603030000 found only covers services turnover 2010-2022 | Medium |
| BFS Swiss Labour Force Survey (SAKE/ESPA), cross-border commuter statistics (GGS, Q1 2026 release seen in search), construction price index | bfs.admin.ch blocked; tables not found in the PxWeb list | Medium (GGS by canton matters for VS/GE/TI) |
| Canton Zurich "Baugesuche im Kanton Zuerich" (opendata.swiss) and Basel-Landschaft permits by commune 1991-2024 (i14y) | 403 / page without dataset content | Medium (German-speaking permit feeds) |
| Valais monthly labour market bulletin ("Situation marche travail") and Valais labour shortage report (vs.ch) | vs.ch blocked by robots.txt | High for the pitch (local figures) |
| SECO list of occupations under the job reporting obligation 2026 (arbeit.swiss PDF) | PDF URL returned 404; the policy page exists (threshold 5%) | Medium |
| Job-Room API (api.job-room.ch, test-api.job-room.ch) | docs blocked by robots.txt; seems to be for publishing ads, read access unclear | Low |
| KOF Datenservice series keys for Job Tracker by canton and occupation, and KOF business survey series for construction and manufacturing | metadata endpoint found via search only; sector survey keys appear restricted | High (key discovery for Job Tracker) |
| Baublatt / Docu Media Infomanager and monthly permit statistics | page returned 500; product is paid | Low for 24 h |
| SNB regional business cycle reports (content), Swissmem statistics page, Zurich Airport official traffic page, Swiss Post annual parcel volumes | not opened | Low |
| Heavy vehicle fee (LSVA) statistics, fuel prices, ASTAG figures, Wueest Partner, scienceindustries | only general pages or nothing found | Low |
| National collective agreement CN 2026-2031 (shop.baumeister.swiss PDF) | not opened | Medium (winter break rules) |

### 7.2 Does not seem to exist publicly

- A temp hours or temp headcount series by sector and canton (swissstaffing publishes only national quarterly changes).
- A national open feed of building permit applications (cantonal formats differ; the national aggregation is commercial).
- A national open series of bad weather compensation by canton and month (only canton St. Gallen publishes it cleanly).
- Indeed Hiring Lab job postings data for Switzerland (the public repo covers AU, CA, DE, ES, FR, GB, IE, IT, NL and US only).
- Job board data with history (jobs.ch and jobup.ch block their API and job detail pages in robots.txt).

## 8. Machine readable catalogue

The same array is saved as `flexsis_catalogue_construction_logistics_industry.json` next to this report.

```json
[
  {
    "name": "Swiss Job Tracker (weekly online job postings index)",
    "publisher": "KOF ETH Zurich, University of Lausanne, data by x28 AG",
    "url": "https://kof.ethz.ch/en/forecasts-and-indicators/indicators/swiss-job-tracker.html",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Weekly count of unique online job postings (job boards + company websites, duplicates and recruitment agency postings removed), indexed Jan 2020 = 100; split by ISCO-08 1-digit occupation, NOGA 1-digit sector and canton",
    "geo_granularity": "canton (all 26), national",
    "time_granularity": "weekly",
    "history_start": "2018-01",
    "publication_lag": "about 1 week (hypothesis, weekly dashboard)",
    "latest_data_point": "weekly, current (exact week not read)",
    "access": "free API (public tsdb-api endpoint); dashboard swissjobtracker.ch",
    "format": "XLSX/CSV/JSON via https://tsdb-api.kof.ethz.ch/v2/ts?keys=ch.kof.jobtracker.total.total.clean.idx&mime=xlsx&access_type=public",
    "licence": "public data per KOF page; cite KOF/x28",
    "cost": "free",
    "lead_time_hypothesis": "Target proxy. Methodology paper reports correlation 0.96 with BFS BESTA vacancies and release weeks before BESTA, so it can also nowcast BESTA by about 2 months",
    "usability_score": 4,
    "notes": "Best free target proxy. ISCO 7 (craft trades: masons, electricians, welders), ISCO 8 (machine operators, drivers) and ISCO 9 (labourers, warehouse helpers) map well to Flexsis temp roles; NOGA F, C, H map to the three subsectors. Agency postings are removed, so temp demand is seen only indirectly. Keys for canton/occupation series must be discovered (KOF metadata endpoint found via search, not opened). Valais, Vaud, Geneva covered."
  },
  {
    "name": "BESTA job vacancies by NOGA division",
    "publisher": "BFS / OFS (Federal Statistical Office)",
    "url": "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0602000000_103/px-x-0602000000_103.px",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Number of open positions, index (Q2 2015=100) and vacancy rate, by selected NOGA divisions (incl. manufacturing subdivisions such as 28 machinery, and construction)",
    "geo_granularity": "national",
    "time_granularity": "quarterly",
    "history_start": "1992-Q2",
    "publication_lag": "about 2 months after quarter end (hypothesis; Q2 2026 available on 3 Oct 2026)",
    "latest_data_point": "2026-Q2",
    "access": "free API (PxWeb, POST JSON query to the URL) and STAT-TAB web UI",
    "format": "PX/JSON/CSV via PxWeb API",
    "licence": "BFS open data terms (attribution)",
    "cost": "free",
    "lead_time_hypothesis": "Target variable (official). Quarterly and lagged, so use as ground truth to validate faster signals",
    "usability_score": 3,
    "notes": "Table id px-x-0602000000_103. Only 20 selected divisions; check whether 49-53 transport/storage is split. bfs.admin.ch pages were blocked to our fetcher by robots.txt, but the PxWeb API answered."
  },
  {
    "name": "BESTA job vacancies by large region",
    "publisher": "BFS / OFS",
    "url": "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0602000000_104/px-x-0602000000_104.px",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Open positions, index and vacancy rate by Grossregion (Region lemanique = VD, VS, GE; Espace Mittelland; NW CH; Zurich; East; Central; Ticino)",
    "geo_granularity": "region (7 large regions)",
    "time_granularity": "quarterly",
    "history_start": "1997-Q1",
    "publication_lag": "about 2 months (hypothesis)",
    "latest_data_point": "2026-Q2",
    "access": "free API (PxWeb)",
    "format": "PX/JSON/CSV",
    "licence": "BFS open data terms",
    "cost": "free",
    "lead_time_hypothesis": "Target variable at regional level",
    "usability_score": 3,
    "notes": "No sector split. Valais only inside Region lemanique."
  },
  {
    "name": "BESTA employment by NOGA division (incl. division 78 employment activities)",
    "publisher": "BFS / OFS",
    "url": "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0602000000_101/px-x-0602000000_101.px",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Employees by NOGA division (41-43, 41-42, 43; 10-33 subdivisions; 49, 52, 53; 78 personnel services = temp agencies), by employment level and sex",
    "geo_granularity": "national",
    "time_granularity": "quarterly",
    "history_start": "1991-Q3",
    "publication_lag": "about 2 months (hypothesis)",
    "latest_data_point": "2026-Q2",
    "access": "free API (PxWeb)",
    "format": "PX/JSON/CSV",
    "licence": "BFS open data terms",
    "cost": "free",
    "lead_time_hypothesis": "Division 78 employment is the closest official proxy for temp worker stock; hypothesis: it moves 1-2 quarters before employment in 10-33 and 41-43",
    "usability_score": 3,
    "notes": "Table px-x-0602000000_102 gives the same by large region but only sectors II/III."
  },
  {
    "name": "Swiss Staffingindex (temp work hours and permanent placements)",
    "publisher": "swissstaffing (with Adecco Group commentary)",
    "url": "https://www.organisator.ch/en/human-resources/hrm/2026-04-29/swiss-staffingindex-temporaermarkt-dreht-nach-drei-jahren-ins-plus/",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Year-on-year change in hours worked by temp workers and in permanent placements by member staffing firms",
    "geo_granularity": "national, with qualitative regional comments (e.g. Eastern Switzerland -2.2%, Mittelland +5.5% in Q1 2026)",
    "time_granularity": "quarterly (plus half-year summary)",
    "history_start": "not verified",
    "publication_lag": "about 1 month after quarter end (Q1 2026 released 29 Apr 2026)",
    "latest_data_point": "2026-Q2 / H1 2026 (temp hours +1.5% yoy)",
    "access": "press releases only; no downloadable series found",
    "format": "web text / press release",
    "licence": "not stated",
    "cost": "free (press releases)",
    "lead_time_hypothesis": "Closest concept to Flexsis demand; use as the quarterly ground truth for the temp market",
    "usability_score": 2,
    "notes": "Q1 2026 was the first positive quarter after 12 declines (+1.3%), driven by industrial clusters (watches). No sector or canton series published. swissstaffing.ch pages were blocked to our fetcher; content read via press reprints (swiss-press.com, organisator.ch)."
  },
  {
    "name": "SECO AMSTAT (unemployed, job seekers, registered vacancies, short-time work)",
    "publisher": "SECO",
    "url": "https://www.amstat.ch/v2/amstat_de.html",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Registered unemployed and job seekers by occupation and economic division, registered vacancies (Job-Room/RAV), allowance recipients, short-time work",
    "geo_granularity": "canton, district (Bezirk), national",
    "time_granularity": "monthly",
    "history_start": "not verified in UI",
    "publication_lag": "about 1 week for unemployment (monthly report around the 6th-7th); about 3 months for short-time work",
    "latest_data_point": "August 2026 (monthly report listed on arbeit.swiss)",
    "access": "free web application (JS app; no public REST API according to the seco-labor-mcp project)",
    "format": "interactive tables; export options not verified",
    "licence": "official statistics, attribution",
    "cost": "free",
    "lead_time_hypothesis": "Registered vacancies in construction occupations: target proxy. Falling unemployment of masons/drivers in a canton = tightening supply, hypothesis 0-1 month lead on temp rates",
    "usability_score": 4,
    "notes": "Canton and occupation detail including Valais, Vaud, Geneva. Vacancies are biased toward occupations under the job reporting obligation (threshold 5% unemployment), which includes many construction and logistics occupations."
  },
  {
    "name": "Die Lage auf dem Arbeitsmarkt (monthly labour market report)",
    "publisher": "SECO",
    "url": "https://www.seco.admin.ch/dam/de/sd-web/3dmYe3hl-IiX/2026-01_Die_Lage_auf_dem_Arbeitsmarkt_DE.pdf",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Unemployed by sector (e.g. construction 14,116 in Jan 2026, +4.1% m/m; industry sector II 35,694), registered vacancies (48,904 in Jan 2026), short-time work (affected workers, units)",
    "geo_granularity": "national and canton tables",
    "time_granularity": "monthly",
    "history_start": "archive of monthly PDFs (2024+ seen)",
    "publication_lag": "about 1 week; short-time work refers to month t-3 (Oct 2025 in the Jan 2026 report)",
    "latest_data_point": "August 2026",
    "access": "free download",
    "format": "PDF",
    "licence": "official publication",
    "cost": "free",
    "lead_time_hypothesis": "Construction unemployment has a strong winter seasonality, useful to calibrate the seasonal baseline",
    "usability_score": 3,
    "notes": "Index page: https://www.arbeit.swiss/en/information-centre/labour-market-statistics-switzerland"
  },
  {
    "name": "Short-time work and bad weather compensation statistics (canton St. Gallen)",
    "publisher": "Kanton St. Gallen, Fachstelle fuer Statistik",
    "url": "https://www.sg.ch/ueber-den-kanton-st-gallen/statistik/themen/B03/kurzarbeit-schlechtwetterentschaedigung.html",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Firms, employees, CHF paid and lost hours under short-time work and under bad weather compensation (Schlechtwetterentschaedigung), split industry / trades / services, with Swiss comparison",
    "geo_granularity": "canton SG and electoral districts, CH comparison",
    "time_granularity": "monthly (annual totals 2015-2025)",
    "history_start": "2016 (monthly)",
    "publication_lag": "updated 4 Aug 2026, includes advance registrations for Aug 2026",
    "latest_data_point": "August 2026 (advance registrations)",
    "access": "free download",
    "format": "XLS, PDF, OGD",
    "licence": "OGD",
    "cost": "free",
    "lead_time_hypothesis": "Bad weather compensation is a direct, observable effect of weather on construction work; use it to calibrate weather rules for construction temp demand (same month)",
    "usability_score": 3,
    "notes": "Only canton SG publishes this cleanly; no national bad-weather series was found in open form."
  },
  {
    "name": "Statistique Vaud: unemployment and job vacancies",
    "publisher": "Statistique Vaud (Canton de Vaud)",
    "url": "https://www.vd.ch/etat-droit-finances/statistique/statistiques-par-domaine/03-vie-active-remuneration-du-travail/chomage-et-places-vacantes",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Job seekers, unemployed and rates by district and month; vacancies by economic activity (annual averages); based on SECO data",
    "geo_granularity": "canton VD, district, commune",
    "time_granularity": "monthly (vacancies by sector annual)",
    "history_start": "1992 (unemployment), 2004 (vacancies)",
    "publication_lag": "about 1 month (hypothesis)",
    "latest_data_point": "monthly, current (exact month not read)",
    "access": "free download",
    "format": "XLSX",
    "licence": "official statistics, attribution",
    "cost": "free",
    "lead_time_hypothesis": "Target proxy for the Renens HQ region",
    "usability_score": 4,
    "notes": "French speaking canton; useful for Flexsis home market."
  },
  {
    "name": "Adecco Group Swiss Job Market Index",
    "publisher": "Adecco Group Switzerland and Stellenmarkt-Monitor Schweiz (University of Zurich)",
    "url": "https://www.adeccogroup.com/de-ch/zukunft-der-arbeit/job-index/job-index-q1-2026",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Number of publicly advertised positions (press, company websites, job portals); quarterly change; occupational groups incl. construction and finishing trades, industrial and craft specialists",
    "geo_granularity": "national; 6 regions on the UZH page",
    "time_granularity": "quarterly",
    "history_start": "2008-03",
    "publication_lag": "about 1 month (Q2 2026 release in July 2026)",
    "latest_data_point": "2026-Q2",
    "access": "PDF study and press release; UZH page offers Excel index files",
    "format": "PDF; XLSX (UZH page)",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Target proxy (job ads), slower than Swiss Job Tracker",
    "usability_score": 2,
    "notes": "UZH page https://www.stellenmarktmonitor.uzh.ch/de/indices/asjmi.html shows downloads but the visible latest release there was 2019, so the Excel may be stale; current figures only in Adecco PDFs (Q1 2026: +0.7% q/q)."
  },
  {
    "name": "x28 Jobradar",
    "publisher": "x28 AG",
    "url": "https://www.jobundkarriereblog.ch/jobradar-2-quartal-2026/",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Job ads crawled from employer websites: counts by canton, industry, top occupations; direct employer vs agency",
    "geo_granularity": "canton",
    "time_granularity": "quarterly",
    "history_start": "not verified",
    "publication_lag": "about 1 month",
    "latest_data_point": "2026-Q2 (construction industry 12,852 postings, 2nd largest)",
    "access": "free basic report; Pro version paid",
    "format": "web article / report",
    "licence": "proprietary",
    "cost": "free basic, paid Pro",
    "lead_time_hypothesis": "Target proxy; quarterly snapshots only in the free version",
    "usability_score": 2,
    "notes": "x28 is also the data provider behind Swiss Job Tracker; contact for raw data is a paid option."
  },
  {
    "name": "STATENT business structure statistics (workplaces and employees by canton and NOGA division)",
    "publisher": "BFS / OFS",
    "url": "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0602010000_101/px-x-0602010000_101.px",
    "subsector": "cross-sector",
    "role": "context",
    "measures": "Workplaces, employees and FTE by canton and 96 NOGA divisions",
    "geo_granularity": "canton (all 26); commune in other tables",
    "time_granularity": "annual",
    "history_start": "2011",
    "publication_lag": "about 20 months (2024 is latest on 3 Oct 2026)",
    "latest_data_point": "2024",
    "access": "free API (PxWeb)",
    "format": "PX/JSON/CSV",
    "licence": "BFS open data terms",
    "cost": "free",
    "lead_time_hypothesis": "No lead. Use as weights to turn national signals into canton estimates (share of construction or logistics employees per canton)",
    "usability_score": 3,
    "notes": "Valais/Vaud/Geneva available."
  },
  {
    "name": "jobs.ch / jobup.ch job boards (scraping only)",
    "publisher": "JobCloud AG",
    "url": "https://www.jobs.ch/robots.txt",
    "subsector": "cross-sector",
    "role": "target proxy",
    "measures": "Live job ads by keyword and location",
    "geo_granularity": "commune/region",
    "time_granularity": "daily",
    "history_start": "none (only current ads)",
    "publication_lag": "real time",
    "latest_data_point": "live",
    "access": "scraping only; robots.txt disallows /api/ and job detail pages (/de/stellenangebote/detail/...) for all agents; terms of use not reviewed",
    "format": "HTML",
    "licence": "proprietary",
    "cost": "free to view",
    "lead_time_hypothesis": "Real-time target proxy, but no history",
    "usability_score": 1,
    "notes": "Not recommended in 24 h: no history and legal risk. Prefer Swiss Job Tracker."
  },
  {
    "name": "Building permit applications, Geneva (SITG 'Autorisation de construire - Dossier')",
    "publisher": "Canton de Geneve, SITG / Office des autorisations de construire",
    "url": "https://sitg.ge.ch/donnees/sit-autor-dossier",
    "subsector": "construction",
    "role": "leading signal",
    "measures": "Each building permit file with location, operation type, filing date (DATE_DEPOT), status and last update",
    "geo_granularity": "parcel / point (canton GE)",
    "time_granularity": "daily updates (event data)",
    "history_start": "dataset published 12 Jun 2025; depth of historical files not verified",
    "publication_lag": "1 day",
    "latest_data_point": "metadata updated 2026-10-03",
    "access": "free API (WFS, ArcGIS REST, WMS); also on opendata.swiss",
    "format": "WFS/GeoJSON, ArcGIS REST",
    "licence": "open access (SITG 'acces libre')",
    "cost": "free",
    "lead_time_hypothesis": "Hypothesis: filings lead site starts by 3-9 months (instruction + tender); main works hiring 3-6 months after filing, finishing trades 6-12 months",
    "usability_score": 4,
    "notes": "Best machine-readable permit source in Romandie. Aggregate weekly counts by operation type (new build vs transformation)."
  },
  {
    "name": "Bulletin officiel du Valais: building permit applications",
    "publisher": "Canton du Valais / Bulletin officiel",
    "url": "https://www.bulletinvalaiswallis.ch/fr/articles/annonces-officielles/",
    "subsector": "construction",
    "role": "leading signal",
    "measures": "Published building permit applications ('demande d'autorisation de construire') and other official notices",
    "geo_granularity": "commune (filter by all Valais communes)",
    "time_granularity": "weekly edition, items dated",
    "history_start": "archive pages back to at least 2025 (about 4,700 items paginated)",
    "publication_lag": "same week",
    "latest_data_point": "live",
    "access": "free web access; scraping needed (no API found); reuse terms not stated",
    "format": "HTML list (plus e-paper)",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Same hypothesis as Geneva permits: 3-9 months to site start in Valais; strong spring seasonality in mountain communes",
    "usability_score": 3,
    "notes": "Only free Valais permit flow found. Check terms with publisher before automated collection; a polite low-frequency crawl of the list page is the minimum."
  },
  {
    "name": "FAO Vaud: building permit enquiries ('permis de construire')",
    "publisher": "Feuille des avis officiels du canton de Vaud",
    "url": "https://www.faovd.ch/permis-de-construire/district/lausanne/",
    "subsector": "construction",
    "role": "leading signal",
    "measures": "Building permit enquiries with date, commune, CAMAC number, nature of works (new, transformation, renovation), description",
    "geo_granularity": "district / commune (VD)",
    "time_granularity": "edition-based (about 100 editions per year)",
    "history_start": "editions 2025-2026 seen",
    "publication_lag": "same day",
    "latest_data_point": "2026-10-02 entry seen",
    "access": "summary list free; full content for subscribers; scraping terms not stated",
    "format": "HTML",
    "licence": "proprietary (subscription model)",
    "cost": "summary free, full text paid",
    "lead_time_hypothesis": "Lead 3-9 months to site start (hypothesis)",
    "usability_score": 3,
    "notes": "Count notices per district per week from the free list. Covers Flexsis HQ area (Renens, Lausanne)."
  },
  {
    "name": "simap.ch public procurement API",
    "publisher": "Verein simap.ch (Confederation, cantons, communes)",
    "url": "https://github.com/Digilac/simap-mcp",
    "subsector": "construction",
    "role": "leading signal",
    "measures": "Public tenders and awards, searchable by text, dates, tender type, canton, CPV code, BKP (construction cost code), NPK, OAG",
    "geo_granularity": "canton / contracting authority",
    "time_granularity": "daily (event data)",
    "history_start": "not verified (new platform since 2024)",
    "publication_lag": "real time",
    "latest_data_point": "live",
    "access": "free API, read-only, no key (per the open source MCP server README)",
    "format": "JSON (REST); docs at https://www.simap.ch/api-doc/ (behind cookie wall for our fetcher)",
    "licence": "not verified",
    "cost": "free",
    "lead_time_hypothesis": "Hypothesis: award notices for civil engineering and building works lead on-site staffing by 1-4 months; tender publication by 3-9 months",
    "usability_score": 4,
    "notes": "Filter CPV 45xxxxxx (construction work) and BKP codes; sum award values per canton per month. Covers Valais and Romandie."
  },
  {
    "name": "SBV quarterly survey (Quartalserhebung): turnover, order intake, order backlog",
    "publisher": "Schweizerischer Baumeisterverband (SSE/SBV)",
    "url": "https://baumeister.swiss/baumeister-5-0/konjunktur-statistiken/baukonjunktur/",
    "subsector": "construction",
    "role": "leading signal",
    "measures": "Main construction trade turnover, order intake, work backlog (Arbeitsvorrat), employment; Hochbau vs Tiefbau; regional and size breakdowns",
    "geo_granularity": "national and regions",
    "time_granularity": "quarterly",
    "history_start": "not verified",
    "publication_lag": "about 8 weeks (Q2 2026 released 26 Aug 2026)",
    "latest_data_point": "2026-Q2 (turnover CHF 6.2 bn, +1.3%; H1 order intake +1.6%; backlog about 8 months)",
    "access": "press releases free; full tables possibly members only (not verified)",
    "format": "web page / PDF",
    "licence": "not stated",
    "cost": "free summaries",
    "lead_time_hypothesis": "Order intake and backlog lead main works employment by 1-3 quarters (hypothesis, backlog of 8 months implies long pipeline)",
    "usability_score": 3,
    "notes": "Main works (gros oeuvre) only; no second oeuvre."
  },
  {
    "name": "SBV Bauindex",
    "publisher": "Schweizerischer Baumeisterverband (with Credit Suisse until Q3 2023)",
    "url": "https://baumeister.swiss/baumeister-5-0/konjunktur-statistiken/bauindex/",
    "subsector": "construction",
    "role": "leading signal",
    "measures": "Forecast of seasonally adjusted main construction turnover for the next quarter and trend for the following three quarters",
    "geo_granularity": "national",
    "time_granularity": "quarterly",
    "history_start": "re-based Q1 2023 = 100 (older CS series exists)",
    "publication_lag": "published at start of quarter",
    "latest_data_point": "2026-Q3 (+1.4% yoy)",
    "access": "web page; series download not found",
    "format": "web / PDF",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Designed as a 1-quarter-ahead turnover forecast",
    "usability_score": 3,
    "notes": "Use as a sanity check, not a model input (structural break 2023)."
  },
  {
    "name": "BFS construction investment and work backlog by canton/commune",
    "publisher": "BFS / OFS",
    "url": "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0904010000_203/px-x-0904010000_203.px",
    "subsector": "construction",
    "role": "leading signal",
    "measures": "Construction investments and work backlog for the following year, by client type (public/private) and building category; companion table px-x-0904010000_201 adds maintenance and new vs renovation",
    "geo_granularity": "large region, canton, commune",
    "time_granularity": "annual",
    "history_start": "1994",
    "publication_lag": "about 20 months",
    "latest_data_point": "2024",
    "access": "free API (PxWeb)",
    "format": "PX/JSON/CSV",
    "licence": "BFS open data terms",
    "cost": "free",
    "lead_time_hypothesis": "Next-year backlog leads annual construction employment by about 1 year (hypothesis)",
    "usability_score": 2,
    "notes": "Annual only; useful for canton weights and long-run context (Valais public vs private split)."
  },
  {
    "name": "BFS building projects (Bauvorhaben) by canton/commune",
    "publisher": "BFS / OFS",
    "url": "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0904010000_112/px-x-0904010000_112.px",
    "subsector": "construction",
    "role": "leading signal",
    "measures": "Building projects by canton/commune, client category, building type and year (see also px-x-0904010000_111 with type of work)",
    "geo_granularity": "canton, commune",
    "time_granularity": "annual",
    "history_start": "not verified",
    "publication_lag": "about 20 months (hypothesis)",
    "latest_data_point": "not verified (likely 2024)",
    "access": "free API (PxWeb)",
    "format": "PX/JSON/CSV",
    "licence": "BFS open data terms",
    "cost": "free",
    "lead_time_hypothesis": "Annual pipeline indicator",
    "usability_score": 2,
    "notes": "Too slow for alerts; good for back-testing by canton."
  },
  {
    "name": "SNB data portal API (interest rates, mortgage rates, exchange rates)",
    "publisher": "Swiss National Bank",
    "url": "https://data.snb.ch/api/cube/zikrepro/data/csv/en",
    "subsector": "cross-sector",
    "role": "leading signal",
    "measures": "Data cubes by id, e.g. zikrepro (interest rates incl. historical mortgage series) and devkum (monthly FX rates); verify dimension codes per cube",
    "geo_granularity": "national",
    "time_granularity": "monthly (some daily)",
    "history_start": "decades (devkum from 1916)",
    "publication_lag": "days",
    "latest_data_point": "cube publishing date 2026-10-01",
    "access": "free API, no key",
    "format": "CSV/JSON via https://data.snb.ch/api/cube/<id>/data/csv/en",
    "licence": "SNB terms (attribution)",
    "cost": "free",
    "lead_time_hypothesis": "Mortgage rates lead permit filings by 6-12 months (hypothesis); CHF appreciation leads export-industry hiring declines by 3-6 months (hypothesis)",
    "usability_score": 4,
    "notes": "Pick cube ids in the portal; zikrepro dimension codes not decoded during this search."
  },
  {
    "name": "KOF Employment Indicator",
    "publisher": "KOF Swiss Economic Institute, ETH Zurich",
    "url": "https://kof.ethz.ch/prognosen-indikatoren/indikatoren/kof-beschaeftigungsindikator.html",
    "subsector": "cross-sector",
    "role": "leading signal",
    "measures": "Balance of firms' employment expectations for the next 3 months (9 industries, about 85% of private employment)",
    "geo_granularity": "national",
    "time_granularity": "quarterly",
    "history_start": "not verified (methodology 2017)",
    "publication_lag": "released in the first month of the quarter (Q3 2026 on 3 Aug 2026)",
    "latest_data_point": "2026-Q3 (2.1 points)",
    "access": "free API",
    "format": "XLSX via https://tsdb-api.kof.ethz.ch/v2/ts?keys=ch.kof.ie.retro.ch_total.ind.d11,ch.kof.ie.retro.ch_total.ass.d11,ch.kof.ie.retro.ch_total.exp.d11&mime=xlsx&access_type=public",
    "licence": "open use with source (opendata.swiss listing)",
    "cost": "free",
    "lead_time_hypothesis": "Explicit 3-month hiring intention, so lead about 1 quarter",
    "usability_score": 3,
    "notes": "Sector series (construction, manufacturing) exist in KOF surveys but public keys not confirmed. API returned data, our fetcher could not parse it; test in Python."
  },
  {
    "name": "KOF Economic Barometer",
    "publisher": "KOF Swiss Economic Institute, ETH Zurich",
    "url": "https://datenservice.kof.ethz.ch/",
    "subsector": "cross-sector",
    "role": "leading signal",
    "measures": "Composite leading indicator of Swiss GDP growth",
    "geo_granularity": "national",
    "time_granularity": "monthly",
    "history_start": "not verified",
    "publication_lag": "end of month (same month)",
    "latest_data_point": "September 2026 (109.1 per secondary source)",
    "access": "free API (public endpoint, key 'kofbarometer')",
    "format": "JSON/CSV/XLSX via https://datenservice.kof.ethz.ch/api/v1/public/ts?keys=kofbarometer&mime=csv",
    "licence": "KOF terms",
    "cost": "free",
    "lead_time_hypothesis": "General cycle signal, about 3-6 months ahead of employment (hypothesis)",
    "usability_score": 4,
    "notes": "API documented on the open docs page; the data URL itself was blocked to our fetcher by robots.txt, test locally."
  },
  {
    "name": "SECO Weekly Economic Activity index (WEA / WWA)",
    "publisher": "SECO",
    "url": "https://www.seco.admin.ch/en/index-weekly-economic-activity",
    "subsector": "cross-sector",
    "role": "leading signal",
    "measures": "Experimental weekly index of economic activity built from daily/weekly indicators, highly correlated with GDP growth",
    "geo_granularity": "national",
    "time_granularity": "weekly",
    "history_start": "not verified",
    "publication_lag": "about 1-2 weeks (week 37 published 23 Sep 2026)",
    "latest_data_point": "2026-W37",
    "access": "free download",
    "format": "CSV https://scheduler.swissdatas.ch/scheduled/wwa.csv ; XLSX per release",
    "licence": "official statistics, attribution",
    "cost": "free",
    "lead_time_hypothesis": "Nowcast of the cycle; turning points visible 1-2 months before monthly data (hypothesis)",
    "usability_score": 4,
    "notes": "National only."
  },
  {
    "name": "SNB Business cycle signals (regional network)",
    "publisher": "Swiss National Bank",
    "url": "https://www.snb.ch/en/publications/business-cycle-signals/2026/quartbul_2026_1_konj",
    "subsector": "cross-sector",
    "role": "leading signal",
    "measures": "Qualitative findings from SNB delegates' talks with companies across regions (staffing, capacity, outlook)",
    "geo_granularity": "regions (qualitative)",
    "time_granularity": "quarterly",
    "history_start": "long archive",
    "publication_lag": "same quarter",
    "latest_data_point": "2026 issues 1-3",
    "access": "free download",
    "format": "PDF",
    "licence": "SNB terms",
    "cost": "free",
    "lead_time_hypothesis": "Qualitative, useful to justify alerts in a pitch",
    "usability_score": 2,
    "notes": "Content of the PDF not read."
  },
  {
    "name": "BAZG foreign trade statistics (SwissImpex, open data, canton files)",
    "publisher": "Federal Office for Customs and Border Security (BAZG/OFDF)",
    "url": "https://www.bazg.admin.ch/de/schweizerische-aussenhandelsstatistik-aktuelle-daten",
    "subsector": "industry",
    "role": "leading signal",
    "measures": "Exports and imports by goods (CPA, SITC, tariff numbers) and country; seasonally adjusted series; canton exports/imports annual Excel 2016-2025",
    "geo_granularity": "national (monthly), canton (annual)",
    "time_granularity": "monthly; canton annual",
    "history_start": "decades nationally; canton 2016",
    "publication_lag": "about 3-4 weeks for monthly data (hypothesis)",
    "latest_data_point": "monthly, current (exact month not read)",
    "access": "free: SwissImpex dashboard, opendata.swiss datasets, Excel",
    "format": "CSV/XLSX",
    "licence": "OGD (attribution)",
    "cost": "free",
    "lead_time_hypothesis": "Exports of machinery, metals, watches lead production hiring by 1-3 months (hypothesis); imports of consumer goods lead warehouse volumes by 2-6 weeks (hypothesis)",
    "usability_score": 4,
    "notes": "Canton page: https://www.bazg.admin.ch/bazg/de/home/themen/schweizerische-aussenhandelsstatistik/daten/kantone.html ; price list exists for custom extractions."
  },
  {
    "name": "procure.ch Purchasing Managers' Index (PMI) manufacturing",
    "publisher": "procure.ch (sponsored by UBS)",
    "url": "https://www.procure.ch/magazin",
    "subsector": "industry",
    "role": "leading signal",
    "measures": "Manufacturing PMI with subindices (employment, delivery times, order backlog, production, purchase volume, inventories)",
    "geo_granularity": "national",
    "time_granularity": "monthly",
    "history_start": "not verified",
    "publication_lag": "first working days of next month",
    "latest_data_point": "September 2026 (55.3, -1.8 points)",
    "access": "free PDF reports; history not downloadable as a file (not found)",
    "format": "PDF",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Order backlog and employment subindices lead manufacturing hiring by 1-3 months (hypothesis)",
    "usability_score": 3,
    "notes": "Transcribe subindices from monthly PDFs for 3-5 years; tradingeconomics/investing.com carry the headline series."
  },
  {
    "name": "Raiffeisen SME PMI (KMU PMI)",
    "publisher": "Raiffeisen Schweiz",
    "url": "https://www.raiffeisen.ch/rch/de/wissen/unternehmensthemen/forschungs-und-werkplatz-schweiz/kmu-pmi-index/aktuelle-ausgabe.html",
    "subsector": "industry",
    "role": "leading signal",
    "measures": "PMI for industrial SMEs with subindices order backlog, production, employment, delivery times, inventories",
    "geo_granularity": "national",
    "time_granularity": "monthly",
    "history_start": "not verified",
    "publication_lag": "first day of next month (Sept 2026 released 1 Oct 2026)",
    "latest_data_point": "September 2026 (54.5)",
    "access": "free PDF",
    "format": "PDF",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "SME focus is closer to Flexsis clients; same lead hypothesis as PMI",
    "usability_score": 3,
    "notes": ""
  },
  {
    "name": "Swissmem quarterly industry figures (tech / MEM industry)",
    "publisher": "Swissmem",
    "url": "https://www.aktuelle-technik.ch/swissmem-schweizer-tech-industrie-h1-2026-auftraege-umsatz-exporte-a-4ec38ffcdcc8da31dc2303ac689d6ab0/",
    "subsector": "industry",
    "role": "leading signal",
    "measures": "Order intake, turnover, capacity utilisation (81.1% in Q2 2026 vs 85.6% long-run), exports of machinery, electrical and metal industry (about 250 reporting firms)",
    "geo_granularity": "national",
    "time_granularity": "quarterly",
    "history_start": "not verified",
    "publication_lag": "about 2 months (H1 2026 released 3 Sep 2026)",
    "latest_data_point": "2026-Q2",
    "access": "press releases free",
    "format": "web / PDF",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Order intake leads MEM employment by 2-4 quarters (hypothesis); capacity utilisation below average signals no hiring",
    "usability_score": 2,
    "notes": "Statistics page https://www.swissmem.ch/de/produkte-dienstleistungen/beratung/branchenstatistiken.html (not opened)."
  },
  {
    "name": "Swissgrid energy overview (Swiss control block load)",
    "publisher": "Swissgrid",
    "url": "https://www.swissgrid.ch/en/home/customers/topics/energy-data-ch.html",
    "subsector": "industry",
    "role": "leading signal",
    "measures": "Quarter-hourly consumption and production of the Swiss control block",
    "geo_granularity": "national",
    "time_granularity": "15 minutes (monthly files)",
    "history_start": "2009",
    "publication_lag": "about 15 working days after month end; final after 6 months",
    "latest_data_point": "annual file 2025 (published 19 May 2026); 2026 monthly updates",
    "access": "free download",
    "format": "XLSX/CSV",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Coincident activity proxy for industry, not a true lead",
    "usability_score": 3,
    "notes": "Weather-sensitive; weekday/working-hour load is a better industrial proxy."
  },
  {
    "name": "FEDRO/ASTRA Swiss automatic road traffic counts (SARTC) monthly results",
    "publisher": "Federal Roads Office (ASTRA/OFROU)",
    "url": "https://www.astra.admin.ch/astra/en/home/documentation/data-and-information-products/traffic-data/data-and-publication/swiss-automatic-road-traffic-counts--sartc-/annual-and-monthly-results.html",
    "subsector": "logistics",
    "role": "leading signal",
    "measures": "Monthly results of automatic counting stations (traffic volumes; heavy vehicle split to be confirmed in the files)",
    "geo_granularity": "station (national road network)",
    "time_granularity": "monthly (hourly values exist in the full census database)",
    "history_start": "annual archives 2021-2025 on the page",
    "publication_lag": "about 6 weeks (June 2026 published 11 Aug 2026)",
    "latest_data_point": "2026-06",
    "access": "free download",
    "format": "XLSX (Bulletin_YYYY_MM_en.xlsx)",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Heavy vehicle volumes are coincident to 1 month ahead of warehouse and driver demand (hypothesis)",
    "usability_score": 4,
    "notes": "Pick stations near logistics hubs (A1 Oensingen/Haerkingen, A9 Valais, A1 Lausanne-Geneva)."
  },
  {
    "name": "opentransportdata.swiss real-time road traffic (automatic counting stations)",
    "publisher": "FEDRO via Open Transport Data Switzerland",
    "url": "https://opentransportdata.swiss/en/road-traffic/",
    "subsector": "logistics",
    "role": "leading signal",
    "measures": "Real-time traffic counts (1-minute updates), traffic situations",
    "geo_granularity": "station",
    "time_granularity": "1 minute",
    "history_start": "archive exists, details not verified",
    "publication_lag": "real time",
    "latest_data_point": "live",
    "access": "free with registration (default 6 months, 260,000 calls per 6 months)",
    "format": "API (DATEX II style, details in cookbook)",
    "licence": "platform terms",
    "cost": "free",
    "lead_time_hypothesis": "Weekly heavy vehicle counts as a coincident logistics activity signal",
    "usability_score": 3,
    "notes": "Vehicle class split not confirmed."
  },
  {
    "name": "Alpine freight traffic semester reports",
    "publisher": "Federal Office of Transport (BAV/OFT)",
    "url": "https://www.bav.admin.ch/de/newnsb/ViWq1MYAkV3B",
    "subsector": "logistics",
    "role": "leading signal",
    "measures": "Heavy goods vehicle trips across Swiss Alps and rail share (H1 2026: 511,000 lorry trips, +7%; rail share 68%)",
    "geo_granularity": "national (by crossing in reports)",
    "time_granularity": "half-yearly",
    "history_start": "long series",
    "publication_lag": "about 2.5 months (H1 2026 published 10 Sep 2026)",
    "latest_data_point": "H1 2026",
    "access": "free",
    "format": "PDF",
    "licence": "official",
    "cost": "free",
    "lead_time_hypothesis": "Too coarse for alerts; context for transit trucking",
    "usability_score": 2,
    "notes": ""
  },
  {
    "name": "Port of Switzerland monthly transshipment bulletin (Rhine ports)",
    "publisher": "Schweizerische Rheinhaefen",
    "url": "https://port-of-switzerland.ch/umschlagsstatistik-bulletin-juni-2026/",
    "subsector": "logistics",
    "role": "leading signal",
    "measures": "Monthly cargo handled in Swiss Rhine ports (tonnage, containers; details in PDF)",
    "geo_granularity": "port (Basel region)",
    "time_granularity": "monthly",
    "history_start": "monthly bulletins since at least 2025 seen",
    "publication_lag": "about 3 weeks (June 2026 published 23 Jul 2026)",
    "latest_data_point": "2026-06",
    "access": "free download",
    "format": "PDF",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Import container volumes lead distribution warehouse work by 2-6 weeks (hypothesis)",
    "usability_score": 3,
    "notes": "Relevant mainly for Northwestern Switzerland."
  },
  {
    "name": "Zurich Airport monthly traffic figures (cargo tonnage)",
    "publisher": "Flughafen Zuerich AG (via press)",
    "url": "https://aviation.direct/flughafen-zuerich-veroeffentlicht-verkehrszahlen-fuer-august-2026",
    "subsector": "logistics",
    "role": "leading signal",
    "measures": "Monthly air cargo tonnage (Aug 2026: 34,444 t, -0.4% yoy)",
    "geo_granularity": "airport",
    "time_granularity": "monthly",
    "history_start": "not verified",
    "publication_lag": "about 2 weeks",
    "latest_data_point": "2026-08",
    "access": "free press releases",
    "format": "web",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Coincident for air freight forwarders, weak for temp demand",
    "usability_score": 2,
    "notes": "Official investor page not opened."
  },
  {
    "name": "Swiss Post peak season parcel figures",
    "publisher": "Swiss Post (via SRF)",
    "url": "https://www.srf.ch/news/schweiz/black-friday-ansturm-post-liefert-7-9-millionen-pakete-und-bricht-damit-rekord",
    "subsector": "logistics",
    "role": "context",
    "measures": "Black Friday week 2025: 7.9 million parcels (about +400,000 yoy), about 500 temp workers added, sorting up to 22 h/day, 370 extra delivery rounds per day",
    "geo_granularity": "national",
    "time_granularity": "event-based (annual)",
    "history_start": "yearly press releases",
    "publication_lag": "days",
    "latest_data_point": "Black Friday week 2025",
    "access": "free press",
    "format": "web",
    "licence": "media",
    "cost": "free",
    "lead_time_hypothesis": "Black Friday and Christmas peak is predictable 6-10 weeks ahead; staffing must start in October",
    "usability_score": 2,
    "notes": "Use for calendar calibration of logistics peaks. Black Friday 2026 is Friday 27 November."
  },
  {
    "name": "Monitoring Consumption Switzerland / Consumer Spending Index",
    "publisher": "University of St. Gallen (HSG), data by Worldline and others",
    "url": "https://monitoringconsumption.com/",
    "subsector": "logistics",
    "role": "leading signal",
    "measures": "Payment card transactions by canton, merchant category, point of sale vs e-commerce; HSG Consumer Spending Index monthly by 7 regions and 6 categories",
    "geo_granularity": "canton (transactions), 7 regions (index)",
    "time_granularity": "daily (transactions), monthly (index)",
    "history_start": "2019-01-01",
    "publication_lag": "days to 2 weeks",
    "latest_data_point": "active; some datasets frozen on 2023-01-04",
    "access": "free dashboards; data stated as freely available, download format not verified",
    "format": "dashboard / downloads (not verified)",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "E-commerce spending growth before Black Friday leads parcel and warehouse peaks by 1-4 weeks (hypothesis)",
    "usability_score": 3,
    "notes": "Consumer Spending Index: https://www.unisg.ch/en/research/research-in-focus/consumer-spending-in-switzerland/"
  },
  {
    "name": "GS1 Logistics Market Study Switzerland (Logistikmarktstudie)",
    "publisher": "GS1 Switzerland with University of St. Gallen",
    "url": "https://handelsverband.swiss/news/logistikmarktstudie-schweiz-01-26-die-zukunft-der-schweizer-logistik-beginnt-jetzt/",
    "subsector": "logistics",
    "role": "context",
    "measures": "Logistics market size, top 100 logistics providers, thematic analyses",
    "geo_granularity": "national",
    "time_granularity": "3 editions per year",
    "history_start": "long running",
    "publication_lag": "n/a",
    "latest_data_point": "01/2026 (5 Mar 2026)",
    "access": "free download at https://lms.gs1.ch/de",
    "format": "PDF",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Context only",
    "usability_score": 1,
    "notes": "Good for pitch numbers on market size."
  },
  {
    "name": "MeteoSwiss open data: automatic weather stations (SwissMetNet)",
    "publisher": "MeteoSwiss",
    "url": "https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations",
    "subsector": "cross-sector",
    "role": "context",
    "measures": "Temperature, precipitation, wind, sunshine, humidity, radiation, pressure at about 160 stations",
    "geo_granularity": "station",
    "time_granularity": "10 min, hourly, daily, monthly, yearly",
    "history_start": "before 1981 (station dependent)",
    "publication_lag": "about 20 minutes",
    "latest_data_point": "live",
    "access": "free API (STAC) and file download, no key",
    "format": "CSV via STAC https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn",
    "licence": "open data, cite 'Source: MeteoSwiss'",
    "cost": "free",
    "lead_time_hypothesis": "Frost, snow and heavy rain cut construction hours within days; catch-up demand 1-4 weeks later (hypothesis)",
    "usability_score": 5,
    "notes": "Valais stations available (e.g. Sion, Visp). Forecast products are documented in other opendatadocs sections (not opened)."
  },
  {
    "name": "OpenHolidays API (school and public holidays by canton)",
    "publisher": "OpenHolidays project (openpotato)",
    "url": "https://www.openholidaysapi.org/en/",
    "subsector": "cross-sector",
    "role": "context",
    "measures": "Public holidays and school holidays per Swiss canton (ISO 3166-2 subdivisions)",
    "geo_granularity": "canton",
    "time_granularity": "daily calendar",
    "history_start": "2020",
    "publication_lag": "n/a (published ahead)",
    "latest_data_point": "future years available",
    "access": "free API, no key",
    "format": "JSON, e.g. /SchoolHolidays?countryIsoCode=CH&subdivisionCode=CH-VS",
    "licence": "open data project (licence on GitHub)",
    "cost": "free",
    "lead_time_hypothesis": "Holiday calendars are known months ahead: deterministic features for seasonality",
    "usability_score": 5,
    "notes": "Cross-check with EDK lists."
  },
  {
    "name": "EDK/CDIP school holiday lists",
    "publisher": "EDK / CDIP",
    "url": "https://edk.ch/de/bildungssystem/kantonale-schulorganisation/Schulferien",
    "subsector": "cross-sector",
    "role": "context",
    "measures": "School holidays per canton (and some communes)",
    "geo_granularity": "canton",
    "time_granularity": "annual lists",
    "history_start": "1987 (edudoc.ch archive)",
    "publication_lag": "published years ahead",
    "latest_data_point": "2026 and 2027 confirmed, 2028 provisional",
    "access": "free download",
    "format": "PDF",
    "licence": "official",
    "cost": "free",
    "lead_time_hypothesis": "Calendar feature",
    "usability_score": 3,
    "notes": "Use for history before 2020 (OpenHolidays starts 2020)."
  },
  {
    "name": "Valais construction employers circular 2026 (work calendar, summer site closure)",
    "publisher": "AVE-WBV (Association valaisanne des entrepreneurs)",
    "url": "https://www.ave-wbv.ch/files/CIRCULAIRE2026-FR.pdf",
    "subsector": "construction",
    "role": "context",
    "measures": "Annual working time 2,112 h; official summer closure of sites 3-10 Aug 2026; holiday rules; switch to calendar-year planning from 1 Jan 2027",
    "geo_granularity": "canton VS",
    "time_granularity": "annual",
    "history_start": "2026",
    "publication_lag": "n/a",
    "latest_data_point": "2026",
    "access": "free download",
    "format": "PDF",
    "licence": "not stated",
    "cost": "free",
    "lead_time_hypothesis": "Deterministic dips and peaks around closures (demand drops during closure, spikes in the 2 weeks before and after: hypothesis)",
    "usability_score": 3,
    "notes": "National collective agreement CN 2026-2031 PDF exists at shop.baumeister.swiss (found via search, not opened)."
  },
  {
    "name": "Google Trends via trendecon R package (consistent long daily series)",
    "publisher": "trendEcon (KOF, SECO, HSG, cynkra and others); data by Google",
    "url": "https://github.com/trendecon/trendecon",
    "subsector": "cross-sector",
    "role": "leading signal",
    "measures": "Google search interest for keywords in Switzerland (geo='CH'), harmonised daily series from daily/weekly/monthly queries",
    "geo_granularity": "national (Google also offers canton-level 'interest by region')",
    "time_granularity": "daily / weekly",
    "history_start": "2004 (Google Trends)",
    "publication_lag": "1-3 days",
    "latest_data_point": "live",
    "access": "free (unofficial access via gtrendsR/pytrends, rate limited)",
    "format": "R time series",
    "licence": "Google Trends terms; package open source",
    "cost": "free",
    "lead_time_hypothesis": "Searches such as 'emploi temporaire', 'Temporärjob', 'cariste', 'Staplerfahrer', 'Kurzarbeit' lead registrations by 0-2 months (hypothesis; literature finds 1-12 month predictive power for employment)",
    "usability_score": 4,
    "notes": "Method published in Eichenauer et al. 2022 (Economic Inquiry). Expect 429 rate limits; cache results."
  }
]
```
