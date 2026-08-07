-- schema.sql — Sprint 1 / Day 04
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS companies;
CREATE TABLE companies (
    company_id      TEXT PRIMARY KEY,
    company_name    TEXT NOT NULL,
    about_company   TEXT,
    website         TEXT,
    nse_profile     TEXT,
    bse_profile     TEXT,
    face_value      REAL,
    book_value      REAL,
    roce_percentage REAL,
    roe_percentage  REAL
);

DROP TABLE IF EXISTS sectors;
CREATE TABLE sectors (
    company_id          TEXT PRIMARY KEY,
    broad_sector         TEXT NOT NULL,
    sub_sector            TEXT,
    index_weight_pct      REAL,
    market_cap_category   TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS profitandloss;
CREATE TABLE profitandloss (
    company_id         TEXT NOT NULL,
    year                INTEGER NOT NULL,
    sales               REAL,
    expenses            REAL,
    operating_profit    REAL,
    opm_percentage      REAL,
    other_income        REAL,
    interest            REAL,
    depreciation        REAL,
    profit_before_tax   REAL,
    tax_percentage      REAL,
    net_profit          REAL,
    eps                 REAL,
    dividend_payout     REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS balancesheet;
CREATE TABLE balancesheet (
    company_id       TEXT NOT NULL,
    year              INTEGER NOT NULL,
    equity_capital     REAL,
    reserves           REAL,
    borrowings         REAL,
    other_liabilities  REAL,
    total_liabilities  REAL,
    fixed_assets       REAL,
    cwip               REAL,
    investments        REAL,
    other_asset        REAL,
    total_assets       REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS cashflow;
CREATE TABLE cashflow (
    company_id        TEXT NOT NULL,
    year               INTEGER NOT NULL,
    operating_activity  REAL,
    investing_activity  REAL,
    financing_activity  REAL,
    net_cash_flow       REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS analysis;
CREATE TABLE analysis (
    id                           INTEGER PRIMARY KEY,
    company_id                   TEXT NOT NULL,
    compounded_sales_growth_raw  TEXT,
    compounded_profit_growth_raw TEXT,
    stock_price_cagr_raw         TEXT,
    roe_raw                      TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS documents;
CREATE TABLE documents (
    company_id     TEXT NOT NULL,
    year            INTEGER NOT NULL,
    annual_report   TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS prosandcons;
CREATE TABLE prosandcons (
    id           INTEGER PRIMARY KEY,
    company_id   TEXT NOT NULL,
    pros         TEXT,
    cons         TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS stock_prices;
CREATE TABLE stock_prices (
    id              INTEGER PRIMARY KEY,
    company_id      TEXT NOT NULL,
    date             TEXT NOT NULL,
    open_price       REAL,
    high_price       REAL,
    low_price        REAL,
    close_price      REAL,
    volume           REAL,
    adjusted_close   REAL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS market_cap;
CREATE TABLE market_cap (
    company_id            TEXT NOT NULL,
    year                   INTEGER NOT NULL,
    market_cap_crore       REAL,
    enterprise_value_crore REAL,
    pe_ratio                REAL,
    pb_ratio                REAL,
    ev_ebitda               REAL,
    dividend_yield_pct      REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS peer_groups;
CREATE TABLE peer_groups (
    id                INTEGER PRIMARY KEY,
    peer_group_name    TEXT NOT NULL,
    company_id         TEXT NOT NULL,
    is_benchmark        INTEGER DEFAULT 0,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS financial_ratios;
CREATE TABLE financial_ratios (
    company_id                    TEXT NOT NULL,
    year                           INTEGER NOT NULL,
    net_profit_margin_pct          REAL,
    operating_profit_margin_pct    REAL,
    return_on_equity_pct           REAL,
    return_on_capital_employed_pct REAL,
    return_on_assets_pct           REAL,
    debt_to_equity                 REAL,
    high_leverage_flag             INTEGER,
    interest_coverage               REAL,
    icr_label                       TEXT,
    icr_warning_flag                 INTEGER,
    net_debt_cr                      REAL,
    asset_turnover                    REAL,
    free_cash_flow_cr                 REAL,
    capex_cr                          REAL,
    earnings_per_share                 REAL,
    book_value_per_share                REAL,
    dividend_payout_ratio_pct            REAL,
    total_debt_cr                         REAL,
    cash_from_operations_cr                REAL,
    revenue_cagr_3yr        REAL, revenue_cagr_3yr_flag TEXT,
    revenue_cagr_5yr        REAL, revenue_cagr_5yr_flag TEXT,
    revenue_cagr_10yr       REAL, revenue_cagr_10yr_flag TEXT,
    pat_cagr_3yr             REAL, pat_cagr_3yr_flag TEXT,
    pat_cagr_5yr             REAL, pat_cagr_5yr_flag TEXT,
    pat_cagr_10yr            REAL, pat_cagr_10yr_flag TEXT,
    eps_cagr_3yr              REAL, eps_cagr_3yr_flag TEXT,
    eps_cagr_5yr              REAL, eps_cagr_5yr_flag TEXT,
    eps_cagr_10yr             REAL, eps_cagr_10yr_flag TEXT,
    cfo_quality_score           REAL,
    capex_intensity_pct          REAL,
    fcf_conversion_pct            REAL,
    composite_quality_score        REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

DROP TABLE IF EXISTS peer_percentiles;
CREATE TABLE peer_percentiles (
    company_id       TEXT NOT NULL,
    peer_group_name   TEXT NOT NULL,
    metric             TEXT NOT NULL,
    value               REAL,
    percentile_rank      REAL,
    year                  INTEGER NOT NULL,
    PRIMARY KEY (company_id, peer_group_name, metric, year)
);
