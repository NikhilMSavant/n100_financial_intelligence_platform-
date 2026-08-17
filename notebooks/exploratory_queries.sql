-- Sprint 1 — Exploratory queries (run against data/nifty100.db)

-- 1. Row counts per table
SELECT 'companies' t, COUNT(*) n FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups;

-- 2. Null check on required P&L fields
SELECT COUNT(*) missing_sales FROM profitandloss WHERE sales IS NULL;

-- 3. Year coverage per company (P&L)
SELECT company_id, COUNT(*) years_available
FROM profitandloss GROUP BY company_id ORDER BY years_available ASC;

-- 4. Companies with < 5 years of P&L history
SELECT company_id, COUNT(*) n FROM profitandloss
GROUP BY company_id HAVING n < 5;

-- 5. Companies missing from balancesheet entirely
SELECT id FROM companies
WHERE id NOT IN (SELECT DISTINCT company_id FROM balancesheet);

-- 6. Sector distribution
SELECT broad_sector, COUNT(*) n FROM sectors GROUP BY broad_sector ORDER BY n DESC;

-- 7. Companies with negative net_profit in the latest available year
SELECT p.company_id, p.year, p.net_profit
FROM profitandloss p
JOIN (SELECT company_id, MAX(year) AS max_year FROM profitandloss GROUP BY company_id) m
  ON p.company_id = m.company_id AND p.year = m.max_year
WHERE p.net_profit < 0;

-- 8. Balance sheet mismatch count (>1% of total_assets)
SELECT COUNT(*) FROM balancesheet
WHERE ABS(total_assets - total_liabilities) / NULLIF(total_assets, 0) > 0.01;

-- 9. Debt-free companies (latest year, borrowings = 0)
SELECT b.company_id FROM balancesheet b
JOIN (SELECT company_id, MAX(year) AS max_year FROM balancesheet GROUP BY company_id) m
  ON b.company_id = m.company_id AND b.year = m.max_year
WHERE b.borrowings = 0;

-- 10. Documents coverage per company
SELECT company_id, COUNT(*) n_reports FROM documents GROUP BY company_id ORDER BY n_reports ASC;
