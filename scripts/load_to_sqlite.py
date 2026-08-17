"""Day 2 - Task 5: Load cleaned CSVs into bluestock_mf.db (SQLite star schema)"""
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data/db/bluestock_mf.db"
SCHEMA_PATH = BASE_DIR / "sql/schema.sql"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DB_PATH.unlink(missing_ok=True)  # rebuild fresh each run

conn = sqlite3.connect(DB_PATH)
conn.executescript(SCHEMA_PATH.read_text())

# ---- dim_fund (from raw fund master) ----
fund_master = pd.read_csv(BASE_DIR / "data/raw/01_fund_master.csv", dtype={"amfi_code": str})
fund_master.to_sql("dim_fund", conn, if_exists="append", index=False)

# ---- dim_date (built from full nav date range) ----
nav = pd.read_csv(BASE_DIR / "data/processed/clean_nav.csv", dtype={"amfi_code": str}, parse_dates=["date"])
dates = pd.DataFrame({"date": pd.date_range(nav["date"].min(), nav["date"].max())})
dates["date_id"] = dates["date"].dt.strftime("%Y%m%d").astype(int)
dates["year"] = dates["date"].dt.year
dates["month"] = dates["date"].dt.month
dates["quarter"] = dates["date"].dt.quarter
dates["is_weekday"] = (dates["date"].dt.dayofweek < 5).astype(int)
dates = dates[["date_id", "date", "year", "month", "quarter", "is_weekday"]]
dates.to_sql("dim_date", conn, if_exists="append", index=False)

# ---- fact_nav ----
nav.to_sql("fact_nav", conn, if_exists="append", index=False)

# ---- fact_transactions ----
tx = pd.read_csv(BASE_DIR / "data/processed/clean_transactions.csv", dtype={"amfi_code": str, "investor_id": str})
tx = tx.drop(columns=["amount_outlier_flag"], errors="ignore")  # optional QA column, not part of schema
tx.to_sql("fact_transactions", conn, if_exists="append", index=False)

# ---- fact_performance ----
perf = pd.read_csv(BASE_DIR / "data/processed/clean_performance.csv", dtype={"amfi_code": str})
perf = perf.drop(columns=["scheme_name", "fund_house", "category", "plan",
                           "expense_ratio_flag", "negative_sharpe_flag", "bad_drawdown_flag"],
                  errors="ignore")  # keep only fact_performance columns per schema
perf.to_sql("fact_performance", conn, if_exists="append", index=False)

# ---- fact_aum ----
aum = pd.read_csv(BASE_DIR / "data/raw/03_aum_by_fund_house.csv")
aum.to_sql("fact_aum", conn, if_exists="append", index=False)

# ---- verify row counts match source ----
checks = {
    "dim_fund": (fund_master, "dim_fund"),
    "fact_nav": (nav, "fact_nav"),
    "fact_transactions": (tx, "fact_transactions"),
    "fact_performance": (perf, "fact_performance"),
    "fact_aum": (aum, "fact_aum"),
}
print(f"{'table':<20}{'source_rows':<15}{'db_rows':<10}match")
for name, (src_df, table) in checks.items():
    db_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{name:<20}{len(src_df):<15}{db_count:<10}{len(src_df) == db_count}")

conn.commit()
conn.close()
print(f"\nDatabase written to {DB_PATH}")
