-- Bluestock MF Analytics — SQLite Star Schema
-- Day 2, Task 4

PRAGMA foreign_keys = ON;

-- ============ DIMENSION TABLES ============

CREATE TABLE dim_fund (
    amfi_code           TEXT PRIMARY KEY,
    fund_house          TEXT NOT NULL,
    scheme_name         TEXT NOT NULL,
    category             TEXT,
    sub_category         TEXT,
    plan                 TEXT,
    launch_date          DATE,
    benchmark            TEXT,
    expense_ratio_pct    REAL,
    exit_load_pct        REAL,
    min_sip_amount        INTEGER,
    min_lumpsum_amount    INTEGER,
    fund_manager          TEXT,
    risk_category         TEXT,
    sebi_category_code    TEXT
);

CREATE TABLE dim_date (
    date_id      INTEGER PRIMARY KEY,   -- YYYYMMDD
    date          DATE NOT NULL UNIQUE,
    year          INTEGER,
    month         INTEGER,
    quarter       INTEGER,
    is_weekday    INTEGER               -- 1 = weekday, 0 = weekend
);

-- ============ FACT TABLES ============

CREATE TABLE fact_nav (
    amfi_code         TEXT NOT NULL,
    date               DATE NOT NULL,
    nav                REAL NOT NULL,
    daily_return_pct   REAL,
    PRIMARY KEY (amfi_code, date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE fact_transactions (
    tx_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id           TEXT NOT NULL,
    amfi_code             TEXT NOT NULL,
    transaction_date      DATE NOT NULL,
    transaction_type      TEXT NOT NULL,   -- SIP / Lumpsum / Redemption
    amount_inr            INTEGER NOT NULL,
    state                 TEXT,
    city                  TEXT,
    city_tier             TEXT,
    age_group             TEXT,
    gender                TEXT,
    annual_income_lakh    REAL,
    payment_mode          TEXT,
    kyc_status             TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE fact_performance (
    amfi_code           TEXT PRIMARY KEY,
    return_1yr_pct       REAL,
    return_3yr_pct       REAL,
    return_5yr_pct       REAL,
    benchmark_3yr_pct    REAL,
    alpha                 REAL,
    beta                  REAL,
    sharpe_ratio          REAL,
    sortino_ratio         REAL,
    std_dev_ann_pct       REAL,
    max_drawdown_pct      REAL,
    aum_crore             INTEGER,
    expense_ratio_pct     REAL,
    morningstar_rating    INTEGER,
    risk_grade            TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE fact_aum (
    fund_house       TEXT NOT NULL,
    date              DATE NOT NULL,
    aum_lakh_crore    REAL,
    aum_crore         INTEGER,
    num_schemes       INTEGER,
    PRIMARY KEY (fund_house, date)
);

-- ============ INDEXES ============
CREATE INDEX idx_fact_nav_date ON fact_nav(date);
CREATE INDEX idx_fact_tx_amficode ON fact_transactions(amfi_code);
CREATE INDEX idx_fact_tx_date ON fact_transactions(transaction_date);
CREATE INDEX idx_fact_tx_investor ON fact_transactions(investor_id);
CREATE INDEX idx_fact_tx_state ON fact_transactions(state);
