PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    company_name TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

CREATE TABLE IF NOT EXISTS profitandloss (
    company_id TEXT,
    year TEXT,
    sales REAL, expenses REAL, operating_profit REAL, opm_percentage REAL,
    other_income REAL, interest REAL, depreciation REAL, profit_before_tax REAL,
    tax_percentage REAL, net_profit REAL, eps REAL, dividend_payout REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS balancesheet (
    company_id TEXT, year TEXT,
    equity_capital REAL, reserves REAL, borrowings REAL, other_liabilities REAL,
    total_liabilities REAL, fixed_assets REAL, cwip REAL, investments REAL,
    other_asset REAL, total_assets REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS cashflow (
    company_id TEXT, year TEXT,
    operating_activity REAL, investing_activity REAL, financing_activity REAL,
    net_cash_flow REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS analysis (
    company_id TEXT PRIMARY KEY,
    compounded_sales_growth TEXT, compounded_profit_growth TEXT,
    stock_price_cagr TEXT, roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS documents (
    company_id TEXT, year INTEGER, annual_report TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY, company_id TEXT, pros TEXT, cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS sectors (
    company_id TEXT PRIMARY KEY, broad_sector TEXT, sub_sector TEXT,
    index_weight_pct REAL, market_cap_category TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS market_cap (
    company_id TEXT, year INTEGER,
    market_cap_crore REAL, enterprise_value_crore REAL, pe_ratio REAL,
    pb_ratio REAL, ev_ebitda REAL, dividend_yield_pct REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS stock_prices (
    company_id TEXT, date TEXT,
    open_price REAL, high_price REAL, low_price REAL, close_price REAL,
    volume INTEGER, adjusted_close REAL,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS peer_groups (
    peer_group_name TEXT, company_id TEXT, is_benchmark INTEGER,
    PRIMARY KEY (peer_group_name, company_id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS financial_ratios (
    company_id TEXT, year TEXT,
    net_profit_margin_pct REAL, operating_profit_margin_pct REAL,
    return_on_equity_pct REAL, return_on_capital_employed_pct REAL,
    return_on_assets_pct REAL,
    debt_to_equity REAL, high_leverage_flag INTEGER,
    interest_coverage REAL, icr_label TEXT, icr_warning_flag INTEGER,
    net_debt_cr REAL, asset_turnover REAL,
    revenue_cagr_3yr REAL, revenue_cagr_3yr_flag TEXT,
    revenue_cagr_5yr REAL, revenue_cagr_5yr_flag TEXT,
    revenue_cagr_10yr REAL, revenue_cagr_10yr_flag TEXT,
    pat_cagr_3yr REAL, pat_cagr_3yr_flag TEXT,
    pat_cagr_5yr REAL, pat_cagr_5yr_flag TEXT,
    pat_cagr_10yr REAL, pat_cagr_10yr_flag TEXT,
    eps_cagr_3yr REAL, eps_cagr_3yr_flag TEXT,
    eps_cagr_5yr REAL, eps_cagr_5yr_flag TEXT,
    eps_cagr_10yr REAL, eps_cagr_10yr_flag TEXT,
    free_cash_flow_cr REAL, capex_cr REAL, capex_intensity_pct REAL, capex_label TEXT,
    cfo_pat_ratio REAL, cfo_quality_label TEXT,
    fcf_conversion_pct REAL,
    earnings_per_share REAL, book_value_per_share REAL,
    dividend_payout_ratio_pct REAL, total_debt_cr REAL, cash_from_operations_cr REAL,
    composite_quality_score REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS peer_percentiles (
    company_id TEXT, peer_group_name TEXT, metric TEXT, value REAL,
    percentile_rank REAL, year TEXT,
    PRIMARY KEY (company_id, peer_group_name, metric, year)
);

CREATE INDEX IF NOT EXISTS idx_pl_company ON profitandloss(company_id);
CREATE INDEX IF NOT EXISTS idx_bs_company ON balancesheet(company_id);
CREATE INDEX IF NOT EXISTS idx_cf_company ON cashflow(company_id);
CREATE INDEX IF NOT EXISTS idx_ratios_company ON financial_ratios(company_id);
CREATE INDEX IF NOT EXISTS idx_ratios_year ON financial_ratios(year);
