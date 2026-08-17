"""
Bluestock MF Analytics Platform — master pipeline script.

Runs the full ETL in order: clean each raw dataset, load into SQLite,
then rebuild the dashboard's data payload. Notebooks (EDA, Performance,
Advanced Analytics) are run separately via nbconvert — see README.md —
since they're exploratory/analytical rather than part of the ETL proper.

Run from the repo root:
    python scripts/etl_pipeline.py
"""
import subprocess
import sys
from pathlib import Path

STEPS = [
    ("Cleaning NAV history",        ["clean_nav.py"]),
    ("Cleaning investor transactions", ["clean_transactions.py"]),
    ("Cleaning scheme performance",  ["clean_performance.py"]),
    ("Loading cleaned data into SQLite", ["load_to_sqlite.py"]),
    ("Rebuilding dashboard data",    ["build_dashboard_data.py"]),
]


def main():
    repo_root = Path(__file__).resolve().parents[1]
    for label, cmd in STEPS:
        print(f"\n{'='*60}\n{label}\n{'='*60}")
        result = subprocess.run([sys.executable, str(repo_root / "scripts" / cmd[0])], cwd=repo_root)
        if result.returncode != 0:
            print(f"\nPipeline stopped: '{label}' failed (exit code {result.returncode}).")
            sys.exit(result.returncode)
    print("\nPipeline complete. Cleaned CSVs are in data/processed/, "
          "the database is at data/db/bluestock_mf.db, and "
          "dashboard/dashboard_data.json is up to date.")
    print("Notebooks (EDA/Performance/Advanced Analytics) and fund_scorecard.csv / "
          "alpha_beta.csv / var_cvar_report.csv are produced separately — see README.md.")


if __name__ == "__main__":
    main()
