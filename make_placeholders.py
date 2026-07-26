pages = {
    "pages/01_home.py": "Home",
    "pages/02_profile.py": "Company Profile",
    "pages/03_screener.py": "Screener",
    "pages/04_peers.py": "Peer Comparison",
    "pages/05_trends.py": "Trend Analysis",
    "pages/06_sectors.py": "Sector Analysis",
    "pages/07_capital.py": "Capital Allocation Map",
    "pages/08_reports.py": "Annual Reports",
}

for path, title in pages.items():
    with open(path, "w") as f:
        f.write(f'''import streamlit as st

st.set_page_config(page_title="{title}", layout="wide")
st.title("{title}")
st.info("This screen is a placeholder - built out on Days 23-25.")
''')

print("Wrote 8 placeholder pages")