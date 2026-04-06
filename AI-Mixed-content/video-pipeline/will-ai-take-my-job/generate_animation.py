#!/usr/bin/env python3
"""
Animated Cinematic Intro — "The AI Chronicle: Editors View — Will AI Take My Job?"
10 seconds @ 25fps = 250 frames

Scenes:
  A  0–2.3s  Human at desk, warm amber office, holographic charts appear
  B  2.3–5.3s Cold blue creeps in, robot arms, "AI HIRED" text materialises
  C  5.3–8s   Human walks away with box, robots take the desk
  D  8–10s    Face close-up, "AI" word glows, particles, fade to black

Run from project root:
    python AI-Mixed-content/video-pipeline/will-ai-take-my-job/generate_animation.py
"""

import math, random, subprocess, shutil, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE     = Path(__file__).parent
FRAMES_D = HERE / "output" / "animation_frames"
OUT_FILE = HERE / "output" / "video" / "cinematic_intro.mp4"
FRAMES_D.mkdir(parents=True, exist_ok=True)
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

FPS   = 25
W, H  = 1920, 1080
TOTAL = 10          # seconds (was 30 — compressed to 10 for snappy intro)
N     = FPS * TOTAL # 250 frames

# ── Brand palette ──────────────────────────────────────────────────────────────
BLUE   = np.array([0,   210, 255], dtype=np.float32)
AMBER  = np.array([255, 160,  40], dtype=np.float32)
WHITE  = np.array([255, 255, 255], dtype=np.float32)
RED    = np.array([255,  40,  40], dtype=np.float32)
DARK   = np.array([6,    8,  18],  dtype=np.float32)


# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def _ft(bold, size):
    for n in (["arialbd.ttf","DejaVuSans-Bold.ttf"] if bold
              else ["arial.ttf","DejaVuSans.ttf"]):
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            pass
    return ImageFont.load_default()

def ease(t):
    """Smooth step 0→1."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def lerp_color(a, b, t):
    return (a * (1 - t) + b * t).clip(0, 255).astype(np.uint8)

def glow(arr, cx, cy, r, col, intensity=0.6):
    h, w = arr.shape[:2]
    ys, xs = np.ogrid[:h, :w]
    d = np.sqrt((xs - cx)**2 + (ys - cy)**2).astype(np.float32)
    mask = np.clip(1.0 - d / r, 0, 1) * intensity
    for c, v in enumerate(col[:3]):
        arr[:, :, c] = np.clip(arr[:, :, c] + mask * v, 0, 255)
    return arr

def bloom(img, r=5, strength=0.3):
    b   = img.filter(ImageFilter.GaussianBlur(r))
    arr = np.clip(np.array(img).astype(np.float32)
                  + np.array(b).astype(np.float32) * strength, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))

def particles(arr, rng, n, col, alpha=0.8, max_r=3):
    h, w = arr.shape[:2]
    for _ in range(n):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        r = rng.randint(1, max_r)
        bright = rng.uniform(0.4, 1.0) * alpha
        for c, v in enumerate(col[:3]):
            y0, y1 = max(0,y-r), min(h,y+r)
            x0, x1 = max(0,x-r), min(w,x+r)
            arr[y0:y1, x0:x1, c] = np.clip(
                arr[y0:y1, x0:x1, c] + v * bright, 0, 255)
    return arr

def scanlines(arr, alpha=0.06):
    arr[::4, :, :] = np.clip(arr[::4, :, :] * (1 - alpha), 0, 255)
    return arr

def draw_text_glow(img, text, x, y, font, col, glow_col, glow_r=18):
    """Draw text with outer glow."""
    tmp = Image.new("RGBA", img.size, (0,0,0,0))
    d   = ImageDraw.Draw(tmp)
    # Glow passes
    for dx in range(-glow_r, glow_r+1, 4):
        for dy in range(-glow_r, glow_r+1, 4):
            if dx*dx + dy*dy <= glow_r*glow_r:
                alpha = int(80 * (1 - math.sqrt(dx*dx+dy*dy)/glow_r))
                d.text((x+dx, y+dy), text, font=font, fill=(*glow_col, alpha))
    d.text((x, y), text, font=font, fill=(*col, 255))
    return Image.alpha_composite(img.convert("RGBA"), tmp).convert("RGB")


# ══════════════════════════════════════════════════════════════════════════════
# SCENE BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def make_base(warm_t, cold_t):
    """
    Background gradient.
    warm_t: 0→1 warm amber presence
    cold_t: 0→1 cold blue presence
    """
    arr = np.zeros((H, W, 3), dtype=np.float32)
    for y in range(H):
        yf = y / H
        # Base dark
        base = DARK + yf * np.array([4, 4, 8], dtype=np.float32)
        # Warm ceiling gradient
        warm = AMBER * (1 - yf) * warm_t * 0.50
        # Cold floor gradient
        cold = BLUE  * yf       * cold_t * 0.40
        arr[y, :] = np.clip(base + warm + cold, 0, 255)
    return arr.astype(np.uint8)


def draw_desk(arr, x, y, w, h, col=(60,45,30)):
    """Simple desk rectangle."""
    arr[y:y+h, x:x+w] = col
    # Desk top highlight
    arr[y:y+4, x:x+w] = tuple(min(255, c+40) for c in col)
    return arr


def draw_human_silhouette(arr, cx, ground_y, alpha=1.0, scale=1.0):
    """Stylised human silhouette sitting/standing."""
    s  = scale
    c  = (int(220*alpha), int(175*alpha), int(130*alpha))
    dc = (int(50*alpha),  int(40*alpha),  int(35*alpha))

    # Torso
    tx, ty = int(cx - 45*s), int(ground_y - 320*s)
    tw, th = int(90*s), int(200*s)
    arr[ty:ty+th, tx:tx+tw] = dc

    # Head
    hx, hy = int(cx - 38*s), int(ground_y - 440*s)
    hw, hh = int(76*s), int(110*s)
    arr[hy:hy+hh, hx:hx+hw] = c

    # Legs
    arr[int(ground_y-120*s):ground_y, int(cx-40*s):int(cx-5*s)]  = dc
    arr[int(ground_y-120*s):ground_y, int(cx+5*s): int(cx+40*s)] = dc

    # Arms
    arr[int(ground_y-310*s):int(ground_y-160*s), int(cx-90*s):int(cx-45*s)] = dc
    arr[int(ground_y-310*s):int(ground_y-160*s), int(cx+45*s):int(cx+90*s)] = dc
    return arr


def draw_robot_silhouette(arr, cx, ground_y, alpha=1.0, scale=1.0, col=None):
    """Stylised robot silhouette."""
    s   = scale
    rc  = col or (int(80*alpha), int(120*alpha), int(160*alpha))
    eye = (int(0*alpha), int(200*alpha), int(255*alpha))

    # Body
    bx, by = int(cx-55*s), int(ground_y-370*s)
    bw, bh = int(110*s), int(240*s)
    arr[by:by+bh, bx:bx+bw] = rc

    # Head
    hx, hy = int(cx-45*s), int(ground_y-480*s)
    hw, hh = int(90*s), int(110*s)
    arr[hy:hy+hh, hx:hx+hw] = rc

    # Eyes
    ey = int(ground_y-440*s)
    arr[ey:ey+int(22*s), int(cx-32*s):int(cx-8*s)]  = eye
    arr[ey:ey+int(22*s), int(cx+8*s): int(cx+32*s)] = eye

    # Legs
    arr[int(ground_y-130*s):ground_y, int(cx-48*s):int(cx-8*s)]  = rc
    arr[int(ground_y-130*s):ground_y, int(cx+8*s): int(cx+48*s)] = rc

    # Arms
    arr[int(ground_y-360*s):int(ground_y-180*s), int(cx-100*s):int(cx-55*s)] = rc
    arr[int(ground_y-360*s):int(ground_y-180*s), int(cx+55*s): int(cx+100*s)] = rc
    return arr


def draw_holographic_chart(img, x, y, w, h, t, col=(0,210,255)):
    """Animated holographic bar chart."""
    bars   = [0.4, 0.7, 0.55, 0.85, 0.65, 0.9, 0.75]
    n      = len(bars)
    bw     = w // n - 4
    d      = ImageDraw.Draw(img)
    # Frame
    d.rectangle([x, y, x+w, y+h], outline=(*col, 80), width=1)
    # Bars animate up
    for i, frac in enumerate(bars):
        bx   = x + i * (bw + 4) + 2
        bh   = int(h * frac * ease(t))
        by   = y + h - bh
        # Bar fill with alpha
        bar_col = (*col, int(120 + 60*math.sin(t*4 + i)))
        d.rectangle([bx, by, bx+bw, y+h], fill=bar_col)
        d.rectangle([bx, by, bx+bw, by+3], fill=(*col, 220))
    # Scanline across chart
    sl_y = y + int((h-4) * ((t * 0.8) % 1.0))
    d.line([(x, sl_y), (x+w, sl_y)], fill=(*col, 60), width=1)
    return img


def draw_box(arr, cx, y, alpha=1.0):
    """Cardboard box the human carries."""
    bc = (int(185*alpha), int(148*alpha), int(90*alpha))
    bx, by = cx-65, y
    bw, bh = 130, 100
    arr[by:by+bh, bx:bx+bw] = bc
    # Flaps
    arr[by:by+15, bx:bx+bw] = (int(200*alpha), int(160*alpha), int(100*alpha))
    # Seam
    arr[by:by+bh, bx+62:bx+68] = (int(140*alpha), int(110*alpha), int(60*alpha))
    return arr


# ══════════════════════════════════════════════════════════════════════════════
# FRAME GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

rng   = random.Random(42)
GY    = H - 180     # ground y for characters


def make_frame(fi):
    t_abs = fi / FPS            # absolute time in seconds
    t_norm = t_abs / TOTAL     # 0→1 over full 30s

    # ── Scene timing ──────────────────────────────────────────────────────────
    # A: 0–2.3s   warm office, human at desk
    # B: 2.3–5.3s cold takeover, robot appears, AI HIRED
    # C: 5.3–8s   human walks away, robots at desk
    # D: 8–10s    face close-up, AI glow, fade out

    scA = ease((t_abs) / 2.3)                           # scene A presence
    scB = ease((t_abs - 2.3) / 3.0)                     # scene B presence
    scC = ease((t_abs - 5.3) / 2.7)                     # scene C presence
    scD = ease((t_abs - 8.0) / 2.0)                     # scene D presence

    warm_t = max(0, 1.0 - scB)
    cold_t = scB

    # ── Background ────────────────────────────────────────────────────────────
    arr = make_base(warm_t, cold_t).astype(np.float32)

    # Ambient blue glow intensifies over time
    if scB > 0:
        arr = glow(arr, W*3//4, H//2, int(400 + 200*scB),
                   BLUE, intensity=0.25*scB)

    # Warm desk light fades out
    if warm_t > 0:
        arr = glow(arr, W//2, GY - 200, 350, AMBER, intensity=0.4*warm_t)

    arr = arr.clip(0, 255).astype(np.uint8)

    img = Image.fromarray(arr)

    # ── Desk ──────────────────────────────────────────────────────────────────
    desk_alpha = max(0, 1.0 - scC * 2)
    if desk_alpha > 0:
        da = img.load()
        DX, DY = int(W//2 - 420), int(GY - 30)
        for py in range(DY, DY+40):
            for px in range(DX, DX+840):
                if 0 <= py < H and 0 <= px < W:
                    r, g, b = da[px, py]
                    nr = int(r*(1-desk_alpha) + 70*desk_alpha)
                    ng = int(g*(1-desk_alpha) + 55*desk_alpha)
                    nb = int(b*(1-desk_alpha) + 35*desk_alpha)
                    da[px, py] = (nr, ng, nb)

    # ── Holographic charts (scene A & early B) ────────────────────────────────
    chart_alpha = max(0, min(1, scA * 2)) * max(0, 1 - scC * 2)
    if chart_alpha > 0.05:
        img = draw_holographic_chart(img, W//2 - 380, GY-340, 280, 220,
                                      t_abs, col=(0,210,255))
        img = draw_holographic_chart(img, W//2 + 100, GY-280, 220, 160,
                                      t_abs + 0.5, col=(0,255,180))

    # ── Human silhouette ──────────────────────────────────────────────────────
    arr = np.array(img)
    human_x = W // 2
    # In scene C human walks left
    if scC > 0:
        walk_x = int(W//2 - scC * 600)
        human_alpha = max(0, 1 - scC * 1.2)
        if human_alpha > 0.05:
            arr = draw_human_silhouette(arr, walk_x, GY, human_alpha)
            # Carry box
            if scC > 0.1:
                arr = draw_box(arr, walk_x - 10, GY - 140, human_alpha)
    else:
        arr = draw_human_silhouette(arr, human_x, GY, 1.0)

    # ── Robot silhouette (materialises in scene B) ────────────────────────────
    robot_alpha = ease(scB * 1.5)
    if robot_alpha > 0.05:
        robot_x = int(W//2 + 180 + (1-robot_alpha)*300)
        arr = draw_robot_silhouette(arr, robot_x, GY, robot_alpha)
        # Second robot in scene C
        if scC > 0.3:
            arr = draw_robot_silhouette(arr, W//2 - 40, GY,
                                         ease((scC-0.3)/0.7),
                                         col=(60,100,140))

    img = Image.fromarray(arr.clip(0,255).astype(np.uint8))

    # ── "AI HIRED" text (scene B peak) ────────────────────────────────────────
    hired_t = ease((t_abs - 3.0) / 1.5) * max(0, 1 - ease((t_abs - 6.0)/1.0))
    if hired_t > 0.05:
        f_hired = _ft(True, int(120 + 20*math.sin(t_abs*2)))
        img = draw_text_glow(img, "AI HIRED",
                             int(W//2 - 280), int(H//2 - 100),
                             f_hired,
                             glow_col=(0, 180, 255),
                             col=(255, 255, 255),
                             glow_r=28)
        # Tint text alpha
        arr2 = np.array(img).astype(np.float32)
        # Pulse
        pulse = 0.85 + 0.15 * math.sin(t_abs * 6)
        arr2 = (arr2 * pulse).clip(0, 255)
        img = Image.fromarray(arr2.astype(np.uint8))

    # ── Scene D: Face close-up + "AI" glow ───────────────────────────────────
    if scD > 0.05:
        arr = np.array(img).astype(np.float32)
        # Dark vignette closing in
        cx2, cy2 = W//2, H//2 + 80
        ys, xs = np.ogrid[:H, :W]
        dist = np.sqrt((xs-cx2)**2 + (ys-cy2)**2).astype(np.float32)
        max_d = math.hypot(W//2, H//2)
        vig  = np.clip(dist / (max_d * (1 - scD*0.5)), 0, 1) ** 1.5
        arr *= (1 - vig[:,:,np.newaxis] * scD)

        # Face oval (warm tone)
        face_r = int(200 * (1 - scD*0.3))
        face_arr = glow(arr, cx2, cy2-60, face_r, AMBER, intensity=0.55*scD)
        # Eye glow (blue reflection from "AI")
        face_arr = glow(face_arr, cx2-55, cy2-80, 40, BLUE, intensity=0.6*scD)
        face_arr = glow(face_arr, cx2+55, cy2-80, 40, BLUE, intensity=0.6*scD)
        arr = face_arr

        img = Image.fromarray(arr.clip(0,255).astype(np.uint8))

        # "AI" floating text
        f_ai = _ft(True, int(180 + 30*math.sin(t_abs*3)))
        ai_alpha_val = int(255 * ease(scD))
        img = draw_text_glow(img, "AI",
                             int(cx2 - 100), int(cy2 - 280),
                             f_ai,
                             glow_col=(0, 180, 255),
                             col=(0, 210, 255),
                             glow_r=40)

    # ── Particles (increases over time) ───────────────────────────────────────
    arr = np.array(img).astype(np.float32)
    n_p = int(30 + 120 * cold_t + 80 * scD)
    arr = particles(arr, rng, n_p, BLUE, alpha=0.6 + 0.4*cold_t)
    if warm_t > 0.1:
        arr = particles(arr, rng, int(20*warm_t), AMBER, alpha=0.3)

    # ── Scanlines ─────────────────────────────────────────────────────────────
    arr = scanlines(arr.clip(0,255).astype(np.uint8).astype(np.float32))
    img = Image.fromarray(arr.clip(0,255).astype(np.uint8))

    # ── Final fade in/out ─────────────────────────────────────────────────────
    fade_in  = ease(t_abs / 0.5)
    fade_out = ease((TOTAL - t_abs) / 0.7) if t_abs > TOTAL - 0.7 else 1.0
    fade     = fade_in * fade_out
    if fade < 0.999:
        arr_f = np.array(img).astype(np.float32) * fade
        img = Image.fromarray(arr_f.clip(0,255).astype(np.uint8))

    # ── Bloom pass ────────────────────────────────────────────────────────────
    img = bloom(img, r=4, strength=0.22)

    # ── Brand bar ─────────────────────────────────────────────────────────────
    if t_abs < 0.7 or t_abs > 9.0:
        bar_alpha = min(ease(t_abs/0.4), ease((TOTAL-t_abs)/0.7))
    else:
        bar_alpha = 1.0

    d = ImageDraw.Draw(img)
    bar_a = int(220 * bar_alpha)  # increased opacity for contrast
    d.rectangle([0, H-62, W, H], fill=(0,0,0,bar_a))
    d.rectangle([0, H-62, W, H-59], fill=(0,210,255,int(200*bar_alpha)))  # cyan accent line
    d.text((60, H-50), "THE AI CHRONICLE: EDITORS VIEW",
           font=_ft(True,26), fill=(255,255,255,int(240*bar_alpha)))
    d.text((W-440, H-50), "@theaichronicle007",
           font=_ft(False,22), fill=(0,210,255,int(220*bar_alpha)))

    return img


# ══════════════════════════════════════════════════════════════════════════════
# RENDER ALL FRAMES
# ══════════════════════════════════════════════════════════════════════════════

def render_frames():
    print(f"Rendering {N} frames @ {FPS}fps ({TOTAL}s) ...")
    for fi in range(N):
        frame = make_frame(fi)
        frame.save(str(FRAMES_D / f"frame_{fi:04d}.png"))
        if fi % 50 == 0:
            print(f"  [{fi+1}/{N}]  t={fi/FPS:.1f}s")
    print(f"  All frames rendered -> {FRAMES_D}")


def encode_video():
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i",         str(FRAMES_D / "frame_%04d.png"),
        "-vf",        "scale=1920:1080,format=yuv420p",
        "-c:v",       "libx264",
        "-preset",    "fast",
        "-crf",       "20",
        str(OUT_FILE),
    ]
    print(f"\nEncoding -> {OUT_FILE.name} ...")
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stderr[-2000:])
        raise RuntimeError("FFmpeg failed")
    size_mb = OUT_FILE.stat().st_size / 1_048_576
    print(f"Saved: {OUT_FILE.name}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    render_frames()
    encode_video()
    print("\nDone. Cinematic intro ready.")
