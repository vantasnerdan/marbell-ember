#!/usr/bin/env python3
"""Ember glass plate: the blurred "shot behind the console", baked once.
Usage: make_plate.py [out.png] [seed]   (re-run with another seed for a new plate)"""
import sys
import numpy as np
from PIL import Image, ImageFilter

out = sys.argv[1] if len(sys.argv) > 1 else "plate.png"
rng = np.random.default_rng(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
W, H = 2560, 1440
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def blob(cx, cy, rx, ry, rgb, a):
    d = ((xx - cx * W) / (rx * W)) ** 2 + ((yy - cy * H) / (ry * H)) ** 2
    return np.exp(-d)[..., None] * (np.array(rgb, np.float32) / 255.0) * a

img = np.zeros((H, W, 3), np.float32) + np.array([7, 11, 22], np.float32) / 255.0
# out-of-focus practicals: one warm source low-left, cool spill top-right, deep blue mid
img += blob(0.10, 0.92, 0.34, 0.42, (244, 120, 83), 0.150)
img += blob(0.93, 0.06, 0.40, 0.46, (79, 209, 197), 0.075)
img += blob(0.55, 0.45, 0.55, 0.60, (40, 62, 120), 0.110)
img += blob(0.80, 0.98, 0.22, 0.20, (242, 184, 102), 0.045)
for _ in range(9):  # bokeh
    img += blob(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(.03, .08), rng.uniform(.05, .12),
                [(244, 120, 83), (79, 209, 197), (60, 90, 170)][rng.integers(0, 3)], rng.uniform(.012, .035))
im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(40))
img = np.asarray(im).astype(np.float32) / 255.0
# vignette + fine silver grain (dithers the gradients so they survive video compression)
v = 1.0 - 0.38 * (((xx / W - .5) * 1.25) ** 2 + ((yy / H - .5) * 1.5) ** 2)
img *= np.clip(v, 0, 1)[..., None]
img += rng.normal(0, 0.006, (H, W, 1)).astype(np.float32)
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out, optimize=True)
print(out)
