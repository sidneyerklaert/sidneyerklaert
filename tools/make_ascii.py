#!/usr/bin/env python3
"""Erzeugt aus einem Foto ein ASCII-Porträt (ascii.txt) für die Profil-SVGs.

Nutzung (lokal, nicht in der GitHub Action):
    pip install pillow            # optional zusätzlich: pip install "rembg[cpu]"
    python tools/make_ascii.py foto.png --rembg --crop 70,10,506,576

--rembg    entfernt den Hintergrund (Person wird freigestellt, Hintergrund = leer)
--crop     Ausschnitt x0,y0,x1,y1 in Pixeln (Kopf + Schultern)
Schreibt ascii.txt (für light_mode) und ascii_dark.txt (für dark_mode, invertiert).
"""
import argparse
from PIL import Image, ImageOps, ImageFilter

# von hell (dünn) nach dunkel (dicht)
RAMP = " .'`,:;!|ijlrkmw%H#M@"

# Zeichenzelle im SVG: ca. 9.6 px breit, 20 px Zeilenhöhe
CELL_W, CELL_H = 9.6, 20.0


def fit(img, target):
    """Auf Seitenverhältnis `target` (b/h) zuschneiden bzw. auffüllen, zentriert."""
    w, h = img.size
    if w / h > target:
        nw = int(h * target)
        return img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    nh = int(w / target)
    if nh <= h:
        return img.crop((0, 0, w, nh))  # oben ausrichten (Kopf behalten)
    canvas = Image.new(img.mode, (w, nh), 0)
    canvas.paste(img, (0, nh - h))  # unten ausrichten, oben auffüllen
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--out", default="ascii.txt")
    ap.add_argument("--cols", type=int, default=38)
    ap.add_argument("--rows", type=int, default=30)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--crop", help="x0,y0,x1,y1")
    ap.add_argument("--rembg", action="store_true", help="Hintergrund entfernen (braucht rembg)")
    ap.add_argument("--min-density", type=float, default=0.08,
                    help="Mindestdichte für Personen-Pixel, damit helle Haut nicht verschwindet")
    ap.add_argument("--flatten", type=float, default=0.6, help="Lichtausgleich 0..1")
    ap.add_argument("--blur", type=float, default=10, help="Bildgröße / Radius für Lichtausgleich")
    a = ap.parse_args()

    img = Image.open(a.image).convert("RGB")
    if a.crop:
        img = img.crop(tuple(int(v) for v in a.crop.split(",")))
    if a.rembg:
        from rembg import remove, new_session
        mask = remove(img, session=new_session("u2net_human_seg"), only_mask=True).convert("L")
    else:
        mask = Image.new("L", img.size, 255)

    gray = img.convert("L")
    if a.flatten > 0:
        # ungleichmäßiges Licht ausgleichen: Hochpass (Bild minus starke Unschärfe)
        from PIL import ImageChops
        blur = gray.filter(ImageFilter.GaussianBlur(radius=max(img.size) / a.blur))
        hp = ImageChops.add(ImageChops.subtract(gray, blur, offset=128), Image.new("L", gray.size, 0))
        gray = Image.blend(gray, hp, a.flatten)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=150, threshold=2))
    # Kontrast nur über die Person strecken
    fg = Image.composite(gray, Image.new("L", gray.size, 128), mask)
    fg = ImageOps.autocontrast(fg, cutoff=2)

    target = (a.cols * CELL_W) / (a.rows * CELL_H)
    fg, mask = fit(fg, target), fit(mask, target)
    fg = fg.resize((a.cols, a.rows), Image.LANCZOS)
    mask = mask.resize((a.cols, a.rows), Image.LANCZOS)

    n = len(RAMP) - 1

    def render(invert):
        lines = []
        for y in range(a.rows):
            row = ""
            for x in range(a.cols):
                if mask.getpixel((x, y)) / 255.0 < 0.35:
                    row += " "
                    continue
                v = fg.getpixel((x, y)) / 255.0
                d = (v if invert else 1.0 - v) ** a.gamma
                d = a.min_density + (1 - a.min_density) * d
                row += RAMP[max(1, round(d * n))]
            lines.append(row.rstrip())
        return "\n".join(lines) + "\n"

    # hell: dunkle Bildbereiche = dichte Zeichen (dunkle Schrift auf hellem Grund)
    # dunkel: helle Bildbereiche = dichte Zeichen (helle Schrift auf dunklem Grund)
    base = a.out[:-4] if a.out.endswith(".txt") else a.out
    for path, inv in ((f"{base}.txt", False), (f"{base}_dark.txt", True)):
        with open(path, "w", encoding="utf-8") as f:
            f.write(render(inv))
        print(f"{path}: {a.cols}x{a.rows}")


if __name__ == "__main__":
    main()
