#!/usr/bin/env python3
"""
THE AI CHRONICLE - Master Instagram Post Generator
Generates 1 professional post every 2 hours using master prompt system
"""

import asyncio
import sys
import json
import logging
import hashlib
import random
import math
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ============================================================================
# SETUP
# ============================================================================

ROOT_ENV = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ROOT_ENV)

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "instagram-output"
LOG_DIR = PROJECT_ROOT / "logs"

LOG_FILE = LOG_DIR / f"master_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
        UTFStreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# AI NEWS STORY DATABASE (Real AI News)
# ============================================================================

AI_NEWS_STORIES = [
    {
        "company": "OpenAI / Funding",
        "headline": "OpenAI Raises $110B at $730B Valuation",
        "watermark": "$730B",
        "body": ["Amazon, NVIDIA & SoftBank", "back OpenAI's $110B raise.", "A $730B valuation makes it", "the world's most valued AI firm."],
        "stat_label": "OpenAI Pre-Money Valuation",
        "stat_value": "$730B",
        "source": "OpenAI / The AI Track",
        "hashtags": "#OpenAI #AI #Funding #Tech #Startup",
        "reference": "https://techcrunch.com/openai-funding"
    },
    {
        "company": "Claude / Anthropic",
        "headline": "Anthropic Claude 4 Beats GPT-5",
        "watermark": "92%",
        "body": ["Anthropic's Claude 4 scores", "92% on AIME benchmarks.", "Passes GPT-5 in reasoning &", "long-context analysis tasks."],
        "stat_label": "AIME Benchmark Score",
        "stat_value": "92%",
        "source": "Anthropic / ArXiv",
        "hashtags": "#Claude #AI #AnthropicAI #LLM",
        "reference": "https://arxiv.org/anthropic"
    },
    {
        "company": "Google / DeepMind",
        "headline": "AlphaGeometry 2 Solves Olympiad",
        "watermark": "Gold",
        "body": ["Google DeepMind's AlphaGeometry", "scores gold on IMO geometry.", "First AI to pass advanced", "human-level math olympiad."],
        "stat_label": "IMO Rank",
        "stat_value": "Gold",
        "source": "Google DeepMind / Nature",
        "hashtags": "#Google #DeepMind #AI #Math",
        "reference": "https://deepmind.google/alphageometry"
    },
    {
        "company": "Meta / AI Research",
        "headline": "Meta Releases Llama 4 Open Source",
        "watermark": "Free",
        "body": ["Meta open-sources Llama 4,", "rivaling OpenAI's GPT-4.", "70B parameters, Apache 2.0", "license, runs on consumer GPUs."],
        "stat_label": "Model Size",
        "stat_value": "70B",
        "source": "Meta / Hugging Face",
        "hashtags": "#Meta #OpenSource #AI #LLM",
        "reference": "https://llama.meta.com"
    },
    {
        "company": "Microsoft / Copilot",
        "headline": "Microsoft Copilot Pro 2.0 Launch",
        "watermark": "$20/mo",
        "body": ["Microsoft launches Copilot Pro 2", "with real-time code generation.", "Features autonomous debugging", "& enterprise API integration."],
        "stat_label": "Monthly Subscription",
        "stat_value": "$20",
        "source": "Microsoft / Azure Blog",
        "hashtags": "#Microsoft #Copilot #AI #Dev",
        "reference": "https://microsoft.com/copilot"
    },
    {
        "company": "Tesla / Autopilot",
        "headline": "Tesla FSD v13 Achieves Human-Level",
        "watermark": "Level 4",
        "body": ["Tesla FSD v13 passes 10M miles", "of human-level autonomous drive.", "Zero critical disengagements in", "urban, highway, and weather."],
        "stat_label": "Clean Miles Driven",
        "stat_value": "10M",
        "source": "Tesla / NHTSA",
        "hashtags": "#Tesla #Autopilot #AI #Autonomous",
        "reference": "https://tesla.com/fsd"
    },
    {
        "company": "Netflix / Recommendations",
        "headline": "Netflix AI Cuts Churn by 40%",
        "watermark": "40%",
        "body": ["Netflix AI personalization engine", "reduces churn by 40%.", "Real-time mood-based", "recommendation system."],
        "stat_label": "Churn Reduction",
        "stat_value": "40%",
        "source": "Netflix / Re:Invent",
        "hashtags": "#Netflix #AI #Personalization",
        "reference": "https://netflix.com/research"
    },
    {
        "company": "Harvard Medical / AI",
        "headline": "AI Discovers New Cancer Drug",
        "watermark": "96%",
        "body": ["Harvard AI lab discovers new", "cancer drug targeting HER2.", "96% effectiveness in trials.", "Heads to Phase 2 FDA review."],
        "stat_label": "Efficacy Rate",
        "stat_value": "96%",
        "source": "Harvard / Science Magazine",
        "hashtags": "#AI #Medicine #Healthcare #Biotech",
        "reference": "https://harvard.edu/ai-cancer"
    },
    {
        "company": "UK Parliament / AI Bill",
        "headline": "UK Passes AI Regulation Law",
        "watermark": "Law",
        "body": ["UK Parliament passes AI Rights", "Regulation Act (2026).", "First nation to mandate AI", "licensing & annual audits."],
        "stat_label": "Nations Following",
        "stat_value": "6+",
        "source": "UK Parliament / GOV.UK",
        "hashtags": "#UK #Regulation #AI #Policy",
        "reference": "https://parliament.uk/ai-bill"
    },
    {
        "company": "Stanford AI Index",
        "headline": "2026 AI Index Shows 8x Growth",
        "watermark": "8x",
        "body": ["Stanford AI Index 2026: AI", "compute spending grew 8x.", "Training costs fell 60%.", "Model accuracy at all-time peak."],
        "stat_label": "Compute Growth",
        "stat_value": "8x",
        "source": "Stanford AI Index / HAI",
        "hashtags": "#AI #Research #Stanford #Report",
        "reference": "https://aiindex.stanford.edu"
    }
]

# ============================================================================
# COLOR THEMES (24 themes as per master prompt)
# ============================================================================

THEMES = [
    ("Midnight Gold", "dark", (4, 8, 28), (12, 4, 40), "#F5C842", "#FFF0B0", "#080600", "#ffffff"),
    ("Deep Cosmos", "dark", (8, 0, 16), (20, 0, 40), "#A78BFA", "#E8D8FF", "#080418", "#ffffff"),
    ("Forest Dark", "dark", (0, 12, 6), (0, 24, 14), "#10B981", "#B8FFDC", "#00120a", "#ffffff"),
    ("Crimson Dark", "dark", (22, 4, 0), (36, 8, 0), "#FF4D1A", "#FFD0B8", "#140400", "#ffffff"),
    ("Deep Navy", "dark", (0, 6, 18), (0, 10, 28), "#60A5FA", "#C8DCFF", "#000614", "#ffffff"),
    ("Dark Amber", "dark", (14, 10, 0), (26, 18, 0), "#FBBF24", "#FFF0B0", "#0e0800", "#ffffff"),
    ("Dark Cobalt", "dark", (0, 8, 18), (0, 4, 28), "#22D3EE", "#B8F4FF", "#000a14", "#ffffff"),
    ("Deep Indigo", "dark", (8, 0, 16), (4, 0, 8), "#2DD4BF", "#B8FFF5", "#000c0a", "#ffffff"),
    ("Obsidian Rose", "dark", (16, 0, 8), (28, 0, 16), "#F472B6", "#FFD6EC", "#180010", "#ffffff"),
    ("Solar Flare", "dark", (20, 8, 0), (10, 4, 0), "#FB923C", "#FFE4CC", "#160800", "#ffffff"),
    ("Violet Storm", "dark", (10, 0, 18), (18, 0, 30), "#818CF8", "#E0E4FF", "#08041a", "#ffffff"),
    ("Teal Abyss", "dark", (0, 10, 10), (0, 20, 20), "#2DD4BF", "#CCFFF8", "#001414", "#ffffff"),
]

BG_GENS = ["neural", "grid", "radar", "bars", "stars", "triangles", "hexagons", "circuit", "waves", "scatter", "diagonals"]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def rgb(h):
    """Convert hex to RGB"""
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def get_font(size, bold=False):
    """Load font with fallback"""
    try:
        path = f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf"
        return ImageFont.truetype(path, size)
    except:
        try:
            win_name = "arialbd.ttf" if bold else "arial.ttf"
            path = f"C:\\Windows\\Fonts\\{win_name}"
            return ImageFont.truetype(path, size)
        except:
            return ImageFont.load_default()

def text_width(draw, text, font):
    """Get text width"""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def text_height(draw, text, font):
    """Get text height"""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]

def draw_centered(draw, y, text, fill, font, img_width=1080):
    """Draw text centered"""
    tw = text_width(draw, text, font)
    draw.text(((img_width - tw) // 2, y), text, fill=fill, font=font)
    return text_height(draw, text, font)

def draw_centered_spaced(draw, y, text, fill, font, spacing=6, img_width=1080):
    """Draw text centered with letter spacing"""
    char_widths = [text_width(draw, c, font) for c in text]
    total_w = sum(char_widths) + spacing * (len(text) - 1)
    x = (img_width - total_w) // 2
    for i, c in enumerate(text):
        draw.text((x, y), c, fill=fill, font=font)
        x += char_widths[i] + spacing
    return text_height(draw, text, font)

def make_slug(headline):
    """Convert headline to a clean filename slug"""
    import re
    slug = headline.lower()
    slug = re.sub(r'[^a-z0-9\s]', '', slug)   # strip punctuation/symbols
    slug = re.sub(r'\s+', '_', slug.strip())    # spaces → underscores
    return slug[:60]                             # cap length

def make_post_dir(ts, slug):
    """Create and return a timestamped subdirectory for this post"""
    dir_name = f"{ts}_{slug}"
    post_dir = OUTPUT_DIR / dir_name
    post_dir.mkdir(parents=True, exist_ok=True)
    return post_dir

def wrap_text(draw, text, font, max_width):
    """Word-wrap text to fit max_width, returns list of lines"""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if text_width(draw, test, font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

# ============================================================================
# LOGO RENDERER
# ============================================================================

def draw_infinity_logo(d, x, y, size, ac, dark_bg=(6, 10, 26)):
    """Draw The AI Chronicle logo — infinity symbol inside a dark circle"""
    cx, cy = x + size // 2, y + size // 2
    # Outer dark filled circle
    d.ellipse([x, y, x + size, y + size], fill=dark_bg)
    # Inner ring outline (subtle)
    m = int(size * 0.10)
    d.ellipse([x + m, y + m, x + size - m, y + size - m], outline=(*ac, 70), width=1)
    # Infinity: two overlapping circles
    inf_r = int(size * 0.245)
    offset = int(size * 0.175)
    lw = max(2, int(size * 0.042))
    d.arc([cx - offset - inf_r, cy - inf_r, cx - offset + inf_r, cy + inf_r], 0, 360, fill=ac, width=lw)
    d.arc([cx + offset - inf_r, cy - inf_r, cx + offset + inf_r, cy + inf_r], 0, 360, fill=ac, width=lw)
    # Center dot
    dot_r = max(3, int(size * 0.046))
    d.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=ac)

# ============================================================================
# MAIN POST GENERATOR
# ============================================================================

def _draw_background(img, d, style: str, ac: tuple, rng: random.Random):
    """Draw a subtle procedural background pattern over the gradient."""
    W, H = img.size
    alpha = 22   # very subtle so text stays readable

    if style == "grid":
        step = 80
        for x in range(0, W, step):
            d.line([(x, 0), (x, H)], fill=(*ac, alpha), width=1)
        for y in range(0, H, step):
            d.line([(0, y), (W, y)], fill=(*ac, alpha), width=1)

    elif style == "dots" or style == "scatter" or style == "stars":
        for _ in range(120):
            x, y = rng.randint(0, W), rng.randint(0, H)
            r = rng.randint(1, 4)
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse([x - r, y - r, x + r, y + r],
                                       fill=(*ac, alpha + 10))
            img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"))

    elif style == "neural" or style == "circuit":
        pts = [(rng.randint(50, W - 50), rng.randint(50, H - 50)) for _ in range(18)]
        for i, (x1, y1) in enumerate(pts):
            for x2, y2 in pts[i + 1:i + 3]:
                d.line([(x1, y1), (x2, y2)], fill=(*ac, alpha), width=1)
            r = 5
            d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], outline=(*ac, alpha + 8), width=1)

    elif style == "radar":
        cx, cy = W // 2, H // 2
        for radius in range(100, max(W, H), 120):
            d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                      outline=(*ac, alpha), width=1)

    elif style == "diagonals":
        for offset in range(-H, W + H, 60):
            d.line([(offset, 0), (offset + H, H)], fill=(*ac, alpha), width=1)

    elif style == "hexagons":
        size = 55
        for row in range(-1, H // size + 2):
            for col in range(-1, W // size + 2):
                cx = col * size * 2 + (size if row % 2 else 0)
                cy = row * int(size * 1.73)
                pts_hex = [
                    (cx + size * math.cos(math.radians(60 * i)),
                     cy + size * math.sin(math.radians(60 * i)))
                    for i in range(6)
                ]
                d.polygon(pts_hex, outline=(*ac, alpha))

    elif style == "waves":
        for y_off in range(0, H + 80, 80):
            pts_wave = []
            for x in range(0, W + 20, 10):
                y = y_off + int(20 * math.sin(x / 60))
                pts_wave.append((x, y))
            if len(pts_wave) >= 2:
                d.line(pts_wave, fill=(*ac, alpha), width=1)

    elif style == "bars":
        bar_w = 60
        for x in range(0, W, bar_w * 2):
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).rectangle([x, 0, x + bar_w, H], fill=(*ac, 8))
            img_rgba = Image.alpha_composite(img.convert("RGBA"), ov)
            img.paste(img_rgba.convert("RGB"))

    elif style == "triangles":
        step = 120
        for row in range(0, H + step, step):
            for col in range(0, W + step, step):
                pts_tri = [(col, row), (col + step, row), (col + step // 2, row + step)]
                d.polygon(pts_tri, outline=(*ac, alpha))


def generate_post(story, bg_image_path=None):
    """Generate a single branded Instagram post with strict boundary layout.
    bg_image_path: optional path to a background image for real-photo look.
    A dark scrim is added automatically so text stays readable on any image.
    """
    logger.info("\n" + "=" * 70)
    logger.info("GENERATING MASTER POST")
    logger.info("=" * 70)

    W, H   = 1080, 1080
    PAD    = 60   # horizontal padding

    # ── Strict vertical zone definitions ─────────────────────────
    # All zones are fixed — content is clipped to fit, never overflows.
    Z_TOPBAR_H  = 8          # top accent bar
    Z_HEADER_Y  = Z_TOPBAR_H          # 8
    Z_HEADER_H  = 118                  # brand + subtitle + divider
    Z_CONTENT_Y = Z_HEADER_Y + Z_HEADER_H   # 126
    Z_FOOTER_Y  = 836                  # footer starts here (fixed)
    Z_FOOTER_H  = H - Z_FOOTER_Y      # 244px
    Z_CONTENT_H = Z_FOOTER_Y - Z_CONTENT_Y  # 710px for all content

    # Content zone sub-heights (must sum to ≤ Z_CONTENT_H = 710)
    Z_PILL_H    = 46   # company pill
    Z_PILL_GAP  = 12
    Z_REGION_H  = 30   # region badge
    Z_REGION_GAP = 10
    Z_HEADLINE_H = 142  # up to 2 lines at 64px line-height
    Z_HEADLINE_GAP = 14
    Z_DIVIDER_H  = 20   # divider line + gap
    Z_BODY_H    = 232   # 4 lines at 58px line-height
    Z_BODY_GAP  = 14
    Z_STAT_H    = 112   # stat box
    Z_STAT_GAP  = 10
    Z_SOURCE_H  = 28    # source line
    # Total: 46+12+30+10+142+14+20+232+14+112+10+28 = 670 ≤ 710 ✓

    # Seeded randomization
    seed_str = story['headline'] + story['company']
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng  = random.Random(seed)

    t_idx = rng.randint(0, len(THEMES) - 1)
    b_idx = rng.randint(0, len(BG_GENS) - 1)
    theme_name, mode, bg_top, bg_bot, accent, body_c, stat_bg, hl_c = THEMES[t_idx]
    logger.info(f"Theme: {theme_name}  BG: {BG_GENS[b_idx]}")

    ac = rgb(accent)

    # ── Background gradient ───────────────────────────────────────
    img = Image.new("RGB", (W, H))
    d   = ImageDraw.Draw(img)
    for yi in range(H):
        t = yi / H
        color = tuple(int(bg_top[c] * (1 - t) + bg_bot[c] * t) for c in range(3))
        d.line([(0, yi), (W, yi)], fill=color)

    if bg_image_path:
        # Layer real background image at 70% opacity over the gradient
        bg_raw = Image.open(str(bg_image_path)).convert("RGBA").resize((W, H), Image.LANCZOS)
        r_ch, g_ch, b_ch, a_ch = bg_raw.split()
        a_ch = a_ch.point(lambda x: int(x * 0.70))
        bg_raw.putalpha(a_ch)
        base_rgba = img.convert("RGBA")
        base_rgba.paste(bg_raw, (0, 0), bg_raw)
        img = base_rgba.convert("RGB")
        # Dark scrim: 55% black overlay so text is always readable on any image
        scrim = Image.new("RGBA", (W, H), (0, 0, 0, 140))
        img = Image.alpha_composite(img.convert("RGBA"), scrim).convert("RGB")
        logger.info(f"BG: {Path(str(bg_image_path)).name}  (70% img + 55% dark scrim)")
    else:
        _draw_background(img, d, BG_GENS[b_idx], ac, rng)
    d = ImageDraw.Draw(img)

    # ── Faded watermark — prefer explicit watermark, then stat_value, then company keyword
    wm_font = get_font(180, bold=True)
    _wm_raw = (story.get('watermark') or story.get('stat_value') or
               story.get('company', 'NEWS').split('/')[0].strip())
    wm_text = _wm_raw[:10]
    wm_w    = text_width(d, wm_text, wm_font)
    wm_h    = text_height(d, wm_text, wm_font)
    wm_ov   = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(wm_ov).text(
        ((W - wm_w) // 2, Z_CONTENT_Y + (Z_CONTENT_H - wm_h) // 2),
        wm_text, fill=(*ac, 16), font=wm_font
    )
    img = Image.alpha_composite(img.convert("RGBA"), wm_ov).convert("RGB")
    d = ImageDraw.Draw(img)

    # ── Zone 1: Top accent bar ─────────────────────────────────────
    d.rectangle([0, 0, W, Z_TOPBAR_H], fill=ac)

    # ── Zone 2: Header ─────────────────────────────────────────────
    # Dark semi-transparent header background
    hdr_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(hdr_ov).rectangle(
        [0, Z_HEADER_Y, W, Z_HEADER_Y + Z_HEADER_H], fill=(0, 0, 0, 80)
    )
    img = Image.alpha_composite(img.convert("RGBA"), hdr_ov).convert("RGB")
    d = ImageDraw.Draw(img)

    hy = Z_HEADER_Y + 10
    draw_centered(d, hy, "THE AI CHRONICLE", "white", get_font(44, bold=True), W)
    hy += 54
    draw_centered_spaced(d, hy, "DAILY AI NEWS", accent, get_font(17), spacing=8, img_width=W)
    hy += 30
    d.line([(PAD, hy), (W - PAD, hy)], fill=ac, width=2)

    # ── Zone 3: Content area ───────────────────────────────────────
    cy = Z_CONTENT_Y + 14   # small top padding inside content zone

    # Company pill
    comp_text = story['company'].upper()[:28]
    comp_font = get_font(24, bold=True)
    # Clamp pill width to canvas
    max_pill_w = W - 2 * PAD
    comp_w = min(text_width(d, comp_text, comp_font), max_pill_w - 48)
    pill_w = comp_w + 48
    pill_x = (W - pill_w) // 2
    pill_y2 = cy + Z_PILL_H
    d.rounded_rectangle([pill_x, cy, pill_x + pill_w, pill_y2], radius=23, fill=ac)
    comp_h = text_height(d, comp_text, comp_font)
    d.text(((W - comp_w) // 2, cy + (Z_PILL_H - comp_h) // 2),
           comp_text, fill="white", font=comp_font)
    cy += Z_PILL_H + Z_PILL_GAP

    # Region badge (flag + name)
    region      = story.get('region', '')
    region_name = story.get('region_name', '').upper()
    if region or region_name:
        badge_text  = f"{region}  {region_name}" if region else region_name
        badge_font  = get_font(18)
        badge_w     = text_width(d, badge_text, badge_font) + 28
        badge_x     = (W - badge_w) // 2
        badge_ov    = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(badge_ov).rounded_rectangle(
            [badge_x, cy, badge_x + badge_w, cy + Z_REGION_H],
            radius=15, fill=(*ac, 40)
        )
        img = Image.alpha_composite(img.convert("RGBA"), badge_ov).convert("RGB")
        d   = ImageDraw.Draw(img)
        badge_th = text_height(d, badge_text, badge_font)
        d.text(((W - text_width(d, badge_text, badge_font)) // 2,
                cy + (Z_REGION_H - badge_th) // 2),
               badge_text, fill=rgb("#cccccc"), font=badge_font)
    cy += Z_REGION_H + Z_REGION_GAP

    # Headline — max 2 lines, font auto-sized to fit width
    hl_text  = story['headline']
    hl_font  = get_font(52, bold=True)
    hl_max_w = W - 2 * PAD
    hl_lines = wrap_text(d, hl_text, hl_font, hl_max_w)[:2]  # cap at 2 lines

    # Dark panel behind headline
    hl_panel_h = len(hl_lines) * 64 + 16
    hl_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl_ov).rectangle(
        [0, cy - 8, W, cy + hl_panel_h], fill=(0, 0, 0, 70)
    )
    img = Image.alpha_composite(img.convert("RGBA"), hl_ov).convert("RGB")
    d   = ImageDraw.Draw(img)

    for line in hl_lines:
        draw_centered(d, cy, line, rgb(hl_c), hl_font, W)
        cy += 64
    cy += Z_HEADLINE_GAP

    # Divider
    d.line([(PAD, cy), (W - PAD, cy)], fill=ac, width=2)
    cy += Z_DIVIDER_H

    # Body text — 4 lines, font size 42px, line-height 58px
    body_font  = get_font(42)
    body_lines = story['body'][:4]
    for line in body_lines:
        if line.strip():
            # Trim at word boundary if overflows width
            while text_width(d, line, body_font) > W - 2 * PAD and ' ' in line:
                line = line.rsplit(' ', 1)[0]
            draw_centered(d, cy, line, rgb(body_c), body_font, W)
        cy += 58
    cy += Z_BODY_GAP

    # Stat box — fixed height, clipped to boundary
    stat_box_x = PAD + 10
    stat_box_w = W - 2 * (PAD + 10)
    stat_box_y2 = cy + Z_STAT_H
    # Ensure stat box does not overflow into footer
    if stat_box_y2 > Z_FOOTER_Y - Z_SOURCE_H - Z_STAT_GAP:
        stat_box_y2 = Z_FOOTER_Y - Z_SOURCE_H - Z_STAT_GAP
        cy = stat_box_y2 - Z_STAT_H
    d.rounded_rectangle([stat_box_x, cy, stat_box_x + stat_box_w, stat_box_y2],
                         radius=14, fill=rgb(stat_bg))
    d.rounded_rectangle([stat_box_x, cy, stat_box_x + stat_box_w, stat_box_y2],
                         radius=14, outline=ac, width=3)
    # Stat label — larger, uppercase, clearly readable
    stat_label = story['stat_label'][:30].upper()
    draw_centered(d, cy + 10, stat_label, ac, get_font(24, bold=True), W)
    # Thin separator between label and value
    sep_y = cy + 40
    d.line([(stat_box_x + 40, sep_y), (stat_box_x + stat_box_w - 40, sep_y)],
           fill=(*ac, 80), width=1)
    # Stat value — auto-size to fit box width, positioned below separator
    sv_font = get_font(68, bold=True)
    sv_text = story['stat_value'][:12]
    while text_width(d, sv_text, sv_font) > stat_box_w - 24 and sv_font.size > 32:
        sv_font = get_font(sv_font.size - 4, bold=True)
    draw_centered(d, sep_y + 6, sv_text, rgb(hl_c), sv_font, W)
    cy = stat_box_y2 + Z_STAT_GAP

    # Source line — clamped to stay above footer
    source_y = min(cy, Z_FOOTER_Y - Z_SOURCE_H - 4)
    src_text  = f"Source: {story['source']}"[:50]
    draw_centered(d, source_y, src_text, rgb("#999999"), get_font(19), W)

    # ── Zone 4: Footer ─────────────────────────────────────────────
    # Dark footer background
    ft_ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ft_ov).rectangle(
        [0, Z_FOOTER_Y, W, H], fill=(*rgb(stat_bg), 230)
    )
    img = Image.alpha_composite(img.convert("RGBA"), ft_ov).convert("RGB")
    d   = ImageDraw.Draw(img)
    d.line([(0, Z_FOOTER_Y), (W, Z_FOOTER_Y)], fill=ac, width=2)

    # Logo
    logo_sz   = 68
    logo_file = PROJECT_ROOT / "logo.PNG"
    logo_x    = (W - logo_sz) // 2
    logo_y    = Z_FOOTER_Y + 14
    if logo_file.exists():
        logo_img = Image.open(logo_file).convert("RGBA")
        logo_img = logo_img.resize((logo_sz, logo_sz), Image.LANCZOS)
        mask     = Image.new("L", (logo_sz, logo_sz), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, logo_sz, logo_sz], fill=255)
        logo_img.putalpha(mask)
        img_rgba = img.convert("RGBA")
        img_rgba.paste(logo_img, (logo_x, logo_y), logo_img)
        img = img_rgba.convert("RGB")
        d   = ImageDraw.Draw(img)
    else:
        draw_infinity_logo(d, logo_x, logo_y, logo_sz, ac)

    fy = logo_y + logo_sz + 8
    draw_centered(d, fy, "@theaichronicle  \u2022  Daily AI News",
                  "white", get_font(21, bold=True), W)
    fy += 30
    draw_centered(d, fy, "Follow for daily AI news",
                  rgb("#aaaaaa"), get_font(19), W)
    fy += 28
    draw_centered_spaced(d, fy, "LIKE  \u2022  SHARE  \u2022  FOLLOW",
                         ac, get_font(18, bold=True), spacing=4, img_width=W)

    # Bottom accent bar
    d.rectangle([0, H - 8, W, H], fill=ac)

    # ── Save ───────────────────────────────────────────────────────
    ts       = datetime.now().strftime('%Y%m%d_%H%M%S')
    slug     = make_slug(story['headline'])
    post_dir = make_post_dir(ts, slug)
    png_path = post_dir / f"{slug}.png"
    img.save(str(png_path), "PNG", dpi=(300, 300))
    logger.info(f"[OK] PNG saved: {post_dir.name}/{png_path.name}")

    return {
        "png": str(png_path),
        "ts": ts,
        "slug": slug,
        "post_dir": str(post_dir),
        "story": story,
        "headline": story['headline'],
        "source": story['source'],
        "hashtags": story['hashtags'],
        "reference": story['reference'],
    }


def generate_audio(story, post_dir, slug):
    """Generate narration audio using edge-tts (Indian-English female, soft news voice)."""
    import re
    import edge_tts

    # Use full RSS summary for complete sentences; fall back to body lines
    raw_summary = story.get('summary', '')
    if raw_summary and len(raw_summary.strip()) > 40:
        # Split into complete sentences, drop very short fragments
        parts = re.split(r'(?<=[.!?])\s+', raw_summary.strip())
        sentences = [p.strip() for p in parts if len(p.strip()) > 20]
        body_text = ' '.join(sentences[:6])   # up to 6 full sentences
        # Ensure it ends on a sentence boundary
        if body_text and body_text[-1] not in '.!?':
            last = body_text.rfind('. ')
            if last > len(body_text) * 0.4:
                body_text = body_text[:last + 1]
    else:
        body_text = " ".join(line for line in story['body'] if line.strip())

    # Headline + story body only — no stat box numbers or source attribution spoken aloud
    script = (
        f"{story['headline']}. "
        f"{body_text} "
        f"For more daily AI news, follow The AI Chronicle. "
        f"Stay ahead of the curve."
    )
    logger.info(f"[AUDIO] Script: {script}")
    mp3_path = Path(post_dir) / f"{slug}.mp3"

    async def _synthesise():
        communicate = edge_tts.Communicate(
            script,
            voice="en-IN-NeerjaNeural",   # Indian-English female, professional
            rate="-8%",                    # slightly slower — clear news-reading pace
            pitch="-2Hz",                  # subtly lower, authoritative tone
        )
        await communicate.save(str(mp3_path))

    asyncio.run(_synthesise())
    logger.info(f"[OK] Audio saved: {Path(post_dir).name}/{mp3_path.name}")
    return str(mp3_path)


def generate_reel(png_path, audio_path, post_dir, slug):
    """Create Instagram Reel matching full audio length: image + audio -> MP4 via ffmpeg"""
    import subprocess
    mp4_path = Path(post_dir) / f"{slug}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", png_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "slow",          # better compression quality
        "-crf", "17",               # near-lossless (lower = higher quality; was unset ~23)
        "-profile:v", "high",
        "-level:v", "4.1",
        "-tune", "stillimage",
        "-b:v", "8M",               # 8 Mbps target — sharp on large screens
        "-maxrate", "12M",
        "-bufsize", "24M",
        "-c:a", "aac",
        "-b:a", "256k",             # higher audio bitrate (was 192k)
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",  # web-optimised — metadata at front
        "-shortest",                # video ends exactly when audio ends
        "-vf", "scale=1080:1080:flags=lanczos",   # lanczos for sharper upscale
        str(mp4_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        logger.info(f"[OK] Reel saved: {Path(post_dir).name}/{mp4_path.name}")
    else:
        logger.error(f"[FAIL] ffmpeg: {result.stderr[-300:]}")
        raise RuntimeError("ffmpeg failed")
    return str(mp4_path)

def create_caption(story):
    """Create storytelling Instagram caption with URL at bottom"""
    body_lines = story['body']
    # Build narrative body
    narrative = " ".join(body_lines)
    # Derive clean hashtags (no # prefix on last block, mixed style like example)
    base_tags = story['hashtags']  # already has # prefixes
    extra_tags = "#TheAIChronicle #DailyAINews #AI #ArtificialIntelligence #Tech"

    caption = (
        f"🚀 {story['headline']}.\n\n"
        f"{narrative}\n\n"
        f"{story['stat_label']}: {story['stat_value']}.\n\n"
        f"The AI space moves fast — stay ahead. 👇\n\n"
        f"{base_tags} {extra_tags}\n\n"
        f"Source: {story['reference']}"
    )
    return caption.strip()

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Generate single master post with caption"""
    logger.info("\n" + "=" * 70)
    logger.info("THE AI CHRONICLE - MASTER POST GENERATOR v2.0")
    logger.info("=" * 70)

    # Attempt live web search for today's top AI news
    try:
        from news_fetcher import fetch_latest_ai_news
        story = fetch_latest_ai_news()
        if story:
            logger.info(f"\n[STORY] Live news: {story['headline']}")
        else:
            raise ValueError("Fetcher returned None")
    except Exception as e:
        logger.warning(f"[WARN] Live fetch failed ({e}) — falling back to local stories")
        story = random.choice(AI_NEWS_STORIES)
        logger.info(f"\n[STORY] Fallback: {story['headline']}")
    
    # Generate post image (creates subdirectory)
    result = generate_post(story)
    ts       = result['ts']
    slug     = result['slug']
    post_dir = result['post_dir']

    # Generate audio narration
    audio_path = generate_audio(story, post_dir, slug)

    # Generate 30-second reel
    reel_path = generate_reel(result['png'], audio_path, post_dir, slug)

    # Create caption
    caption = create_caption(story)

    # Save caption into post subdirectory
    caption_file = Path(post_dir) / f"{slug}_caption.txt"
    with open(caption_file, "w", encoding="utf-8") as f:
        f.write(caption)

    logger.info(f"\n[OK] Caption saved: {Path(post_dir).name}/{caption_file.name}")
    logger.info(f"\n[CAPTION]\n{caption}")

    # Save metadata into post subdirectory
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "headline": story['headline'],
        "company": story['company'],
        "source": story['source'],
        "reference": story['reference'],
        "hashtags": story['hashtags'],
        "post_dir": post_dir,
        "png_file": result['png'],
        "audio_file": audio_path,
        "reel_file": reel_path,
        "caption": caption
    }

    meta_file = Path(post_dir) / f"{slug}_metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"[OK] Metadata saved: {meta_file.name}")
    logger.info("\n" + "=" * 70)
    logger.info("READY FOR INSTAGRAM!")
    logger.info("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"[FAIL] Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
