from pathlib import Path 
import pandas as  pd

BASE_DIR = Path(r"D:\Bluestock")

INPUT_FILE  = BASE_DIR / "data" / "raw" / "02_nav_history.csv"
OUTPUT_FILE  = BASE_DIR / "data" / "processed" / "nav_history.csv"


OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT_FILE)
print(f'Original Rows : {len(df)}')

df["date"] = pd.to_datetime(df['date'], errors="coerce")

duplicates = df.duplicated().sum()

df = df.drop_duplicates()

df = df.sort_values(['amfi_code','date'])
df['nav'] = df.groupby('amfi_code')['nav'].ffill()

missing_nav = df['nav'].isnull().sum()
invalid_nav = (df['nav'] < 0).sum()

print(f"Duplicates Removed : {duplicates}")
print(f"Missing NAV        : {missing_nav}")
print(f"Invalid NAV        : {invalid_nav}")

df = df[df["nav"] > 0]

print(f"Final Rows         : {len(df)}")

df.to_csv(OUTPUT_FILE, index=False)

print("\nCleaned file saved")
print(OUTPUT_FILE)