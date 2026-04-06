#!/usr/bin/env python3
"""
Generate B-roll graphics + thumbnails for:
  "Will AI Take My Job?" — The AI Chronicle

Uses real reference images from backgrounds/ directory, cropped and
composited with brand overlays (scrim, glow, grid, particles).

Output: ../output/graphics/  (BG-01 through BG-07, THUMB-A, THUMB-B)

Run from project root:
    python AI-Mixed-content/video-pipeline/will-ai-take-my-job/graphics/generate_graphics.py
"""

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE    = Path(__file__).parent
OUTPUT  = HERE.parent / "output" / "graphics"
OUTPUT.mkdir(parents=True, exist_ok=True)

BG_DIR  = Path("youtube-improve/backgrounds")   # relative to project root

# ── Scene -> source image mapping ─────────────────────────────────────────────
SCENE_IMAGES = {
    "BG-01-title.png":   "BG1.png",                        # robots in office — clear, on-topic
    "BG-02-search.png":  "Copilot_20260331_223102.png",    # human + robot hand reaching AI — concern
    "BG-03-tasks.png":   "Copilot_20260331_223110.png",    # robot with tablet — tasks/pro context
    "BG-04-roles.png":   "Copilot_20260331_223104.png",    # human + holographic AI — role exposure
    "BG-05-steps.png":   "Copilot_20260331_214806.png",    # AI network icons — practical steps
    "BG-06-risks.png":   "Copilot_20260331_214804.png",    # lock / security — guardrails
    "BG-07-outro.png":   "BG2.png",                        # robots in command — strong outro close
}

# ── Brand palette ──────────────────────────────────────────────────────────────
BLUE    = (0, 210, 255)
PURPLE  = (210, 100, 255)
WHITE   = (255, 255, 255)
W, H    = 1920, 1080
TW, TH  = 1280, 720


# ══════════════════════════════════════════════════════════════════════════════
# IMAGE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def load_and_crop(src: Path, out_w: int, out_h: int) -> Image.Image:
    """Load image, crop-fill to out_w x out_h, return RGB."""
    img   = Image.open(src).convert("RGB")
    ratio = img.width / img.height
    if ratio > out_w / out_h:
        new_h = out_h
        new_w = int(ratio * out_h)
    else:
        new_w = out_w
        new_h = int(out_w / ratio)
    img  = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - out_w) // 2
    top  = (new_h - out_h) // 2
    return img.crop((left, top, left + out_w, top + out_h))


def apply_dark_overlay(img: Image.Image, opacity: float = 0.55) -> Image.Image:
    """Uniform dark tint over whole image to push back background."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, int(255 * opacity)))
    base    = img.convert("RGBA")
    return Image.alpha_composite(base, overlay).convert("RGB")


def apply_left_scrim(img: Image.Image, left_alpha: int = 242,
                     right_alpha: int = 90, scrim_pct: float = 0.62) -> Image.Image:
    """Left-heavy gradient scrim — 95% opacity on text column, lighter on right."""
    arr    = np.array(img.convert("RGBA")).astype(np.float32)
    w      = img.width
    scrim_w = int(w * scrim_pct)
    for x in range(w):
        if x < scrim_w:
            a = left_alpha + (right_alpha - left_alpha) * (x / scrim_w) ** 0.65
        else:
            a = right_alpha
        arr[:, x, :3] = arr[:, x, :3] * (1 - a / 255)
    return Image.fromarray(arr.astype(np.uint8)).convert("RGB")


def add_accent_tint(img: Image.Image, accent, strength: float = 0.12) -> Image.Image:
    """Subtle brand colour tint over the image."""
    tint = Image.new("RGB", img.size, accent)
    return Image.blend(img.convert("RGB"), tint, strength)


def draw_glow_circle(img: Image.Image, cx: int, cy: int,
                     radius: int, accent, intensity: float = 0.45) -> Image.Image:
    arr  = np.array(img).astype(np.float32)
    h, w = arr.shape[:2]
    ys, xs = np.ogrid[:h, :w]
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2).astype(np.float32)
    mask = np.clip(1.0 - dist / radius, 0, 1) * intensity
    for c, val in enumerate(accent):
        arr[:, :, c] = np.clip(arr[:, :, c] + mask * val, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def draw_particles(draw: ImageDraw.Draw, w: int, h: int,
                   accent, n: int = 80, seed: int = 1):
    rng = random.Random(seed)
    for _ in range(n):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        r = rng.randint(1, 3)
        bright = rng.randint(140, 255)
        col = tuple(int(c * bright / 255) for c in accent)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=col)


def draw_grid(draw: ImageDraw.Draw, w: int, h: int, accent, spacing=100, alpha=18):
    col = (*accent, alpha)
    for x in range(0, w, spacing):
        draw.line([(x, 0), (x, h)], fill=col, width=1)
    for y in range(0, h, spacing):
        draw.line([(0, y), (w, y)], fill=col, width=1)


def apply_bloom(img: Image.Image, radius: int = 5) -> Image.Image:
    blurred = img.filter(ImageFilter.GaussianBlur(radius))
    arr_o   = np.array(img).astype(np.float32)
    arr_b   = np.array(blurred).astype(np.float32)
    result  = np.clip(arr_o + arr_b * 0.28, 0, 255).astype(np.uint8)
    return Image.fromarray(result)


def brand_composite(base: Image.Image, accent=BLUE,
                    glow_cx: int = None, glow_cy: int = None,
                    glow_r: int = 400, glow_strength: float = 0.30,
                    particles: int = 70, grid: bool = True,
                    seed: int = 1) -> Image.Image:
    """Full brand treatment: scrim + tint + glow + grid + particles + bloom."""
    img = apply_left_scrim(base, left_alpha=242, right_alpha=90)
    img = add_accent_tint(img, accent, strength=0.10)
    if glow_cx is None:
        glow_cx = img.width // 5
    if glow_cy is None:
        glow_cy = img.height // 2
    img = draw_glow_circle(img, glow_cx, glow_cy, glow_r, accent, glow_strength)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d       = ImageDraw.Draw(overlay)
    if grid:
        draw_grid(d, img.width, img.height, accent, spacing=110, alpha=16)
    draw_particles(d, img.width, img.height, accent, n=particles, seed=seed)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return apply_bloom(img, radius=4)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE GENERATORS  (each picks its source, composites, saves)
# ══════════════════════════════════════════════════════════════════════════════

def make_scene(out_name: str, accent=BLUE, glow_cx=None, glow_cy=None,
               glow_r=420, glow_strength=0.30, particles=70, seed=1):
    src_name = SCENE_IMAGES[out_name]
    src_path = BG_DIR / src_name
    print(f"  {out_name:<22} <- {src_name}")
    base = load_and_crop(src_path, W, H)
    img  = brand_composite(base, accent,
                           glow_cx=glow_cx, glow_cy=glow_cy,
                           glow_r=glow_r, glow_strength=glow_strength,
                           particles=particles, seed=seed)
    img.save(str(OUTPUT / out_name))


def _ft(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    candidates = (
        ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]
        if bold else
        ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def gen_thumbnail(accent, variant_label: str, bg_src_name: str):
    src_path = BG_DIR / bg_src_name
    base = load_and_crop(src_path, TW, TH)

    # Dark overlay + left scrim
    base = apply_dark_overlay(base, opacity=0.40)
    base = apply_left_scrim(base, left_alpha=242, right_alpha=80, scrim_pct=0.68)
    base = add_accent_tint(base, accent, strength=0.12)

    # Accent glow bottom-left
    base = draw_glow_circle(base, TW // 5, TH * 2 // 3, 340, accent, 0.50)
    base = apply_bloom(base, radius=5)

    img = base.convert("RGBA")
    d   = ImageDraw.Draw(img)
    PAD = 48

    # Top bar
    d.rectangle([0, 0, TW, 60], fill=(0, 0, 0, 170))
    d.text((PAD, 12), "THE AI CHRONICLE", font=_ft(True, 30), fill=(*WHITE, 255))

    # Accent label
    d.text((PAD, 78), "A CLEAR TASK-LEVEL ANSWER",
           font=_ft(True, 26), fill=(*accent, 255))

    # Main headline — 2 lines auto-sized
    headline = "WILL AI\nTAKE MY JOB?"
    for fs in [108, 94, 80, 68]:
        f = _ft(True, fs)
        bb = d.textbbox((0, 0), headline, font=f)
        if bb[2] < TW * 0.54:
            break
    d.text((PAD, 116), headline, font=f, fill=(*WHITE, 255))

    # Date box
    dbx, dby = PAD, TH - 118
    d.rectangle([dbx, dby, dbx + 148, dby + 48],
                outline=(*accent, 210), width=2, fill=(*accent, 28))
    d.line([(dbx, dby), (dbx, dby + 48)], fill=(*WHITE, 255), width=4)
    d.text((dbx + 12, dby + 11), "APR 2026", font=_ft(True, 22),
           fill=(*WHITE, 230))

    # Bottom bar
    d.rectangle([0, TH - 54, TW, TH], fill=(0, 0, 0, 170))
    d.text((PAD, TH - 42), "@theaichronicle007  ·  #AI  #Jobs  #FutureOfWork",
           font=_ft(False, 20), fill=(*WHITE, 200))

    out  = img.convert("RGB")
    path = OUTPUT / f"THUMB-{variant_label}.png"
    out.save(str(path))
    print(f"  THUMB-{variant_label}.png             <- {bg_src_name}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"\nGenerating graphics -> {OUTPUT}\n")

    # BG-01 Title — robots in command, strong glow centre
    make_scene("BG-01-title.png",  accent=BLUE,   glow_cx=W//2, glow_cy=H//2,
               glow_r=500, glow_strength=0.32, particles=60, seed=1)

    # BG-02 What people are asking — human+robot hands, concern framing
    make_scene("BG-02-search.png", accent=BLUE,   glow_cx=W//3, glow_cy=H//2,
               glow_r=420, glow_strength=0.28, particles=55, seed=2)

    # BG-03 Tasks vs Jobs — robots in office
    make_scene("BG-03-tasks.png",  accent=BLUE,   glow_cx=W//4, glow_cy=H*2//3,
               glow_r=380, glow_strength=0.25, particles=50, seed=3)

    # BG-04 Role exposure — robot with tablet, professional
    make_scene("BG-04-roles.png",  accent=BLUE,   glow_cx=W//5, glow_cy=H//2,
               glow_r=400, glow_strength=0.28, particles=55, seed=4)

    # BG-05 Practical steps — human + holographic AI
    make_scene("BG-05-steps.png",  accent=BLUE,   glow_cx=W//4, glow_cy=H//3,
               glow_r=420, glow_strength=0.30, particles=65, seed=5)

    # BG-06 Risks & Guardrails — security/lock/cyber
    make_scene("BG-06-risks.png",  accent=PURPLE, glow_cx=W//2, glow_cy=H//2,
               glow_r=460, glow_strength=0.35, particles=70, seed=6)

    # BG-07 Outro — AI news branding, robots
    make_scene("BG-07-outro.png",  accent=BLUE,   glow_cx=W//2, glow_cy=H*2//3,
               glow_r=500, glow_strength=0.30, particles=50, seed=7)

    # Thumbnails
    gen_thumbnail(BLUE,   "A", "BG2.png")                     # blue — robots in command
    gen_thumbnail(PURPLE, "B", "Copilot_20260331_223102.png") # purple — human+robot hand

    print(f"\nDone. All files -> {OUTPUT}\n")
