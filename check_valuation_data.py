import pandas as pd
df = pd.read_excel("output/valuation_summary.xlsx")

# check known-bad-ROE companies aren't affected here (valuation doesn't use ROE)
print(df[df["company_id"].isin(["BEL", "HAL", "INDIGO", "LT", "PNB"])].to_string())

print()
# check TCS specifically, since we know its numbers well by now
print(df[df["company_id"] == "TCS"].to_string())