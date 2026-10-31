#!/usr/bin/env python3
"""Erzeugt aus einem Foto ein ASCII-Porträt (ascii.txt) für die Profil-SVGs.

Nutzung (lokal, nicht in der GitHub Action):
    pip install pillow
    python tools/make_ascii.py portrait.jpg            # schreibt ascii.txt
    python tools/make_ascii.py portrait.jpg --cols 40 --rows 26 --gamma 1.1

Dunkle Bildbereiche werden zu dichten Zeichen (@, M, %), helle zu Leerraum.
Tipp: ein Foto mit ruhigem, hellem Hintergrund und gut ausgeleuchtetem Gesicht
liefert das schönste Ergebnis.
"""
import argparse
from PIL import Image, ImageOps, ImageFilter

# von hell (leer) nach dunkel (dicht)
RAMP = " .'`,^:;!|ijlrkmw%H#M@"

# Zeichenzelle im SVG: ca. 9.6 px breit, 20 px Zeilenhöhe
CELL_W, CELL_H = 9.6, 20.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--out", default="ascii.txt")
    ap.add_argument("--cols", type=int, default=38)
    ap.add_argument("--rows", type=int, default=26)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--invert", action="store_true", help="helle Bereiche dicht statt dunkle")
    a = ap.parse_args()

    img = Image.open(a.image).convert("L")
    # auf das Seitenverhältnis der Zeichenfläche zuschneiden (zentriert)
    target = (a.cols * CELL_W) / (a.rows * CELL_H)
    w, h = img.size
    if w / h > target:
        nw = int(h * target)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    img = img.filter(ImageFilter.SMOOTH)
    img = ImageOps.autocontrast(img, cutoff=1)
    img = img.resize((a.cols, a.rows), Image.LANCZOS)

    lines = []
    n = len(RAMP) - 1
    for y in range(a.rows):
        row = ""
        for x in range(a.cols):
            v = img.getpixel((x, y)) / 255.0
            v = v ** a.gamma
            d = v if a.invert else 1.0 - v
            row += RAMP[round(d * n)]
        lines.append(row.rstrip())
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{a.out}: {a.cols}x{a.rows}")


if __name__ == "__main__":
    main()
