#!/usr/bin/env python3
"""
Create two reference background images inspired by:
  REF-1: Comic/illustration — sad office worker carrying box, robot in background
  REF-2: Cinematic split — human face top / AI robot face bottom, dramatic dark tone

Saves to youtube-improve/backgrounds/
Run from project root:
    python youtube-improve/backgrounds/create_reference_bgs.py
"""

import math
import random
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path("youtube-improve/backgrounds")
W, H = 1920, 1080


def _ft(bold, size):
    for name in (["arialbd.ttf","DejaVuSans-Bold.ttf"] if bold else ["arial.ttf","DejaVuSans.ttf"]):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def apply_bloom(img, radius=6):
    b   = img.filter(ImageFilter.GaussianBlur(radius))
    arr = np.clip(np.array(img).astype(np.float32) + np.array(b).astype(np.float32)*0.3, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


# ══════════════════════════════════════════════════════════════════════════════
# REF-1  Office Worker Being Replaced
# Warm desaturated office + dark robot silhouette + "AI" sign
# ══════════════════════════════════════════════════════════════════════════════

def draw_ref1():
    img = Image.new("RGB", (W, H), (28, 24, 20))
    d   = ImageDraw.Draw(img)

    # ── Office floor gradient ──
    arr = np.array(img).astype(np.float32)
    for y in range(H):
        v = int(22 + (y / H) * 18)
        arr[y, :] = [v, v - 2, v - 5]
    img = Image.fromarray(arr.astype(np.uint8))
    d   = ImageDraw.Draw(img)

    # ── Back wall (light warm grey) ──
    d.rectangle([0, 0, W, H * 3 // 5], fill=(58, 52, 46))

    # ── Window / light source top-right ──
    for r in range(240, 0, -8):
        alpha = int(18 * (1 - r / 240))
        d.ellipse([W - 380 - r, 40 - r, W - 380 + r, 40 + r],
                  fill=(200, 180, 120))

    # ── Floor line ──
    d.line([(0, H * 3 // 5), (W, H * 3 // 5)], fill=(40, 36, 30), width=4)

    # ── Desk (right bg) ──
    d.rectangle([W * 3 // 5, H // 2 + 40, W - 60, H // 2 + 100], fill=(70, 58, 44))
    d.rectangle([W * 3 // 5, H // 2 + 100, W * 3 // 5 + 30, H * 3 // 5], fill=(55, 44, 32))
    d.rectangle([W - 90, H // 2 + 100, W - 60, H * 3 // 5], fill=(55, 44, 32))

    # ── AI sign (top right of robot area) ──
    sign_x, sign_y = W * 3 // 5 + 20, 80
    d.rectangle([sign_x, sign_y, sign_x + 200, sign_y + 110],
                fill=(230, 225, 210), outline=(160, 155, 140), width=3)
    d.text((sign_x + 28, sign_y + 16), "AI", font=_ft(True, 72), fill=(30, 30, 30))

    # ── Robot silhouette (right side, standing tall) ──
    rx, ry = W * 3 // 5 + 260, H // 5
    rw, rh = 220, 520
    # Body
    d.rectangle([rx, ry + 160, rx + rw, ry + rh], fill=(110, 120, 130))
    # Head
    d.rectangle([rx + 30, ry + 60, rx + rw - 30, ry + 160], fill=(130, 140, 150))
    # Eyes
    d.ellipse([rx + 55, ry + 88, rx + 95, ry + 120], fill=(0, 200, 255))
    d.ellipse([rx + 115, ry + 88, rx + 155, ry + 120], fill=(0, 200, 255))
    # Neck
    d.rectangle([rx + 70, ry + 155, rx + rw - 70, ry + 175], fill=(100, 110, 118))
    # Arms
    d.rectangle([rx - 50, ry + 175, rx + 10, ry + 400], fill=(100, 110, 120))
    d.rectangle([rx + rw - 10, ry + 175, rx + rw + 50, ry + 400], fill=(100, 110, 120))
    # Legs
    d.rectangle([rx + 20, ry + rh, rx + 90, ry + rh + 160], fill=(90, 100, 108))
    d.rectangle([rx + 110, ry + rh, rx + rw - 20, ry + rh + 160], fill=(90, 100, 108))
    # Robot glow accent
    for glow_r in [180, 120, 70]:
        alpha = int(20 * (1 - glow_r / 180))
        glow_arr = np.array(img).astype(np.float32)
        cx, cy = rx + rw // 2, ry + 300
        ys, xs = np.ogrid[:H, :W]
        dist = np.sqrt((xs - cx)**2 + (ys - cy)**2).astype(np.float32)
        mask = np.clip(1.0 - dist / glow_r, 0, 1) * 0.18
        glow_arr[:, :, 2] = np.clip(glow_arr[:, :, 2] + mask * 255, 0, 255)
        glow_arr[:, :, 0] = np.clip(glow_arr[:, :, 0] + mask * 0, 0, 255)
        img = Image.fromarray(glow_arr.astype(np.uint8))
    d = ImageDraw.Draw(img)

    # ── Worker silhouette (left-centre, walking away with box) ──
    wx, wy = W // 5 + 60, H // 4
    # Body
    d.rectangle([wx + 20, wy + 120, wx + 120, wy + 320], fill=(55, 50, 45))
    # Head
    d.ellipse([wx + 30, wy + 40, wx + 110, wy + 130], fill=(180, 150, 120))
    # Hair
    d.ellipse([wx + 30, wy + 40, wx + 110, wy + 90], fill=(60, 45, 30))
    # Neck
    d.rectangle([wx + 55, wy + 120, wx + 85, wy + 140], fill=(170, 140, 110))
    # Tie
    d.polygon([(wx + 65, wy + 140), (wx + 75, wy + 200), (wx + 78, wy + 260),
               (wx + 70, wy + 270), (wx + 62, wy + 260), (wx + 65, wy + 200)],
              fill=(80, 30, 30))
    # Shirt collar (white)
    d.polygon([(wx + 45, wy + 130), (wx + 65, wy + 165), (wx + 75, wy + 130)], fill=(220, 215, 210))
    d.polygon([(wx + 75, wy + 130), (wx + 75, wy + 165), (wx + 95, wy + 130)], fill=(215, 210, 205))
    # Arms (slightly forward holding box)
    d.rectangle([wx - 10, wy + 130, wx + 24, wy + 310], fill=(50, 45, 40))   # left arm
    d.rectangle([wx + 116, wy + 130, wx + 150, wy + 310], fill=(50, 45, 40)) # right arm
    # Legs
    d.rectangle([wx + 22, wy + 318, wx + 68, wy + 500], fill=(40, 40, 50))
    d.rectangle([wx + 72, wy + 318, wx + 118, wy + 500], fill=(38, 38, 48))
    # Shoes
    d.rectangle([wx + 14, wy + 495, wx + 72, wy + 520], fill=(25, 22, 20))
    d.rectangle([wx + 70, wy + 495, wx + 128, wy + 520], fill=(25, 22, 20))
    # Cardboard box (held in front)
    bx, by = wx - 30, wy + 260
    d.rectangle([bx, by, bx + 175, by + 155], fill=(185, 150, 95),
                outline=(140, 110, 65), width=3)
    d.line([(bx, by + 60), (bx + 175, by + 60)], fill=(140, 110, 65), width=2)
    d.line([(bx + 87, by), (bx + 87, by + 60)], fill=(140, 110, 65), width=2)
    # Items sticking out of box
    d.rectangle([bx + 20, by - 40, bx + 55, by + 5], fill=(60, 100, 140))   # folder
    d.rectangle([bx + 65, by - 55, bx + 85, by + 5], fill=(80, 140, 80))    # plant stem
    d.ellipse([bx + 55, by - 80, bx + 100, by - 30], fill=(60, 130, 70))   # plant
    d.ellipse([bx + 78, by - 95, bx + 115, by - 50], fill=(50, 120, 60))

    # ── Sad expression detail on face ──
    # Eyebrows (angled down = sad)
    d.line([(wx + 38, wy + 72), (wx + 60, wy + 82)], fill=(50, 35, 25), width=4)
    d.line([(wx + 80, wy + 82), (wx + 102, wy + 72)], fill=(50, 35, 25), width=4)
    # Eyes
    d.ellipse([wx + 44, wy + 82, wx + 62, wy + 98], fill=(55, 40, 30))
    d.ellipse([wx + 78, wy + 82, wx + 96, wy + 98], fill=(55, 40, 30))
    # Mouth (frown)
    d.arc([wx + 50, wy + 100, wx + 90, wy + 122], start=200, end=340,
          fill=(100, 60, 50), width=3)

    # ── Subtle vignette ──
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for r in range(min(W, H) // 2, 0, -20):
        a = int(80 * (1 - r / (min(W, H) // 2)))
        ImageDraw.Draw(vignette).ellipse(
            [W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r],
            fill=(0, 0, 0, a))
    img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")

    img = apply_bloom(img, radius=3)
    path = OUT / "ref_worker_robot.png"
    img.save(str(path))
    print(f"  Saved: {path.name}  ({path.stat().st_size//1024} KB)")


# ══════════════════════════════════════════════════════════════════════════════
# REF-2  Cinematic Split — Human Face / AI Face + "Will AI Replace Human Jobs?"
# ══════════════════════════════════════════════════════════════════════════════

def draw_ref2():
    img = Image.new("RGB", (W, H), (8, 8, 12))
    d   = ImageDraw.Draw(img)

    # ── Top half — warm office meeting (blurred human scene) ──
    arr = np.array(img).astype(np.float32)
    # Warm amber gradient top half
    for y in range(H // 2):
        t  = y / (H // 2)
        arr[y, :] = [int(55 + t * 30), int(40 + t * 20), int(20 + t * 10)]
    # Cool blue gradient bottom half
    for y in range(H // 2, H):
        t  = (y - H // 2) / (H // 2)
        arr[y, :] = [int(8 + t * 5), int(12 + t * 8), int(30 + t * 25)]
    img = Image.fromarray(arr.astype(np.uint8))

    # Blur the halves for cinematic feel
    top_half  = img.crop([0, 0, W, H // 2]).filter(ImageFilter.GaussianBlur(18))
    bot_half  = img.crop([0, H // 2, W, H]).filter(ImageFilter.GaussianBlur(8))
    img.paste(top_half, (0, 0))
    img.paste(bot_half, (0, H // 2))
    d = ImageDraw.Draw(img)

    # ── Top half: silhouetted people in meeting ──
    for i, (px, ph, pw) in enumerate([
        (W//6,      180, 80),
        (W//6+160,  210, 90),
        (W//6+330,  160, 70),
        (W*2//3,    190, 85),
        (W*2//3+170,165, 75),
    ]):
        py = H // 2 - ph
        # Body
        d.rectangle([px, py, px + pw, H // 2 + 10], fill=(30, 22, 14))
        # Head
        d.ellipse([px + pw//4, py - 65, px + 3*pw//4, py + 5], fill=(28, 20, 12))

    # Table
    d.rectangle([W//8, H//2 - 30, W*7//8, H//2 + 20], fill=(42, 32, 20))

    # ── Dividing neon line ──
    for thickness, alpha_mult in [(6, 1.0), (14, 0.5), (28, 0.2)]:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        a = int(255 * alpha_mult)
        od.line([(0, H // 2), (W, H // 2)], fill=(0, 180, 255, a), width=thickness)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    # ── Bottom half: robot/AI face (circuit pattern) ──
    cx, cy = W // 2, H * 3 // 4
    # Skull outline
    d.ellipse([cx - 200, cy - 260, cx + 200, cy + 100],
              outline=(0, 180, 255), width=3, fill=(12, 16, 28))
    # Jaw
    d.rectangle([cx - 130, cy - 30, cx + 130, cy + 100],
                fill=(12, 16, 28), outline=(0, 180, 255), width=2)
    # Eyes — glowing visor
    d.rectangle([cx - 160, cy - 140, cx + 160, cy - 70],
                fill=(0, 5, 20), outline=(0, 180, 255), width=2)
    # Visor glow
    glow = np.array(img).astype(np.float32)
    ys, xs = np.ogrid[:H, :W]
    visor_cx, visor_cy = cx, cy - 105
    dist = np.sqrt((xs - visor_cx)**2 + (ys - visor_cy)**2).astype(np.float32)
    mask = np.clip(1.0 - dist / 180, 0, 1) * 0.6
    glow[:, :, 2] = np.clip(glow[:, :, 2] + mask * 255, 0, 255)
    glow[:, :, 1] = np.clip(glow[:, :, 1] + mask * 160, 0, 255)
    glow[:, :, 0] = np.clip(glow[:, :, 0] + mask * 0, 0, 255)
    img = Image.fromarray(glow.astype(np.uint8))
    d   = ImageDraw.Draw(img)
    # Scan lines across visor
    for sy in range(cy - 138, cy - 72, 8):
        d.line([(cx - 155, sy), (cx + 155, sy)], fill=(0, 100, 200, 80), width=1)
    # Circuit lines on face
    rng = random.Random(42)
    for _ in range(24):
        x1 = rng.randint(cx - 190, cx + 190)
        y1 = rng.randint(cy - 250, cy + 90)
        ln = rng.randint(20, 70)
        horiz = rng.choice([True, False])
        col = (0, rng.randint(100, 200), rng.randint(180, 255))
        if horiz:
            d.line([(x1, y1), (x1 + ln, y1)], fill=col, width=1)
            d.ellipse([x1 + ln - 3, y1 - 3, x1 + ln + 3, y1 + 3], fill=col)
        else:
            d.line([(x1, y1), (x1, y1 + ln)], fill=col, width=1)
            d.ellipse([x1 - 3, y1 + ln - 3, x1 + 3, y1 + ln + 3], fill=col)
    # Nose bridge (thin line)
    d.line([(cx - 8, cy - 70), (cx - 8, cy - 20)], fill=(0, 120, 200), width=2)
    d.line([(cx + 8, cy - 70), (cx + 8, cy - 20)], fill=(0, 120, 200), width=2)
    # Mouth grille
    for gx in range(cx - 80, cx + 82, 22):
        d.rectangle([gx, cy + 20, gx + 14, cy + 55],
                    fill=(0, 50, 100), outline=(0, 140, 220), width=1)

    # ── Text overlay ──
    # Dark background band for text (left side)
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd   = ImageDraw.Draw(band)
    bd.rectangle([0, H * 3 // 5 - 20, W * 5 // 8, H * 3 // 5 + 220],
                 fill=(0, 0, 0, 170))
    img = Image.alpha_composite(img.convert("RGBA"), band).convert("RGB")
    d   = ImageDraw.Draw(img)

    tx, ty = 80, H * 3 // 5
    d.text((tx, ty), "Will ", font=_ft(False, 88), fill=(255, 255, 255))
    w1 = int(d.textlength("Will ", font=_ft(False, 88)))
    d.text((tx + w1, ty), "AI", font=_ft(True, 88), fill=(0, 200, 255))
    w2 = int(d.textlength("AI", font=_ft(True, 88)))
    d.text((tx + w1 + w2, ty), " Replace", font=_ft(False, 88), fill=(255, 255, 255))
    d.text((tx, ty + 100), "Human ", font=_ft(False, 88), fill=(0, 200, 255))
    w3 = int(d.textlength("Human ", font=_ft(False, 88)))
    d.text((tx + w3, ty + 100), "Jobs?", font=_ft(True, 88), fill=(255, 255, 255))

    img = apply_bloom(img, radius=5)
    path = OUT / "ref_ai_replace_jobs.png"
    img.save(str(path))
    print(f"  Saved: {path.name}  ({path.stat().st_size//1024} KB)")


if __name__ == "__main__":
    print(f"\nCreating reference backgrounds -> {OUT}\n")
    print("[1/2] REF-1: Office worker + robot ...")
    draw_ref1()
    print("[2/2] REF-2: Cinematic human/AI split ...")
    draw_ref2()
    print("\nDone.\n")
