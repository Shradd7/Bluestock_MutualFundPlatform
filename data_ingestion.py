from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
REPORT_PATH = ROOT / "reports" / "data_quality_summary.txt"


def print_dataset_report(path: Path, frame: pd.DataFrame) -> list[str]:
    """Print requested profiling details and return anomaly messages."""
    print("\n" + "=" * 80)
    print(f"FILE: {path.name}")
    print(f"shape: {frame.shape}")
    print("dtypes:")
    print(frame.dtypes.to_string())
    print("head():")
    print(frame.head().to_string(index=False))

    anomalies: list[str] = []
    if frame.empty:
        anomalies.append("empty dataset")
    if frame.columns.duplicated().any():
        anomalies.append("duplicate column names")
    missing = frame.isna().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        anomalies.append("missing values: " + ", ".join(f"{k}={v}" for k, v in missing.items()))
    duplicate_rows = int(frame.duplicated().sum())
    if duplicate_rows:
        anomalies.append(f"duplicate rows: {duplicate_rows}")
    if not anomalies:
        anomalies.append("none detected")
    print("anomalies: " + "; ".join(anomalies))
    return anomalies


def find_column(frame: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    normalized = {str(column).strip().lower(): column for column in frame.columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    for column in frame.columns:
        lowered = str(column).strip().lower()
        if any(candidate.lower() in lowered for candidate in candidates):
            return column
    return None


def load_all_csvs() -> dict[str, pd.DataFrame]:
    files = sorted(RAW_DIR.glob("*.csv"))
    if len(files) != 10:
        print(f"\nWARNING: expected 10 CSV datasets, found {len(files)} in {RAW_DIR}")
    datasets: dict[str, pd.DataFrame] = {}
    report_lines = ["Day 1 data quality summary", "=" * 28, f"CSV files found: {len(files)}"]
    for path in files:
        try:
            frame = pd.read_csv(path)
            datasets[path.name] = frame
            anomalies = print_dataset_report(path, frame)
            report_lines.append(f"{path.name}: shape={frame.shape}; anomalies={'; '.join(anomalies)}")
        except Exception as exc:  # keep profiling the remaining files
            message = f"read error: {type(exc).__name__}: {exc}"
            print(f"{path.name}: {message}")
            report_lines.append(f"{path.name}: {message}")
    return datasets, report_lines


def explore_fund_master(datasets: dict[str, pd.DataFrame], report_lines: list[str]) -> None:
    matches = [(name, frame) for name, frame in datasets.items() if "fund_master" in name.lower()]
    if not matches:
        report_lines.append("fund_master: not found; fund master exploration deferred")
        print("\nFund master: not found in data/raw; exploration deferred.")
        return
    name, frame = matches[0]
    print(f"\nFUND MASTER EXPLORATION: {name}")
    report_lines.append(f"fund_master file: {name}")
    for label, candidates in {
        "fund houses": ("fund_house", "fund house", "amc"),
        "categories": ("category",),
        "sub-categories": ("sub_category", "sub-category", "subcategory"),
        "risk grades": ("risk_grade", "risk grade", "risk"),
    }.items():
        column = find_column(frame, candidates)
        values = sorted(frame[column].dropna().astype(str).str.strip().unique().tolist()) if column else []
        print(f"unique {label} ({column}): {values}")
        report_lines.append(f"unique {label} ({column}): {values}")
    code_column = find_column(frame, ("scheme_code", "scheme code", "amfi_code", "code"))
    if code_column:
        print("AMFI scheme code structure: numeric scheme identifiers; leading zeroes, if supplied, are preserved as strings.")
        report_lines.append("AMFI scheme code structure: numeric scheme identifiers; preserve as strings to avoid formatting loss.")


def validate_amfi_codes(datasets: dict[str, pd.DataFrame], report_lines: list[str]) -> None:
    master_items = [(n, f) for n, f in datasets.items() if "fund_master" in n.lower()]
    nav_items = [(n, f) for n, f in datasets.items() if "nav_history" in n.lower()]
    if not master_items or not nav_items:
        message = "AMFI validation: skipped because fund_master.csv or nav_history.csv is missing"
        print("\n" + message)
        report_lines.append(message)
        return
    master = master_items[0][1]
    nav = nav_items[0][1]
    master_code = find_column(master, ("scheme_code", "scheme code", "amfi_code", "code"))
    nav_code = find_column(nav, ("scheme_code", "scheme code", "amfi_code", "code"))
    if not master_code or not nav_code:
        message = "AMFI validation: skipped because a scheme-code column was not identified"
        print("\n" + message)
        report_lines.append(message)
        return
    master_codes = set(master[master_code].dropna().astype(str).str.strip())
    nav_codes = set(nav[nav_code].dropna().astype(str).str.strip())
    missing = sorted(master_codes - nav_codes)
    message = f"AMFI validation: {len(master_codes)} fund_master codes; {len(missing)} missing from nav_history"
    print("\n" + message)
    if missing:
        print("Missing codes:", missing[:25])
        report_lines.append(message + f"; missing sample={missing[:25]}")
    else:
        report_lines.append(message + "; all codes present")


def main() -> None:
    datasets, report_lines = load_all_csvs()
    explore_fund_master(datasets, report_lines)
    validate_amfi_codes(datasets, report_lines)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"\nWrote data quality summary to {REPORT_PATH}")


if __name__ == "__main__":
    main()
