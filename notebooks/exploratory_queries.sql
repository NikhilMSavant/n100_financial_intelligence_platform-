-- exploratory_queries.sql — Sprint 1 / Day 07
-- Run with: sqlite3 db/nifty100.db < notebooks/exploratory_queries.sql

-- 1. Company count
SELECT COUNT(*) AS n_companies FROM companies;

-- 2. Sector distribution
SELECT broad_sector, COUNT(*) AS n FROM sectors GROUP BY broad_sector ORDER BY n DESC;

-- 3. Companies with fewest years of P&L history
SELECT company_id, COUNT(*) AS n_years FROM profitandloss GROUP BY company_id ORDER BY n_years ASC LIMIT 10;

-- 4. Latest-year sales leaders
SELECT company_id, year, sales FROM profitandloss WHERE year = (SELECT MAX(year) FROM profitandloss) ORDER BY sales DESC LIMIT 10;

-- 5. Debt-free companies in the latest year (borrowings = 0)
SELECT b.company_id, b.year FROM balancesheet b
WHERE b.year = (SELECT MAX(year) FROM balancesheet) AND b.borrowings = 0;

-- 6. Average OPM by sector, latest year
SELECT s.broad_sector, AVG(p.opm_percentage) AS avg_opm
FROM profitandloss p JOIN sectors s ON p.company_id = s.company_id
WHERE p.year = (SELECT MAX(year) FROM profitandloss)
GROUP BY s.broad_sector ORDER BY avg_opm DESC;

-- 7. Companies where balance sheet doesn't balance within 1%
SELECT company_id, year, total_liabilities, total_assets
FROM balancesheet
WHERE ABS(total_liabilities - total_assets) / NULLIF(ABS(total_assets),0) >= 0.01;

-- 8. Peer group sizes
SELECT peer_group_name, COUNT(*) AS n_members FROM peer_groups GROUP BY peer_group_name ORDER BY n_members DESC;

-- 9. Median market cap by sector (approx via AVG, SQLite lacks native MEDIAN)
SELECT s.broad_sector, AVG(m.market_cap_crore) AS avg_mcap
FROM market_cap m JOIN sectors s ON m.company_id = s.company_id
WHERE m.year = (SELECT MAX(year) FROM market_cap)
GROUP BY s.broad_sector ORDER BY avg_mcap DESC;

-- 10. Row counts across all tables (quick health check)
SELECT 'companies' t, COUNT(*) n FROM companies
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups;
