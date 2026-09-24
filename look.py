# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
import json

with open("data/aurora-kp.json") as f:
    rows = json.load(f)

print("Number of rows:", len(rows))
print("First row:", rows[0])
print("Last row:", rows[-1])