import os

for root, dirs, files in os.walk("tests"):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path) as file:
                content = file.read()
            if "DQ-" in content or "dq_rule" in content.lower() or "validator" in content.lower():
                print(f"Found DQ-related content in: {path}")