#!/usr/bin/env python3
"""
THE AI CHRONICLE — YouTube Video Generator
1920×1080 daily AI news video: 12 slides (intro + 10 stories + outro)
edge-tts narration · xfade slideleft transitions · auto thumbnail · metadata.txt
Completely independent from the Instagram pipeline.
"""

import asyncio
import hashlib
import json
import logging
import math
import os
import random
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

ROOT_ENV = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ROOT_ENV)

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR   = PROJECT_ROOT / "output"
LOG_DIR      = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Logo: youtube-posting/logo.PNG → fallback instagram-posting
LOGO_PATH = PROJECT_ROOT / "logo.PNG"
if not LOGO_PATH.exists():
    LOGO_PATH = Path(__file__).parent.parent.parent / "instagram-posting" / "logo.PNG"

# ffmpeg
_WINGET = (
    Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-8.1-full_build/bin/ffmpeg.exe"
)
FFMPEG_BIN = str(_WINGET) if _WINGET.exists() else "ffmpeg"

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
# CANVAS — 1920×1080 landscape
# ─────────────────────────────────────────────

W, H    = 1920, 1080
PAD     = 72
L_W     = 1080          # left column width
R_X     = L_W + 40      # right column start
R_W     = W - R_X - PAD # right column width

TTS_VOICE = "en-IN-PrabhatNeural"
TTS_RATE  = "+23%"
TTS_PITCH = "+8Hz"

# ─────────────────────────────────────────────
# FONTS
# ─────────────────────────────────────────────

_FONT_DIRS = [
    Path("C:/Windows/Fonts"),
    Path.home() / "AppData/Local/Microsoft/Windows/Fonts",
]
_SANS_N  = ["DejaVuSans.ttf",      "arial.ttf",     "segoeui.ttf"]
_SANS_B  = ["DejaVuSans-Bold.ttf", "arialbd.ttf",   "segoeuib.ttf"]
_SERIF_N = ["DejaVuSerif.ttf",     "georgia.ttf",   "arial.ttf"]
_SERIF_B = ["DejaVuSerif-Bold.ttf","georgiab.ttf",  "arialbd.ttf"]

def _ff(candidates):
    for n in candidates:
        for d in _FONT_DIRS:
            p = d / n
            if p.exists():
                return str(p)
    return None

def _ft(sz, bold=False, serif=False):
    path = _ff((_SERIF_B if bold else _SERIF_N) if serif else (_SANS_B if bold else _SANS_N))
    try:
        if path:
            return ImageFont.truetype(path, sz)
    except Exception:
        pass
    return ImageFont.load_default()

F  = lambda s, b=False: _ft(s, b, False)
SF = lambda s, b=False: _ft(s, b, True)

# ─────────────────────────────────────────────
# COLOR HELPERS
# ─────────────────────────────────────────────

def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _tw(d, t, f):
    bb = d.textbbox((0, 0), t, font=f)
    return bb[2] - bb[0]

def _th(d, t, f):
    bb = d.textbbox((0, 0), t, font=f)
    return bb[3] - bb[1]

def _al(img, fn):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(ov))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

def _ap(img, cr, x, y, w, h, a):
    return _al(img, lambda d: d.rectangle([x, y, x+w, y+h], fill=(*cr, a)))

def _wrap(d, t, f, max_w):
    lines, cur = [], ""
    for word in t.split():
        test = (cur + " " + word).strip()
        if _tw(d, test, f) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

# ─────────────────────────────────────────────
# THEMES — 10 saturated dark backgrounds
# ─────────────────────────────────────────────

THEMES = [
    ("dark",(8, 12, 55),(22, 8, 80),  "#F5C842","#FFFFFF","#0E0B30","#FFFFFF"),  # gold/deep violet
    ("dark",(18, 2, 48),(38, 0, 80),  "#C084FC","#FFFFFF","#120030","#FFFFFF"),  # purple/deep magenta
    ("dark",(55, 8,  8),(90,12, 12),  "#FF6B4A","#FFFFFF","#280400","#FFFFFF"),  # red/dark crimson
    ("dark",(0, 12, 55),(0, 20, 90),  "#60A5FA","#FFFFFF","#000C30","#FFFFFF"),  # blue/royal blue
    ("dark",(0, 22, 45),(0, 12, 75),  "#22D3EE","#FFFFFF","#001828","#FFFFFF"),  # cyan/deep teal
    ("dark",(30, 20,  0),(55,32,  0), "#FBBF24","#FFFFFF","#1A0E00","#FFFFFF"),  # amber/dark bronze
    ("dark",(0, 35, 18),(0, 55, 25),  "#34D399","#FFFFFF","#001E0A","#FFFFFF"),  # green/forest
    ("dark",(18, 5, 55),(28, 0, 80),  "#818CF8","#FFFFFF","#0C0038","#FFFFFF"),  # indigo/deep navy
    ("dark",(50,10, 10),(80,15, 15),  "#FB923C","#FFFFFF","#300800","#FFFFFF"),  # orange/dark rust
    ("dark",(0, 30, 40),(0, 45, 60),  "#2DD4BF","#FFFFFF","#001C28","#FFFFFF"),  # teal/deep ocean
]

# ─────────────────────────────────────────────
# BACKGROUND PATTERNS
# ─────────────────────────────────────────────

def _bg_nodes(img, acr, rng):
    centres = [(rng.randint(200,700),rng.randint(250,830)),
               (960,rng.randint(300,780)),
               (rng.randint(1200,1720),rng.randint(250,830))]
    nodes = []
    for cx, cy in centres:
        for _ in range(rng.randint(10, 16)):
            ag = rng.uniform(0, 6.28)
            r  = rng.uniform(30, 180)
            nodes.append((int(cx+r*math.cos(ag)), int(cy+r*math.sin(ag)), cx, cy))
    for p,(x1,y1,c1x,c1y) in enumerate(nodes):
        for q,(x2,y2,c2x,c2y) in enumerate(nodes):
            if p < q:
                ds   = math.hypot(x2-x1, y2-y1)
                same = (c1x == c2x and c1y == c2y)
                lim  = 200 if same else 130
                if ds < lim and rng.random() < (.75 if same else .05):
                    img = _al(img, lambda d, a=(x1,y1,x2,y2,ds,lim):
                        d.line([(a[0],a[1]),(a[2],a[3])],
                               fill=(*acr, max(4, int(28*(1-a[4]/a[5]))))))
    for rv, av in [(90,16),(140,11),(190,8)]:
        for cx, cy in centres:
            img = _al(img, lambda d, c=(cx,cy), r=rv, a=av:
                d.ellipse([c[0]-r,c[1]-r,c[0]+r,c[1]+r], outline=(*acr,a)))
    return img

def _bg_grid(img, acr, rng):
    g = rng.choice([80, 100, 120])
    for y in range(0, H, g):
        img = _al(img, lambda d, y=y: d.line([(0,y),(W,y)], fill=(*acr,12)))
    for x in range(0, W, g):
        img = _al(img, lambda d, x=x: d.line([(x,0),(x,H)], fill=(*acr,12)))
    return img

def _bg_rings(img, acr, rng):
    cx, cy = W//2, H//2 + rng.randint(-80, 80)
    for v, av in [(560,10),(430,14),(310,18),(200,16),(100,13)]:
        img = _al(img, lambda d, cx=cx, cy=cy, v=v, av=av:
            d.ellipse([cx-v,cy-v,cx+v,cy+v], outline=(*acr,av)))
    return img

def _bg_diag(img, acr, rng):
    for _ in range(rng.randint(18, 28)):
        x1, y1 = rng.randint(0, W), rng.randint(0, H)
        dx = rng.choice([-1,1]) * rng.randint(200, 500)
        dy = rng.randint(-200, 200)
        img = _al(img, lambda d, pts=(x1,y1,x1+dx,y1+dy):
            d.line([(pts[0],pts[1]),(pts[2],pts[3])], fill=(*acr,14)))
    return img

BG_FNS = [_bg_nodes, _bg_grid, _bg_rings, _bg_diag]

# ─────────────────────────────────────────────
# SLIDE RENDERERS
# ─────────────────────────────────────────────

def _make_gradient(bt, bb):
    img = Image.new("RGB", (W, H))
    d   = ImageDraw.Draw(img)
    for y in range(H):
        d.line([(0,y),(W,y)], fill=tuple(int(a*(1-y/H)+b*(y/H)) for a,b in zip(bt,bb)))
    return img


def render_story_slide(story: dict, story_num: int, total: int,
                        date_str: str, out_png: Path) -> None:
    """1920×1080 cinematic story slide — two-column broadcast layout."""
    sd  = int(hashlib.md5((story['headline']+story['company']).encode()).hexdigest()[:8], 16)
    rng = random.Random(sd)
    mo, bt, bb, ac, bc, sb, hc = THEMES[rng.randint(0, len(THEMES)-1)]
    bg_fn = BG_FNS[rng.randint(0, len(BG_FNS)-1)]
    acr   = rgb(ac)

    img = _make_gradient(bt, bb)

    # Faded watermark
    wf  = SF(320, b=True)
    wm  = story.get('watermark', 'AI')
    d_  = ImageDraw.Draw(img)
    img = _al(img, lambda dv: dv.text(
        ((W-_tw(dv,wm,wf))//2, (H-_th(dv,wm,wf))//2+60),
        wm, fill=(*acr,12), font=wf))

    img = bg_fn(img, acr, rng)
    img = Image.blend(img, Image.new("RGB",(W,H),tuple(bb)), alpha=.18)
    d   = ImageDraw.Draw(img)

    # Top accent bar
    d.rectangle([0, 0, W, 8], fill=acr)

    # Header band
    hdr_h = 96
    img = _ap(img, (0,0,0), 0, 8, W, hdr_h, 200)
    d   = ImageDraw.Draw(img)

    d.text((PAD, 18), "THE AI CHRONICLE", fill=(255,255,255), font=SF(48,b=True))
    dt_f = F(20)
    d.text(((W-_tw(d,date_str,dt_f))//2, 30), date_str, fill=rgb(ac), font=dt_f)

    if story_num > 0:
        badge = f"STORY  {story_num} / {total}"
        bf2   = F(18, b=True)
        bw    = _tw(d,badge,bf2)+40; bh = 36
        bx    = W-PAD-bw; by = 24
        d.rounded_rectangle([bx,by,bx+bw,by+bh], radius=18, fill=acr)
        d.text((bx+20, by+(bh-_th(d,badge,bf2))//2), badge, fill=(255,255,255), font=bf2)

    y = 8 + hdr_h
    d.line([(0,y),(W,y)], fill=acr, width=1)
    y += 32

    # ── LEFT COLUMN ──────────────────────────────────────
    lx      = PAD
    col_w   = L_W - PAD

    # Company pill
    pf = F(22, b=True); pl = story['company'].upper()
    pw = _tw(d, pl, pf) + 68
    d.rounded_rectangle([lx, y, lx+pw, y+52], radius=26, fill=acr)
    d.text((lx+34, y+(52-_th(d,pl,pf))//2), pl, fill=(255,255,255), font=pf)

    region = story.get('region', '')
    if region:
        d.text((lx+pw+20, y+12), region, fill=rgb(ac), font=F(28))
    y += 76

    # Headline
    hf      = SF(72, b=True)
    hl_lines = _wrap(d, story['headline'], hf, col_w)
    hl_h    = sum(_th(d,l,hf)+10 for l in hl_lines[:3]) + 20
    img     = _ap(img, (0,0,0), lx-12, y-8, col_w+24, hl_h, 200)
    d       = ImageDraw.Draw(img)
    for l in hl_lines[:3]:
        d.text((lx, y), l, fill=(255,255,255), font=hf)
        y += _th(d,l,hf) + 10
    y += 16

    # Summary quote
    summary = story.get('summary', '')
    if summary:
        sum_f    = F(26)
        sum_lines = _wrap(d, f'"{summary}"', sum_f, col_w)
        sh        = sum(_th(d,sl,sum_f)+8 for sl in sum_lines[:2]) + 16
        img       = _ap(img, (0,0,0), lx-12, y-4, col_w+24, sh, 185)
        d         = ImageDraw.Draw(img)
        for sl in sum_lines[:2]:
            d.text((lx, y), sl, fill=acr, font=sum_f)
            y += _th(d,sl,sum_f) + 8
        y += 14

    d.line([(lx,y),(lx+col_w,y)], fill=acr, width=2)
    y += 22

    # Body bullets 2×2 grid
    body_f = F(34)
    lh     = _th(d, story['body'][0], body_f) + 18
    img    = _ap(img, (0,0,0), 0, y-8, L_W+PAD, lh*2+16, 200)
    d      = ImageDraw.Draw(img)
    col_half = col_w // 2
    for row in range(2):
        for col in range(2):
            idx = row*2 + col
            if idx < len(story['body']):
                bx2 = lx if col == 0 else lx+col_half
                d.text((bx2, y+row*lh), f"• {story['body'][idx]}",
                       fill=(240,240,240), font=body_f)
    y += lh*2 + 20

    # Hashtag pills
    hashtags = story.get('hashtags', [])
    if hashtags:
        hf2 = F(17, b=True); pill_h = 30; gap = 8; hx = lx
        for tag in hashtags[:5]:
            tw2 = _tw(d, tag, hf2) + 24
            if hx + tw2 > L_W - PAD:
                break
            img = _al(img, lambda dv, hx=hx, y=y, tw2=tw2, ph=pill_h:
                dv.rounded_rectangle([hx,y,hx+tw2,y+ph], radius=15, fill=(*acr,45)))
            d = ImageDraw.Draw(img)
            d.rounded_rectangle([hx,y,hx+tw2,y+pill_h], radius=15, outline=acr, width=1)
            d.text((hx+12, y+(pill_h-_th(d,tag,hf2))//2), tag, fill=acr, font=hf2)
            hx += tw2 + gap
        y += pill_h + 16

    # Source
    src_c = (220,210,190)
    src_f = F(18)
    src_y = H - 80 - 38
    dot_r = 5
    img = _al(img, lambda dv, sy=src_y:
        dv.ellipse([lx,sy+6,lx+dot_r*2,sy+6+dot_r*2], fill=(*acr,140)))
    d = ImageDraw.Draw(img)
    d.text((lx+dot_r*2+8, src_y), story['source'], fill=src_c, font=src_f)

    # Vertical divider
    vd_x = L_W + 20
    img = _al(img, lambda dv:
        dv.line([(vd_x,8+hdr_h+32),(vd_x,H-80)], fill=(*acr,50), width=1))
    d = ImageDraw.Draw(img)

    # ── RIGHT COLUMN — stat card ──────────────────────────
    rx = R_X; rw = R_W
    card_h  = 240
    top_space = 8 + hdr_h + 32
    card_y  = top_space + (H-80-top_space-card_h)//2

    sl_t = story['stat_label']; sv_t = story['stat_value']
    sl_f = F(20); sv_f = SF(96, b=True)

    img = _ap(img, (0,0,0), rx, card_y, rw, card_h, 235)
    d   = ImageDraw.Draw(img)
    d.rounded_rectangle([rx,card_y,rx+rw,card_y+card_h], radius=20, outline=acr, width=4)

    sl_h = _th(d,sl_t,sl_f); sv_h = _th(d,sv_t,sv_f)
    ty   = card_y + (card_h - sl_h - 18 - sv_h) // 2
    d.text((rx+(rw-_tw(d,sl_t,sl_f))//2, ty), sl_t, fill=acr, font=sl_f)
    d.text((rx+(rw-_tw(d,sv_t,sv_f))//2, ty+sl_h+18), sv_t, fill=(255,255,255), font=sv_f)

    lbl_f = F(15)
    lbl_t = "THE AI CHRONICLE  •  " + date_str.upper()
    d.text((rx+(rw-_tw(d,lbl_t,lbl_f))//2, card_y+card_h+16), lbl_t,
           fill=(160,160,160), font=lbl_f)

    # Impact text
    impact = story.get('impact', '')
    if impact:
        imp_f  = F(21)
        imp_y  = card_y + card_h + 44
        imp_lines = _wrap(d, impact, imp_f, rw-8)
        panel_h   = sum(_th(d,il,imp_f)+9 for il in imp_lines[:4]) + 16
        img = _ap(img, (0,0,0), rx-4, imp_y-8, rw+8, panel_h, 200)
        d   = ImageDraw.Draw(img)
        for il in imp_lines[:4]:
            d.text((rx+(rw-_tw(d,il,imp_f))//2, imp_y), il, fill=(220,215,200), font=imp_f)
            imp_y += _th(d,il,imp_f) + 9

    # ── FOOTER ───────────────────────────────────────────
    fy = H - 80
    d.rectangle([0,fy,W,H], fill=rgb("#050912"))
    d.line([(0,fy),(W,fy)], fill=acr, width=1)

    if LOGO_PATH.exists():
        lg = Image.open(LOGO_PATH).convert("RGBA").resize((52,52), Image.LANCZOS)
        img.paste(lg, (PAD, fy+14), lg)

    d = ImageDraw.Draw(img)
    src_c2 = (min(acr[0]+60,210), min(acr[1]+45,190), min(acr[2]+45,190))
    d.text((PAD+62, fy+14), "@theaichronicle007  •  Daily AI News", fill=rgb(ac), font=F(18))
    d.text((PAD+62, fy+40), "Subscribe  •  Like  •  Ring the Bell", fill=src_c2, font=F(14))
    cta_f = F(16, b=True); cta_t = "SUBSCRIBE FOR DAILY AI NEWS"
    d.text((W-PAD-_tw(d,cta_t,cta_f), fy+28), cta_t, fill=acr, font=cta_f)

    d.rectangle([0, H-6, W, H], fill=acr)

    img.save(out_png, "PNG", dpi=(300, 300))
    logger.info(f"  Slide {story_num}/{total}: {out_png.name}")


def render_intro_slide(stories: list, date_str: str, out_png: Path) -> None:
    """Cover slide: full ordered story list on the left, stat card on right."""
    rng = random.Random(99)
    mo, bt, bb, ac, bc, sb, hc = THEMES[0]   # always gold theme for cover
    acr = rgb(ac)

    img = _make_gradient(bt, bb)
    wf  = SF(320, b=True)
    img = _al(img, lambda dv: dv.text(
        ((W-_tw(dv,"AI",wf))//2, (H-_th(dv,"AI",wf))//2+60),
        "AI", fill=(*acr,12), font=wf))
    img = _bg_nodes(img, acr, rng)
    img = Image.blend(img, Image.new("RGB",(W,H),tuple(bb)), alpha=.52)
    d   = ImageDraw.Draw(img)

    d.rectangle([0,0,W,8], fill=acr)
    hdr_h = 96
    img = _ap(img, (4,4,16), 0, 8, W, hdr_h, 220)
    d   = ImageDraw.Draw(img)
    d.text((PAD,18), "THE AI CHRONICLE", fill=(255,255,255), font=SF(48,b=True))
    d.text(((W-_tw(d,date_str,F(20)))//2, 30), date_str, fill=rgb(ac), font=F(20))

    badge = f"TODAY'S TOP {len(stories)} STORIES"
    bf2   = F(18,b=True); bw = _tw(d,badge,bf2)+40; bh = 36
    bx    = W-PAD-bw; by = 24
    d.rounded_rectangle([bx,by,bx+bw,by+bh], radius=18, fill=acr)
    d.text((bx+20, by+(bh-_th(d,badge,bf2))//2), badge, fill=(255,255,255), font=bf2)

    sep_y = 8 + hdr_h
    d.line([(0,sep_y),(W,sep_y)], fill=acr, width=1)

    content_top = sep_y + 18
    footer_y    = H - 80

    vd_x = L_W + 20
    img = _al(img, lambda dv: dv.line([(vd_x,content_top),(vd_x,footer_y)], fill=(*acr,50), width=1))
    d   = ImageDraw.Draw(img)

    # Story list — fill left column
    lx       = PAD
    col_w    = L_W - PAD - 24
    n        = len(stories)
    avail_h  = footer_y - content_top - 8
    item_h   = avail_h // n
    num_f    = F(16,b=True); head_f = F(19,b=True); summ_f = F(15)
    summ_c   = (min(acr[0]+60,210), min(acr[1]+45,190), min(acr[2]+45,190))

    for i, s in enumerate(stories):
        iy = content_top + i*item_h
        num_tx = f"{i+1:02d}"
        nw = _tw(d,num_tx,num_f)+14; nh = _th(d,num_tx,num_f)+8
        d.rounded_rectangle([lx,iy+4,lx+nw,iy+4+nh], radius=5, fill=acr)
        d.text((lx+7, iy+4+(nh-_th(d,num_tx,num_f))//2), num_tx, fill=(255,255,255), font=num_f)

        tx = lx+nw+12; mhw = col_w-nw-12
        hl = s['headline']
        while _tw(d,hl+"…",head_f) > mhw and len(hl) > 8:
            hl = hl.rsplit(' ',1)[0]
        if hl != s['headline']:
            hl += "…"
        co_tx = s['company'].upper()
        full  = f"{co_tx}  ·  {hl}"
        if _tw(d,full,head_f) <= mhw:
            d.text((tx,iy+5), full, fill=rgb(hc), font=head_f)
        else:
            d.text((tx,iy+5), co_tx, fill=acr, font=num_f)
            d.text((tx+_tw(d,co_tx,num_f)+12, iy+5), hl, fill=rgb(hc), font=head_f)

        summary = s.get('summary', s['body'][0] if s.get('body') else '')
        if summary:
            slines = _wrap(d, summary, summ_f, mhw)
            d.text((tx, iy+28), slines[0] if slines else summary, fill=summ_c, font=summ_f)

        if i < n-1:
            sy = iy + item_h - 1
            img = _al(img, lambda dv, _sy=sy:
                dv.line([(lx,_sy),(L_W-20,_sy)], fill=(*acr,22), width=1))
            d = ImageDraw.Draw(img)

    # Right stat card
    rx = R_X; rw = R_W
    card_h = 220; card_y = content_top + (footer_y-content_top-card_h)//2
    sl_t = f"{n} Stories Today"
    sv_t = date_str.split(",")[0] if "," in date_str else "Today"
    sl_f = F(20); sv_f = SF(88,b=True)
    d.rounded_rectangle([rx,card_y,rx+rw,card_y+card_h], radius=20, fill=rgb(sb))
    d.rounded_rectangle([rx,card_y,rx+rw,card_y+card_h], radius=20, outline=acr, width=3)
    sl_h = _th(d,sl_t,sl_f); sv_h = _th(d,sv_t,sv_f)
    ty   = card_y + (card_h-sl_h-18-sv_h)//2
    d.text((rx+(rw-_tw(d,sl_t,sl_f))//2, ty), sl_t, fill=acr, font=sl_f)
    d.text((rx+(rw-_tw(d,sv_t,sv_f))//2, ty+sl_h+18), sv_t, fill=rgb(hc), font=sv_f)
    lbl_f = F(14); lbl_t = "THE AI CHRONICLE  •  " + date_str.upper()
    d.text((rx+(rw-_tw(d,lbl_t,lbl_f))//2, card_y+card_h+14), lbl_t, fill=(150,150,150), font=lbl_f)

    # Footer
    d.rectangle([0,footer_y,W,H], fill=rgb("#050912"))
    d.line([(0,footer_y),(W,footer_y)], fill=acr, width=1)
    if LOGO_PATH.exists():
        lg = Image.open(LOGO_PATH).convert("RGBA").resize((52,52), Image.LANCZOS)
        img.paste(lg, (PAD, footer_y+14), lg)
    d = ImageDraw.Draw(img)
    src_c2 = (min(acr[0]+60,210), min(acr[1]+45,190), min(acr[2]+45,190))
    d.text((PAD+62, footer_y+14), "@theaichronicle007  •  Daily AI News", fill=rgb(ac), font=F(18))
    d.text((PAD+62, footer_y+40), "Subscribe  •  Like  •  Ring the Bell", fill=src_c2, font=F(14))
    d.rectangle([0, H-6, W, H], fill=acr)

    img.save(out_png, "PNG", dpi=(300,300))
    logger.info(f"  Slide 0/intro: {out_png.name}")


# ─────────────────────────────────────────────
# THUMBNAIL — 1280×720
# ─────────────────────────────────────────────

def generate_thumbnail(stories: list, date_str: str, out_path: Path) -> Path:
    TW, TH   = 1280, 720
    PAD_L    = 44
    PAD_R    = 44

    # ── Brand palette ─────────────────────────────────────────────────
    GOLD   = rgb("#F5C518")   # bright yellow-gold
    RED    = rgb("#E8273A")   # vivid red
    CYAN   = rgb("#06C8E0")   # electric teal
    PURPLE = rgb("#9F6EFF")   # medium purple
    GREEN  = rgb("#22D46A")   # bright green
    ORANGE = rgb("#FF8C1A")   # amber orange
    WHITE  = (255, 255, 255)
    NEAR_W = (230, 235, 248)  # off-white for body text
    DIM_W  = (150, 158, 180)  # dimmed white for secondary

    ROW_ACCENTS = [CYAN, PURPLE, GREEN, ORANGE]

    # ── Background — near-black base + glows ──────────────────────────
    yy, xx = np.mgrid[0:TH, 0:TW].astype(np.float32)
    # Very dark navy base (max ~30 brightness)
    r = ( 5 + xx/TW*10 + yy/TH* 6).clip(0, 255)
    g = ( 6 + xx/TW* 6 + yy/TH* 8).clip(0, 255)
    b = (16 + xx/TW*16 + yy/TH*20).clip(0, 255)
    base = np.stack([r, g, b], axis=2).astype(np.float32)

    # Teal glow — upper-right
    dist_t = np.sqrt((xx - TW*0.82)**2 + (yy - TH*0.12)**2)
    glow_t = np.clip(1.0 - dist_t/520.0, 0, 1)**2.0
    base[:,:,1] += glow_t * 38;  base[:,:,2] += glow_t * 90

    # Gold glow — lower-left
    dist_g = np.sqrt((xx - TW*0.08)**2 + (yy - TH*0.88)**2)
    glow_g = np.clip(1.0 - dist_g/420.0, 0, 1)**2.5
    base[:,:,0] += glow_g * 60;  base[:,:,1] += glow_g * 40

    img = Image.fromarray(base.clip(0, 255).astype(np.uint8))

    # Subtle hex grid
    hex_ov = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hex_ov)
    HS, row_h = 50, int(50 * 1.732)
    for row in range(-1, TH // row_h + 3):
        for col in range(-1, TW // int(HS * 1.5) + 3):
            hx = col * int(HS * 1.5)
            hy = row * row_h + (col % 2) * (row_h // 2)
            pts = [(hx + HS * math.cos(math.radians(60 * i + 30)),
                    hy + HS * math.sin(math.radians(60 * i + 30))) for i in range(6)]
            hd.polygon(pts, outline=(80, 220, 255, 10))
    img = Image.alpha_composite(img.convert("RGBA"), hex_ov).convert("RGB")

    d = ImageDraw.Draw(img)

    # ── TOP BAR (0 → TOP_H) ──────────────────────────────────────────
    TOP_H = 62
    img = _al(img, lambda dv: dv.rectangle([0, 0, TW, TOP_H], fill=(0, 0, 0, 200)))
    img = _al(img, lambda dv: dv.rectangle([0, TOP_H - 2, TW, TOP_H], fill=(*GOLD, 180)))
    d = ImageDraw.Draw(img)

    # Logo
    lw_logo = 0
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        lh_ = 46
        lw_logo = int(logo.width * lh_ / logo.height)
        logo = logo.resize((lw_logo, lh_), Image.LANCZOS)
        img.paste(logo, (PAD_L, (TOP_H - lh_) // 2), logo)
        d = ImageDraw.Draw(img)

    # Channel name beside logo
    f_chan = F(22, b=True)
    chan_x = PAD_L + lw_logo + (12 if lw_logo else 0)
    d.text((chan_x, (TOP_H - _th(d, "Ag", f_chan)) // 2),
           "THE AI CHRONICLE", fill=WHITE, font=f_chan)

    # Date badge — top-right
    try:
        dt_obj  = datetime.strptime(date_str, "%B %d, %Y")
        date_tx = dt_obj.strftime("%b %d, %Y").upper()
    except Exception:
        date_tx = (date_str or "DAILY DIGEST").upper()
    f_date  = F(18, b=True)
    d_tmp   = ImageDraw.Draw(img)
    dbw     = _tw(d_tmp, date_tx, f_date) + 28
    dbh     = 32
    dbx     = TW - PAD_R - dbw
    dby     = (TOP_H - dbh) // 2
    img = _al(img, lambda dv, x=dbx, y=dby, w=dbw, h=dbh:
        dv.rounded_rectangle([x, y, x+w, y+h], radius=16, fill=(*GOLD, 210)))
    d = ImageDraw.Draw(img)
    d.text((dbx + 14, dby + (dbh - _th(d, date_tx, f_date)) // 2),
           date_tx, fill=(10, 10, 20), font=f_date)

    # ── HERO SECTION (TOP_H → HERO_BOT) ─────────────────────────────
    # Layout: label · big headline · source + company pills
    CTA_H    = 56
    ROW_H    = 46
    ROW_GAP  = 5
    N_ROWS   = 4
    ROWS_BLK = N_ROWS * ROW_H + (N_ROWS - 1) * ROW_GAP
    ROWS_TOP = TH - CTA_H - ROWS_BLK - 10
    HERO_BOT = ROWS_TOP - 10
    HERO_TOP = TOP_H + 12

    # Ordered: hero is always story[0], rows are 1-4
    thumb_stories = list(stories)[:5]
    hero = thumb_stories[0] if thumb_stories else {"headline": "AI NEWS TODAY",
                                                    "company": "AI", "source": ""}

    # Sub-label
    f_sub = F(17, b=True)
    sub_tx = "TODAY'S TOP 10 AI STORIES"
    d.text((PAD_L, HERO_TOP + 4), sub_tx, fill=(*GOLD, 210), font=f_sub)
    sub_h = _th(d, sub_tx, f_sub) + 10

    # Big hero headline — auto-fit to 3 lines max in available width
    HERO_TW = TW - PAD_L - PAD_R
    f_hero  = F(72, b=True)
    while f_hero.size > 38:
        lines = _wrap(d, hero.get("headline", "AI NEWS TODAY").upper(), f_hero, HERO_TW)
        if len(lines) <= 3:
            break
        f_hero = F(f_hero.size - 4, b=True)

    hero_lines = _wrap(d, hero.get("headline", "AI NEWS TODAY").upper(), f_hero, HERO_TW)[:3]
    lh_h = _th(d, "Ag", f_hero) + 4
    total_hero_h = len(hero_lines) * lh_h

    # Vertically centre headline in available hero space
    avail_hero = HERO_BOT - HERO_TOP - sub_h - 42  # 42 reserved for pills below
    hy = HERO_TOP + sub_h + max(0, (avail_hero - total_hero_h) // 2)

    for li, line in enumerate(hero_lines):
        fill_c = WHITE if li == 0 else NEAR_W
        d.text((PAD_L, hy), line, fill=fill_c, font=f_hero)
        hy += lh_h

    # Company + source pills below headline
    pill_y = hy + 8
    f_pill = F(18, b=True)
    px = PAD_L
    for pill_tx, pill_col in [
        (hero.get("company", "")[:22], CYAN),
        (hero.get("source",  "")[:22], GOLD),
    ]:
        if not pill_tx:
            continue
        pw = _tw(d, pill_tx, f_pill) + 26
        ph = 30
        img = _al(img, lambda dv, x=px, y=pill_y, w=pw, h=ph, c=pill_col:
            dv.rounded_rectangle([x, y, x+w, y+h], radius=15, fill=(*c, 45)))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([px, pill_y, px + pw, pill_y + ph],
                            radius=15, outline=(*pill_col, 220), width=1)
        d.text((px + 13, pill_y + (ph - _th(d, pill_tx, f_pill)) // 2),
               pill_tx, fill=pill_col, font=f_pill)
        px += pw + 10

    # ── NEWS ROWS (stories 2–5) ───────────────────────────────────────
    f_num  = F(19, b=True)    # story number
    f_co   = F(15, b=True)    # company label
    f_hl   = F(21, b=True)    # headline
    f_src  = F(14)             # source

    for ri, story in enumerate(thumb_stories[1:5]):
        ac  = ROW_ACCENTS[ri]
        ry  = ROWS_TOP + ri * (ROW_H + ROW_GAP)

        # Row background — dark semi-transparent card
        img = _al(img, lambda dv, y=ry, h=ROW_H:
            dv.rectangle([0, y, TW, y + h], fill=(0, 0, 0, 155)))
        # Left accent bar (4 px)
        img = _al(img, lambda dv, y=ry, h=ROW_H, c=ac:
            dv.rectangle([0, y, 4, y + h], fill=(*c, 255)))
        d = ImageDraw.Draw(img)

        # Story number
        num_tx = f"#{ri + 2}"
        num_w  = _tw(d, num_tx, f_num)
        d.text((10, ry + (ROW_H - _th(d, num_tx, f_num)) // 2),
               num_tx, fill=(*GOLD, 230), font=f_num)

        # Company pill
        co_raw = story.get("company", "AI")[:18]
        co_pw  = _tw(d, co_raw, f_co) + 18
        co_ph  = 26
        co_px  = 10 + num_w + 10
        co_py  = ry + (ROW_H - co_ph) // 2
        img = _al(img, lambda dv, x=co_px, y=co_py, w=co_pw, h=co_ph, c=ac:
            dv.rounded_rectangle([x, y, x+w, y+h], radius=13, fill=(*c, 55)))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([co_px, co_py, co_px + co_pw, co_py + co_ph],
                            radius=13, outline=(*ac, 200), width=1)
        d.text((co_px + 9, co_py + (co_ph - _th(d, co_raw, f_co)) // 2),
               co_raw, fill=ac, font=f_co)

        # Source — right-aligned, always visible
        src_raw = story.get("source", "")[:20]
        src_w   = _tw(d, src_raw, f_src) + 8
        src_x   = TW - PAD_R - src_w + 4
        src_y   = ry + (ROW_H - _th(d, src_raw, f_src)) // 2
        if src_raw:
            # Subtle source badge
            img = _al(img, lambda dv, x=src_x-4, y=src_y-2, w=src_w, h=_th(d,src_raw,f_src)+4:
                dv.rectangle([x, y, x+w, y+h], fill=(255, 255, 255, 12)))
            d = ImageDraw.Draw(img)
            d.text((src_x, src_y), src_raw, fill=(*DIM_W, 230), font=f_src)

        # Headline — fills space between company pill and source badge
        hl_x     = co_px + co_pw + 12
        hl_max_w = src_x - hl_x - 16
        hl_full  = story.get("headline", "")
        # Fit to one line by trimming words
        hl_tx = hl_full
        while hl_tx and _tw(d, hl_tx, f_hl) > hl_max_w:
            parts = hl_tx.rsplit(" ", 1)
            hl_tx = parts[0] if len(parts) > 1 else hl_tx[:-1]
        if hl_tx != hl_full:
            # Remove trailing partial word then add ellipsis
            hl_tx = hl_tx.rstrip(" ,.;:") + "..."
        d.text((hl_x, ry + (ROW_H - _th(d, hl_tx, f_hl)) // 2),
               hl_tx, fill=WHITE, font=f_hl)

    # ── CTA BAR (bottom CTA_H px) ────────────────────────────────────
    CTA_Y = TH - CTA_H
    img = _al(img, lambda dv: dv.rectangle([0, CTA_Y, TW, TH], fill=(0, 0, 0, 230)))
    img = _al(img, lambda dv: dv.rectangle([0, CTA_Y, TW, CTA_Y + 2], fill=(*RED, 200)))
    d = ImageDraw.Draw(img)

    f_cta   = F(22, b=True)
    BTN_H   = 38
    BTN_R   = 19
    btn_cy  = CTA_Y + (CTA_H - BTN_H) // 2

    CTA_ITEMS  = [("LIKE", GOLD), ("SUBSCRIBE", RED), ("COMMENT", CYAN)]
    # Measure channel handle first so we know how much space buttons have
    ch_tx  = "@theaichronicle007"
    f_ch   = F(20, b=True)
    ch_w   = _tw(d, ch_tx, f_ch)
    ch_x   = TW - PAD_R - ch_w
    d.text((ch_x, CTA_Y + (CTA_H - _th(d, ch_tx, f_ch)) // 2),
           ch_tx, fill=(*GOLD, 220), font=f_ch)

    # Distribute buttons evenly in [PAD_L … ch_x - PAD_L]
    btn_widths  = [_tw(d, lbl, f_cta) + 40 for lbl, _ in CTA_ITEMS]
    total_bw    = sum(btn_widths)
    usable_w    = ch_x - PAD_L - 20
    gap         = max(14, (usable_w - total_bw) // (len(CTA_ITEMS) + 1))

    bx = PAD_L + gap
    for (label, col), bw in zip(CTA_ITEMS, btn_widths):
        img = _al(img, lambda dv, x=bx, y=btn_cy, w=bw, h=BTN_H, c=col:
            dv.rounded_rectangle([x, y, x+w, y+h], radius=BTN_R, fill=(*c, 55)))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([bx, btn_cy, bx + bw, btn_cy + BTN_H],
                            radius=BTN_R, outline=(*col, 240), width=2)
        d.text((bx + 20, btn_cy + (BTN_H - _th(d, label, f_cta)) // 2),
               label, fill=col, font=f_cta)
        bx += bw + gap

    img.save(str(out_path), quality=95)
    logger.info(f"[OK] Thumbnail: {out_path.name}  (1280×720)")
    return out_path

# ─────────────────────────────────────────────
# TTS — edge-tts
# ─────────────────────────────────────────────

async def _tts_async(text: str, out_mp3: Path):
    import edge_tts
    await edge_tts.Communicate(
        text=text, voice=TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH
    ).save(str(out_mp3))

def generate_tts(text: str, out_mp3: Path):
    asyncio.run(_tts_async(text, out_mp3))
    logger.info(f"[TTS] {out_mp3.name}  ({len(text.split())} words)")

# ─────────────────────────────────────────────
# AUDIO DURATION
# ─────────────────────────────────────────────

def _audio_dur(path: Path) -> float:
    ffprobe = str(Path(FFMPEG_BIN).parent / "ffprobe.exe")
    if not Path(ffprobe).exists():
        ffprobe = "ffprobe"
    r = subprocess.run(
        [ffprobe,"-v","quiet","-show_entries","format=duration",
         "-of","default=noprint_wrappers=1:nokey=1",str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 20.0

# ─────────────────────────────────────────────
# VIDEO COMPOSER — xfade slideleft transitions
# ─────────────────────────────────────────────

def compose_video(png_paths: list, tts_files: list, out_mp4: Path,
                   transition: str = "slideleft", trans_dur: float = 0.5,
                   pad: float = 0.8) -> list:
    n = len(png_paths)
    durations = []
    for i, tts in enumerate(tts_files):
        d = _audio_dur(tts)
        durations.append(d + (1.5 if i == n-1 else pad))

    total = sum(durations) - (n-1)*trans_dur
    logger.info(f"[VIDEO] {n} slides · {total:.1f}s ({total/60:.1f} min)")

    cmd = [FFMPEG_BIN, "-y"]
    for png, dur in zip(png_paths, durations):
        cmd += ["-loop","1","-t",str(dur),"-r","30","-i",str(png).replace("\\","/")]
    for tts in tts_files:
        cmd += ["-i", str(tts).replace("\\","/")]

    fc = []
    for i in range(n):
        fc.append(f"[{i}:v]fps=30,scale={W}:{H},format=yuv420p[v{i}]")

    cum = 0.0; v_prev = "v0"
    for i in range(n-1):
        cum += durations[i]; off = cum - (i+1)*trans_dur
        v_next = f"v{i+1}"; v_out = "vout" if i == n-2 else f"vx{i}"
        fc.append(f"[{v_prev}][{v_next}]xfade=transition={transition}:"
                  f"duration={trans_dur:.3f}:offset={off:.3f}[{v_out}]")
        v_prev = v_out

    fc.append("".join(f"[{n+i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[audio]")

    cmd += [
        "-filter_complex", ";".join(fc),
        "-map", "[vout]", "-map", "[audio]",
        "-c:v","libx264","-preset","fast","-crf","18",
        "-c:a","aac","-b:a","192k",
        "-pix_fmt","yuv420p","-movflags","+faststart",
        str(out_mp4).replace("\\","/"),
    ]

    logger.info(f"[VIDEO] Composing {n}-slide video...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg error:\n{r.stderr[-1500:]}")
    logger.info(f"[OK] Video saved: {out_mp4.name}")
    return durations

# ─────────────────────────────────────────────
# METADATA .TXT
# ─────────────────────────────────────────────

def write_metadata(stories: list, date_str: str, mp4_path: Path,
                    thumb_path: Path, out_path: Path):
    top    = stories[0] if stories else {}
    second = stories[1] if len(stories) > 1 else {}

    top_hl  = top.get("headline","AI News Today")
    sec_co  = second.get("company","")
    date_sh = datetime.now().strftime("%b %d")
    title   = f"{top_hl} | {sec_co} & More — {date_sh}"
    if len(title) > 70:
        title = f"{top_hl[:50]}… | {date_sh}"

    # Timestamps (~36s per story + 6s intro)
    stamps = ["0:00 Intro"]
    t = 6
    for i, s in enumerate(stories, 1):
        m, sec = divmod(t, 60)
        stamps.append(f"{m}:{sec:02d} {s.get('company','Story '+str(i))} — {s.get('headline','')[:50]}")
        t += 36
    m, sec = divmod(t, 60)
    stamps.append(f"{m}:{sec:02d} Outro")

    story_lines = "\n".join(
        f"{i}. [{s.get('region','')}] {s.get('company','')} — {s.get('headline','')}. "
        f"{s.get('summary','')[:120]}"
        for i, s in enumerate(stories, 1)
    )

    seen_tags: set = set(); inline_tags: list = []
    for s in stories:
        for tag in s.get("hashtags",[]):
            if tag not in seen_tags:
                seen_tags.add(tag); inline_tags.append(tag)
            if len(inline_tags) >= 8:
                break
    inline_tags_str = " ".join(inline_tags[:8])

    description = (
        f"{top.get('summary',top_hl)} — watch all {len(stories)} stories now!\n\n"
        f"{story_lines}\n\n"
        f"⏱ TIMESTAMPS\n{chr(10).join(stamps)}\n\n"
        f"👍 Like | 💬 Comment | 🔔 Subscribe & Ring the Bell\n\n"
        f"Drop a comment — which story surprised you most today?\n\n"
        f"{inline_tags_str}"
    )

    companies   = list(dict.fromkeys(s.get("company","") for s in stories if s.get("company")))
    keywords    = (
        ["TheAIChronicle","AI News","Daily AI","Artificial Intelligence","AI 2026"]
        + companies[:8]
        + ["machine learning","LLM","ChatGPT","OpenAI","Google AI",
           "AI agents","generative AI","AI research","tech news","AI today"]
    )
    keywords_str = ", ".join(keywords[:20])

    brand_tags   = "#TheAIChronicle #AINews #DailyAI #ArtificialIntelligence #AIUpdate"
    company_tags = " ".join(f"#{c.replace(' ','')}" for c in companies[:5])
    topic_tags   = "#MachineLearning #LLM #GenerativeAI #AIResearch #DeepLearning"
    action_tags  = "#Subscribe #WatchNow #MustWatch #TechNews #AI2026"

    top3 = list(dict.fromkeys(
        tag for s in stories[:3] for tag in s.get("hashtags",[])
    ))[:3]

    lines = [
        f"YouTube Upload Metadata — {date_str}",
        "="*62,
        f"MP4  : {mp4_path}",
        f"THUMB: {thumb_path}",
        "",
        "TITLE",
        "-"*40,
        title,
        "",
        "DESCRIPTION",
        "-"*40,
        description,
        "",
        "KEYWORDS / TAGS (20)",
        "-"*40,
        keywords_str,
        "",
        "HASHTAGS (20)",
        "-"*40,
        f"{brand_tags}\n{company_tags}\n{topic_tags}\n{action_tags}",
        "",
        "DEFAULT UPLOAD SETTINGS",
        "-"*40,
        "Category : Science & Technology",
        "Language : English (India)",
        "Audience : Not made for kids",
        "Visibility: Public",
        "Playlist : AI Chronicle Daily News",
        "",
        "TOP 3 DISCOVERY HASHTAGS",
        "-"*40,
    ] + [f"  {t}" for t in top3]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"[OK] Metadata saved: {out_path.name}")

# ─────────────────────────────────────────────
# SLIDE SCRIPTS
# ─────────────────────────────────────────────

INTRO_STORY = {
    "company":    "The AI Chronicle",
    "headline":   "Your Daily AI World Briefing",
    "watermark":  "AI NEWS",
    "body":       ["Top stories today","Global AI updates","Like & Subscribe","Ring the Bell"],
    "stat_label": "Stories today",
    "stat_value": "10 stories",
    "source":     "@theaichronicle007",
    "region":     "",
    "summary":    "Your daily AI briefing starts now.",
    "impact":     "",
    "hashtags":   [],
}

OUTRO_STORY = {
    "company":    "The AI Chronicle",
    "headline":   "Subscribe for Daily AI News",
    "watermark":  "SUBSCRIBE",
    "body":       ["New episode every day","Hit the Like button","Ring the bell","Comment your take"],
    "stat_label": "New episodes",
    "stat_value": "Every Day",
    "source":     "@theaichronicle007",
    "region":     "",
    "summary":    "See you tomorrow on The AI Chronicle.",
    "impact":     "",
    "hashtags":   [],
}

INTRO_TTS = (
    "Welcome to The AI Chronicle — your daily AI news briefing. "
    "Before we dive in, if you find this valuable, please hit Like, Subscribe, "
    "and ring the notification bell so you never miss an episode. "
    "Here are today's top AI stories."
)

OUTRO_TTS = (
    "That's a wrap on today's AI world. The pace of change in artificial intelligence "
    "is extraordinary — and we're here to keep you ahead of it every single day. "
    "If today's stories opened your eyes, smash that Like button and Subscribe. "
    "Drop a comment — which story surprised you most? "
    "See you tomorrow on The AI Chronicle."
)

# ─────────────────────────────────────────────
# MAIN GENERATE FUNCTION
# ─────────────────────────────────────────────

def generate(stories: list) -> dict:
    """
    Full generation pipeline: slides → TTS → video → thumbnail → metadata.
    Returns dict of output paths.
    """
    from news_fetcher import FALLBACK_STORIES

    if not stories:
        stories = FALLBACK_STORIES

    date_str = datetime.now().strftime("%B %d, %Y")
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Output dir named after top story
    import re as _re
    slug = stories[0]['headline'].lower()
    slug = _re.sub(r'[^a-z0-9\s]', '', slug)
    slug = _re.sub(r'\s+', '_', slug.strip())[:50]
    post_dir = OUTPUT_DIR / f"{ts}_{slug}"
    post_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output: {post_dir.name}")

    tmpdir = post_dir
    n = len(stories)

    # Update intro stat
    INTRO_STORY['stat_value'] = f"{n} stories"
    INTRO_STORY['body'][0]    = f"{n} top stories today"

    all_slides   = [INTRO_STORY] + stories + [OUTRO_STORY]
    tts_scripts  = [INTRO_TTS] + [s["tts_script"] for s in stories] + [OUTRO_TTS]
    total_slides = len(all_slides)

    # ── 1. TTS ─────────────────────────────────────────────
    logger.info(f"[TTS] Generating {total_slides} segments ({TTS_VOICE})...")
    tts_paths = []
    for i, script in enumerate(tts_scripts):
        p = tmpdir / f"_tts_{i}.mp3"
        generate_tts(script, p)
        tts_paths.append(p)

    # ── 2. Render slides ────────────────────────────────────
    logger.info(f"[SLIDES] Rendering {total_slides} slides (1920×1080)...")
    png_paths = []
    for i, story in enumerate(all_slides):
        p = tmpdir / f"_slide_{i}.png"
        if i == 0:
            render_intro_slide(stories, date_str, p)
        else:
            story_num = 0 if i == total_slides-1 else i
            render_story_slide(story, story_num, n, date_str, p)
        png_paths.append(p)

    # ── 3. Compose video ────────────────────────────────────
    mp4_path = post_dir / f"yt_daily_{ts}.mp4"
    compose_video(png_paths, tts_paths, mp4_path)

    # ── 4. Cover PNG (copy of intro slide) ─────────────────
    cover_path = post_dir / f"yt_cover_{ts}.png"
    shutil.copy2(png_paths[0], cover_path)

    # ── 5. Thumbnail ────────────────────────────────────────
    thumb_path = post_dir / f"yt_thumb_{ts}.jpg"
    generate_thumbnail(stories, date_str, thumb_path)

    # ── 6. Metadata .txt ────────────────────────────────────
    meta_path = post_dir / f"yt_meta_{ts}.txt"
    write_metadata(stories, date_str, mp4_path, thumb_path, meta_path)

    # ── 7. JSON metadata ────────────────────────────────────
    json_path = post_dir / f"yt_metadata_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp":  datetime.now().isoformat(),
            "date":       date_str,
            "stories":    stories,
            "mp4":        str(mp4_path),
            "thumbnail":  str(thumb_path),
            "cover":      str(cover_path),
            "metadata":   str(meta_path),
        }, f, indent=2, ensure_ascii=False)

    # ── 8. Clean up temp files ──────────────────────────────
    for p in tts_paths + png_paths:
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass

    logger.info("="*62)
    logger.info("GENERATION COMPLETE")
    logger.info(f"  MP4   : {mp4_path.name}")
    logger.info(f"  THUMB : {thumb_path.name}")
    logger.info(f"  META  : {meta_path.name}")
    logger.info("="*62)

    return {
        "post_dir":  post_dir,
        "mp4":       mp4_path,
        "thumbnail": thumb_path,
        "cover":     cover_path,
        "metadata_txt": meta_path,
        "metadata_json": json_path,
        "stories":   stories,
        "date":      date_str,
    }


if __name__ == "__main__":
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from news_fetcher import fetch_todays_stories, FALLBACK_STORIES

    logger.info("Fetching stories...")
    stories = fetch_todays_stories()
    if not stories:
        logger.warning("Using fallback stories")
        stories = FALLBACK_STORIES

    result = generate(stories)
    print(f"\nOutput dir : {result['post_dir']}")
    print(f"MP4        : {result['mp4']}")
    print(f"Thumbnail  : {result['thumbnail']}")
    print(f"Metadata   : {result['metadata_txt']}")
