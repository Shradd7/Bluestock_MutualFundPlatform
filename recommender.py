"""
Day 6 - Task 5: Simple fund recommendation engine.

Input: investor risk appetite (Low / Moderate / High)
Output: top 3 funds by Sharpe ratio within the matching risk grade.

Run directly for a demo across all three appetites:
    python recommender.py
Or import and call recommend() from other code:
    from recommender import recommend
    recommend("High")
"""
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# The dataset's actual risk_category has 5 SEBI-style levels, not 3.
# Mapped down to Low / Moderate / High for a simple recommender — this
# bucketing is a design choice, documented here rather than hidden:
RISK_BUCKET_MAP = {
    "Low": "Low",
    "Moderate": "Moderate",
    "Moderately High": "Moderate",
    "High": "High",
    "Very High": "High",
}


def load_data():
    scorecard = pd.read_csv(BASE_DIR / "fund_scorecard.csv", dtype={"amfi_code": str})
    fund_master = pd.read_csv(BASE_DIR / "data/raw/01_fund_master.csv", dtype={"amfi_code": str})
    df = scorecard.merge(fund_master[["amfi_code", "risk_category"]], on="amfi_code")
    df["risk_bucket"] = df["risk_category"].map(RISK_BUCKET_MAP)
    return df


def recommend(risk_appetite: str, top_n: int = 3):
    """Return top_n funds by Sharpe ratio within the matching risk bucket."""
    risk_appetite = risk_appetite.strip().title()
    if risk_appetite not in {"Low", "Moderate", "High"}:
        raise ValueError("risk_appetite must be one of: Low, Moderate, High")

    df = load_data()
    matched = df[df["risk_bucket"] == risk_appetite]
    if matched.empty:
        print(f"No funds found in the '{risk_appetite}' risk bucket.")
        return pd.DataFrame()

    top = matched.sort_values("sharpe_ratio", ascending=False).head(top_n)
    return top[["scheme_name", "category", "risk_category", "sharpe_ratio", "cagr_3yr", "expense_ratio_pct"]]


if __name__ == "__main__":
    for appetite in ["Low", "Moderate", "High"]:
        print(f"\n=== Top {3} funds for '{appetite}' risk appetite ===")
        result = recommend(appetite)
        if not result.empty:
            print(result.to_string(index=False))
