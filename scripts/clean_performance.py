"""Day 2 - Task 3: Clean scheme_performance.csv"""
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW = BASE_DIR / "data/raw/07_scheme_performance.csv"
OUT = BASE_DIR / "data/processed/clean_performance.csv"

NUMERIC_COLS = [
    "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct",
    "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct",
    "max_drawdown_pct", "expense_ratio_pct",
]

df = pd.read_csv(RAW, dtype={"amfi_code": str})
n0 = len(df)

# validate numeric columns are actually numeric; coerce failures to NaN and report
for col in NUMERIC_COLS:
    before_na = df[col].isna().sum()
    df[col] = pd.to_numeric(df[col], errors="coerce")
    new_na = df[col].isna().sum() - before_na
    if new_na:
        print(f"WARNING: {new_na} non-numeric values found in '{col}' -> set to NaN")

# expense_ratio_pct should be within 0.1% - 2.5% (per project spec)
out_of_range = ~df["expense_ratio_pct"].between(0.1, 2.5)
if out_of_range.any():
    print(f"WARNING: {out_of_range.sum()} rows have expense_ratio_pct outside 0.1%-2.5% -> flagged, not dropped")
df["expense_ratio_flag"] = out_of_range

# flag (don't drop) anomalies: negative Sharpe, max_drawdown that isn't negative
df["negative_sharpe_flag"] = df["sharpe_ratio"] < 0
df["bad_drawdown_flag"] = df["max_drawdown_pct"] > 0  # drawdown should always be <= 0
if df["bad_drawdown_flag"].any():
    print(f"WARNING: {df['bad_drawdown_flag'].sum()} rows have a positive max_drawdown_pct (should be <=0) -> flagged")

# drop rows where a core numeric field is missing after coercion (can't compute rankings without it)
core = ["return_3yr_pct", "sharpe_ratio", "alpha"]
before = len(df)
df = df.dropna(subset=core)
print(f"Dropped {before - len(df)} rows missing core metrics {core}")

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Rows: {n0} -> {len(df)}")
print(f"Saved {OUT}")
