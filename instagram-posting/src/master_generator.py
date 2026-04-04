#!/usr/bin/env python3
"""
THE AI CHRONICLE — Master Instagram Post Generator v12
Generates professional 1080×1080 PNG + MP4 with synthesized music
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import math
import random
import hashlib
import subprocess
from scipy.io import wavfile
import os
import sys

W, H = 1080, 1080
PAD = 70
SR = 44100

# ── STORY DATA ──────────────────────────────────────────────────
story = {
    "company": "OpenAI / Funding",
    "headline": "OpenAI Raises $110B at $730B Valuation",
    "watermark": "$730B",
    "body": [
        "Amazon, NVIDIA & SoftBank",
        "back OpenAI's $110B raise.",
        "A $730B valuation makes it",
        "the world's most valued AI firm."
    ],
    "stat_label": "OpenAI Pre-Money Valuation",
    "stat_value": "$730B",
    "source": "OpenAI / The AI Track",
}

LOGO_PATH = "logo.PNG"
DURATION = 30
OUT_PNG = "output/theaichronicle_post.png"
OUT_MP4 = "output/theaichronicle_post.mp4"
OUT_WAV = "output/theaichronicle_music.wav"

# ── HELPERS ─────────────────────────────────────────────────────
def rgb(h):
    """Convert hex color to RGB tuple"""
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def F(sz, bold=False):
    """Load font with fallback"""
    try:
        p = f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf"
        return ImageFont.truetype(p, sz)
    except:
        try:
            p = f"C:\\Windows\\Fonts\\arial{'' if not bold else ''}.ttf"
            return ImageFont.truetype(p, sz)
        except:
            return ImageFont.load_default()

def SF(sz, bold=False):
    """Load serif font with fallback"""
    try:
        p = f"/usr/share/fonts/truetype/dejavu/DejaVuSerif{'-Bold' if bold else ''}.ttf"
        return ImageFont.truetype(p, sz)
    except:
        try:
            p = f"C:\\Windows\\Fonts\\garamond.ttf" if not bold else f"C:\\Windows\\Fonts\\garamondb.ttf"
            return ImageFont.truetype(p, sz)
        except:
            return F(sz, bold)

def tw(d, t, f):
    """Text width"""
    bb = d.textbbox((0, 0), t, font=f)
    return bb[2] - bb[0]

def th(d, t, f):
    """Text height"""
    bb = d.textbbox((0, 0), t, font=f)
    return bb[3] - bb[1]

def draw_c(d, y, text, fill, fnt):
    """Draw centered text"""
    fc = rgb(fill) if isinstance(fill, str) else fill
    d.text(((W - tw(d, text, fnt)) // 2, y), text, fill=fc, font=fnt)
    return th(d, text, fnt)

def wrap(d, text, fnt, max_w):
    """Wrap text to max width"""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if tw(d, test, fnt) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def alpha_paste(img, cr, x, y, w, h, alpha):
    """Paste semi-transparent rectangle"""
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rectangle([x, y, x + w, y + h], fill=(*cr, alpha))
    base = img.convert("RGBA")
    base.paste(ov, (0, 0), ov)
    return base.convert("RGB")

# ── BACKGROUND GENERATORS ──────────────────────────────────────
def bg_neural(img, ac, rng):
    """Neural network background"""
    clusters = [(rng.randint(150, 350), rng.randint(300, 580)),
                (540, rng.randint(280, 440)),
                (rng.randint(730, 930), rng.randint(300, 580))]
    nodes = []
    for cx, cy in clusters:
        for _ in range(rng.randint(14, 22)):
            a = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(25, 165)
            nodes.append((int(cx + d * math.cos(a)), int(cy + d * math.sin(a)), cx, cy))
    for i, (x1, y1, c1x, c1y) in enumerate(nodes):
        for j, (x2, y2, c2x, c2y) in enumerate(nodes):
            if i < j:
                dist = math.hypot(x2 - x1, y2 - y1)
                same = (c1x == c2x and c1y == c2y)
                if dist < (195 if same else 140) and rng.random() < (0.88 if same else 0.07):
                    alpha = int((32 if same else 13) * (1 - dist / 195))
                    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    ImageDraw.Draw(ov).line([(x1, y1), (x2, y2)], fill=(*ac, max(5, alpha)), width=1)
                    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    for r, a in [(68, 24), (108, 17), (148, 11)]:
        for cx, cy in clusters:
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*ac, a), width=1)
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    return img

def bg_grid(img, ac, rng):
    """Grid background"""
    gap = rng.choice([54, 72, 90])
    for gy in range(0, H, gap):
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).line([(0, gy), (W, gy)], fill=(*ac, 20), width=1)
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    for gx in range(0, W, gap):
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).line([(gx, 0), (gx, H)], fill=(*ac, 20), width=1)
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    for gy in range(0, H, gap):
        for gx in range(0, W, gap):
            d.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=(*ac, 50))
    return img

def bg_radar(img, ac, rng):
    """Radar background"""
    cx, cy = W // 2, H // 2 + rng.randint(-50, 50)
    for r, a in [(420, 16), (320, 20), (220, 26), (130, 22), (60, 18)]:
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*ac, a), width=1)
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    for i in range(8):
        angle = math.radians(i * 45)
        x2 = int(cx + 450 * math.cos(angle))
        y2 = int(cy + 450 * math.sin(angle))
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).line([(cx, cy), (x2, y2)], fill=(*ac, 13), width=1)
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    return img

def bg_bars(img, ac, rng):
    """Bars background"""
    n = rng.randint(7, 10)
    bw = int((W - 120) / n) - 8
    heights = [min(80 + i * rng.randint(28, 55) + rng.randint(0, 25), 700) for i in range(n)]
    for i, bh in enumerate(heights):
        bx = 60 + i * (bw + 8)
        by = H - 80 - bh
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d2 = ImageDraw.Draw(ov)
        d2.rectangle([bx, by, bx + bw, H - 60], fill=(*ac, 20))
        d2.rectangle([bx, by, bx + bw, by + 4], fill=(*ac, 55))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    return img

def bg_stars(img, ac, rng):
    """Stars background"""
    for _ in range(rng.randint(200, 320)):
        px = rng.randint(0, W)
        py = rng.randint(0, H)
        ps = rng.randint(1, 3)
        pa = rng.randint(20, 75)
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).ellipse([px - ps, py - ps, px + ps, py + ps], fill=(*ac, pa))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    return img

BG_GENS = [bg_neural, bg_grid, bg_radar, bg_bars, bg_stars]

# ── THEME LIBRARY ──────────────────────────────────────────────
THEMES = [
    ("Midnight Gold", "dark", (4, 8, 28), (12, 4, 40), "#F5C842", "#FFF0B0", "#080600", "#ffffff"),
    ("Deep Cosmos", "dark", (8, 0, 16), (20, 0, 40), "#A78BFA", "#E8D8FF", "#080418", "#ffffff"),
    ("Forest Dark", "dark", (0, 12, 6), (0, 24, 14), "#10B981", "#B8FFDC", "#00120a", "#ffffff"),
    ("Crimson Dark", "dark", (22, 4, 0), (36, 8, 0), "#FF4D1A", "#FFD0B8", "#140400", "#ffffff"),
    ("Deep Navy", "dark", (0, 6, 18), (0, 10, 28), "#60A5FA", "#C8DCFF", "#000614", "#ffffff"),
]

# ── MUSIC SYNTHESIZER ──────────────────────────────────────────
def build_music(track_idx, dur, np_seed):
    """Build synthesized music track"""
    track = np.zeros(int(SR * dur))
    np.random.seed(np_seed % (2 ** 32))

    def note(freq, d, vol=0.4, wave='sine'):
        t = np.linspace(0, d, int(SR * d), False)
        if wave == 'sine':
            s = np.sin(2 * np.pi * freq * t)
        elif wave == 'saw':
            s = 2 * (t * freq - np.floor(0.5 + t * freq))
        elif wave == 'square':
            s = np.sign(np.sin(2 * np.pi * freq * t))
        else:
            s = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
        fade = max(1, int(SR * 0.015))
        env = np.ones(len(t))
        env[:fade] = np.linspace(0, 1, fade)
        env[-fade:] = np.linspace(1, 0, fade)
        return s * env * vol

    def add(sig, start):
        s = int(start * SR)
        e = s + len(sig)
        if e > len(track):
            e = len(track)
            sig = sig[:e - s]
        track[s:e] += sig

    def kick(f=100, dc=20, v=0.55):
        t = np.linspace(0, 0.18, int(SR * 0.18))
        return np.sin(2 * np.pi * (f * np.exp(-dc * t) + 40) * t) * np.exp(-16 * t) * v

    def snare(v=0.38):
        t = np.linspace(0, 0.12, int(SR * 0.12))
        return (np.random.randn(len(t)) * 0.28 + np.sin(2 * np.pi * 200 * t) * 0.15) * np.exp(-28 * t) * v

    def hat(v=0.15, dc=80):
        t = np.linspace(0, 0.04, int(SR * 0.04))
        return np.random.randn(len(t)) * np.exp(-dc * t) * v

    roots = [55, 65.4, 73.4, 82.4, 87.3, 98, 110, 123.5, 130.8, 146.8, 164.8, 174.6]
    root = roots[track_idx % len(roots)]
    BPMs = [72, 82, 88, 95, 105, 110, 118, 125, 128, 132, 138, 140]
    BPM = BPMs[track_idx % len(BPMs)]
    BEAT = 60 / BPM
    
    scale = [1, 1.122, 1.26, 1.498, 1.682]
    bp_idx = [0, 0, 2, 2, 1, 1, 2, 0]
    bp = [root * scale[min(i, len(scale) - 1)] for i in bp_idx]
    
    for bar in range(int(dur / (8 * BEAT / 2)) + 1):
        for i, f in enumerate(bp):
            tt = bar * 8 * BEAT / 2 + i * BEAT / 2
            if tt < dur:
                add(note(f, BEAT / 2 * 0.82, 0.20, 'sine'), tt)
    
    for bar in range(int(dur / BEAT) + 1):
        add(kick(v=0.40), (bar * 4) * BEAT)
        add(snare(v=0.28), (bar * 4 + 2) * BEAT)
        add(hat(), (bar * 4) * BEAT)
    
    fi = int(SR * min(2.0, dur * 0.1))
    track[:fi] *= np.linspace(0.1, 1, fi)
    track[-int(SR * 3):] *= np.linspace(1, 0, int(SR * 3))
    
    pk = np.max(np.abs(track))
    track = track / pk * 0.84 if pk > 0 else track
    return np.column_stack([track, track])

# ── MAIN GENERATOR ─────────────────────────────────────────────
def generate(story, logo_path, dur, out_png, out_mp4, out_wav):
    """Generate Instagram post"""
    seed_str = story['headline'] + story['company']
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    np_seed = seed % (2 ** 32)

    t_idx = rng.randint(0, len(THEMES) - 1)
    b_idx = rng.randint(0, len(BG_GENS) - 1)
    mu_idx = rng.randint(0, 63)

    name, mode, bg_top, bg_bot, accent, body_c, stat_bg, hl_c = THEMES[t_idx]
    ac = rgb(accent)
    print(f"Theme: {name} ({mode}) | BG: {BG_GENS[b_idx].__name__}")

    # Gradient background
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(bg_top[0] * (1 - t) + bg_bot[0] * t)
        g = int(bg_top[1] * (1 - t) + bg_bot[1] * t)
        b = int(bg_top[2] * (1 - t) + bg_bot[2] * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))

    # Watermark
    wm_fnt = SF(200, bold=True)
    wm_txt = story.get('watermark', 'AI')
    d = ImageDraw.Draw(img)
    wm_w = tw(d, wm_txt, wm_fnt)
    wm_h = th(d, wm_txt, wm_fnt)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).text(
        ((W - wm_w) // 2, (H - wm_h) // 2 + 20),
        wm_txt, fill=(*ac, 18), font=wm_fnt
    )
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

    # Background elements
    img = BG_GENS[b_idx](img, ac, rng)

    d = ImageDraw.Draw(img)

    # Top bar
    d.rectangle([0, 0, W, 8], fill=ac)

    # Header
    y = 8 + 32
    if mode == "dark":
        img = alpha_paste(img, (4, 4, 14), 0, y - 10, W, 112, 215)
        d = ImageDraw.Draw(img)
    y += draw_c(d, y, "THE AI CHRONICLE", "#ffffff", SF(40, bold=True)) + 12
    y += draw_c(d, y, "D A I L Y  A I  N E W S", accent, F(18)) + 22
    d.line([(PAD, y), (W - PAD, y)], fill=ac, width=1)
    y += 28

    # Category pill
    pf = F(20, bold=True)
    plbl = story['company'].upper()
    ptw_ = tw(d, plbl, pf)
    ph = 50
    pw = ptw_ + 64
    px_ = (W - pw) // 2
    d.rounded_rectangle([px_, y, px_ + pw, y + ph], radius=25, fill=ac)
    d.text(((W - ptw_) // 2, y + (ph - th(d, plbl, pf)) // 2), plbl, fill=(255, 255, 255), font=pf)
    y += ph + 30

    # Headline
    hf = SF(56, bold=True)
    hlines = wrap(d, story['headline'], hf, W - 2 * PAD)
    hblock = sum(th(d, hl, hf) + 8 for hl in hlines[:2])
    if mode == "dark":
        img = alpha_paste(img, (4, 4, 14), PAD - 12, y - 8, W - 2 * PAD + 24, hblock + 20, 215)
        d = ImageDraw.Draw(img)
    for hl in hlines[:2]:
        d.text(((W - tw(d, hl, hf)) // 2, y), hl, fill=rgb(hl_c), font=hf)
        y += th(d, hl, hf) + 8
    y += 18

    # Divider
    d.line([(PAD, y), (W - PAD, y)], fill=ac, width=2)
    y += 28

    # Body
    bf = F(56)
    lh = th(d, story['body'][0], bf) + 14
    body_h = lh * len(story['body'])
    if mode == "dark":
        img = alpha_paste(img, (4, 4, 14), 0, y - 8, W, body_h + 16, 200)
        d = ImageDraw.Draw(img)
    for line in story['body']:
        d.text(((W - tw(d, line, bf)) // 2, y), line, fill=rgb(body_c), font=bf)
        y += lh
    y += 22

    # Stat box
    sbh = 160
    sbw = W - 2 * PAD - 80
    sbx = (W - sbw) // 2
    d.rounded_rectangle([sbx, y, sbx + sbw, y + sbh], radius=14, fill=rgb(stat_bg))
    d.rounded_rectangle([sbx, y, sbx + sbw, y + sbh], radius=14, outline=ac, width=3)
    slf = F(18)
    slbl = story['stat_label']
    svf = SF(68, bold=True)
    sval = story['stat_value']
    slbl_h = th(d, slbl, slf)
    sval_h = th(d, sval, svf)
    gap = 12
    total = slbl_h + gap + sval_h
    by_ = y + (sbh - total) // 2
    d.text(((W - tw(d, slbl, slf)) // 2, by_), slbl, fill=ac, font=slf)
    d.text(((W - tw(d, sval, svf)) // 2, by_ + slbl_h + gap), sval, fill=rgb(hl_c), font=svf)
    y += sbh + 20

    # Source
    sf2 = F(16)
    stxt = f"Source: {story['source']}"
    sc = (min(ac[0] + 55, 200), min(ac[1] + 40, 180), min(ac[2] + 40, 180)) if mode == "dark" else (100, 80, 120)
    d.text(((W - tw(d, stxt, sf2)) // 2, y), stxt, fill=sc, font=sf2)

    # Footer
    FH = 168
    fy = H - FH
    fb = rgb("#050912") if mode == "dark" else rgb(stat_bg)
    d.rectangle([0, fy, W, H], fill=fb)
    d.line([(0, fy), (W, fy)], fill=ac, width=1)
    
    # Add simple logo placeholder if doesn't exist
    if not os.path.exists(logo_path):
        logo = Image.new("RGBA", (88, 88), (*ac, 200))
        ImageDraw.Draw(logo).text((20, 35), "AI", fill=(255, 255, 255), font=F(40, bold=True))
    else:
        logo_src = Image.open(logo_path).convert("RGBA")
        logo = logo_src.resize((88, 88), Image.LANCZOS)
    
    if mode == "light":
        la = np.array(logo).astype(float)
        la[:, :, :3] = 255 - la[:, :, :3]
        logo = Image.fromarray(la.astype(np.uint8))
    
    img.paste(logo, ((W - 88) // 2, fy + 10), logo)
    d = ImageDraw.Draw(img)
    lb = fy + 10 + 88
    htxt = "@theaichronicle  •  Daily AI News"
    d.text(((W - tw(d, htxt, F(16))) // 2, lb + 8), htxt, fill=sc, font=F(16))
    ctxt = "Follow for daily AI news"
    d.text(((W - tw(d, ctxt, F(17))) // 2, lb + 30), ctxt, fill=ac, font=F(17))
    d.rectangle([0, H - 8, W, H], fill=ac)

    img.save(out_png, "PNG", dpi=(300, 300))
    print(f"✅ PNG saved: {out_png}")

    # Audio
    stereo = build_music(mu_idx, dur, np_seed)
    wavfile.write(out_wav, SR, (stereo * 32767).astype(np.int16))
    print(f"✅ WAV saved: {out_wav}")

    # MP4 via ffmpeg
    cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", out_png,
           "-i", out_wav, "-c:v", "libx264", "-preset", "fast", "-crf", "18",
           "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
           "-vf", f"scale={W}:{H}", "-t", str(dur), "-movflags", "+faststart", out_mp4]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        print(f"✅ MP4 saved: {out_mp4}")
    else:
        print("⚠️  FFmpeg warning (PNG still created):", result.stderr.decode()[-200:])

# ── RUN ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("THE AI CHRONICLE — Master Post Generator v12")
    print("=" * 70)
    generate(story, LOGO_PATH, DURATION, OUT_PNG, OUT_MP4, OUT_WAV)
    print("=" * 70)
    print("✅ Post generation complete!")
    print("=" * 70)
