# Bluestock MF Analytics — Data Dictionary

Database: `data/db/bluestock_mf.db` (SQLite)
Source: AMFI India (public), mfapi.in, NSE/BSE — see `Bluestock_MF_Capstone_Project.pdf` for full provenance notes.

## dim_fund
Master list of the 40 mutual fund schemes covered by this project.

| Column | Type | Description |
|---|---|---|
| amfi_code | TEXT (PK) | AMFI unique scheme identifier. Stored as text to preserve leading zeros/formatting. |
| fund_house | TEXT | Asset Management Company name (e.g. SBI Mutual Fund). |
| scheme_name | TEXT | Full official AMFI scheme name. |
| category | TEXT | Equity / Debt / Hybrid. |
| sub_category | TEXT | Large Cap / Mid Cap / Small Cap / Liquid / etc. |
| plan | TEXT | Regular or Direct. |
| launch_date | DATE | Fund launch date. |
| benchmark | TEXT | Official benchmark index for the scheme. |
| expense_ratio_pct | REAL | Annual expense ratio, %. |
| exit_load_pct | REAL | Exit load, %. |
| min_sip_amount | INTEGER | Minimum SIP investment, INR. |
| min_lumpsum_amount | INTEGER | Minimum lumpsum investment, INR. |
| fund_manager | TEXT | Primary fund manager name. |
| risk_category | TEXT | SEBI risk category: Low / Moderate / High / Very High. |
| sebi_category_code | TEXT | Internal SEBI code (e.g. EC01 = Large Cap). |

## dim_date
Calendar dimension spanning the full range of NAV history.

| Column | Type | Description |
|---|---|---|
| date_id | INTEGER (PK) | Date as YYYYMMDD integer. |
| date | DATE (UNIQUE) | Calendar date. |
| year / month / quarter | INTEGER | Standard date parts. |
| is_weekday | INTEGER | 1 = Mon–Fri, 0 = weekend. |

## fact_nav
Daily NAV per scheme, gap-filled to a full business-day calendar.

| Column | Type | Description |
|---|---|---|
| amfi_code | TEXT (FK → dim_fund) | Scheme identifier. |
| date | DATE | NAV date. |
| nav | REAL | NAV in INR. Holiday/weekend gaps forward-filled from prior trading day. |
| daily_return_pct | REAL | `(nav_t / nav_t-1 - 1) * 100`, computed per scheme. |

**Primary key:** (amfi_code, date)

## fact_transactions
Individual investor transactions (SIP / Lumpsum / Redemption).

| Column | Type | Description |
|---|---|---|
| tx_id | INTEGER (PK) | Auto-generated surrogate key. |
| investor_id | TEXT | Unique investor identifier (INV000001–INV005000). |
| amfi_code | TEXT (FK → dim_fund) | Fund the transaction relates to. |
| transaction_date | DATE | Date of transaction. |
| transaction_type | TEXT | SIP / Lumpsum / Redemption (standardised during cleaning). |
| amount_inr | INTEGER | Transaction amount, INR. Validated > 0. |
| state | TEXT | Investor's state. |
| city | TEXT | Investor's city. |
| city_tier | TEXT | T30 (top 30 cities) or B30, per AMFI classification. |
| age_group | TEXT | 18-25 / 26-35 / 36-45 / 46-55 / 56+. |
| gender | TEXT | Male / Female. |
| annual_income_lakh | REAL | Annual income, INR lakh. |
| payment_mode | TEXT | UPI / Net Banking / Mandate / Cheque. |
| kyc_status | TEXT | Verified / Pending (standardised during cleaning; unrecognised values default to Pending). |

## fact_performance
One row per scheme — computed return and risk metrics.

| Column | Type | Description |
|---|---|---|
| amfi_code | TEXT (PK, FK → dim_fund) | Scheme identifier. |
| return_1yr_pct / return_3yr_pct / return_5yr_pct | REAL | Trailing returns (3yr/5yr are CAGR). |
| benchmark_3yr_pct | REAL | Benchmark index 3yr CAGR for comparison. |
| alpha | REAL | Excess return vs benchmark. |
| beta | REAL | Sensitivity to market moves (1.0 = moves with market). |
| sharpe_ratio | REAL | Risk-adjusted return; >1 generally considered good. |
| sortino_ratio | REAL | Like Sharpe, penalises only downside volatility. |
| std_dev_ann_pct | REAL | Annualised standard deviation of daily returns. |
| max_drawdown_pct | REAL | Worst peak-to-trough decline (always ≤ 0). |
| aum_crore | INTEGER | Scheme-level AUM, INR crore. |
| expense_ratio_pct | REAL | Annual expense ratio, %. Flagged (not dropped) if outside 0.1–2.5%. |
| morningstar_rating | INTEGER | 1–5 star rating. |
| risk_grade | TEXT | Risk classification. |

## fact_aum
Quarterly AUM by fund house (industry-level, not scheme-level).

| Column | Type | Description |
|---|---|---|
| fund_house | TEXT | AMC name. |
| date | DATE | Quarter-end date. |
| aum_lakh_crore | REAL | AUM in INR lakh crore. |
| aum_crore | INTEGER | AUM in INR crore. |
| num_schemes | INTEGER | Number of schemes managed by the fund house. |

**Primary key:** (fund_house, date)

---

## Cleaning rules applied (summary)

- **fact_nav**: dates parsed to datetime; sorted by amfi_code + date; reindexed to a full
  business-day calendar per fund with NAV forward-filled across gaps; NAV ≤ 0 or non-numeric
  dropped; exact duplicates removed.
- **fact_transactions**: transaction_type standardised to {SIP, Lumpsum, Redemption}, unmapped
  values dropped; amount_inr validated > 0 and coerced to numeric; dates parsed, unparseable
  rows dropped; kyc_status standardised to {Verified, Pending}, unrecognised values defaulted
  to Pending; exact duplicate transactions dropped.
- **fact_performance**: all numeric fields coerced, non-numeric values set to NaN and reported;
  expense_ratio_pct flagged (not dropped) if outside the expected 0.1%–2.5% range; negative
  Sharpe and positive max_drawdown flagged for review; rows missing core ranking metrics
  (return_3yr_pct, sharpe_ratio, alpha) dropped.

## Known data limitations

- `fact_transactions` covers 2024-01-01 onward only — earlier-period YoY comparisons are not
  meaningful with this dataset.
- Investor transaction data is synthetically generated (real geographic/demographic
  distributions, simulated individual records) — see source PDF, Section 8, "Note on Data
  Authenticity."
