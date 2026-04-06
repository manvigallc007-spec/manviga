#!/usr/bin/env python3
"""
Create brand assets for "Will AI Take My Job?" slides:
  - logo.png       : The AI Chronicle infinity-symbol logo (400x400)
  - avatar.png     : Illustrated avatar portrait (400x540)

Run from project root:
    python AI-Mixed-content/video-pipeline/will-ai-take-my-job/create_assets.py
"""

import math
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path("AI-Mixed-content/video-pipeline/will-ai-take-my-job/output/assets")
OUT.mkdir(parents=True, exist_ok=True)


def _ft(bold, size):
    for n in (["arialbd.ttf","DejaVuSans-Bold.ttf"] if bold
              else ["arial.ttf","DejaVuSans.ttf"]):
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            pass
    return ImageFont.load_default()


# ══════════════════════════════════════════════════════════════════════════════
# LOGO — Infinity symbol in dark navy circle
# ══════════════════════════════════════════════════════════════════════════════

def make_logo(size=400):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx, cy, r = size//2, size//2, size//2 - 4

    # Outer circle (dark navy fill)
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(13, 20, 40, 255))

    # Inner ring
    d.ellipse([cx-r+6, cy-r+6, cx+r-6, cy+r-6],
              outline=(30, 45, 70, 200), width=2)

    # ── Infinity / figure-8 path ───────────────────────────────────────────────
    # Draw using two overlapping circles (Bernoulli lemniscate approximation)
    GREEN  = (0, 200, 130)
    stroke = 7
    lw = int(size * 0.18)   # lobe width
    lh = int(size * 0.12)   # lobe height
    lx = int(size * 0.23)   # horizontal centre offset for each lobe

    # Left lobe
    d.ellipse([cx - lx - lw, cy - lh, cx - lx + lw, cy + lh],
              outline=GREEN, width=stroke)
    # Right lobe
    d.ellipse([cx + lx - lw, cy - lh, cx + lx + lw, cy + lh],
              outline=GREEN, width=stroke)

    # Centre dot
    dot_r = stroke + 2
    d.ellipse([cx-dot_r, cy-dot_r, cx+dot_r, cy+dot_r], fill=GREEN)

    # ── Brand text ────────────────────────────────────────────────────────────
    f = _ft(False, int(size * 0.085))
    txt = "THE AI CHRONICLE"
    bb  = d.textbbox((0, 0), txt, font=f)
    tw  = bb[2] - bb[0]
    d.text((cx - tw//2, cy + r - int(size*0.20)), txt,
           font=f, fill=(0, 200, 130, 220))

    # Soft glow on infinity
    blurred = img.filter(ImageFilter.GaussianBlur(8))
    arr_o = np.array(img).astype(np.float32)
    arr_b = np.array(blurred).astype(np.float32)
    arr_o = np.clip(arr_o + arr_b * 0.4, 0, 255).astype(np.uint8)
    img   = Image.fromarray(arr_o)

    path = OUT / "logo.png"
    img.save(str(path))
    print(f"  Saved: {path.name}  ({size}x{size})")
    return img


# ══════════════════════════════════════════════════════════════════════════════
# AVATAR — Illustrated South Asian male portrait
# ══════════════════════════════════════════════════════════════════════════════

def make_avatar(w=380, h=520):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx  = w // 2

    # ── Background (light cream) ───────────────────────────────────────────────
    d.rectangle([0, 0, w, h], fill=(240, 232, 218, 255))

    # ── Jacket / body ─────────────────────────────────────────────────────────
    jy = int(h * 0.58)
    # Main jacket (brown/dark)
    d.polygon([
        (0, h), (0, jy+30), (cx-70, jy), (cx, jy+20),
        (cx+70, jy), (w, jy+30), (w, h)
    ], fill=(85, 55, 30))
    # Inner shirt (navy blue)
    d.polygon([
        (cx-40, jy+10), (cx+40, jy+10),
        (cx+50, h), (cx-50, h)
    ], fill=(40, 60, 100))
    # Jacket lapels
    d.polygon([(cx-70, jy), (cx-15, jy+60), (cx, jy+20)], fill=(70, 45, 22))
    d.polygon([(cx+70, jy), (cx+15, jy+60), (cx, jy+20)], fill=(70, 45, 22))
    # Sherpa collar
    d.polygon([
        (cx-70, jy), (cx-80, jy-12), (cx, jy+8), (cx+80, jy-12), (cx+70, jy)
    ], fill=(200, 195, 185))

    # ── Neck ──────────────────────────────────────────────────────────────────
    neck_y = int(h * 0.52)
    d.rectangle([cx-22, neck_y, cx+22, jy+15], fill=(185, 140, 100))

    # ── Face ──────────────────────────────────────────────────────────────────
    face_cx, face_cy = cx, int(h * 0.35)
    face_rx, face_ry = 85, 100
    # Face shape (slightly wide oval)
    d.ellipse([face_cx-face_rx, face_cy-face_ry,
               face_cx+face_rx, face_cy+face_ry], fill=(200, 155, 105))

    # Jaw / lower face (slightly wider)
    d.ellipse([face_cx-78, face_cy+10,
               face_cx+78, face_cy+face_ry+30], fill=(195, 150, 100))

    # ── Hair ──────────────────────────────────────────────────────────────────
    # Main hair mass
    d.ellipse([face_cx-88, face_cy-face_ry-10,
               face_cx+88, face_cy+10], fill=(30, 25, 22))
    # Hair detail streaks
    for i in range(-70, 75, 12):
        d.line([(face_cx+i, face_cy-face_ry-8),
                (face_cx+i+6, face_cy-face_ry+30)],
               fill=(50, 42, 38), width=2)
    # Side hair
    d.ellipse([face_cx-90, face_cy-60, face_cx-65, face_cy+30],
              fill=(30, 25, 22))
    d.ellipse([face_cx+65, face_cy-60, face_cx+90, face_cy+30],
              fill=(30, 25, 22))

    # ── Eyebrows ──────────────────────────────────────────────────────────────
    ey = face_cy - 28
    # Left brow (thick, slightly angled)
    for i in range(4):
        d.line([(face_cx-65, ey+i), (face_cx-20, ey-4+i)],
               fill=(30, 22, 16), width=3)
    # Right brow
    for i in range(4):
        d.line([(face_cx+20, ey-4+i), (face_cx+65, ey+i)],
               fill=(30, 22, 16), width=3)

    # ── Eyes ──────────────────────────────────────────────────────────────────
    for ex_off in [-38, 38]:
        ex = face_cx + ex_off
        ey2 = face_cy - 12
        # Eye white
        d.ellipse([ex-18, ey2-11, ex+18, ey2+11], fill=(235, 228, 218))
        # Iris (dark brown)
        d.ellipse([ex-10, ey2-9, ex+10, ey2+9], fill=(60, 38, 22))
        # Pupil
        d.ellipse([ex-5, ey2-5, ex+5, ey2+5], fill=(18, 12, 8))
        # Highlight
        d.ellipse([ex+3, ey2-6, ex+7, ey2-2], fill=(255, 255, 255, 180))
        # Upper eyelid line
        d.arc([ex-18, ey2-11, ex+18, ey2+11], start=200, end=340,
              fill=(30, 20, 12), width=2)

    # ── Nose ──────────────────────────────────────────────────────────────────
    ny = face_cy + 15
    d.line([(face_cx, face_cy), (face_cx-6, ny+18)], fill=(165, 120, 80), width=2)
    d.arc([face_cx-18, ny+8, face_cx+18, ny+28],
          start=180, end=360, fill=(165, 120, 80), width=2)
    d.ellipse([face_cx-14, ny+14, face_cx-2, ny+26], fill=(175, 130, 88))
    d.ellipse([face_cx+2,  ny+14, face_cx+14, ny+26], fill=(175, 130, 88))

    # ── Moustache ─────────────────────────────────────────────────────────────
    my = face_cy + 40
    d.ellipse([face_cx-32, my-6, face_cx+2, my+16], fill=(80, 72, 68))
    d.ellipse([face_cx-2,  my-6, face_cx+32, my+16], fill=(80, 72, 68))
    # Salt-and-pepper dots
    for px, py_ in [(face_cx-22, my+2), (face_cx+15, my+4),
                    (face_cx-8, my+8), (face_cx+22, my+2)]:
        d.ellipse([px-2, py_-2, px+2, py_+2], fill=(200, 195, 190))

    # ── Stubble beard (lower face) ────────────────────────────────────────────
    for i in range(60):
        import random
        rng = random.Random(i)
        bx = rng.randint(face_cx-55, face_cx+55)
        by_ = rng.randint(my+14, face_cy+face_ry+18)
        d.ellipse([bx-1, by_-1, bx+1, by_+1],
                  fill=(100, 88, 82, 160))

    # ── Mouth ─────────────────────────────────────────────────────────────────
    mouth_y = face_cy + 58
    d.line([(face_cx-22, mouth_y), (face_cx+22, mouth_y)],
           fill=(145, 95, 65), width=3)

    # ── Ears ──────────────────────────────────────────────────────────────────
    for ex2, ear_x0, ear_x1 in [
        (face_cx - face_rx + 2, face_cx - face_rx - 8, face_cx - face_rx + 14),
        (face_cx + face_rx - 2, face_cx + face_rx - 14, face_cx + face_rx + 8),
    ]:
        d.ellipse([ear_x0, face_cy-20, ear_x1, face_cy+22], fill=(190, 145, 98))

    # ── Subtle vignette ───────────────────────────────────────────────────────
    vig = Image.new("RGBA", (w, h), (0,0,0,0))
    dv  = ImageDraw.Draw(vig)
    for r2 in range(min(w,h)//2, 0, -15):
        a = int(40 * (1 - r2/(min(w,h)//2)))
        dv.ellipse([cx-r2, h//2-r2, cx+r2, h//2+r2], fill=(0,0,0,a))
    img = Image.alpha_composite(img, vig)

    path = OUT / "avatar.png"
    img.save(str(path))
    print(f"  Saved: {path.name}  ({w}x{h})")
    return img


if __name__ == "__main__":
    print(f"\nCreating brand assets -> {OUT}\n")
    print("[1/2] Logo ...")
    make_logo(400)
    print("[2/2] Avatar ...")
    make_avatar(380, 520)
    print("\nDone.\n")
