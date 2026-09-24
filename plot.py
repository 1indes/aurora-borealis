# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "scipy"]
# ///
import json
import os

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d

REACH = 1.2        # how far the light rises above a calm reading (in Kp units)
SOFTNESS = 1.4     # bigger = the light fades out faster as it rises
BLOOM = 5          # how far every ray spreads sideways (in pixel columns)
HALO = 40          # how far a storm's halo spreads sideways (in pixel columns)
HALO_GAIN = 1.8    # how strong the storm halos are
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


def smooth_year(kps, columns):
    # A smooth curve that passes through every real Kp value, sampled
    # at `columns` evenly spaced points along the year.
    curve = PchipInterpolator(np.arange(len(kps)), kps)
    fine_x = np.linspace(0, len(kps) - 1, columns)
    return np.clip(curve(fine_x), 0, 9)


def make_light(kp, colours, heights, storm_only, spread):
    # One layer of light: a grid with one column per point along the year.
    # Every column is brightest at the bottom and fades out towards its reach.
    rows = len(heights)
    columns = len(kp)
    alpha = np.zeros((rows, columns))
    colour = np.zeros((rows, columns, 3))
    for i in range(columns):
        reach = kp[i] + REACH
        strength = np.clip(1 - heights / reach, 0, 1) ** SOFTNESS
        if storm_only:
            # only the strong readings feed the halo
            strength = strength * np.clip((kp[i] - 3.5) / 3, 0, 1) * HALO_GAIN
        else:
            strength = strength * (0.55 + 0.45 * kp[i] / 9)
        alpha[:, i] = strength
        for c in range(3):
            colour[:, i, c] = colours[i][c]
    # spread the light sideways (colour is weighted by brightness)
    light = colour * alpha[:, :, None]
    alpha = gaussian_filter1d(alpha, spread, axis=1)
    light = gaussian_filter1d(light, spread, axis=1)
    return light, alpha


with open("data/kp-1year.json") as f:
    data = json.load(f)

kps = data["Kp"]

columns = 3600
rows = 500
kp = smooth_year(kps, columns)

colours = []
for value in kp:
    colours.append(kp_to_colour(value))

top = max(kps) + REACH                # the tallest the light ever gets
heights = np.linspace(0, top, rows)   # height of each pixel row, in Kp units

# two layers laid on top of each other: every ray, and the storm halos
light_a, alpha_a = make_light(kp, colours, heights, False, BLOOM)
light_b, alpha_b = make_light(kp, colours, heights, True, HALO)
light = light_a + light_b
alpha = np.clip(alpha_a + alpha_b, 0, 1)

picture = np.zeros((rows, columns, 4))
for c in range(3):
    picture[:, :, c] = np.clip(light[:, :, c] / np.maximum(alpha_a + alpha_b, 1e-6), 0, 1)
picture[:, :, 3] = alpha

fig = plt.figure(figsize=(16, 6))
fig.patch.set_facecolor(BACKGROUND)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor(BACKGROUND)
ax.axis("off")
ax.imshow(picture, extent=[0, columns, 0, top], origin="lower",
          aspect="auto", interpolation="bilinear")

os.makedirs("out", exist_ok=True)
plt.savefig("out/aurora.png", dpi=150, facecolor=BACKGROUND)
print("Saved out/aurora.png")