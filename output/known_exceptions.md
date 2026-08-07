# Known Data Exceptions — Sprint 1

## Resolved CRITICAL failures (DQ-06, DQ-07)
- **ADANIENSOL, Mar 2014**: source profitandloss and balancesheet rows are entirely
  zero-valued (pre-listing placeholder row in the vendor export). Fabricating a
  non-zero value would misstate financials, so this row is excluded at load time
  in `loader.py` (any statement row where every numeric column is 0/NaN is treated
  as a shell row and dropped). Resulting company history for ADANIENSOL starts at
  Mar 2015, which is its first substantive reporting year.

## WARNING-level anomalies (documented, not blocking)
- DQ-05 (OPM cross-check): 216 rows where computed OPM differs from the source
  `opm_percentage` field by >1pp — mostly companies with material other-income lines
  that shift the reported margin. Ratio engine uses the *computed* value for analytics.
- DQ-09 (tax rate sanity): 90 rows with tax_percentage outside [0,60]% — includes
  legitimate deferred-tax-credit years (negative effective tax rate).
- DQ-11 (annual report URL format): 296 rows — a batch of BSE attachment links use a
  relative/malformed path in the vendor export; still usable but flagged.
- DQ-16 (no peer group assigned): 36 companies are not mapped to any of the 11 peer
  groups (peer-group coverage is intentionally partial — Nifty 100 spans more
  industries than the 11 curated peer groups). Peer engine handles this by returning
  "No peer group assigned" rather than raising.
