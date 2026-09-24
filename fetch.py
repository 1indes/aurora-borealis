# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
import requests

URL = "https://kp.gfz.de/app/json/?start=2025-09-24T00:00:00Z&end=2026-09-23T23:59:59Z&index=Kp"

reply = requests.get(URL)
reply.raise_for_status()

with open("data/kp-1year.json", "wb") as f:
    f.write(reply.content)

print("Saved", len(reply.content), "bytes")