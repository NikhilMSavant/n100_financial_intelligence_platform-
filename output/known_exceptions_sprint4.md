# Sprint 4 known exceptions and deviations

## company_name data quality issue (Day 23)
- 17 companies had extra content after an embedded newline character in
  their company_name field. Most were just a trailing "\n"; two
  (APOLLOHOSP, ASIANPAINT) had an actual company description leaked into
  the name field from the source Excel file (e.g. "Asian Paints\nIndian
  Multi-National Paint and Coating Manufacturing Company").
- Fixed in db.py's get_companies() by taking only the text before the
  first newline - applies globally to every dashboard screen that uses
  this function, not just the Company Profile page where it was found.
  