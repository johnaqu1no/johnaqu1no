#!/usr/bin/env python3
"""Render source-prepped.png as an animated ASCII SVG.

Each row is revealed by a horizontal wipe, staggered top to bottom.
Plays once and freezes.

Usage: python scripts/make_ascii_svg.py
Writes: ascii-art.svg
"""
import html

import numpy as np
from PIL import Image

from common import FONT, ROOT, config, write

CHAR_W = 7.2          # monospace advance at font-size 12
LINE_H = 12.5
ROW_STAGGER = 0.045   # seconds between row reveals
WIPE_DUR = 0.5


def main():
    cfg = config()
    a, t = cfg["ascii"], cfg["theme"]
    cols, ramp = a["cols"], a["ramp"]

    img = Image.open(ROOT / a["source"]).convert("L")
    # crop to the subject so it fills the frame instead of floating in white
    bbox = Image.eval(img, lambda v: 255 if v < 245 else 0).getbbox()
    if bbox:
        pad = round(max(img.size) * 0.03)
        img = img.crop((max(bbox[0] - pad, 0), max(bbox[1] - pad, 0),
                        min(bbox[2] + pad, img.width), min(bbox[3] + pad, img.height)))
    # character cells are ~2x taller than wide, so halve vertical sampling
    rows = int(img.height / img.width * cols * 0.5)
    px = np.array(img.resize((cols, rows), Image.LANCZOS))

    lines = []
    for r in range(rows):
        lines.append("".join(
            ramp[min(int((255 - v) / 256 * len(ramp)), len(ramp) - 1)] for v in px[r]
        ).rstrip())
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()

    W = round(cols * CHAR_W + 20)
    H = round(len(lines) * LINE_H + 24)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}" font-size="12">',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="8" fill="{t["bg"]}" stroke="{t["border"]}"/>',
    ]
    for i, text in enumerate(lines):
        if not text:
            continue
        y = 12 + (i + 1) * LINE_H - 3
        out.append(
            f'<clipPath id="c{i}"><rect x="0" y="{y - LINE_H:.1f}" width="0" height="{LINE_H + 2:.1f}">'
            f'<animate attributeName="width" from="0" to="{W}" begin="{i * ROW_STAGGER:.3f}s" '
            f'dur="{WIPE_DUR}s" fill="freeze"/></rect></clipPath>'
            f'<text x="10" y="{y:.1f}" xml:space="preserve" fill="{a["fg"]}" '
            f'clip-path="url(#c{i})">{html.escape(text)}</text>'
        )
    out.append("</svg>")
    write("ascii-art.svg", "\n".join(out))


if __name__ == "__main__":
    main()
