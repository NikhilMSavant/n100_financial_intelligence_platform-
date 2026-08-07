# Sprint 5 Retrospective — Intelligence, NLP & PDF Reports

## NLP parser (Day 29)
64 rows parsed from the 16 loaded `analysis` records (4 fields x up to 4 period rows
each), 0 parse failures. Extended the spec's stated regex (`(\d+)\s*Years?:?\s*([\d.]+)%`)
to also recognise `TTM:`, `1 Year:` and `Last Year:` variants actually present in the
source data, and to accept a leading minus sign (`-2%`) -- the literal spec regex alone
would have logged most of the real dataset as parse failures. Cross-validated parsed
5yr/10yr CAGR against the ratio engine's computed CAGR: 0 divergences exceeded 5pp on
this data.

## Pros/Cons generator (Day 30)
24 rules implemented as specified. The literal ">60% confidence, include only if
above threshold" rule left 35/92 companies with zero pros or zero cons (many companies
in this dataset simply don't trip any rule at high confidence -- e.g. no 3-year ROE
run above 20%). Rather than silently violating the Day 30 exit criterion ("every
company has >=1 pro and >=1 con"), added a documented fallback pass: for any company
still missing a pro or con after the threshold filter, its single highest-confidence
candidate of that type is included even if <=60%. All 92 companies now have >=1 pro
and >=1 con (569 total rows).

## Cash-flow intelligence (Day 31-32)
92/92 rows. 13 companies flagged with a distress signal (CFO<0 and CFF>0 in the latest
year). `fcf_cagr_5yr` column is left null -- the ratio engine tracks FCF *level* per
year but not a dedicated FCF CAGR series; computing one would need >=2 FCF-CAGR
endpoints per company, which the current schema doesn't store separately from the
CAGR engine's revenue/PAT/EPS-only scope. Flagged as a fast-follow, not fabricated.

## PDF Tearsheets (Day 33-34)
Tested on TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL first (Day 33 requirement) --
all passed with no overflow. Batch run: 91/92 tearsheets generated, all >=35KB (min
30KB requirement met with margin). JIOFIN skipped (2 years of financial_ratios history,
below the <3-year skip threshold) and logged to `output/skipped_tearsheets.csv` --
this is real data, not a generator bug.

## Sector PDFs (Day 34)
10 PDFs generated, one per `broad_sector`. The sprint brief's "11 sector PDFs" figure
matches the peer-group count (11), not the broad-sector count -- this dataset's
`sectors` table has 10 distinct broad sectors (Industrials, Energy, Materials,
Healthcare, Financials, Consumer Discretionary, Communication Services, Consumer
Staples, Real Estate, Information Technology). Generating by broad_sector was the
more defensible reading since sector_report.py groups on that column per spec Day 34
wording ("11 sheets -- one per peer group" was Sprint 3's Excel deliverable, not this one).

## Portfolio summary (Day 35)
92-page PDF (one per company, alphabetical by ticker), trend arrows computed vs the
prior fiscal year with the specified 2% flat-band.
