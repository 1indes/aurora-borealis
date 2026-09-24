# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "scipy"]
# ///
import json
import os

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d, map_coordinates

BASE_RADIUS = 0.30   # where the bright edge of the ring sits (1 = edge of the picture)
DEPTH = 0.66         # how far the light can reach outward, at most
SPILL = 0.16         # how far the glow spills inward, past the bright edge
SOFTNESS = 1.3       # bigger = the light fades out faster as it rises
BLOOM = 5            # how far every ray spreads sideways (in pixel columns)
HALO = 40            # how far a storm's halo spreads sideways (in pixel columns)
HALO_GAIN = 1.6      # how strong the storm halos are
BRIGHTNESS = 1.25    # overall glow
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
    # Row 0 is the innermost part of the ring, the last row the outermost.
    rows = len(heights)
    columns = len(kp)
    alpha = np.zeros((rows, columns))
    colour = np.zeros((rows, columns, 3))
    outward = np.maximum(heights, 0)
    inward = np.minimum(heights, 0)
    for i in range(columns):
        # calm readings still fill over half the ring, storms fill all of it
        reach = DEPTH * (0.42 + 0.58 * (kp[i] / 9) ** 0.6)
        up = np.clip(1 - outward / reach, 0, 1)
        down = np.clip(1 + inward / SPILL, 0, 1)
        strength = (up * down) ** SOFTNESS
        if storm_only:
            # only the strong readings feed the halo
            strength = strength * np.clip((kp[i] - 3.5) / 3, 0, 1) * HALO_GAIN
        else:
            strength = strength * (0.6 + 0.4 * kp[i] / 9)
        alpha[:, i] = strength
        for c in range(3):
            colour[:, i, c] = colours[i][c]
    # spread the light sideways (colour is weighted by brightness)
    light = colour * alpha[:, :, None]
    alpha = gaussian_filter1d(alpha, spread, axis=1, mode="wrap")
    light = gaussian_filter1d(light, spread, axis=1, mode="wrap")
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

# heights run from inside the ring (negative) to its outer reach
heights = np.linspace(-SPILL, DEPTH, rows)

# two layers laid on top of each other: every ray, and the storm halos
light_a, alpha_a = make_light(kp, colours, heights, False, BLOOM)
light_b, alpha_b = make_light(kp, colours, heights, True, HALO)
light = light_a + light_b
alpha = alpha_a + alpha_b

# bend the flat picture (year along the width) into a ring (year around the circle)
size = 2000
pad = 60
rows_idx, cols_idx = np.mgrid[0:size, 0:size]
x = (cols_idx - size / 2) / (size / 2)
y = (size / 2 - rows_idx) / (size / 2)
radius = np.hypot(x, y)
angle = np.arctan2(x, y) % (2 * np.pi)          # 0 at the top, going clockwise

row_at = (radius - (BASE_RADIUS - SPILL)) / (DEPTH + SPILL) * (rows - 1)
col_at = angle / (2 * np.pi) * columns + pad


def bend(grid):
    # copy a few columns from each end so the year joins up around the circle
    wrapped = np.concatenate([grid[:, -pad:], grid, grid[:, :pad]], axis=1)
    return map_coordinates(wrapped, [row_at, col_at], order=1, cval=0.0)


ring_alpha = bend(alpha)
ring = np.zeros((size, size, 4))
for c in range(3):
    ring_light = bend(light[:, :, c])
    ring[:, :, c] = np.clip(ring_light / np.maximum(ring_alpha, 1e-6), 0, 1)
ring[:, :, 3] = np.clip(ring_alpha * BRIGHTNESS, 0, 1)

fig = plt.figure(figsize=(10, 10))
fig.patch.set_facecolor(BACKGROUND)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor(BACKGROUND)
ax.axis("off")
ax.imshow(ring)

os.makedirs("out", exist_ok=True)
plt.savefig("out/aurora.png", dpi=200, facecolor=BACKGROUND)
print("Saved out/aurora.png")