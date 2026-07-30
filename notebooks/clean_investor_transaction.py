from pathlib import Path
import pandas as pd

BASE_DIR = Path(r"D:/Bluestock")
INPUT_FILE = BASE_DIR / "data" / "raw" / "08_investor_transactions.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "investor_transactions.csv"

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT_FILE)

print(f"Original Rows : {len(df)}")

df['transaction_date'] = pd.to_datetime(df['transaction_date'],errors="coerce" )
df['transaction_type'] = (
    df['transaction_type']
    .str.strip()
    .str.title()
)

mapping = {
    "Sip": "SIP",
    "Lumpsum": "Lumpsum",
    "Redemption": "Redemption"
}

df["transaction_type"] = df["transaction_type"].replace(mapping)

invalid_amount = (df["amount_inr"] <= 0).sum()
df["kyc_status"] = (
    df["kyc_status"]
    .str.strip()
    .str.title()
)

valid_kyc = ["Verified", "Pending", "Rejected"]

invalid_kyc = ~df["kyc_status"].isin(valid_kyc)

print("\nUnique Transaction Types")
print(df["transaction_type"].unique())

print("\nUnique KYC Values")
print(df["kyc_status"].unique())

print(f"\nInvalid Amount Rows : {invalid_amount}")
print(f"Invalid KYC Rows    : {invalid_kyc.sum()}")


duplicates = df.duplicated().sum()

df = df.drop_duplicates()

print(f"Duplicates Removed : {duplicates}")


df = df[df["amount_inr"] > 0]

print(f"Final Rows : {len(df)}")


df.to_csv(OUTPUT_FILE, index=False)

print("\nCleaned file saved to:")
print(OUTPUT_FILE)