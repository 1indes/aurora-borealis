
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "scipy"]
# ///
import json
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy.interpolate import PchipInterpolator

HEIGHT = 0.26      # how tall one Kp unit is. Lower it if the curtains feel crowded.
FADE = 1.1         # how far the glow falls below each curve (bigger = fuller curtain)
BACKGROUND = "#050814"
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Kp value -> colour. Between these points the colour blends smoothly.
# These colours are my choice. The data itself has no colour in it.
STOPS = [
    (0, (0.03, 0.25, 0.20)),  # dim green
    (3, (0.20, 0.90, 0.50)),  # bright green
    (4.5, (0.20, 0.70, 0.95)),  # cyan-blue
    (6, (0.60, 0.30, 0.95)),  # purple
    (7.5, (0.95, 0.35, 0.75)),  # pink
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


def smooth_curve(xs, kps):
    # A smooth curve that passes through every real Kp value.
    curve = PchipInterpolator(xs, kps)
    fine_x = np.linspace(xs[0], xs[-1], 900)
    fine_kp = np.clip(curve(fine_x), 0, 9)
    return fine_x, fine_kp


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
    # the middle of the 3-hour slot, as a position along the month
    xs_by_month[key].append(day - 1 + (hour + 1.5) / 24)
    kps_by_month[key].append(kps[i])

max_height = max(kps) * HEIGHT
fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor(BACKGROUND)
ax.set_facecolor(BACKGROUND)

# oldest month at the top; each later month is drawn in front of the one above
for m in range(len(months)):
    key = months[m]
    base = -m
    x, kp = smooth_curve(xs_by_month[key], kps_by_month[key])
    top = base + kp * HEIGHT

    colours = []
    for value in kp:
        colours.append(kp_to_colour(value))

    # 1. hide whatever is behind this curtain
    ax.fill_between(x, base - 1.5, top, color=BACKGROUND, linewidth=0,
                    zorder=3 * m)

    # 2. the soft curtain of light, brightest at the curve and fading downward
    rows = 120
    heights = np.linspace(0, max_height, rows)
    glow = np.zeros((rows, len(x), 4))
    for i in range(len(x)):
        depth = kp[i] * HEIGHT - heights
        alpha = np.clip(1 - depth / FADE, 0, 1) * (depth >= 0) * 0.6
        glow[:, i, 0] = colours[i][0]
        glow[:, i, 1] = colours[i][1]
        glow[:, i, 2] = colours[i][2]
        glow[:, i, 3] = alpha
    ax.imshow(glow, extent=[x[0], x[-1], base, base + max_height],
              origin="lower", aspect="auto", interpolation="bilinear",
              zorder=3 * m + 1)

    # 3. the glowing edge: three passes, wide and faint to thin and bright
    points = np.array([x, top]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    for width, alpha in [(7, 0.06), (3.5, 0.15), (1.2, 0.95)]:
        edge = LineCollection(segments, colors=colours[:-1], linewidths=width,
                              alpha=alpha, capstyle="round",
                              zorder=3 * m + 2)
        ax.add_collection(edge)

ticks = []
labels = []
for m in range(len(months)):
    ticks.append(-m)
    labels.append(month_label(months[m]))
ax.set_yticks(ticks)
ax.set_yticklabels(labels)

ax.set_xlim(0, 31)
ax.set_ylim(-(len(months) - 1) - 0.4, max_height + 0.3)
ax.set_xlabel("Day of month (UTC)")
ax.set_title("A year of geomagnetic activity, one curtain per month",
             color="#e8ecf5", pad=14)
ax.tick_params(colors="#c8d0e0", length=0)
ax.xaxis.label.set_color("#c8d0e0")
for side in ax.spines:
    ax.spines[side].set_visible(False)

# a small key: which colour means which Kp
key_ax = fig.add_axes([0.62, 0.05, 0.28, 0.016])
strip = np.zeros((1, 200, 3))
for i in range(200):
    strip[0, i] = kp_to_colour(9 * i / 199)
key_ax.imshow(strip, aspect="auto", extent=[0, 9, 0, 1])
key_ax.set_yticks([])
key_ax.set_xticks([0, 3, 5, 7, 9])
key_ax.tick_params(colors="#c8d0e0", labelsize=8, length=2)
key_ax.set_xlabel("Kp index (colours chosen by me, not measured)",
                  color="#c8d0e0", fontsize=8)
for side in key_ax.spines:
    key_ax.spines[side].set_visible(False)

fig.subplots_adjust(bottom=0.17)

os.makedirs("out", exist_ok=True)
plt.savefig("out/aurora.png", dpi=150, facecolor=BACKGROUND)
print("Saved out/aurora.png")