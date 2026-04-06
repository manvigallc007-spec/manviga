#!/usr/bin/env python3
"""
THE AI CHRONICLE — Improved YouTube Video Generator
~10-minute 1920x1080 video: intro + 10 stories + outro
10 distinct color themes · AI background textures · narrative structure
Hook → What Happened → Why It Matters → What's Next
H264 CRF20 · AAC 192k · 30fps
"""

import json
import logging
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

ROOT_ENV  = Path(__file__).parent.parent.parent / ".env"
LOCAL_ENV = Path(__file__).parent.parent / ".env"
load_dotenv(ROOT_ENV)
load_dotenv(LOCAL_ENV)

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR   = PROJECT_ROOT / "output"
LOG_DIR      = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# FFmpeg binary
_FFMPEG_WINGET_PATHS = [
    Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-7.1-full_build/bin/ffmpeg.exe",
    Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-8.1-full_build/bin/ffmpeg.exe",
]
FFMPEG_BIN = next((str(p) for p in _FFMPEG_WINGET_PATHS if p.exists()), "ffmpeg")

LOG_FILE = LOG_DIR / f"video_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


class UTFStreamHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(
            open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)
        )
    def emit(self, record):
        try:
            super().emit(record)
        except Exception:
            pass


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        UTFStreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CANVAS CONSTANTS
# ─────────────────────────────────────────────

W, H    = 1920, 1080
PAD     = 60
STORIES = 10

THUMBNAIL_TTS = "The AI Chronicle."
INTRO_TEXT = "Today's top ten AI stories."
OUTRO_TEXT = (
    "That's your AI Chronicle update for today. "
    "Hit like, subscribe, and the notification bell for daily AI news. "
    "See you tomorrow."
)
SUPPORT_TEXT = (
    "Enjoying The AI Chronicle? Please like, follow, subscribe, comment and share. "
    "Help us make AI knowledge reachable for more people. "
    "Your support helps us produce better quality news every day."
)

# Layout Y positions
Y_HEADER   = 72    # header bar bottom
Y_SUB      = 116   # subtitle bar bottom (44px)
Y_HOOK     = 126   # hook text starts
Y_PILLS    = 330   # pills row starts (after hook ~200px)
Y_CONTENT  = 388   # content area starts (pills+52)
Y_STRIP    = 802   # stories strip starts
Y_CTA      = 1012  # CTA bar starts
# Content area: 388-802 = 414px
# Strip: 802-1012 = 210px (3 rows × 70px)
# CTA: 1012-1080 = 68px

# ─────────────────────────────────────────────
# LOGO LOADER
# ─────────────────────────────────────────────

def _load_logo(size=(56, 56)):
    candidates = [
        Path(__file__).parent.parent.parent / "logo.PNG",
        Path(__file__).parent.parent.parent / "youtube-posting" / "logo.PNG",
        Path(__file__).parent.parent.parent / "instagram-posting" / "logo.PNG",
    ]
    for p in candidates:
        if p.exists():
            try:
                logo = Image.open(p).convert("RGBA")
                logo = logo.resize(size, Image.LANCZOS)
                return logo
            except Exception:
                pass
    return None


# ─────────────────────────────────────────────
# 10 STORY THEMES (one per story slot)
# ─────────────────────────────────────────────

STORY_THEMES = [
    # 0 — electric blue (story 1)
    {"bg1": (5,10,35),   "bg2": (10,20,60),  "accent": (0,210,255),   "accent2": (0,150,220),
     "headline_color": (255,255,255), "text_color": (180,220,255), "stat_bg": (0,40,100),
     "pill_bg": (0,55,130),  "grid_color": (0,50,110)},
    # 1 — deep purple (story 2)
    {"bg1": (20,5,40),   "bg2": (35,10,65),  "accent": (190,110,255), "accent2": (140,70,215),
     "headline_color": (255,255,255), "text_color": (220,190,255), "stat_bg": (55,15,105),
     "pill_bg": (65,20,115), "grid_color": (50,15,90)},
    # 2 — amber gold (story 3)
    {"bg1": (35,15,0),   "bg2": (55,25,5),   "accent": (255,185,0),   "accent2": (225,135,0),
     "headline_color": (255,255,255), "text_color": (255,230,180), "stat_bg": (90,45,0),
     "pill_bg": (105,52,0),  "grid_color": (80,40,0)},
    # 3 — crimson red (story 4)
    {"bg1": (40,5,5),    "bg2": (60,10,10),  "accent": (255,80,80),   "accent2": (215,30,30),
     "headline_color": (255,255,255), "text_color": (255,210,210), "stat_bg": (95,10,10),
     "pill_bg": (105,12,12), "grid_color": (85,8,8)},
    # 4 — emerald green (story 5)
    {"bg1": (5,30,15),   "bg2": (5,48,25),   "accent": (0,225,125),   "accent2": (0,175,95),
     "headline_color": (255,255,255), "text_color": (180,255,210), "stat_bg": (0,68,32),
     "pill_bg": (0,72,38),   "grid_color": (0,55,28)},
    # 5 — indigo night (story 6)
    {"bg1": (15,15,45),  "bg2": (25,20,68),  "accent": (110,140,255), "accent2": (75,100,225),
     "headline_color": (255,255,255), "text_color": (200,210,255), "stat_bg": (28,38,118),
     "pill_bg": (32,44,125), "grid_color": (25,35,105)},
    # 6 — orange fire (story 7)
    {"bg1": (40,15,0),   "bg2": (62,25,0),   "accent": (255,130,0),   "accent2": (225,90,0),
     "headline_color": (255,255,255), "text_color": (255,215,185), "stat_bg": (108,42,0),
     "pill_bg": (115,45,0),  "grid_color": (95,38,0)},
    # 7 — teal ocean (story 8)
    {"bg1": (5,25,30),   "bg2": (5,42,48),   "accent": (0,205,195),   "accent2": (0,165,155),
     "headline_color": (255,255,255), "text_color": (180,242,242), "stat_bg": (0,58,62),
     "pill_bg": (0,62,68),   "grid_color": (0,50,55)},
    # 8 — rose pink (story 9)
    {"bg1": (35,10,20),  "bg2": (52,15,32),  "accent": (255,110,160), "accent2": (225,70,120),
     "headline_color": (255,255,255), "text_color": (255,205,225), "stat_bg": (98,18,48),
     "pill_bg": (108,22,55), "grid_color": (88,15,42)},
    # 9 — silver steel (story 10)
    {"bg1": (15,20,25),  "bg2": (25,32,38),  "accent": (175,200,225), "accent2": (140,168,192),
     "headline_color": (255,255,255), "text_color": (200,218,235), "stat_bg": (38,52,68),
     "pill_bg": (42,58,75),  "grid_color": (35,48,62)},
]


# ─────────────────────────────────────────────
# DRAWING HELPERS
# ─────────────────────────────────────────────

def draw_rounded_rect(draw, xy, radius, fill, outline=None, outline_width=2):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill,
                            outline=outline, width=outline_width)


def draw_gradient_rect(img, xy, color1, color2, direction="vertical"):
    x0, y0, x1, y1 = xy
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return
    if direction == "vertical":
        gradient = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(h):
            t = i / max(h - 1, 1)
            gradient[i, :] = [int(color1[j] * (1 - t) + color2[j] * t) for j in range(3)]
    else:
        gradient = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(w):
            t = i / max(w - 1, 1)
            gradient[:, i] = [int(color1[j] * (1 - t) + color2[j] * t) for j in range(3)]
    patch = Image.fromarray(gradient, 'RGB')
    img.paste(patch, (x0, y0))


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    return lines if lines else [""]


def draw_glow(img, center, radius, color, intensity=0.4):
    arr = np.array(img).astype(np.float32)
    cx, cy = center
    h, w = arr.shape[:2]
    y_idx, x_idx = np.ogrid[:h, :w]
    dist = np.sqrt((x_idx - cx) ** 2 + (y_idx - cy) ** 2)
    mask = np.clip(1.0 - dist / max(radius, 1), 0, 1) ** 2 * intensity
    for c, col_val in enumerate(color[:3]):
        arr[:, :, c] = np.clip(arr[:, :, c] + mask * col_val, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def _tw(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _th(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def _draw_text_shadow(draw, pos, text, font, fill, shadow_offset=3):
    draw.text((pos[0] + shadow_offset, pos[1] + shadow_offset), text, font=font, fill=(0, 0, 0))
    draw.text(pos, text, font=font, fill=fill)


def _draw_pill(draw, x, y, text, font, bg_color, text_color=(255, 255, 255),
               radius=12, pad_x=18, pad_y=8):
    tw = _tw(draw, text, font)
    th = _th(draw, text, font)
    x2 = x + tw + pad_x * 2
    y2 = y + th + pad_y * 2
    draw_rounded_rect(draw, (x, y, x2, y2), radius, fill=bg_color)
    draw.text((x + pad_x, y + pad_y), text, font=font, fill=text_color)
    return x2, y2


def _draw_hashtags(draw, x, y, hashtags, font, color, max_width=None):
    cx = x
    for tag in hashtags:
        if max_width and cx - x > max_width:
            break
        draw.text((cx, y), tag, font=font, fill=color)
        cx += _tw(draw, tag + "  ", font)


# ─────────────────────────────────────────────
# FONTS
# ─────────────────────────────────────────────

def load_fonts() -> dict:
    font_dirs = [
        Path("C:/Windows/Fonts"),
        Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
    ]

    def _find(name):
        for d in font_dirs:
            p = d / name
            if p.exists():
                return str(p)
        return None

    def _ft(name, size):
        path = _find(name)
        try:
            if path:
                return ImageFont.truetype(path, size)
        except Exception:
            pass
        try:
            return ImageFont.truetype(_find("arial.ttf") or "", size)
        except Exception:
            pass
        return ImageFont.load_default()

    return {
        # Bold headline sizes
        "h96":    _ft("arialbd.ttf",  96),
        "h88":    _ft("arialbd.ttf",  88),
        "h80":    _ft("arialbd.ttf",  80),
        "h72":    _ft("arialbd.ttf",  72),
        "h64":    _ft("arialbd.ttf",  64),
        "h56":    _ft("arialbd.ttf",  56),
        "h52":    _ft("arialbd.ttf",  52),
        "h48":    _ft("arialbd.ttf",  48),
        "h44":    _ft("arialbd.ttf",  44),
        "h40":    _ft("arialbd.ttf",  40),
        "h43":    _ft("arialbd.ttf",  43),
        "h36":    _ft("arialbd.ttf",  36),
        "bold38": _ft("arialbd.ttf",  38),
        "bold32": _ft("arialbd.ttf",  32),
        "bold31": _ft("arialbd.ttf",  31),
        "bold28": _ft("arialbd.ttf",  28),
        "bold26": _ft("arialbd.ttf",  26),
        "bold24": _ft("arialbd.ttf",  24),
        "bold22": _ft("arialbd.ttf",  22),
        "bold20": _ft("arialbd.ttf",  20),
        "bold18": _ft("arialbd.ttf",  18),
        "bold16": _ft("arialbd.ttf",  16),
        # Regular body sizes
        "h32":    _ft("arial.ttf",    32),
        "h30":    _ft("arial.ttf",    30),
        "h28":    _ft("arial.ttf",    28),
        "h26":    _ft("arial.ttf",    26),
        "h24":    _ft("arial.ttf",    24),
        "h22":    _ft("arial.ttf",    22),
        "h20":    _ft("arial.ttf",    20),
        "h18":    _ft("arial.ttf",    18),
        "h16":    _ft("arial.ttf",    16),
        # Stat display
        "stat_huge":  _ft("arialbd.ttf", 120),
        "stat_large": _ft("arialbd.ttf",  88),
        "stat_med":   _ft("arialbd.ttf",  64),
        # Aliases used by helpers
        "title":   _ft("arialbd.ttf",  52),
        "body":    _ft("arial.ttf",    24),
        "small":   _ft("arial.ttf",    20),
        "pill":    _ft("arialbd.ttf",  22),
        "channel": _ft("arialbd.ttf",  28),
        # ── News-friendly fonts (Georgia serif where available) ──
        "news_label":   _ft("arialbd.ttf",  40),   # bold label  (+25% from bold32)
        "news_body":    _ft("georgiab.ttf", 44),   # body bold   (+22% from h36), falls back to Arial
        "news_body_sm": _ft("georgia.ttf",  40),   # body regular for wrapping lines
        # ── Left-column section fonts (larger, fill content area) ──
        "sec_label":    _ft("arialbd.ttf",  44),   # section header label
        "sec_body":     _ft("georgiab.ttf", 44),   # bullet body text
        "sec_sm":       _ft("georgia.ttf",  40),   # para / secondary text
    }


# ─────────────────────────────────────────────
# HEADER BAR
# ─────────────────────────────────────────────

def _draw_header(draw, img, theme, fonts, date_str, story_num, total_stories):
    header_color = tuple(max(0, c - 15) for c in theme["bg1"])
    draw.rectangle([0, 0, W, Y_HEADER], fill=header_color)

    # Logo
    logo = _load_logo(size=(48, 48))
    if logo:
        try:
            img.paste(logo, (PAD, 12), logo if logo.mode == 'RGBA' else None)
        except Exception:
            img.paste(logo, (PAD, 12))

    draw.text((PAD + 58, 22), "THE AI CHRONICLE", font=fonts["bold28"], fill=(255, 255, 255))

    # Date badge
    badge_text = date_str
    bw = _tw(draw, badge_text, fonts["bold22"]) + 32
    bx = W - PAD - bw
    draw_rounded_rect(draw, (bx, 14, bx + bw, 58), 8, fill=theme["accent"])
    draw.text((bx + 16, 20), badge_text, font=fonts["bold22"], fill=(255, 255, 255))

    # Story counter
    if story_num > 0:
        counter = f"STORY {story_num}/{total_stories}"
        cx = bx - _tw(draw, counter, fonts["bold18"]) - 24
        draw.text((cx, 26), counter, font=fonts["bold18"], fill=theme["text_color"])

    draw.line([(0, Y_HEADER), (W, Y_HEADER)], fill=theme["accent"], width=2)


# ─────────────────────────────────────────────
# CTA BAR
# ─────────────────────────────────────────────

def _draw_cta_bar(draw, img, theme, fonts):
    bar_color = tuple(max(0, c - 10) for c in theme["bg2"])
    draw.rectangle([0, Y_CTA, W, H], fill=bar_color)
    draw.line([(0, Y_CTA), (W, Y_CTA)], fill=theme["accent"], width=2)

    btn_y = Y_CTA + 13
    btn_h = 42

    buttons = [
        ("LIKE",      theme["accent"]),
        ("SHARE",     theme["accent2"]),
        ("SUBSCRIBE", (210, 30, 30)),
    ]
    total_btn_w = sum(_tw(draw, b[0], fonts["bold22"]) + 60 for b in buttons) + 40
    bx = (W - total_btn_w) // 2 - 100

    for label, color in buttons:
        bw = _tw(draw, label, fonts["bold22"]) + 60
        draw_rounded_rect(draw, (bx, btn_y, bx + bw, btn_y + btn_h), 8, fill=color)
        tw = _tw(draw, label, fonts["bold22"])
        draw.text((bx + (bw - tw) // 2, btn_y + 9), label, font=fonts["bold22"], fill=(255, 255, 255))
        bx += bw + 20

    handle = "@theaichronicle007"
    hw = _tw(draw, handle, fonts["bold22"])
    draw.text((W - PAD - hw, btn_y + 9), handle, font=fonts["bold22"], fill=theme["accent"])


# ─────────────────────────────────────────────
# AI BACKGROUND TEXTURE
# ─────────────────────────────────────────────

def _draw_bg_texture(img, theme, seed=42):
    """Subtle AI-themed background: dot grid + node network + corner glows + circuit traces."""
    import random
    rng = random.Random(seed)
    draw = ImageDraw.Draw(img)
    gc = theme["grid_color"]

    # 1. Sparse dot grid (every 90px, very subtle)
    for gx in range(90, W, 90):
        for gy in range(90, H, 90):
            r = rng.randint(1, 3)
            draw.ellipse([gx - r, gy - r, gx + r, gy + r], fill=gc)

    # 2. Node network (16 random nodes connected by thin lines)
    nodes = [(rng.randint(120, W - 120), rng.randint(120, H - 120)) for _ in range(16)]
    for i, (x1, y1) in enumerate(nodes):
        for x2, y2 in nodes[i + 1:i + 3]:
            if ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 < 380:
                draw.line([(x1, y1), (x2, y2)], fill=gc, width=1)
        nr = rng.randint(3, 6)
        draw.ellipse([x1 - nr, y1 - nr, x1 + nr, y1 + nr], fill=gc)

    # 3. Corner glow blobs (accent color, very low intensity)
    img = draw_glow(img, (W - 180, 160), 280, theme["accent"], intensity=0.10)
    img = draw_glow(img, (160, H - 180), 220, theme["accent"], intensity=0.07)

    # 4. L-shaped circuit traces
    draw = ImageDraw.Draw(img)
    for _ in range(5):
        x = rng.randint(PAD, W - PAD - 200)
        y = rng.randint(140, H - 200)
        ln = rng.randint(60, 160)
        lv = rng.randint(30, 70)
        draw.line([(x, y), (x + ln, y)], fill=gc, width=1)
        draw.line([(x + ln, y), (x + ln, y + lv)], fill=gc, width=1)
        draw.ellipse([x + ln - 3, y - 3, x + ln + 3, y + 3], fill=theme["accent"])

    return img


# ─────────────────────────────────────────────
# KEYWORD HIGHLIGHT TEXT
# ─────────────────────────────────────────────

def draw_highlighted_line(draw, x, y, text, font, default_color, highlight_color, keywords):
    """Draw a line of text word-by-word, highlighting keywords in accent color."""
    kw_lower = [k.lower().strip('.,!?:;()-') for k in keywords]
    for word in text.split():
        clean = word.lower().strip('.,!?:;()-')
        color = highlight_color if clean in kw_lower else default_color
        # Shadow
        draw.text((x + 4, y + 4), word, font=font, fill=(0, 0, 0))
        draw.text((x, y), word, font=font, fill=color)
        x += _tw(draw, word + ' ', font)
    return x


# ─────────────────────────────────────────────
# STORIES STRIP (3×3 GRID showing 9 other stories)
# ─────────────────────────────────────────────

def _draw_stories_strip(draw, img, theme, fonts, all_stories, current_idx):
    """3×3 grid of the 9 other stories below the main story area."""
    strip_bg = tuple(max(0, c - 5) for c in theme["bg2"])
    draw.rectangle([0, Y_STRIP, W, Y_CTA], fill=strip_bg)
    draw.line([(0, Y_STRIP), (W, Y_STRIP)], fill=theme["accent"], width=1)

    others = [(i, s) for i, s in enumerate(all_stories) if i != current_idx][:9]
    rows, cols = 3, 3
    row_h = (Y_CTA - Y_STRIP) // rows   # 70px
    col_w = W // cols                    # 640px

    for idx, (orig_idx, story) in enumerate(others):
        row = idx // cols
        col = idx % cols
        ry = Y_STRIP + row * row_h
        rx = col * col_w

        # Alternating row background
        if row % 2 == 1:
            row_bg = tuple(min(255, c + 10) for c in strip_bg)
            draw.rectangle([rx, ry, rx + col_w, ry + row_h], fill=row_bg)

        # Vertical divider between cols
        if col > 0:
            draw.line([(rx, ry), (rx, ry + row_h)], fill=theme["grid_color"], width=1)

        # Story number badge
        num_text = f"#{orig_idx + 1}"
        nw = _tw(draw, num_text, fonts["bold18"])
        draw.text((rx + 10, ry + (row_h - 18) // 2), num_text,
                  font=fonts["bold18"], fill=theme["accent"])

        # Company pill (small)
        company = story["company"][:14]
        pill_x = rx + 10 + nw + 8
        pill_theme = STORY_THEMES[orig_idx % len(STORY_THEMES)]
        px2, _ = _draw_pill(draw, pill_x, ry + (row_h - 28) // 2, company,
                             fonts["bold16"], pill_theme["pill_bg"],
                             (255, 255, 255), radius=6, pad_x=8, pad_y=5)

        # Headline (truncated to fit column)
        hl_x = px2 + 10
        hl_max = rx + col_w - hl_x - 10
        hl_text = story["headline"]
        while hl_text and _tw(draw, hl_text, fonts["h20"]) > hl_max:
            hl_text = hl_text.rsplit(" ", 1)[0] + "…"
        draw.text((hl_x, ry + (row_h - 20) // 2), hl_text,
                  font=fonts["h20"], fill=(255, 255, 255))

        # Row separator
        if row < rows - 1:
            draw.line([(rx + 8, ry + row_h), (rx + col_w - 8, ry + row_h)],
                      fill=theme["grid_color"], width=1)


# ─────────────────────────────────────────────
# MAIN STORY SLIDE RENDERER
# ─────────────────────────────────────────────

def render_story_slide(draw, img, story, theme, fonts, date_str,
                       story_num, total_stories, all_stories=None, story_idx=0):
    """
    Renders one story slide with full narrative layout:
    Header | Subtitle | HOOK (big, keyword-highlighted) | Pills
    | Left: What Happened + Why It Matters + What's Next
    | Right: Stat Card
    | Stories Strip (3×3 grid) | CTA Bar
    """
    # 1. Background gradient
    draw_gradient_rect(img, (0, 0, W, H), theme["bg1"], theme["bg2"], "vertical")
    draw = ImageDraw.Draw(img)

    # 2. AI background texture (subtle)
    img = _draw_bg_texture(img, theme, seed=story_idx * 17 + 3)
    draw = ImageDraw.Draw(img)

    # 3. CTA bar
    _draw_cta_bar(draw, img, theme, fonts)

    # 5. Header
    _draw_header(draw, img, theme, fonts, date_str, story_num, total_stories)

    # 6. Subtitle bar (Y_HEADER to Y_SUB) — region flag only
    sub_bg = tuple(min(255, c + 8) for c in theme["bg1"])
    draw.rectangle([0, Y_HEADER, W, Y_SUB], fill=sub_bg)
    region_str = story.get("region", "") + "  " + story.get("region_name", "").upper()
    rw = _tw(draw, region_str, fonts["bold20"])
    draw.text((W - PAD - rw, Y_HEADER + 12), region_str,
              font=fonts["bold20"], fill=theme["text_color"])

    # 7. HOOK text — big, ALL CAPS, hero word(s) at +20% font, centered in zone
    hook_text = story.get("hook", story["headline"]).upper()

    # Auto-size base font to fit in 2 lines
    hook_font = fonts["h88"]
    for fk in ["h88", "h72", "h64", "h56", "h48", "h44", "h40", "h36"]:
        fnt = fonts[fk]
        if len(wrap_text(hook_text, fnt, W - PAD * 2, draw)) <= 2:
            hook_font = fnt
            break

    # Hero font: 20% bigger than hook_font, clamped to available sizes
    _hero_size = int(hook_font.size * 1.2)
    _hero_key  = min(
        ["h96", "h88", "h80", "h72", "h64", "h56", "h48"],
        key=lambda k: abs(fonts[k].size - _hero_size)
    )
    hero_font = fonts[_hero_key]

    # Identify hero words: numbers first, then first 2 significant stop-filtered words
    _stop = {"a", "an", "the", "to", "of", "in", "is", "are", "and", "for",
             "with", "at", "by", "as", "on", "its", "from", "that", "this"}
    _words_upper = hook_text.split()
    _hero_words  = set()
    # Pass 1: any word containing a digit
    for w in _words_upper:
        if any(c.isdigit() for c in w):
            _hero_words.add(w.strip(".,!?:;()-"))
    # Pass 2: if no numbers found, pick first 2 significant words
    if not _hero_words:
        _sig = [w for w in _words_upper if w.strip(".,!?:;()-").lower() not in _stop]
        _hero_words = {w.strip(".,!?:;()-") for w in _sig[:2]}

    def _draw_hook_line(draw, x, y, text, base_font, hero_font, hero_words,
                        base_color, hero_color):
        """Render one hook line word-by-word; hero words are bigger + accent coloured."""
        line_h = max(_th(draw, "A", base_font), _th(draw, "A", hero_font))
        right_limit = W - PAD
        for word in text.split():
            word_w = _tw(draw, word, hero_font if word.strip(".,!?:;()-") in hero_words else base_font)
            if x + word_w > right_limit:
                break   # never draw a word that starts beyond the safe right edge
            clean = word.strip(".,!?:;()-")
            is_hero = clean in hero_words
            f     = hero_font if is_hero else base_font
            color = hero_color if is_hero else base_color
            # Baseline-align: shift smaller words down so bottoms align
            offset_y = line_h - _th(draw, word, f)
            draw.text((x + 4, y + offset_y + 4), word, font=f, fill=(0, 0, 0))
            draw.text((x,     y + offset_y),     word, font=f, fill=color)
            x += _tw(draw, word + " ", f)
        return line_h

    # Wrap using hero_font (worst-case width) so hero words never overflow right edge
    lines = wrap_text(hook_text, hero_font, W - PAD * 2, draw)[:2]

    # Measure total block height for vertical centering in hook zone
    _line_h = max(_th(draw, "A", hook_font), _th(draw, "A", hero_font))
    _gap    = 12
    _block_h = len(lines) * _line_h + (len(lines) - 1) * _gap + 20  # +20 for underline
    hook_zone_h = Y_PILLS - Y_HOOK
    hy = Y_HOOK + max(0, (hook_zone_h - _block_h) // 2)

    for line in lines:
        lh = _draw_hook_line(draw, PAD, hy, line, hook_font, hero_font,
                             _hero_words, theme["headline_color"], theme["accent"])
        hy += lh + _gap

    # Accent underline below hook
    draw.line([(PAD, hy + 4), (min(W - PAD, PAD + 900), hy + 4)],
              fill=theme["accent"], width=3)

    # 8. Pills row (Y_PILLS area, capped to avoid overflow)
    pills_y = min(hy + 16, Y_PILLS)
    pill_x = PAD

    company_text = story["company"][:22]
    px2, py2 = _draw_pill(draw, pill_x, pills_y, company_text, fonts["bold22"],
                           theme["pill_bg"], (255, 255, 255), radius=10, pad_x=16, pad_y=8)
    pill_x = px2 + 14

    source_text = story["source"][:24]
    px2, py2 = _draw_pill(draw, pill_x, pills_y, source_text, fonts["bold20"],
                           theme["accent2"], (255, 255, 255), radius=10, pad_x=14, pad_y=8)

    # 9. Content area (Y_CONTENT to Y_CTA)
    content_y = max(py2 + 14, Y_CONTENT)
    left_w  = 940
    right_x = left_w + 24
    right_w = W - PAD - right_x   # ~856px
    card_x  = right_x
    card_y  = content_y
    card_h  = Y_CTA - card_y - 10
    card_w  = right_w

    # ── RIGHT COLUMN: Background image card ───────────────────
    bg_paths = sorted(p for p in (Path(__file__).parent.parent / "backgrounds").iterdir()
                      if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".jfif"}
                      ) if (Path(__file__).parent.parent / "backgrounds").exists() else []
    if bg_paths:
        try:
            bg_img = Image.open(bg_paths[story_idx % len(bg_paths)]).convert("RGB")
            ratio  = bg_img.width / bg_img.height
            tile_r = card_w / card_h
            if ratio > tile_r:
                new_h, new_w = card_h, int(ratio * card_h)
            else:
                new_w, new_h = card_w, int(card_w / ratio)
            bg_img = bg_img.resize((new_w, new_h), Image.LANCZOS)
            left_c = (new_w - card_w) // 2
            top_c  = (new_h - card_h) // 2
            bg_crop = bg_img.crop((left_c, top_c, left_c + card_w, top_c + card_h))

            # Rounded-corner mask
            mask = Image.new("L", (card_w, card_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, card_w, card_h], radius=20, fill=255)
            img.paste(bg_crop, (card_x, card_y), mask)

            # Dark overlay for contrast
            arr = np.array(img)
            r = arr[card_y:card_y + card_h, card_x:card_x + card_w].astype(np.float32)
            r = r * 0.38
            arr[card_y:card_y + card_h, card_x:card_x + card_w] = np.clip(r, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr)
            draw = ImageDraw.Draw(img)

            # Accent glow over image
            img = draw_glow(img, (card_x + card_w // 2, card_y + card_h // 2),
                            240, theme["accent"], intensity=0.18)
            draw = ImageDraw.Draw(img)

            # Accent border
            draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                                   radius=20, outline=theme["accent"], width=2)
        except Exception:
            bg_paths = []   # fall through to plain card

    if not bg_paths:
        draw_rounded_rect(draw, (card_x, card_y, card_x + card_w, card_y + card_h),
                          20, fill=theme["stat_bg"], outline=theme["accent"], outline_width=2)
        img = draw_glow(img, (card_x + card_w // 2, card_y + card_h // 2),
                        200, theme["accent"], intensity=0.15)
        draw = ImageDraw.Draw(img)

    # Stat value overlaid on image/card
    sv      = story["stat_value"]
    sv_font = fonts["stat_large"]
    for _sv_fk in ("stat_large", "stat_med", "bold38", "bold28"):
        if _tw(draw, sv, fonts[_sv_fk]) <= card_w - 40:
            sv_font = fonts[_sv_fk]
            break
    sv_w    = _tw(draw, sv, sv_font)
    sv_y    = card_y + 30
    # Shadow for contrast
    draw.text((card_x + (card_w - sv_w) // 2 + 4, sv_y + 4), sv, font=sv_font, fill=(0, 0, 0))
    draw.text((card_x + (card_w - sv_w) // 2, sv_y), sv, font=sv_font, fill=theme["accent"])

    sl = story["stat_label"]
    while sl and _tw(draw, sl, fonts["bold28"]) > card_w - 20:
        sl = sl[:-1]
    if sl != story["stat_label"]:
        sl = sl.rstrip() + "\u2026"
    sl_w = _tw(draw, sl, fonts["bold28"])
    sl_y = sv_y + _th(draw, sv, sv_font) + 10
    draw.text((card_x + (card_w - sl_w) // 2 + 2, sl_y + 2), sl, font=fonts["bold28"], fill=(0, 0, 0))
    draw.text((card_x + (card_w - sl_w) // 2, sl_y), sl, font=fonts["bold28"], fill=(255, 255, 255))

    wm   = story.get("watermark", "")
    wm_w = _tw(draw, wm, fonts["bold28"])
    wm_y = card_y + card_h - 60
    draw.text((card_x + (card_w - wm_w) // 2 + 2, wm_y + 2), wm, font=fonts["bold28"], fill=(0, 0, 0))
    draw.text((card_x + (card_w - wm_w) // 2, wm_y), wm, font=fonts["bold28"], fill=theme["accent2"])

    # ── LEFT COLUMN: Narrative structure ──────────────────────
    cy       = content_y
    txt_max  = left_w - PAD
    # Hard bottom boundary — never draw below the stories strip
    bottom_y = Y_CTA - 10   # full content area — strip is not drawn on story slides

    # ── Font aliases for this section ──
    _lbl_fn  = fonts["sec_label"]   # arialbd 46px  — header label + arrow
    _body_fn = fonts["sec_body"]    # georgiab 46px — bullet body
    _sm_fn   = fonts["sec_sm"]      # georgia  42px — para text

    # Emoji font for section icons (Segoe UI Emoji on Windows)
    _ef = None
    for _ef_name in ["seguiemj.ttf", "seguisym.ttf"]:
        _ef_path = Path("C:/Windows/Fonts") / _ef_name
        if _ef_path.exists():
            try:
                _ef = ImageFont.truetype(str(_ef_path), 44)
                break
            except Exception:
                pass

    def _section_header(emoji, label, color):
        """Emoji + bold label row."""
        nonlocal cy, draw
        if cy >= bottom_y:
            return
        x = PAD
        if _ef:
            try:
                lh  = _th(draw, label, _lbl_fn)
                eh  = _th(draw, emoji, _ef)
                edy = max(0, (lh - eh) // 2)
                draw.text((x, cy + edy), emoji, font=_ef, fill=color)
                x += _tw(draw, emoji, _ef) + 12
            except Exception:
                pass
        else:
            r     = 10
            mid_y = cy + _th(draw, "A", _lbl_fn) // 2
            draw.ellipse([x, mid_y - r, x + r * 2, mid_y + r], fill=color)
            x += r * 2 + 14
        draw.text((x + 2, cy + 2), label, font=_lbl_fn, fill=(0, 0, 0))
        draw.text((x, cy),         label, font=_lbl_fn, fill=color)
        cy += _th(draw, label, _lbl_fn) + 24
        if cy > bottom_y:
            cy = bottom_y

    def _bullet(text, color):
        """Single-line arrow bullet — punchy fact."""
        nonlocal cy, draw
        if cy >= bottom_y:
            return
        b = str(text).strip()
        if not b:
            return
        arrow   = "\u25ba  "
        arrow_w = _tw(draw, arrow, _lbl_fn)
        bx      = PAD + 24
        lines   = wrap_text(b, _body_fn, txt_max - 24 - arrow_w, draw)
        line    = lines[0] if lines else b
        lh      = _th(draw, line, _body_fn)
        arr_h   = _th(draw, arrow, _lbl_fn)
        arr_dy  = max(0, (lh - arr_h) // 2)
        draw.text((bx + 2, cy + arr_dy + 2), arrow, font=_lbl_fn,  fill=(0, 0, 0))
        draw.text((bx, cy + arr_dy),          arrow, font=_lbl_fn,  fill=color)
        draw.text((bx + arrow_w + 2, cy + 2), line,  font=_body_fn, fill=(0, 0, 0))
        draw.text((bx + arrow_w, cy),          line,  font=_body_fn, fill=(255, 255, 255))
        cy += lh + 20
        if cy > bottom_y:
            cy = bottom_y

    def _para(text, color, max_lines=1):
        """Paragraph — fills remaining space after gap calculation."""
        nonlocal cy, draw
        if cy >= bottom_y:
            return
        lines = wrap_text(str(text), _sm_fn, txt_max - 24, draw)[:max_lines]
        for line in lines:
            if cy >= bottom_y:
                break
            lh = _th(draw, line, _sm_fn)
            draw.text((PAD + 26, cy + 2), line, font=_sm_fn, fill=(0, 0, 0))
            draw.text((PAD + 24, cy),     line, font=_sm_fn, fill=color)
            cy += lh + 16

    import re as _re

    # ── WHAT HAPPENED ─────────────────────────────────────────
    _section_header("\U0001f4f0", "WHAT HAPPENED", theme["accent"])

    bullets_raw = story.get("what_happened", story.get("body", []))[:3]
    seen_keys = []
    for b in bullets_raw:
        b = str(b).strip()
        if not b:
            continue
        key = _re.sub(r'\W+', ' ', b[:40].lower()).strip()
        if key not in seen_keys:
            seen_keys.append(key)
            _bullet(b, theme["accent"])

    # ── Distribute remaining space evenly between WHY and WHAT'S NEXT ──
    # Match the updated spacing used in _section_header and _para
    _lh_hdr = _th(draw, "Ag", _lbl_fn) + 24   # header height  (matches +24 in _section_header)
    _lh_sm  = _th(draw, "Ag", _sm_fn)  + 16   # para line height (matches +16 in _para)

    # Each of the 2 sections uses: header + 1 para line
    # Remaining budget: split equally into 2 gaps
    _n_para_lines = 2
    _used = 2 * _lh_hdr + 2 * _n_para_lines * _lh_sm
    _gap  = max(8, (bottom_y - cy - _used) // 2)

    cy += _gap

    # ── WHY IT MATTERS ────────────────────────────────────────
    _section_header("\U0001f4a1", "WHY IT MATTERS", theme["accent"])
    wim = story.get("why_it_matters", story.get("impact", ""))
    _para(wim, theme["text_color"], max_lines=_n_para_lines)

    cy += _gap

    # ── WHAT'S NEXT ───────────────────────────────────────────
    _section_header("\U0001f680", "WHAT'S NEXT", theme["accent2"])
    nxt = story.get("whats_next", "")
    _para(nxt, theme["accent"], max_lines=_n_para_lines)

    return img


# ─────────────────────────────────────────────
# SLIDE ENTRY POINT
# ─────────────────────────────────────────────

def render_slide(story, theme, fonts, date_str, story_num, total_stories,
                 all_stories=None, story_idx=0):
    img  = Image.new("RGB", (W, H), theme["bg1"])
    draw = ImageDraw.Draw(img)
    img = render_story_slide(draw, img, story, theme, fonts, date_str,
                             story_num, total_stories, all_stories, story_idx)
    return img


# ─────────────────────────────────────────────
# INTRO SLIDE
# ─────────────────────────────────────────────
# THUMBNAIL SLIDE (1920×1080 title card — first 3 seconds of video)
# ─────────────────────────────────────────────

def render_thumbnail_slide(stories, date_str, fonts):
    """1920×1080 title card for the opening 3 seconds of the video."""
    theme = STORY_THEMES[0]
    story = stories[0]

    img = Image.new("RGB", (W, H), theme["bg1"])
    draw_gradient_rect(img, (0, 0, W, H), theme["bg1"], theme["bg2"], "vertical")
    img = draw_glow(img, (W // 2, H // 2), 600, theme["accent"], intensity=0.12)
    img = draw_glow(img, (200, 200), 350, theme["accent2"], intensity=0.08)
    draw = ImageDraw.Draw(img)

    # ── Top bar ───────────────────────────────────────────────────────
    bar_h = 80
    bar_color = tuple(max(0, c - 15) for c in theme["bg1"])
    draw.rectangle([0, 0, W, bar_h], fill=bar_color)
    draw.line([(0, bar_h), (W, bar_h)], fill=theme["accent"], width=3)

    # Logo
    logo = _load_logo(size=(56, 56))
    if logo:
        try:
            img.paste(logo, (PAD, 12), logo if logo.mode == "RGBA" else None)
        except Exception:
            img.paste(logo, (PAD, 12))

    # Channel name
    draw.text((PAD + 68, 22), "THE AI CHRONICLE", font=fonts["bold28"], fill=(255, 255, 255))

    # Date badge top-right
    date_badge = date_str.upper()
    dbw = _tw(draw, date_badge, fonts["bold20"])
    badge_x = W - PAD - dbw - 24
    draw_rounded_rect(draw, (badge_x - 12, 18, badge_x + dbw + 12, 62), 8, fill=theme["accent"])
    draw.text((badge_x, 26), date_badge, font=fonts["bold20"], fill=(0, 0, 0))

    # ── Subtitle strip ────────────────────────────────────────────────
    sub_y = bar_h + 4
    sub_h = 50
    sub_color = tuple(min(255, c + 10) for c in theme["bg1"])
    draw.rectangle([0, sub_y, W, sub_y + sub_h], fill=sub_color)
    draw.text((PAD, sub_y + 10), "TODAY'S TOP 10 AI STORIES",
              font=fonts["bold22"], fill=theme["accent"])

    # ── Main headline (hook) ──────────────────────────────────────────
    hook = story.get("hook", story["headline"]).upper()
    keywords = [k.upper() for k in story.get("keywords", [])]

    hook_y = sub_y + sub_h + 50
    hook_font = fonts["h88"]
    for fk in ["h88", "h72", "h64", "h56", "h48"]:
        fnt = fonts[fk]
        lines = wrap_text(hook, fnt, W - PAD * 2, draw)
        if len(lines) <= 2:
            hook_font = fnt
            break

    hook_lines = wrap_text(hook, hook_font, W - PAD * 2, draw)[:2]
    line_h = hook_font.size + 16
    for li, line in enumerate(hook_lines):
        draw_highlighted_line(draw, PAD, hook_y + li * line_h, line,
                              hook_font, (255, 255, 255), theme["accent"], keywords)

    # ── Company + source pills ────────────────────────────────────────
    pill_y = hook_y + len(hook_lines) * line_h + 28
    px, _ = _draw_pill(draw, PAD, pill_y, story["company"][:22], fonts["bold22"],
                       theme["pill_bg"], (255, 255, 255), radius=10, pad_x=18, pad_y=8)
    _draw_pill(draw, px + 16, pill_y, story.get("source", "")[:22], fonts["bold22"],
               theme["accent2"], (0, 0, 0), radius=10, pad_x=18, pad_y=8)

    # ── Stat card (right side) ────────────────────────────────────────
    card_x = W // 2 + 60
    card_y = sub_y + sub_h + 30
    card_w = W - PAD - card_x
    card_h = H - card_y - 100

    draw_rounded_rect(draw, (card_x, card_y, card_x + card_w, card_y + card_h), 20,
                      fill=tuple(max(0, c - 5) for c in theme["bg2"]),
                      outline=theme["accent"], outline_width=2)

    stat_val = story.get("stat_value", "")
    sv_font = fonts["stat_huge"]
    svw = _tw(draw, stat_val, sv_font)
    if svw > card_w - 20:
        sv_font = fonts["bold48"] if "bold48" in fonts else fonts["h48"]
    svw = _tw(draw, stat_val, sv_font)
    draw.text((card_x + (card_w - svw) // 2, card_y + 40), stat_val,
              font=sv_font, fill=theme["accent"])

    stat_label = story.get("stat_label", "").upper()
    slw = _tw(draw, stat_label, fonts["bold22"])
    sv_h = _th(draw, stat_val, sv_font)
    draw.text((card_x + (card_w - slw) // 2, card_y + 40 + sv_h + 10), stat_label,
              font=fonts["bold22"], fill=theme["text_color"])

    wm = story.get("watermark", "")
    wmw = _tw(draw, wm, fonts["bold24"])
    draw.text((card_x + (card_w - wmw) // 2, card_y + card_h - 60), wm,
              font=fonts["bold24"], fill=theme["accent2"])

    # ── Region flag + name ────────────────────────────────────────────
    region_str = story.get("region", "") + "  " + story.get("region_name", "").upper()
    rw = _tw(draw, region_str, fonts["bold20"])
    draw.text((W - PAD - rw, sub_y + 60), region_str,
              font=fonts["bold20"], fill=theme["text_color"])

    # ── Bottom bar ────────────────────────────────────────────────────
    _draw_cta_bar(draw, img, theme, fonts)

    return img


# ─────────────────────────────────────────────

def _load_intro_backgrounds():
    """Load up to 4 background images from youtube-improve/backgrounds/.
    Accepts any filename and any common image extension including .jfif.
    Returns a list of PIL Images (may be empty if no files found)."""
    bg_dir = Path(__file__).parent.parent / "backgrounds"
    if not bg_dir.exists():
        return []
    exts = {".jpg", ".jpeg", ".png", ".webp", ".jfif"}
    files = sorted(p for p in bg_dir.iterdir()
                   if p.suffix.lower() in exts)
    images = []
    for p in files[:4]:
        try:
            images.append(Image.open(p).convert("RGB"))
        except Exception:
            pass
    return images


def _build_mosaic_background(bg_images):
    """Tile up to 4 images into a 1920×1080 2×2 mosaic with a dark overlay."""
    mosaic = Image.new("RGB", (W, H), (10, 10, 30))
    tile_w, tile_h = W // 2, H // 2
    positions = [(0, 0), (tile_w, 0), (0, tile_h), (tile_w, tile_h)]
    for i, bg in enumerate(bg_images[:4]):
        # Scale to fill tile (crop-to-fill)
        bg_ratio = bg.width / bg.height
        tile_ratio = tile_w / tile_h
        if bg_ratio > tile_ratio:
            new_h = tile_h
            new_w = int(bg_ratio * tile_h)
        else:
            new_w = tile_w
            new_h = int(tile_w / bg_ratio)
        bg_resized = bg.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - tile_w) // 2
        top  = (new_h - tile_h) // 2
        bg_crop = bg_resized.crop((left, top, left + tile_w, top + tile_h))
        mosaic.paste(bg_crop, positions[i])

    # Dark overlay so text stays readable (90% opacity black)
    overlay = Image.new("RGB", (W, H), (0, 0, 0))
    mosaic = Image.blend(mosaic, overlay, alpha=0.90)
    return mosaic


def render_intro_slide(stories, date_str, fonts):
    theme = STORY_THEMES[0]

    # ── Background: mosaic of real images or plain gradient ───
    bg_images = _load_intro_backgrounds()
    if len(bg_images) >= 1:
        img = _build_mosaic_background(bg_images)
        # Subtle accent glow on top
        img = draw_glow(img, (W // 2, H // 2), 700, theme["accent"], intensity=0.06)
    else:
        img = Image.new("RGB", (W, H), theme["bg1"])
        draw_gradient_rect(img, (0, 0, W, H), theme["bg1"], theme["bg2"], "vertical")
        img = _draw_bg_texture(img, theme, seed=1)

    draw = ImageDraw.Draw(img)
    _draw_cta_bar(draw, img, theme, fonts)
    _draw_header(draw, img, theme, fonts, date_str, 0, 0)

    # ── Title + date at top ───────────────────────────────────
    title_y = Y_HEADER + 14
    draw.text((PAD, title_y), "TODAY'S TOP 10 AI STORIES",
              font=fonts["h64"], fill=(255, 255, 255))
    date_display = date_str.upper()
    draw.text((PAD, title_y + 76), date_display,
              font=fonts["h40"], fill=theme["accent"])
    div_y = title_y + 76 + 52
    draw.line([(PAD, div_y), (W - PAD, div_y)], fill=theme["accent"], width=3)

    # ── Two-column story list (5 per column) ──────────────────
    gap      = 52
    col_w    = (W - PAD * 2 - gap) // 2       # ~904px
    col_x    = [PAD, PAD + col_w + gap]
    rows     = 5
    badge_sz = 72                               # +20% from 60
    hl_font  = fonts["h43"]                     # +20% from h36
    badge_fn = fonts["bold38"]                  # +20% from bold32
    comp_fn  = fonts["bold31"]                  # +20% from bold26
    line_h   = 52                               # line height for headlines

    # Measure total block height to vertically centre in available zone
    avail_h   = Y_CTA - (div_y + 16)
    row_h     = avail_h // rows
    block_h   = rows * row_h
    list_top  = div_y + 16 + (avail_h - block_h) // 2

    def _draw_highlighted_headline(draw, x, y, text, font, accent_col, max_w):
        """Draw headline with first 2 words in accent colour, rest in white."""
        words = text.split()
        if len(words) <= 2:
            # Short headline — highlight entirely
            draw.text((x, y), text, font=font, fill=accent_col)
            return
        highlight = " ".join(words[:2])
        rest      = " ".join(words[2:])
        hw = _tw(draw, highlight + " ", font)
        # Check if highlight + rest fits on one line; if not, wrap normally
        full_lines = wrap_text(text, font, max_w, draw)[:2]
        if len(full_lines) == 1:
            draw.text((x, y), highlight, font=font, fill=accent_col)
            draw.text((x + hw, y), rest, font=font, fill=(255, 255, 255))
        else:
            # Multi-line: highlight first line in accent, second in white
            draw.text((x, y),          full_lines[0], font=font, fill=accent_col)
            draw.text((x, y + line_h), full_lines[1], font=font, fill=(255, 255, 255))

    for i, s in enumerate(stories[:10]):
        col = i // rows
        row = i % rows
        cx  = col_x[col]
        ry  = list_top + row * row_h

        badge_theme = STORY_THEMES[i % len(STORY_THEMES)]

        # Row separator
        if row > 0:
            draw.line([(cx, ry), (cx + col_w, ry)],
                      fill=(255, 255, 255, 40), width=1)

        # Number badge — vertically centred in row
        badge  = f"{i + 1:02d}"
        bdg_y  = ry + (row_h - badge_sz) // 2
        draw_rounded_rect(draw,
                          (cx, bdg_y, cx + badge_sz, bdg_y + badge_sz), 14,
                          fill=badge_theme["accent"])
        bw = _tw(draw, badge, badge_fn)
        bh = _th(draw, badge, badge_fn)
        draw.text((cx + (badge_sz - bw) // 2, bdg_y + (badge_sz - bh) // 2),
                  badge, font=badge_fn,
                  fill=(0, 0, 0) if sum(badge_theme["accent"]) > 400 else (255, 255, 255))

        # Text block: company pill + headline, vertically centred in row
        text_x   = cx + badge_sz + 16
        hl_max   = col_w - badge_sz - 16
        hl_lines = wrap_text(s["headline"], hl_font, hl_max, draw)[:2]
        pill_h   = _th(draw, "A", comp_fn) + 16   # approx pill height
        text_h   = pill_h + 8 + len(hl_lines) * line_h
        text_y   = ry + (row_h - text_h) // 2

        # Company pill
        _draw_pill(draw, text_x, text_y, s["company"][:22], comp_fn,
                   badge_theme["pill_bg"], (255, 255, 255), radius=10, pad_x=16, pad_y=8)

        # Highlighted headline
        hl_y = text_y + pill_h + 8
        _draw_highlighted_headline(draw, text_x, hl_y, s["headline"],
                                   hl_font, badge_theme["accent"], hl_max)

    return img


# ─────────────────────────────────────────────
# OUTRO SLIDE
# ─────────────────────────────────────────────

def render_outro_slide(stories, date_str, fonts):
    theme = STORY_THEMES[9]
    img   = Image.new("RGB", (W, H), theme["bg1"])
    draw_gradient_rect(img, (0, 0, W, H), theme["bg1"], theme["bg2"], "vertical")
    img = _draw_bg_texture(img, theme, seed=99)
    draw = ImageDraw.Draw(img)

    _draw_cta_bar(draw, img, theme, fonts)
    _draw_header(draw, img, theme, fonts, date_str, 0, 0)

    # Centered content
    for y, text, font_key, color in [
        (150, "THAT'S A WRAP",                          "h80",    (255, 255, 255)),
        (258, "@theaichronicle007",                     "h52",    theme["accent"]),
        (335, "DAILY AI NEWS FROM AROUND THE WORLD",    "h28",    theme["text_color"]),
        (390, "NEW VIDEOS EVERY DAY",                   "h24",    theme["text_color"]),
    ]:
        fnt = fonts[font_key]
        tw  = _tw(draw, text, fnt)
        _draw_text_shadow(draw, ((W - tw) // 2, y), text, fnt, color)

    # SUBSCRIBE button
    sub_bw, sub_bh = 320, 60
    sub_bx = (W - sub_bw) // 2
    draw_rounded_rect(draw, (sub_bx, 460, sub_bx + sub_bw, 460 + sub_bh), 12, fill=(210, 30, 30))
    slabel = "SUBSCRIBE NOW"
    slw = _tw(draw, slabel, fonts["bold28"])
    draw.text((sub_bx + (sub_bw - slw) // 2, 475), slabel, font=fonts["bold28"],
              fill=(255, 255, 255))

    # Logo
    logo = _load_logo(size=(80, 80))
    if logo:
        lx = (W - 80) // 2
        try:
            img.paste(logo, (lx, 550), logo if logo.mode == 'RGBA' else None)
        except Exception:
            img.paste(logo, (lx, 550))

    return img


def _render_support_slide(date_str, fonts):
    theme = STORY_THEMES[5]   # indigo night — dark professional
    img   = Image.new("RGB", (W, H), theme["bg1"])
    draw_gradient_rect(img, (0, 0, W, H), theme["bg1"], theme["bg2"], "vertical")
    img  = _draw_bg_texture(img, theme, seed=55)
    img  = draw_glow(img, (W // 2, H // 2), 550, theme["accent"], intensity=0.12)
    draw = ImageDraw.Draw(img)
    _draw_header(draw, img, theme, fonts, date_str, 0, 0)
    _draw_cta_bar(draw, img, theme, fonts)

    content = [
        (180,  "SUPPORT THE SHOW",                                    "h80",    (255, 255, 255)),
        (310,  "Please Like  \u00b7  Follow  \u00b7  Subscribe",      "h52",    theme["accent"]),
        (390,  "Comment  \u00b7  Share",                              "h52",    theme["accent"]),
        (490,  "Help us make AI knowledge reachable for more people.", "h32",    theme["text_color"]),
        (542,  "Your support helps us produce better quality news.",   "h32",    theme["text_color"]),
    ]
    for y, text, fk, color in content:
        fnt = fonts.get(fk, fonts["h44"])
        tw  = _tw(draw, text, fnt)
        _draw_text_shadow(draw, ((W - tw) // 2, y), text, fnt, color)

    # Accent divider below title
    draw.line([(W // 2 - 320, 272), (W // 2 + 320, 272)], fill=theme["accent"], width=3)

    # Logo
    logo = _load_logo(size=(80, 80))
    if logo:
        lx = (W - 80) // 2
        try:
            img.paste(logo, (lx, 610), logo if logo.mode == "RGBA" else None)
        except Exception:
            img.paste(logo, (lx, 610))
    return img


# ─────────────────────────────────────────────
# VIDEO COMPOSITION
# ─────────────────────────────────────────────

def compose_video(png_paths, tts_paths, durations, out_mp4):
    assert len(png_paths) == len(tts_paths) == len(durations)

    n = len(png_paths)
    logger.info(f"[VIDEO] Composing {n} slides, total ~{sum(durations):.1f}s")

    inputs = []
    for png, dur in zip(png_paths, durations):
        inputs += ["-loop", "1", "-t", str(dur), "-i", str(png)]
    for mp3 in tts_paths:
        inputs += ["-i", str(mp3)]

    fade_dur = 0.4
    vfilter_parts = []
    for i in range(n):
        vfilter_parts.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v{i}]"
        )

    if n == 1:
        vfilter_parts.append("[v0]copy[vout]")
    else:
        chain  = "[v0]"
        offset = 0.0
        for i in range(1, n):
            offset += durations[i - 1] - fade_dur
            offset  = max(0.0, offset)
            next_v  = f"[v{i}]"
            out_lbl = f"[xf{i}]" if i < n - 1 else "[vout]"
            vfilter_parts.append(
                f"{chain}{next_v}xfade=transition=fade:duration={fade_dur}:offset={offset:.3f}{out_lbl}"
            )
            chain = out_lbl if i < n - 1 else ""

    audio_inputs = "".join(f"[{n + j}:a]" for j in range(n))
    vfilter_parts.append(f"{audio_inputs}concat=n={n}:v=0:a=1[aout]")

    filter_complex = "; ".join(vfilter_parts)

    cmd = (
        [FFMPEG_BIN, "-y"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k",
            "-r", "30", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_mp4),
        ]
    )

    logger.info(f"[VIDEO] FFmpeg: {' '.join(cmd[:18])}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if result.returncode != 0:
        logger.error(f"[VIDEO] FFmpeg stderr:\n{result.stderr[-3000:]}")
        raise RuntimeError(f"FFmpeg failed (exit {result.returncode})")

    logger.info(f"[VIDEO] Output: {out_mp4} ({out_mp4.stat().st_size // 1024} KB)")
    return out_mp4


# ─────────────────────────────────────────────
# METADATA WRITER
# ─────────────────────────────────────────────

def write_metadata(stories, date_str, video_path, thumb_a_path, thumb_b_path, out_dir):
    title = stories[0]["titles"][0] if stories[0].get("titles") else stories[0]["headline"]
    title = title[:100]

    lead = (f"Today on The AI Chronicle: {stories[0]['headline']}. "
            f"Plus {len(stories)-1} more top AI stories from {date_str}.")[:150]

    desc_lines = [lead, "", "📋 TODAY'S 10 STORIES:", ""]

    t = 15
    timestamps = ["0:00 Introduction"]
    for i, s in enumerate(stories[:10], 1):
        ts = f"{t // 60}:{t % 60:02d}"
        timestamps.append(f"{ts} Story {i}: {s['headline']}")
        desc_lines.append(f"{ts}  Story {i}: {s['headline']} {s['region']}")
        t += 55

    desc_lines += ["", "📰 SOURCES:"]
    for s in stories[:10]:
        desc_lines.append(f"  • {s['company']} — {s['source']}")

    desc_lines += [
        "",
        "🔔 Subscribe for daily AI news: @theaichronicle007",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    all_tags = []
    for s in stories[:10]:
        all_tags.extend(s.get("hashtags", []))
    desc_lines.append(" ".join(list(dict.fromkeys(all_tags))[:25]))

    description = "\n".join(desc_lines)[:5000]

    tag_list = [s["company"] for s in stories[:10]]
    tag_list += ["AI News", "Artificial Intelligence", "Machine Learning",
                 "The AI Chronicle", "AINews", "TechNews"]
    tag_list = list(dict.fromkeys(tag_list))[:35]

    txt_path = out_dir / "yt_meta.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"TITLE: {title}\n\n")
        f.write(f"DESCRIPTION:\n{description}\n\n")
        f.write(f"TAGS: {', '.join(tag_list)}\n\n")
        f.write("TIMESTAMPS:\n")
        for ts in timestamps:
            f.write(f"  {ts}\n")
        f.write(f"\nTHUMBNAIL_A: {thumb_a_path}\n")
        f.write(f"THUMBNAIL_B: {thumb_b_path}\n")

    json_path = out_dir / "yt_metadata.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp":    datetime.now().isoformat(),
            "date_str":     date_str,
            "title":        title,
            "description":  description,
            "youtube_tags": tag_list,
            "timestamps":   timestamps,
            "video_path":   str(video_path),
            "thumbnail_a":  str(thumb_a_path),
            "thumbnail_b":  str(thumb_b_path),
            "stories":      stories,
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"[META] Written: {txt_path.name}, {json_path.name}")
    return txt_path, json_path


# ─────────────────────────────────────────────
# MAIN GENERATE FUNCTION
# ─────────────────────────────────────────────

def generate(stories: list) -> dict:
    """Generate a YouTube video from up to 10 stories. Returns dict of output paths."""
    from tts_engine import generate_story_tts, get_audio_duration
    from thumbnail_generator import generate_thumbnail_a, generate_thumbnail_b

    date_str = datetime.now().strftime("%B %d, %Y")
    slug     = stories[0]["company"].lower().replace(" ", "_")[:12]
    dir_name = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{slug}"
    post_dir = OUTPUT_DIR / dir_name
    post_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = post_dir / "temp"
    temp_dir.mkdir(exist_ok=True)

    logger.info(f"\n{'='*60}")
    logger.info(f"GENERATING VIDEO: {dir_name}")
    logger.info(f"Stories: {len(stories)}")
    logger.info(f"{'='*60}")

    fonts     = load_fonts()
    png_paths = []
    tts_paths = []
    durations = []

    # ── INTRO / NEWS LIST (3 seconds) ─────────────────────────
    logger.info("[SLIDE] Rendering news list slide...")
    intro_png = temp_dir / "01_intro.png"
    intro_tts = temp_dir / "01_intro.mp3"
    render_intro_slide(stories, date_str, fonts).save(str(intro_png))
    generate_story_tts({"tts_script": INTRO_TEXT, "headline": "Intro"}, intro_tts)
    intro_dur = max(get_audio_duration(intro_tts), 3.0)
    png_paths.append(intro_png); tts_paths.append(intro_tts); durations.append(intro_dur)
    logger.info(f"[INTRO] Duration: {intro_dur:.1f}s")

    # ── STORIES ────────────────────────────────────────────────
    story_list = stories[:STORIES]
    for i, story in enumerate(story_list):
        story_num = i + 1
        logger.info(f"[SLIDE] Story {story_num}/{len(story_list)}: {story['headline']}")
        s_png = temp_dir / f"{story_num:02d}_story.png"
        s_tts = temp_dir / f"{story_num:02d}_story.mp3"

        theme = STORY_THEMES[i % len(STORY_THEMES)]
        slide = render_slide(story, theme, fonts, date_str, story_num,
                             len(story_list), all_stories=story_list, story_idx=i)
        slide.save(str(s_png))

        generate_story_tts(story, s_tts)
        dur = max(get_audio_duration(s_tts), 10.0)

        png_paths.append(s_png); tts_paths.append(s_tts); durations.append(dur)
        logger.info(f"  Duration: {dur:.1f}s  score={story['score']['total']}  [{story['region_name']}]")

    # ── SUPPORT SLIDE ──────────────────────────────────────────
    logger.info("[SLIDE] Rendering support slide...")
    support_png = temp_dir / "98_support.png"
    support_tts = temp_dir / "98_support.mp3"
    _render_support_slide(date_str, fonts).save(str(support_png))
    generate_story_tts({"tts_script": SUPPORT_TEXT, "headline": "Support"}, support_tts)
    support_dur = max(get_audio_duration(support_tts), 8.0)
    png_paths.append(support_png); tts_paths.append(support_tts); durations.append(support_dur)
    logger.info(f"[SUPPORT] Duration: {support_dur:.1f}s")

    # ── OUTRO ──────────────────────────────────────────────────
    logger.info("[SLIDE] Rendering outro slide...")
    outro_png = temp_dir / "99_outro.png"
    outro_tts = temp_dir / "99_outro.mp3"
    render_outro_slide(stories, date_str, fonts).save(str(outro_png))
    generate_story_tts({"tts_script": OUTRO_TEXT, "headline": "Outro"}, outro_tts)
    outro_dur = max(get_audio_duration(outro_tts), 15.0)
    png_paths.append(outro_png); tts_paths.append(outro_tts); durations.append(outro_dur)
    logger.info(f"[OUTRO] Duration: {outro_dur:.1f}s")

    total_dur = sum(durations)
    logger.info(f"[VIDEO] Estimated total duration: {total_dur:.1f}s ({total_dur/60:.1f} min)")

    # ── COMPOSE ────────────────────────────────────────────────
    out_mp4 = post_dir / f"{dir_name}.mp4"
    compose_video(png_paths, tts_paths, durations, out_mp4)

    # ── THUMBNAILS ─────────────────────────────────────────────
    logger.info("[THUMB] Generating thumbnails...")
    thumb_a = post_dir / f"{dir_name}_thumbnail_a.png"
    thumb_b = post_dir / f"{dir_name}_thumbnail_b.png"
    generate_thumbnail_a(stories, date_str, thumb_a)
    generate_thumbnail_b(stories, date_str, thumb_b)

    # ── METADATA ───────────────────────────────────────────────
    meta_txt, meta_json = write_metadata(
        stories, date_str, out_mp4, thumb_a, thumb_b, post_dir
    )

    # ── CLEANUP ────────────────────────────────────────────────
    logger.info("[CLEAN] Removing temp files...")
    shutil.rmtree(temp_dir, ignore_errors=True)

    result = {
        "post_dir":      post_dir,
        "video":         out_mp4,
        "thumbnail_a":   thumb_a,
        "thumbnail_b":   thumb_b,
        "metadata_txt":  meta_txt,
        "metadata_json": meta_json,
        "duration_secs": total_dur,
    }

    logger.info(f"\n{'='*60}")
    logger.info(f"VIDEO COMPLETE: {out_mp4.name}")
    logger.info(f"Duration: {total_dur:.1f}s ({total_dur/60:.1f} min)")
    logger.info(f"{'='*60}")
    return result


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from news_fetcher import FALLBACK_STORIES
    result = generate(FALLBACK_STORIES)
    print(f"\nVideo: {result['video']}")
    print(f"Duration: {result['duration_secs']:.1f}s")
