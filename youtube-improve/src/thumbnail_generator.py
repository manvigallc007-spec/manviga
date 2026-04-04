#!/usr/bin/env python3
"""
THE AI CHRONICLE — YouTube Thumbnail Generator (1280×720)
Full-bleed AI background image with cinematic gradient scrim.
Variant A: first available image  |  Variant B: second available image
"""

import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

logger = logging.getLogger(__name__)

TW, TH = 1280, 720
PAD = 52


# ─────────────────────────────────────────────
# BACKGROUND LOADER
# ─────────────────────────────────────────────

def _list_backgrounds():
    """Return sorted list of all image paths in backgrounds/ folder."""
    bg_dir = Path(__file__).parent.parent / "backgrounds"
    exts   = {".jpg", ".jpeg", ".png", ".webp", ".jfif"}
    if not bg_dir.exists():
        return []
    return sorted(p for p in bg_dir.iterdir()
                  if p.suffix.lower() in exts and p.stem != "README")


def _load_background(index=0):
    """Load backgrounds[index], crop-fill to 1280×720. Returns PIL Image or None."""
    paths = _list_backgrounds()
    if not paths:
        return None
    p = paths[index % len(paths)]
    try:
        img = Image.open(p).convert("RGB")
        # Crop-fill to TW×TH
        ratio = img.width / img.height
        if ratio > TW / TH:
            new_h, new_w = TH, int(ratio * TH)
        else:
            new_w, new_h = TW, int(TW / ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - TW) // 2
        top  = (new_h - TH) // 2
        return img.crop((left, top, left + TW, top + TH))
    except Exception as e:
        logger.warning(f"[THUMB] Could not load {p.name}: {e}")
        return None


def _apply_scrim(img, dark_color=(0, 0, 0), left_opacity=0.82, right_opacity=0.25):
    """
    Left-to-right gradient scrim: very dark on the left (text area),
    fading to semi-transparent on the right (image shows through).
    """
    arr     = np.array(img).astype(np.float32)
    dark    = np.array(dark_color, dtype=np.float32)
    w       = arr.shape[1]
    opacity = np.linspace(left_opacity, right_opacity, w, dtype=np.float32)
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1 - opacity) + dark[c] * opacity
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _apply_color_tint(img, color, intensity=0.18):
    """Blend a colour tint over the image."""
    arr  = np.array(img).astype(np.float32)
    tint = np.array(color[:3], dtype=np.float32)
    for c in range(3):
        arr[:, :, c] = np.clip(arr[:, :, c] + tint[c] * intensity, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def _glow(img, center, radius, color, intensity=0.35):
    arr = np.array(img).astype(np.float32)
    cx, cy = center
    h, w = arr.shape[:2]
    y_idx, x_idx = np.ogrid[:h, :w]
    dist = np.sqrt((x_idx - cx)**2 + (y_idx - cy)**2)
    mask = np.clip(1.0 - dist / max(radius, 1), 0, 1)**2 * intensity
    for c, val in enumerate(color[:3]):
        arr[:, :, c] = np.clip(arr[:, :, c] + mask * val, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


# ─────────────────────────────────────────────
# LOGO LOADER
# ─────────────────────────────────────────────

def _load_logo(size=(60, 60)):
    candidates = [
        Path(__file__).parent.parent.parent / "logo.PNG",
        Path(__file__).parent.parent.parent / "youtube-posting"   / "logo.PNG",
        Path(__file__).parent.parent.parent / "instagram-posting" / "logo.PNG",
    ]
    for p in candidates:
        if p.exists():
            try:
                logo = Image.open(p).convert("RGBA")
                return logo.resize(size, Image.LANCZOS)
            except Exception:
                pass
    return None


# ─────────────────────────────────────────────
# FONT LOADER
# ─────────────────────────────────────────────

def _load_thumb_fonts():
    dirs = [Path("C:/Windows/Fonts"),
            Path.home() / "AppData/Local/Microsoft/Windows/Fonts"]

    def _find(name):
        for d in dirs:
            p = d / name
            if p.exists():
                return str(p)
        return None

    def _ft(name, size):
        path = _find(name)
        for f in ([path] if path else []) + [_find("arial.ttf")]:
            try:
                if f:
                    return ImageFont.truetype(f, size)
            except Exception:
                pass
        return ImageFont.load_default()

    return {
        "hl_xl":   _ft("arialbd.ttf", 110),
        "hl_lg":   _ft("arialbd.ttf",  90),
        "hl_md":   _ft("arialbd.ttf",  74),
        "hl_sm":   _ft("arialbd.ttf",  62),
        "date":    _ft("arialbd.ttf",  72),
        "label":   _ft("arialbd.ttf",  34),
        "brand":   _ft("arialbd.ttf",  30),
        "pill":    _ft("arialbd.ttf",  24),
        "hash":    _ft("arialbd.ttf",  26),
        "small":   _ft("arial.ttf",    22),
    }


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _tw(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _th(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def _shadow(draw, x, y, text, font, fill, offset=4):
    draw.text((x + offset, y + offset), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)


def _pill(draw, x, y, text, font, bg, fg=(255, 255, 255), r=10, px=16, py=8):
    tw = _tw(draw, text, font)
    th = _th(draw, text, font)
    x2, y2 = x + tw + px * 2, y + th + py * 2
    draw.rounded_rectangle([x, y, x2, y2], radius=r, fill=bg)
    draw.text((x + px, y + py), text, font=font, fill=fg)
    return x2


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], []
    for word in words:
        test = " ".join(cur + [word])
        if _tw(draw, test, font) <= max_w:
            cur.append(word)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


def _top_story(stories):
    return max(stories, key=lambda s: s.get("score", {}).get("total", 0))


# ─────────────────────────────────────────────
# CORE RENDER ENGINE
# ─────────────────────────────────────────────

def _render_thumbnail(stories, date_str, accent, accent2, fallback_bg,
                      bg_index=0):
    fonts = _load_thumb_fonts()
    hero  = _top_story(stories)

    # ── Background ────────────────────────────────────────────
    bg = _load_background(bg_index)
    if bg:
        # Uniform 70% dark overlay so text is clearly readable over any image
        img = _apply_scrim(bg, dark_color=(0, 0, 0),
                           left_opacity=0.70, right_opacity=0.70)
        img = _apply_color_tint(img, accent, intensity=0.10)
    else:
        img = Image.new("RGB", (TW, TH), fallback_bg)
        from PIL import ImageDraw as _ID
        _g_draw = _ID.Draw(img)

    img = _glow(img, (PAD * 2, TH // 2 - 60), 340, accent, intensity=0.22)
    draw = ImageDraw.Draw(img)

    # ── Top bar ───────────────────────────────────────────────
    bar_h = 76
    # Semi-transparent bar using numpy
    arr = np.array(img)
    arr[:bar_h, :] = (arr[:bar_h, :].astype(np.float32) * 0.25 +
                      np.array([0, 0, 0], dtype=np.float32) * 0.75).astype(np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    draw.line([(0, bar_h), (TW, bar_h)], fill=accent, width=3)

    # Logo
    logo = _load_logo(size=(50, 50))
    if logo:
        try:
            img.paste(logo, (PAD, 13), logo if logo.mode == "RGBA" else None)
        except Exception:
            img.paste(logo, (PAD, 13))
        draw = ImageDraw.Draw(img)

    draw.text((PAD + 62, 20), "THE AI CHRONICLE", font=fonts["brand"],
              fill=(255, 255, 255))

    # ── Content zone (left 62% of width) ─────────────────────
    text_w    = int(TW * 0.62)
    bot_y     = TH - 62          # reserve space for bottom bar
    content_h = bot_y - bar_h    # usable height ~582px
    content_y = bar_h + int(content_h * 0.06)   # 6% top padding

    # ── "TOP 10 STORIES FROM TODAY" label + thin accent rule ─
    label = "YOUR TOP 10 AI NEWS FROM TODAY"
    draw.text((PAD, content_y), label, font=fonts["label"], fill=accent)
    content_y += _th(draw, label, fonts["label"]) + 10
    draw.line([(PAD, content_y), (PAD + 320, content_y)],
              fill=accent, width=2)
    content_y += 18 + int(content_h * 0.04)     # gap after rule

    # ── Headline — auto-sized, 2 lines max ───────────────────
    hook = hero.get("hook", hero["headline"]).upper()
    chosen = fonts["hl_xl"]
    for fk in ["hl_xl", "hl_lg", "hl_md", "hl_sm"]:
        fnt = fonts[fk]
        if len(_wrap(draw, hook, fnt, text_w - PAD)) <= 2:
            chosen = fnt
            break

    for line in _wrap(draw, hook, chosen, text_w - PAD)[:2]:
        _shadow(draw, PAD, content_y, line, chosen, (255, 255, 255), offset=5)
        content_y += chosen.size + 12

    content_y += int(content_h * 0.06)          # gap after headline

    # ── Date block with decorative graphics ──────────────────
    date_text = date_str.upper()
    dw = _tw(draw, date_text, fonts["date"])
    dh = _th(draw, date_text, fonts["date"])

    # Pill-shaped highlight box behind the date
    box_pad_x, box_pad_y = 20, 10
    box_x1 = PAD - box_pad_x
    box_y1 = content_y - box_pad_y
    box_x2 = PAD + dw + box_pad_x
    box_y2 = content_y + dh + box_pad_y

    # Semi-transparent filled rectangle (numpy blend)
    arr = np.array(img)
    region = arr[box_y1:box_y2, box_x1:box_x2].astype(np.float32)
    tint   = np.array(accent[:3], dtype=np.float32)
    region = region * 0.35 + tint * 0.65
    arr[box_y1:box_y2, box_x1:box_x2] = np.clip(region, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)

    # Rounded border on top of box
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2],
                            radius=10, outline=(255, 255, 255), width=2)

    # Left accent bar
    draw.rectangle([box_x1, box_y1, box_x1 + 6, box_y2],
                   fill=(255, 255, 255))

    # Date text (dark on accent background)
    date_fg = (0, 0, 0) if sum(accent) > 450 else (255, 255, 255)
    draw.text((PAD, content_y), date_text, font=fonts["date"], fill=date_fg)

    # Small star/diamond decorations either side
    star_y = content_y + dh // 2
    for sx in [box_x2 + 14, box_x2 + 30]:
        r = 5 if sx == box_x2 + 14 else 3
        draw.ellipse([sx - r, star_y - r, sx + r, star_y + r], fill=accent)

    content_y = box_y2 + int(content_h * 0.05)  # gap after date


    # ── Bottom bar ────────────────────────────────────────────
    arr = np.array(img)
    arr[bot_y:, :] = (arr[bot_y:, :].astype(np.float32) * 0.2 +
                      np.array([0, 0, 0], dtype=np.float32) * 0.8).astype(np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    draw.line([(0, bot_y), (TW, bot_y)], fill=accent, width=2)

    # Logo small bottom-left
    logo_sm = _load_logo(size=(38, 38))
    if logo_sm:
        try:
            img.paste(logo_sm, (PAD, bot_y + 12),
                      logo_sm if logo_sm.mode == "RGBA" else None)
        except Exception:
            img.paste(logo_sm, (PAD, bot_y + 12))
        draw = ImageDraw.Draw(img)

    handle = "@theaichronicle007"
    draw.text((PAD + 50, bot_y + 18), handle, font=fonts["hash"], fill=accent)

    hashtags = "#AI  #AINews  #ArtificialIntelligence"
    hw = _tw(draw, hashtags, fonts["small"])
    draw.text((TW - PAD - hw, bot_y + 22), hashtags,
              font=fonts["small"], fill=(190, 200, 230))

    return img


# ─────────────────────────────────────────────
# BACKGROUND SELECTION — random distinct pair each run
# ─────────────────────────────────────────────

def _pick_bg_indices():
    """Pick two distinct random background indices.
    Seeded from current minute so A and B agree when called in the same run."""
    import random as _rnd
    import time as _time
    paths = _list_backgrounds()
    n = len(paths)
    if n == 0:
        return 0, 1
    if n == 1:
        return 0, 0
    seed = int(_time.time()) // 60   # same value for both calls within a minute
    rng = _rnd.Random(seed)
    idx_a = rng.randrange(n)
    idx_b = rng.randrange(n - 1)
    if idx_b >= idx_a:
        idx_b += 1               # ensure A and B are always distinct
    logger.info(f"[THUMB] bg A={paths[idx_a].name}  B={paths[idx_b].name}")
    return idx_a, idx_b


# ─────────────────────────────────────────────
# VARIANT A — Navy / Electric Blue
# ─────────────────────────────────────────────

def generate_thumbnail_a(stories: list, date_str: str, out_path: Path) -> Path:
    idx_a, _ = _pick_bg_indices()
    img = _render_thumbnail(
        stories, date_str,
        accent      = (0, 210, 255),
        accent2     = (255, 180, 0),
        fallback_bg = (4, 10, 28),
        bg_index    = idx_a,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path))
    logger.info(f"[THUMB-A] {out_path.name}")
    return out_path


# ─────────────────────────────────────────────
# VARIANT B — Deep Purple / Violet
# ─────────────────────────────────────────────

def generate_thumbnail_b(stories: list, date_str: str, out_path: Path) -> Path:
    _, idx_b = _pick_bg_indices()
    img = _render_thumbnail(
        stories, date_str,
        accent      = (210, 100, 255),
        accent2     = (0, 230, 180),
        fallback_bg = (10, 4, 28),
        bg_index    = idx_b,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path))
    logger.info(f"[THUMB-B] {out_path.name}")
    return out_path


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from datetime import datetime
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sys.path.insert(0, str(Path(__file__).parent))
    from news_fetcher import FALLBACK_STORIES

    date_str = datetime.now().strftime("%B %d, %Y")
    out_dir = Path(__file__).parent.parent / "output" / "test_thumbnails"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_thumbnail_a(FALLBACK_STORIES, date_str, out_dir / "thumb_a.png")
    generate_thumbnail_b(FALLBACK_STORIES, date_str, out_dir / "thumb_b.png")
    print(f"Saved to {out_dir}")
