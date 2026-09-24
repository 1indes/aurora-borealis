
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///
import json
import os
import matplotlib.pyplot as plt

with open("data/kp-1year.json") as f:
    data = json.load(f)

kps = data["Kp"]

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(kps)
ax.set_xlabel("3-hour slot number (0 = 24 Sep 2025)")
ax.set_ylabel("Kp index")

os.makedirs("out", exist_ok=True)
plt.savefig("out/first-plot.png", dpi=150)
print("Saved out/first-plot.png")