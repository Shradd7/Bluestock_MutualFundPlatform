-- Bluestock MF Analytics — Day 2, Task 6: 10 Analytical Queries
-- Run against data/db/bluestock_mf.db

-- 1. Top 5 funds by latest AUM (from fact_performance, most reliable per-scheme AUM)
SELECT f.scheme_name, f.fund_house, p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month, per fund (example: HDFC Top 100, amfi_code 125497)
SELECT strftime('%Y-%m', date) AS month, ROUND(AVG(nav), 2) AS avg_nav
FROM fact_nav
WHERE amfi_code = '125497'
GROUP BY month
ORDER BY month;

-- 3. SIP transaction volume YoY growth (computed from fact_transactions;
--    for true industry-wide SIP inflow YoY, load 04_monthly_sip_inflows.csv into its
--    own table — it's not part of the 6-table core schema, so this uses schema data)
WITH yearly AS (
    SELECT strftime('%Y', transaction_date) AS year, SUM(amount_inr) AS total_sip_inr
    FROM fact_transactions
    WHERE transaction_type = 'SIP'
    GROUP BY year
)
SELECT year, total_sip_inr,
       ROUND(100.0 * (total_sip_inr - LAG(total_sip_inr) OVER (ORDER BY year))
             / LAG(total_sip_inr) OVER (ORDER BY year), 2) AS yoy_growth_pct
FROM yearly
ORDER BY year;

-- 4. Total transaction amount by state
SELECT state, COUNT(*) AS num_transactions, SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;

-- 5. Funds with expense_ratio_pct < 1%
SELECT scheme_name, fund_house, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct;

-- 6. Top 10 funds by Sharpe ratio (best risk-adjusted return)
SELECT f.scheme_name, p.sharpe_ratio, p.return_3yr_pct
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 10;

-- 7. Average SIP amount by age group
SELECT age_group, ROUND(AVG(amount_inr), 0) AS avg_amount_inr, COUNT(*) AS num_tx
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY age_group
ORDER BY avg_amount_inr DESC;

-- 8. City-tier split of transaction volume (T30 vs B30)
SELECT city_tier, COUNT(*) AS num_tx, SUM(amount_inr) AS total_amount_inr,
       ROUND(100.0 * SUM(amount_inr) / (SELECT SUM(amount_inr) FROM fact_transactions), 2) AS pct_of_total
FROM fact_transactions
GROUP BY city_tier;

-- 9. Latest AUM by fund house (most recent quarter)
SELECT fund_house, aum_crore, num_schemes
FROM fact_aum
WHERE date = (SELECT MAX(date) FROM fact_aum)
ORDER BY aum_crore DESC;

-- 10. Funds with the worst (most negative) max_drawdown, by category
SELECT f.category, f.scheme_name, p.max_drawdown_pct
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.max_drawdown_pct ASC
LIMIT 10;
