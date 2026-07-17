-- exploratory_queries.sql
-- Day 7 deliverable: 10 sanity/exploration queries against nifty100.db
-- Run with: sqlite3 db/nifty100.db < notebooks/exploratory_queries.sql

-- 1. Row counts per table (sanity check vs load_audit.csv)
SELECT 'companies' AS tbl, COUNT(*) AS n FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups;

-- 2. Companies with the fewest years of P&L history (coverage gaps, DQ-16)
SELECT company_id, COUNT(DISTINCT year) AS years_covered
FROM profitandloss
WHERE year != 'TTM'
GROUP BY company_id
ORDER BY years_covered ASC
LIMIT 10;

-- 3. Top 10 companies by latest reported sales
SELECT company_id, year, sales
FROM profitandloss
WHERE year = (SELECT MAX(year) FROM profitandloss p2 WHERE p2.company_id = profitandloss.company_id AND year != 'TTM')
ORDER BY sales DESC
LIMIT 10;

-- 4. Sector breakdown: company count and average ROE per broad sector
SELECT s.broad_sector, COUNT(*) AS n_companies, ROUND(AVG(c.roe_percentage), 2) AS avg_roe
FROM sectors s
JOIN companies c ON c.company_id = s.company_id
GROUP BY s.broad_sector
ORDER BY avg_roe DESC;

-- 5. Companies whose latest balance sheet doesn't balance within 1% (DQ-04 violations)
SELECT company_id, year, total_assets, total_liabilities,
       ROUND(ABS(total_assets - total_liabilities) * 100.0 / NULLIF(total_liabilities, 0), 2) AS diff_pct
FROM balancesheet
WHERE ABS(total_assets - total_liabilities) * 100.0 / NULLIF(total_liabilities, 0) > 1.0
ORDER BY diff_pct DESC
LIMIT 10;

-- 6. Highest dividend-payout companies (last 3 fiscal years)
SELECT company_id, year, dividend_payout
FROM profitandloss
WHERE dividend_payout IS NOT NULL AND year != 'TTM'
ORDER BY year DESC, dividend_payout DESC
LIMIT 10;

-- 7. Stock price volatility proxy: highest (high-low)/close range in the dataset
SELECT company_id, date, open_price, high_price, low_price, close_price,
       ROUND((high_price - low_price) / NULLIF(close_price, 0) * 100, 2) AS range_pct
FROM stock_prices
ORDER BY range_pct DESC
LIMIT 10;

-- 8. Companies referenced in transaction tables but missing from companies.xlsx (DQ-03 gap)
SELECT DISTINCT company_id FROM (
    SELECT company_id FROM profitandloss
    UNION SELECT company_id FROM balancesheet
    UNION SELECT company_id FROM cashflow
) t
WHERE company_id NOT IN (SELECT company_id FROM companies);

-- 9. Peer group composition with benchmark flag
SELECT peer_group_name, company_id, is_benchmark
FROM peer_groups
ORDER BY peer_group_name, is_benchmark DESC;

-- 10. Market cap growth: companies with highest CAGR-style jump between first and last year on record
SELECT company_id,
       MIN(year) AS first_year, MAX(year) AS last_year,
       MIN(market_cap_crore) AS first_cap, MAX(market_cap_crore) AS last_cap,
       ROUND((MAX(market_cap_crore) - MIN(market_cap_crore)) * 100.0 / NULLIF(MIN(market_cap_crore), 0), 1) AS pct_change
FROM market_cap
GROUP BY company_id
HAVING COUNT(*) >= 2
ORDER BY pct_change DESC
LIMIT 10;
