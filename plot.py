
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
END_FADE = 1.2     # how many days each ribbon takes to fade in and out
BACKGROUND = "#050814"

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
fig = plt.figure(figsize=(10, 9))
fig.patch.set_facecolor(BACKGROUND)
ax = fig.add_axes([0.04, 0.03, 0.92, 0.94])
ax.set_facecolor(BACKGROUND)
ax.axis("off")

# oldest month at the top; each later month is drawn in front of the one above
for m in range(len(months)):
    key = months[m]
    base = -m
    x, kp = smooth_curve(xs_by_month[key], kps_by_month[key])
    top = base + kp * HEIGHT

    colours = []
    for value in kp:
        colours.append(kp_to_colour(value))

    # each ribbon fades in and out at its two ends instead of stopping dead
    ends = np.clip((x - x[0]) / END_FADE, 0, 1) * np.clip((x[-1] - x) / END_FADE, 0, 1)

    # 1. the soft curtain of light, brightest at the curve and fading downward
    #    (it carries on below the baseline, so nothing ends in a flat edge)
    rows = 160
    heights = np.linspace(-FADE, max_height, rows)
    glow = np.zeros((rows, len(x), 4))
    for i in range(len(x)):
        depth = kp[i] * HEIGHT - heights
        # taller peaks get a longer glow, so storms hang all the way down
        glow_length = kp[i] * HEIGHT + FADE
        alpha = np.clip(1 - depth / glow_length, 0, 1) ** 1.5
        alpha = alpha * (depth >= 0) * 0.55 * ends[i]
        glow[:, i, 0] = colours[i][0]
        glow[:, i, 1] = colours[i][1]
        glow[:, i, 2] = colours[i][2]
        glow[:, i, 3] = alpha
    ax.imshow(glow, extent=[x[0], x[-1], base - FADE, base + max_height],
              origin="lower", aspect="auto", interpolation="bilinear",
              zorder=3 * m + 1)

    # 2. the glowing edge: three passes, wide and faint to thin and bright
    points = np.array([x, top]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    for width, strength in [(7, 0.06), (3.5, 0.15), (1.2, 0.95)]:
        edge_colours = []
        for i in range(len(x) - 1):
            r, g, b = colours[i]
            edge_colours.append((r, g, b, strength * ends[i]))
        edge = LineCollection(segments, colors=edge_colours, linewidths=width,
                              capstyle="round", zorder=3 * m + 2)
        ax.add_collection(edge)

# just the light: no axes, no labels, no title
top_limit = max(kps_by_month[months[0]]) * HEIGHT + 0.4
ax.set_xlim(-1, 32)
ax.set_ylim(-(len(months) - 1) - FADE - 0.2, top_limit)

os.makedirs("out", exist_ok=True)
plt.savefig("out/aurora.png", dpi=150, facecolor=BACKGROUND)
print("Saved out/aurora.png")