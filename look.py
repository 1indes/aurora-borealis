# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
import json

with open("data/kp-1year.json") as f:
    data = json.load(f)

print("Keys in the file:", list(data.keys()))

kps = data["Kp"]
print("Number of values:", len(kps))
print("Lowest Kp:", min(kps))
print("Highest Kp:", max(kps))

calm = 0
active = 0
storm = 0
for kp in kps:
    if kp < 4:
        calm += 1
    elif kp < 5:
        active += 1
    else:
        storm += 1
print("Calm (under 4):", calm)
print("Active (4 to 4.99):", active)
print("Storm (5 or more):", storm)

if "datetime" in data:
    print("First time:", data["datetime"][0])
    print("Last time:", data["datetime"][-1])
    print("Strong slots (Kp 6 or more):")
    for i in range(len(kps)):
        if kps[i] >= 6:
            print(data["datetime"][i], kps[i])

print("Meta:", data["meta"])
print("Status values:", set(data["status"]))
pre_count = 0
first_pre = None
for i in range(len(data["status"])):
    if data["status"][i] == "pre":
        pre_count += 1
        if first_pre is None:
            first_pre = data["datetime"][i]
print("Preliminary values:", pre_count)
print("First preliminary slot:", first_pre)