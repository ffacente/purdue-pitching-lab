# Purdue Pitching Lab

Purdue Pitching Lab is a production-grade Streamlit application for pitch-by-pitch analysis, player development planning, bullpen scenario matching, and staff-wide pitch design benchmarking.

## Features

- Modular multi-page Streamlit architecture with separate analytics engines in `pages/`, `models/`, and `utils/`
- Centralized Parquet schema discovery with fuzzy column alias mapping and graceful degradation for missing metrics
- Cached metric computation, pitcher filtering, bullpen scoring, and staff leaderboards with `st.cache_data`
- Purdue-branded dashboards for player profiles, development cards, pitch design, bullpen scenarios, and staff analytics
- Downloadable CSV, Excel, PNG, and PDF exports for filtered datasets and performance summaries
- Automated pytest coverage for formulas, filters, bullpen scoring, configuration, and small-sample edge cases

## Project Structure

```text
purdue_pitching_lab/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── logs/
│   └── app.log
├── assets/
├── data/
│   └── combined_data.parquet
├── models/
│   ├── __init__.py
│   ├── rule.py
│   └── thresholds.py
├── pages/
│   ├── __init__.py
│   ├── home.py
│   ├── player_profile.py
│   ├── development.py
│   ├── pitch_design.py
│   ├── arsenal_optimization.py
│   ├── bullpen.py
│   └── staff_dashboard.py
├── utils/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── filters.py
│   ├── metrics.py
│   ├── plotting.py
│   ├── recommendations.py
│   ├── scenario_engine.py
│   ├── pitch_design_engine.py
│   └── helpers.py
└── tests/
    ├── test_config.py
    ├── test_filters.py
    ├── test_metrics.py
    └── test_scenario_engine.py
```

## Setup

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Confirm the data file is present at `data/combined_data.parquet`.
4. Run the app:

```bash
streamlit run app.py
```

## Application Modules

- `Home`: central launch screen, pitcher search, favorites, recent views, and dataset notes
- `Pitcher Performance Profile`: arsenal visuals, sticky filters, traditional metrics, and contact-quality outputs
- `Player Development Engine`: rule-driven recommendation cards and PDF report generation
- `Pitch Design Lab`: movement cluster classification, staff benchmark comparisons, and coaching notes
- `Arsenal Optimization`: best-pitch selection logic for matchup and usage questions
- `Bullpen Scenario Matcher`: live tactical scenario picker with weighted success scores
- `Staff Dashboard`: team distributions, roster leaderboards, and profile routing

## Data Notes

- The app uses fuzzy alias detection for key fields such as pitcher, pitch type, velocity, spin, team, break metrics, and batted-ball type.
- If a required field for a chart is missing, the corresponding component is disabled with a user-facing explanation rather than crashing the page.
- If a filtered sample contains fewer than five pitches, the app shows a reliability warning and avoids overstating the output.
- The current source dataset does not contain an exact `PitcherTeam == Purdue` label, so the app falls back to available pitchers and records that note in the UI.

## Testing

Run the test suite with:

```bash
pytest
```

## Troubleshooting

- If `streamlit` or `loguru` imports fail, install dependencies from `requirements.txt` in the active interpreter.
- If Plotly PNG export fails, confirm `kaleido` is installed.
- If PDF generation fails, confirm `fpdf2` is installed.
- If the app loads but no Purdue pitchers appear, review the notes on the Home page for team-label fallback details.
- Check `logs/app.log` for dataset load events, missing alias warnings, filter activity, and runtime errors.