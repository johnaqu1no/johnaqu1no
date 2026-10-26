#!/usr/bin/env python3
"""Prep a photo for ASCII conversion: cut out the subject, boost local
contrast, and drop it on white so brightness maps cleanly onto the ramp.

Only needs running when the photo changes, so its heavy deps live in
requirements-photo.txt, not the daily workflow.

Usage: python scripts/prep_photo.py [source-photo.png]
Writes: source-prepped.png (grayscale)
"""
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

from common import ROOT


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else ROOT / "source-photo.png"
    img = Image.open(src).convert("RGBA")

    cut = remove(img, session=new_session("u2net"))
    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    arr = np.array(Image.alpha_composite(white, cut).convert("L"))

    arr = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(arr)
    # CLAHE greys the background a little, push it back to white
    arr[np.array(cut.split()[3]) < 120] = 255

    Image.fromarray(arr).save(ROOT / "source-prepped.png")
    print(f"wrote source-prepped.png ({arr.shape[1]}x{arr.shape[0]})")


if __name__ == "__main__":
    main()
