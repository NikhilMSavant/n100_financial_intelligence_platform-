# DQ CRITICAL Failure Resolution Log

Every CRITICAL finding from validator.py's Day 3 rules (DQ-01..DQ-16), as required by Sprint 1's exit criterion ("CRITICAL failures resolved"). Written by loader.py on every run, alongside output/quarantined_critical_rows.csv.

## Resolved by quarantining the row

- **ADANIENSOL, 2014-03** (profitandloss + balancesheet): every financial field zeroed out simultaneously (sales=0, total_assets=0, total_liabilities=0) - not a real business event, corrupted/placeholder source data. Rejected at load time via KNOWN_BAD_ROWS in loader.py. Triggered DQ-06 and DQ-10.

## Accepted as a genuine data-coverage limitation (not quarantined)

- **JIOFIN**: only 2 distinct fiscal years of P&L data (2023-03, 2024-03), below DQ-16's 3-year CRITICAL threshold. Jio Financial Services was demerged from Reliance Industries and listed in 2023, so this is genuine, uncorrupted data for a recently-listed company - there is no earlier history to load. Rejecting these 2 valid rows would remove real data for no benefit. Every downstream CAGR/growth computation already handles this correctly via cagr.py's INSUFFICIENT flag (returns None + a named flag rather than crashing or producing a misleading number from too short a window) - verified in tests/kpi/test_cagr.py.
