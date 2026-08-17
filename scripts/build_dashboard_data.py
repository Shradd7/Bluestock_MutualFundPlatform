"""
Day 5 (adapted): Prepares dashboard_data.json for the standalone HTML dashboard,
since Power BI Desktop isn't available. Run this before opening dashboard.html.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA = BASE_DIR / "data"
OUT = BASE_DIR / "dashboard/dashboard_data.json"

nav = pd.read_csv(DATA / "processed/clean_nav.csv", parse_dates=["date"], dtype={"amfi_code": str})
fund_master = pd.read_csv(DATA / "raw/01_fund_master.csv", dtype={"amfi_code": str})
aum = pd.read_csv(DATA / "raw/03_aum_by_fund_house.csv", parse_dates=["date"])
sip = pd.read_csv(DATA / "raw/04_monthly_sip_inflows.csv")
sip["month"] = pd.to_datetime(sip["month"])
cat_inflow = pd.read_csv(DATA / "raw/05_category_inflows.csv")
cat_inflow["month"] = pd.to_datetime(cat_inflow["month"])
folios = pd.read_csv(DATA / "raw/06_industry_folio_count.csv")
folios["month"] = pd.to_datetime(folios["month"])
tx = pd.read_csv(DATA / "processed/clean_transactions.csv", parse_dates=["transaction_date"], dtype={"amfi_code": str})
bench = pd.read_csv(DATA / "raw/10_benchmark_indices.csv", parse_dates=["date"])
scorecard = pd.read_csv(BASE_DIR / "fund_scorecard.csv", dtype={"amfi_code": str})
perf = pd.read_csv(DATA / "processed/clean_performance.csv", dtype={"amfi_code": str})

nav = nav.merge(fund_master[["amfi_code", "scheme_name", "fund_house", "category", "plan"]], on="amfi_code")

payload = {}

# ---------------- KPIs ----------------
latest_aum_date = aum["date"].max()
total_aum_latest = aum[aum["date"] == latest_aum_date]["aum_crore"].sum()
sip_latest = sip.sort_values("month").iloc[-1]
folios_latest = folios.sort_values("month").iloc[-1]

payload["kpis"] = {
    "total_aum_crore": float(total_aum_latest),
    "total_aum_date": latest_aum_date.strftime("%b %Y"),
    "sip_inflow_crore": float(sip_latest["sip_inflow_crore"]),
    "sip_month": sip_latest["month"].strftime("%b %Y"),
    "folios_crore": float(folios_latest["total_folios_crore"]),
    "folios_month": folios_latest["month"].strftime("%b %Y"),
    "num_schemes": int(fund_master.shape[0]),
    # honesty note: dataset has 40 real schemes; industry-wide figure (1,908) is cited
    # separately in the project brief as context, not as this dataset's own count.
}

# ---------------- Page 1: Industry Overview ----------------
aum_yearly = aum.copy()
aum_yearly["year"] = aum_yearly["date"].dt.year
industry_aum_trend = aum_yearly.groupby("date", as_index=False)["aum_crore"].sum().sort_values("date")
payload["industry_aum_trend"] = {
    "dates": industry_aum_trend["date"].dt.strftime("%Y-%m-%d").tolist(),
    "aum_crore": industry_aum_trend["aum_crore"].tolist(),
}

aum_by_house_latest = aum[aum["date"] == latest_aum_date].sort_values("aum_crore", ascending=False)
payload["aum_by_house"] = {
    "fund_house": aum_by_house_latest["fund_house"].tolist(),
    "aum_crore": aum_by_house_latest["aum_crore"].tolist(),
}

# ---------------- Page 2: Fund Performance ----------------
perf_merged = scorecard.merge(
    fund_master[["amfi_code", "fund_house", "plan"]], on="amfi_code"
).merge(
    perf[["amfi_code", "aum_crore", "std_dev_ann_pct"]], on="amfi_code"
)
payload["fund_scatter"] = perf_merged[[
    "amfi_code", "scheme_name", "fund_house", "category", "plan",
    "cagr_3yr", "std_dev_ann_pct", "aum_crore", "sharpe_ratio", "score"
]].round(4).to_dict(orient="records")

payload["fund_scorecard_table"] = scorecard.merge(
    fund_master[["amfi_code", "fund_house", "plan"]], on="amfi_code"
)[[
    "overall_rank", "scheme_name", "fund_house", "category", "plan",
    "score", "cagr_3yr", "sharpe_ratio", "alpha", "expense_ratio_pct"
]].round(4).to_dict(orient="records")

# NAV series for top 10 funds by AUM + Nifty 50/100 (indexed to 100), last 3 years
top10 = perf.nlargest(10, "aum_crore")["amfi_code"].tolist()
three_yr_start = nav["date"].max() - pd.DateOffset(years=3)
nav_series = {}
for code in top10:
    g = nav[(nav["amfi_code"] == code) & (nav["date"] >= three_yr_start)].sort_values("date")
    nav_series[code] = {
        "name": g["scheme_name"].iloc[0],
        "dates": g["date"].dt.strftime("%Y-%m-%d").tolist(),
        "indexed": (g["nav"] / g["nav"].iloc[0] * 100).round(2).tolist(),
    }
payload["nav_series"] = nav_series

bench_series = {}
for idx_name in ["NIFTY50", "NIFTY100"]:
    b = bench[(bench["index_name"] == idx_name) & (bench["date"] >= three_yr_start)].sort_values("date")
    bench_series[idx_name] = {
        "dates": b["date"].dt.strftime("%Y-%m-%d").tolist(),
        "indexed": (b["close_value"] / b["close_value"].iloc[0] * 100).round(2).tolist(),
    }
payload["benchmark_series"] = bench_series

payload["filter_options"] = {
    "fund_house": sorted(fund_master["fund_house"].unique().tolist()),
    "category": sorted(fund_master["category"].unique().tolist()),
    "plan": sorted(fund_master["plan"].unique().tolist()),
}

# ---------------- Page 3: Investor Analytics ----------------
# compact per-group summary (not raw 32k rows) so client-side filtering stays fast
group_cols = ["state", "age_group", "city_tier", "transaction_type"]
tx["month"] = tx["transaction_date"].dt.to_period("M").astype(str)
tx_summary = tx.groupby(group_cols + ["month"], as_index=False).agg(
    total_amount=("amount_inr", "sum"),
    count=("amount_inr", "size"),
)
payload["tx_summary"] = tx_summary.to_dict(orient="records")

payload["filter_options"]["state"] = sorted(tx["state"].unique().tolist())
payload["filter_options"]["age_group"] = sorted(tx["age_group"].unique().tolist())
payload["filter_options"]["city_tier"] = sorted(tx["city_tier"].unique().tolist())

# ---------------- Page 4: SIP & Market Trends ----------------
n50_monthly = bench[bench["index_name"] == "NIFTY50"].copy()
n50_monthly["month"] = n50_monthly["date"].dt.to_period("M").astype(str)
n50_monthly = n50_monthly.groupby("month", as_index=False)["close_value"].last()

sip_indexed = sip.copy()
sip_indexed["month_str"] = sip_indexed["month"].dt.strftime("%Y-%m")
payload["sip_vs_nifty"] = {
    "months": sip_indexed["month_str"].tolist(),
    "sip_inflow_crore": sip_indexed["sip_inflow_crore"].tolist(),
    "nifty50_close": n50_monthly.set_index("month").reindex(sip_indexed["month_str"])["close_value"].tolist(),
}

cat_pivot = cat_inflow.pivot_table(index="category", columns="month", values="net_inflow_crore", aggfunc="sum")
payload["category_heatmap"] = {
    "categories": cat_pivot.index.tolist(),
    "months": [c.strftime("%Y-%m") for c in cat_pivot.columns],
    "values": cat_pivot.fillna(0).values.tolist(),
}

fy25 = cat_inflow[(cat_inflow["month"] >= "2024-04-01") & (cat_inflow["month"] <= "2025-03-31")]
top5_cat = fy25.groupby("category")["net_inflow_crore"].sum().nlargest(5)
payload["top5_categories_fy25"] = {
    "categories": top5_cat.index.tolist(),
    "net_inflow_crore": top5_cat.values.tolist(),
}

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w") as f:
    json.dump(payload, f)
print(f"Saved {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
