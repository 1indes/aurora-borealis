# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///
import json
import os
import matplotlib.pyplot as plt

HEIGHT = 0.3  # how tall one Kp unit is. Lower it if the bands feel crowded.
BACKGROUND = "#050814"
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Kp value -> colour. Between these points the colour blends smoothly.
STOPS = [
    (0, (0.02, 0.20, 0.15)),  # dim green
    (3, (0.15, 0.85, 0.45)),  # bright green
    (5, (0.90, 0.35, 0.75)),  # pink
    (7, (0.65, 0.25, 0.95)),  # purple
    (9, (1.00, 0.30, 0.30)),  # red
]


def kp_to_colour(kp):
    if kp <= STOPS[0][0]:
        return STOPS[0][1]
    for i in range(1, len(STOPS)):
        low_kp, low_col = STOPS[i - 1]
        high_kp, high_col = STOPS[i]
        if kp <= high_kp:
            t = (kp - low_kp) / (high_kp - low_kp)
            return tuple(low_col[j] + (high_col[j] - low_col[j]) * t
                         for j in range(3))
    return STOPS[-1][1]


def month_label(key):
    # "2025-09" -> "Sep 2025"
    return MONTH_NAMES[int(key[5:7]) - 1] + " " + key[:4]


with open("data/kp-1year.json") as f:
    data = json.load(f)

kps = data["Kp"]
times = data["datetime"]

# sort the values into months
months = []
xs_by_month = {}
kps_by_month = {}
for i in range(len(kps)):
    stamp = times[i]
    key = stamp[:7]
    if key not in kps_by_month:
        months.append(key)
        xs_by_month[key] = []
        kps_by_month[key] = []
    day = int(stamp[8:10])
    hour = int(stamp[11:13])
    xs_by_month[key].append(day - 1 + hour / 24)
    kps_by_month[key].append(kps[i])

fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor(BACKGROUND)
ax.set_facecolor(BACKGROUND)

# oldest month at the top, each later month drawn in front of the one above
for m in range(len(months)):
    key = months[m]
    colours = []
    heights = []
    for kp in kps_by_month[key]:
        colours.append(kp_to_colour(kp))
        heights.append(kp * HEIGHT)
    ax.bar(xs_by_month[key], heights, width=3 / 24, bottom=-m,
           align="edge", color=colours, edgecolor=colours,
           linewidth=0.4, zorder=m)

ticks = []
labels = []
for m in range(len(months)):
    ticks.append(-m)
    labels.append(month_label(months[m]))
ax.set_yticks(ticks)
ax.set_yticklabels(labels)

ax.set_xlim(0, 31)
ax.set_ylim(-(len(months) - 1) - 0.2, max(kps) * HEIGHT + 0.2)
ax.set_xlabel("Day of month (UTC)")
ax.set_title("A year of geomagnetic activity, one curtain per month",
             color="#e8ecf5")
ax.tick_params(colors="#c8d0e0")
ax.xaxis.label.set_color("#c8d0e0")
for side in ax.spines:
    ax.spines[side].set_visible(False)

os.makedirs("out", exist_ok=True)
plt.savefig("out/curtains.png", dpi=150, facecolor=BACKGROUND)
print("Saved out/curtains.png")
