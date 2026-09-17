# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
import requests, pathlib, json

# NOAA planetary Kp index feed (3-hour values)
url = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
response = requests.get(url)
data = response.json()

pathlib.Path("data").mkdir(exist_ok=True)

with open("data/aurora-kp.json", "w") as f:
    json.dump(data, f)
