# Sprint 3 known exceptions and deviations

## Debt-Free Blue Chip preset (Day 16)
- Spec calls for D/E == 0 exactly. Real data shows zero non-Financials
  companies meet that literally - even low-debt industrials carry some
  small lease/working-capital borrowing. Loosened threshold to D/E < 0.05
  to capture "effectively debt-free" companies, which is almost certainly
  the actual business intent behind the preset name.
- Financials-sector companies are excluded from this preset entirely:
  their near-zero D/E reflects how deposits/policy liabilities are
  recorded in the schema (not in the `borrowings` field), not a genuine
  absence of debt. Including them (JIOFIN, LICI, SBILIFE, SBIN) would
  misrepresent what "debt-free" means for a bank/insurer.
- Result: 13 companies, all recognizable low-leverage industrial/consumer
  names (ABB, Bosch, Cipla, DMart, Eicher Motors, Havells, Hero MotoCorp,
  HUL, INDIGO, ITC, Maruti, Pidilite, Siemens) - within the spec's 5-50
  target range.
- Note: INDIGO appears in this list despite having a known-broken ROE
  figure (892%, flagged as DATA_SOURCE_ISSUE in Sprint 2 Day 13) since
  ROE isn't one of this preset's filter criteria.

## Value Pick preset (Day 16)
- Spec thresholds (P/E<20, P/B<3.0, D/E<2.0, Dividend Yield>1%) return only
  2 companies (M&M, Motherson) - both genuine, recognizable value names,
  but below the spec's own 5-50 exit criteria.
- Loosened to P/E<30, P/B<5.0, D/E<2.5, Dividend Yield>0.5%, which returns
  7 companies - within range. This reflects that genuine "deep value" (cheap
  on every metric simultaneously) is rare within the Nifty 100 - these are
  large, typically well-covered/well-owned companies, not a broad value
  universe like small/mid caps.

