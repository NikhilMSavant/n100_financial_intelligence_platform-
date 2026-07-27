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
  
## CSV download scope fix (Day 24)
- Spec: "CSV download button generates well-formed CSV with all visible
  columns." Initial implementation exported the full 24-column internal
  dataframe, not just the 6 columns actually shown in the on-screen
  table. Fixed to export result[display_cols] instead of the full
  result dataframe.