import sys
sys.path.insert(0, "src/dashboard/utils")
from db import get_pl

df = get_pl("JIOFIN")
print(df[["year", "sales", "net_profit"]])