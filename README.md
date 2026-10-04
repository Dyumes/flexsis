# flexsis

Early-warning forecasts of staffing demand in Valais (construction, logistics, industry). Built for the Flexsis challenge at the Foire du Valais 2026 hackathon.

The pipeline downloads public data (weather, holidays, KOF indicators, SNB rates, SIMAP tenders, STATENT, ...), builds a weekly feature table, and uses one ExtraTrees model per horizon (2, 4, 8 and 13 weeks) to predict the future % change of the Valais job-ad index (Swiss Job Tracker). Results are shown in a standalone HTML page.

## How to use

Run all commands from the project root.

### 1. Train the models (once)

```bash
python predict.py --train
```

Trains the ExtraTrees models, prints a test-year check (R², MAE, directional accuracy per horizon) and saves them to `models/et_bundle.pkl`. Re-run it whenever you want to refresh the models.

### 2. Predict (weekly)

```bash
python predict.py
```

Downloads fresh data, rebuilds `data/master_weekly.csv`, builds the features of the last complete week (Mon-Sun), predicts every horizon and appends the results to `predictions/et_predictions.csv`.

To skip the downloads and reuse the CSVs already in `data/`:

```bash
python predict.py --no-fetch
```

### 3. View the results in the HTML page

1. Open `prevision.html` in your browser (double-click the file, no server needed).
2. Click **Charger et_predictions.csv** and select `predictions/et_predictions.csv`.
3. Click **Charger labels_valais_weekly.csv** and select `data_seb/labels_valais_weekly.csv` to show the historical comparison.
4. Pick the starting week in the **Semaine de départ** dropdown if you want an older run.

You can also drag and drop both CSV files onto the page. A default history is built into the page, so the labels file is optional.

## Installation

Requires Python 3.13 or newer.

With [uv](https://docs.astral.sh/uv/) (recommended, a lockfile is included):

```bash
git clone https://github.com/Dyumes/flexsis.git
cd flexsis
uv sync
uv run python predict.py --train
```

With pip:

```bash
pip install scikit-learn seaborn pandas numpy requests
```

## Command-line options

| Option | Description |
|--------|-------------|
| `--train` | (Re)train the models and save them to `models/et_bundle.pkl` |
| `--no-fetch` | Do not download data, rebuild from `data/*.csv` |
| `--labels PATH` | Labels CSV used for training (default `data_seb/labels_valais_weekly.csv`) |
| `--fit-on all` / `train_val` | `all` (default) fits on every labelled week; `train_val` holds out the test year like the notebook |

## What the output means

`predictions/et_predictions.csv` has one row per run and horizon:

| Column | Description |
|--------|-------------|
| `run_at` | When the prediction was made |
| `feature_week` | Monday of the week the features come from |
| `horizon` | `2w`, `4w`, `8w` or `13w` |
| `horizon_end_week` | Monday of the target week |
| `target` | Predicted series, e.g. `y_vs_chg_4w` |
| `prediction` | Expected relative change of the Valais job-ad index (`-0.02` = 2% decrease) |

If a run for the same `feature_week` and horizon already exists, it is replaced.

## Project structure

```
flexsis/
├── predict.py             # Train (--train) and predict
├── features_extract.py    # Downloads sources, builds data/master_weekly.csv
├── prevision.html         # Dashboard: load the prediction CSVs in the browser
├── build_labels_valais.py # Builds the Valais label table from the Job Tracker
├── main.ipynb             # Exploration, model comparison, hyper-parameter search
├── data/                  # Downloaded sources and the weekly master table
├── data_seb/              # Job Tracker, BFS and SIMAP data, labels
├── data_catalogue/        # Catalogue of candidate data sources
├── models/                # Trained models (et_bundle.pkl)
└── predictions/           # Prediction log (et_predictions.csv)
```

## Troubleshooting

- **`models/et_bundle.pkl not found`**: run `python predict.py --train` first.
- **`WARNING: the master is older than the last complete week`**: some downloads failed. Check the `FAIL` lines printed at the end of the run. Missing features are carried forward for at most 4 weeks, after which that horizon is skipped.
- **No internet**: use `python predict.py --no-fetch`.

## License

See [LICENSE](LICENSE).