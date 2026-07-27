import requests

url = "https://www.bseindia.com/bseplus/AnnualReport/532540/5325400319.pdf"

print("--- Without User-Agent ---")
try:
    resp = requests.head(url, timeout=5)
    print("Status:", resp.status_code)
except Exception as e:
    print("Failed:", e)

print("\n--- With a browser-like User-Agent ---")
try:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    resp = requests.head(url, timeout=5, headers=headers)
    print("Status:", resp.status_code)
except Exception as e:
    print("Failed:", e)