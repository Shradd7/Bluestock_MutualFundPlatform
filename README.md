# Mutual Fund Analytics — Day 1

## Setup

```powershell
python -m pip install -r requirements.txt
```

Place the ten supplied CSV datasets in `data/raw/`, then run:

```powershell
python data_ingestion.py
python live_nav_fetch.py
```

`data_ingestion.py` prints each dataset's shape, dtypes, head, and basic anomalies. It also explores `fund_master.csv`, validates AMFI scheme codes against `nav_history.csv`, and writes `reports/data_quality_summary.txt`.

`live_nav_fetch.py` retrieves the six requested scheme histories from mfapi.in and saves them as raw CSV files under `data/raw/`.

AMFI scheme codes are identifiers rather than numerical measures; preserve them as strings so formatting or leading zeroes are not lost.
