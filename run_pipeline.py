"""
Bluestock MF Analytics Platform — master pipeline script.

Runs the full ETL in order: clean each raw dataset, load into SQLite,
then rebuild the dashboard's data payload. Notebooks (EDA, Performance,
Advanced Analytics) are run separately via nbconvert — see README.md —
since they're exploratory/analytical rather than part of the ETL proper.

Run from the repo root:
    python run_pipeline.py
"""
import subprocess
import sys
from pathlib import Path

STEPS = [
    ("Cleaning NAV history",        ["python", "clean_nav.py"]),
    ("Cleaning investor transactions", ["python", "clean_transactions.py"]),
    ("Cleaning scheme performance",  ["python", "clean_performance.py"]),
    ("Loading cleaned data into SQLite", ["python", "load_to_sqlite.py"]),
    ("Rebuilding dashboard data",    ["python", "build_dashboard_data.py"]),
]


def main():
    repo_root = Path(__file__).resolve().parent
    for label, cmd in STEPS:
        print(f"\n{'='*60}\n{label}\n{'='*60}")
        result = subprocess.run(cmd, cwd=repo_root)
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
