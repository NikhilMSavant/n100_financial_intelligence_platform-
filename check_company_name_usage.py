import os

for root, dirs, files in os.walk("."):
    if ".venv" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, encoding="utf-8", errors="ignore") as file:
                content = file.read()
            if "company_name" in content and ("WHERE" in content.upper() or "filter" in content.lower() or "==" in content):
                # just flag files that reference company_name at all, for manual review
                print(path)