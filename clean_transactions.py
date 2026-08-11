"""Day 2 - Task 2: Clean investor_transactions.csv"""
import pandas as pd
from pathlib import Path

RAW = Path("data/raw/08_investor_transactions.csv")
OUT = Path("data/processed/clean_transactions.csv")

VALID_TYPES = {"sip": "SIP", "lumpsum": "Lumpsum", "lump sum": "Lumpsum", "redemption": "Redemption"}
VALID_KYC = {"verified": "Verified", "pending": "Pending"}

df = pd.read_csv(RAW, dtype={"amfi_code": str, "investor_id": str})
n0 = len(df)

# standardise transaction_type
df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.lower().map(VALID_TYPES)
print(f"Dropping {df['transaction_type'].isna().sum()} rows with unrecognised transaction_type")
df = df.dropna(subset=["transaction_type"])

# validate amount > 0
df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")
bad_amt = df["amount_inr"].isna() | (df["amount_inr"] <= 0)
print(f"Dropping {bad_amt.sum()} rows with amount_inr <= 0 or non-numeric")
df = df[~bad_amt]

# fix dates
df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
print(f"Dropping {df['transaction_date'].isna().sum()} rows with unparseable dates")
df = df.dropna(subset=["transaction_date"])

# check kyc_status enum
df["kyc_status"] = df["kyc_status"].astype(str).str.strip().str.lower().map(VALID_KYC)
n_bad_kyc = df["kyc_status"].isna().sum()
if n_bad_kyc:
    print(f"WARNING: {n_bad_kyc} rows had unrecognised kyc_status -> defaulted to 'Pending'")
    df["kyc_status"] = df["kyc_status"].fillna("Pending")

# drop exact duplicate transactions
before = len(df)
df = df.drop_duplicates(subset=["investor_id", "amfi_code", "transaction_date", "amount_inr", "transaction_type"])
print(f"Dropped {before - len(df)} exact duplicate transactions")

df = df.sort_values(["investor_id", "transaction_date"]).reset_index(drop=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Rows: {n0} -> {len(df)}")
print(f"Saved {OUT}")
