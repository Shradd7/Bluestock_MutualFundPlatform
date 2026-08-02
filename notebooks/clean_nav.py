"""Day 2 - Task 1: Clean nav_history.csv"""
import pandas as pd
from pathlib import Path

RAW = Path("data/raw/02_nav_history.csv")
OUT = Path("data/processed/clean_nav.csv")

df = pd.read_csv(RAW, dtype={"amfi_code": str})
n0 = len(df)

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])                                   # unparseable dates
df = df.sort_values(["amfi_code", "date"])
df = df.drop_duplicates(subset=["amfi_code", "date"])              # exact dupes

df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
bad_nav = df["nav"].isna() | (df["nav"] <= 0)
print(f"Dropping {bad_nav.sum()} rows with invalid NAV (<=0 or non-numeric)")
df = df[~bad_nav]

# reindex each fund to a full business-day calendar and forward-fill holiday/weekend gaps
filled = []
for code, g in df.groupby("amfi_code"):
    full_idx = pd.bdate_range(g["date"].min(), g["date"].max())
    g = g.set_index("date").reindex(full_idx).rename_axis("date").reset_index()
    g["amfi_code"] = code
    g["nav"] = g["nav"].ffill()
    filled.append(g)
df = pd.concat(filled, ignore_index=True)[["amfi_code", "date", "nav"]]

df["daily_return_pct"] = df.groupby("amfi_code")["nav"].pct_change() * 100

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Rows: {n0} -> {len(df)} (after gap-filling to full business-day calendar)")
print(f"Saved {OUT}")
