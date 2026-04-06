#!/usr/bin/env python3
"""
Video Composer — "The AI Chronicle: Editors View — Will AI Take My Job?"
12 slides (1 intro + 10 content + 1 branding outro) @ 1920x1080.

Run from project root:
    python AI-Mixed-content/video-pipeline/will-ai-take-my-job/generate_video.py
"""

import subprocess, shutil, tempfile, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE     = Path(__file__).parent
GRAPHICS = HERE / "output" / "graphics"
ASSETS   = HERE / "output" / "assets"
AUDIO    = HERE / "output" / "audio" / "voiceover_prabhat_v4.mp3"
MUSIC    = HERE / "output" / "audio" / "music_bed.wav"
OUT_DIR  = HERE / "output" / "video"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "will_ai_take_my_job.mp4"

# ── Brand colours ──────────────────────────────────────────────────────────────
CYAN    = (0, 210, 255)
WHITE   = (255, 255, 255)
LGRAY   = (192, 200, 216)
DARK    = (8,  12,  28)
BLACK   = (0,   0,   0)
RED_CTA = (210,  40,  40)
W, H    = 1920, 1080

# ── Timing — 360 seconds total (6 minutes) ────────────────────────────────────
TOTAL_AUDIO = 390.0   # 1041 words @ +12% rate ≈ 6.5 min
# Proportional weights per slide (12 slides): intro + 10 content + outro
PLAN        = [25, 40, 50, 50, 25, 25, 25, 25, 35, 30, 30, 15]
SCALE       = TOTAL_AUDIO / sum(PLAN)
DURATIONS   = [round(p * SCALE, 2) for p in PLAN]
DURATIONS[-1] = round(TOTAL_AUDIO - sum(DURATIONS[:-1]), 2)
print("Slide durations (s):", DURATIONS)
print("Total:", sum(DURATIONS))

# ── Slide content — 12 slides ─────────────────────────────────────────────────
SLIDES = [
    # ── SLIDE 0 — Intro / Thumbnail ──────────────────────────────────────────
    {
        "type":    "intro",
        "bg":      "BG-01-title.png",
        "label":   "THE AI CHRONICLE: EDITORS VIEW",
        "hook":    "WILL AI\nTAKE\nMY JOB?",
        "bullets": [],
        "sub":     "A practical answer for every working person.",
        "date":    "APR 2026",
        "cta":     None,
    },
    # ── SLIDE 1 — The Number One Question ────────────────────────────────────
    {
        "type":    "content",
        "bg":      "BG-02-search.png",
        "label":   "SCENE 1  —  THE #1 QUESTION",
        "hook":    "EVERYONE\nIS ASKING",
        "bullets": [
            "People fear being left behind — not just replaced.",
            "AI tools are improving every few months.",
            "Question changed: not 'What is AI?' but 'How do I live with it?'",
            "Real answer needed: no hype, no panic — just facts.",
        ],
        "sub":     '"In 2026, the conversation shifted from \'What is it?\' to \'How do we live with it.\'"',
        "date":    None,
        "cta":     None,
    },
    # ── SLIDE 2 — Tasks, Not Whole Jobs ──────────────────────────────────────
    {
        "type":    "content",
        "bg":      "BG-03-tasks.png",
        "label":   "SCENE 2  —  THE KEY IDEA",
        "hook":    "AI TAKES\nTASKS —\nNOT JOBS",
        "bullets": [
            "Your job is a mix of many tasks — some simple, some complex.",
            "AI handles the simple, repeatable ones very well.",
            "Humans stay in charge of judgment, relationships, decisions.",
            "Ask: which parts of my job will change?",
        ],
        "sub":     "AUTOMATE = routine   |   AUGMENT = mixed   |   HUMAN-ONLY = judgment",
        "date":    None,
        "cta":     None,
    },
    # ── SLIDE 3 — Jobs Are Changing, Not Disappearing ─────────────────────────
    {
        "type":    "content",
        "bg":      "BG-02-search.png",
        "label":   "SCENE 3  —  THE PATTERN",
        "hook":    "HISTORY\nSHOWS\nUS THIS",
        "bullets": [
            "New technology reshapes jobs — it rarely wipes them out entirely.",
            "Calculators came in → accountants focused on advice, not arithmetic.",
            "Routine parts move to machines. Human parts grow in value.",
            "Many companies use AI to expand what their teams can do.",
        ],
        "sub":     "The shape of work changes. The human role gets more meaningful.",
        "date":    None,
        "cta":     None,
    },
    # ── SLIDE 4 — Job Evolution: The Engineer ────────────────────────────────
    {
        "type":    "content",
        "bg":      "BG-03-tasks.png",
        "label":   "SCENE 4A  —  JOB EVOLUTION",
        "hook":    "THE\nENGINEER'S\nNEW ROLE",
        "bullets": [
            "AI writes basic code, flags bugs, and suggests fixes.",
            "Engineers now focus on system design and architecture.",
            "Time saved on repetitive coding goes to higher-level thinking.",
            "The engineer becomes the guide — AI is the tool.",
        ],
        "sub":     "Before: Write every line.   After: Design the whole system.",
        "date":    None,
        "cta":     None,
    },
    # ── SLIDE 5 — Job Evolution: The Architect ───────────────────────────────
    {
        "type":    "content",
        "bg":      "BG-06-risks.png",
        "label":   "SCENE 4B  —  JOB EVOLUTION",
        "hook":    "THE\nARCHITECT'S\nNEW ROLE",
        "bullets": [
            "AI generates floor plans and 3D models in minutes.",
            "Safety simulations run automatically — no manual calculation.",
            "AI cannot understand what a community actually needs.",
            "Human creativity, empathy, and vision lead the design.",
        ],
        "sub":     "AI speeds up the draft. The architect shapes the meaning.",
        "date":    None,
        "cta":     None,
    },
    # ── SLIDE 6 — Job Evolution: The Lawyer ──────────────────────────────────
    {
        "type":    "content",
        "bg":      "BG-04-roles.png",
        "label":   "SCENE 5A  —  JOB EVOLUTION",
        "hook":    "THE\nLAWYER'S\nNEW ROLE",
        "bullets": [
            "AI scans thousands of case documents in seconds.",
            "Legal research that took days now takes minutes.",
            "Strategy, courtroom judgment, and client care stay human.",
            "The lawyer focuses on nuance, argument, and outcome.",
        ],
        "sub":     "AI does the reading. The lawyer does the thinking.",
        "date":    None,
        "cta":     None,
    },
    # ── SLIDE 7 — Job Evolution: The Teacher ─────────────────────────────────
    {
        "type":    "content",
        "bg":      "BG-02-search.png",
        "label":   "SCENE 5B  —  JOB EVOLUTION",
        "hook":    "THE\nTEACHER'S\nNEW ROLE",
        "bullets": [
            "AI grades essays, generates quizzes, explains concepts on demand.",
            "Students get personalised explanations 24 hours a day.",
            "Knowing which student needs encouragement — that is human.",
            "Inspiring someone to believe in themselves stays with the teacher.",
        ],
        "sub":     "AI delivers content. The teacher changes lives.",
        "date":    None,
        "cta":     None,
    },
    # ── SLIDE 8 — Role Exposure Ranges ───────────────────────────────────────
    {
        "type":    "content",
        "bg":      "BG-04-roles.png",
        "label":   "SCENE 6  —  EXPOSURE RANGES",
        "hook":    "HOW MUCH\nIS AT RISK?",
        "bullets": [
            "Software Engineer       25–45% of tasks automatable",
            "Architect / Designer    20–40% of tasks automatable",
            "Lawyer / Paralegal      30–55% of tasks automatable",
            "Teacher / Educator      20–40% of tasks automatable",
            "Market Analyst          40–60% of tasks automatable",
            "HR / Talent Specialist  25–50% of tasks automatable",
        ],
        "sub":     "Freed-up time is an opportunity — not a threat.",
        "date":    None,
        "cta":     None,
    },
    # ── SLIDE 9 — How to Reskill ──────────────────────────────────────────────
    {
        "type":    "content",
        "bg":      "BG-05-steps.png",
        "label":   "SCENE 7  —  RESKILLING",
        "hook":    "WHAT TO\nLEARN NOW",
        "bullets": [
            "Learn the AI tools built for your own industry — start there.",
            "Focus on judgment, creativity, and leadership — AI cannot copy these.",
            "30 minutes a week on free/low-cost courses adds up fast.",
            "Do not wait for your company — start independently.",
        ],
        "sub":     "Engineers → prompt engineering   |   Lawyers → legal AI platforms   |   Teachers → AI curriculum tools",
        "date":    None,
        "cta":     None,
    },
    # ── SLIDE 10 — Action Plan + Key Takeaways ────────────────────────────────
    {
        "type":    "content",
        "bg":      "BG-05-steps.png",
        "label":   "SCENE 8  —  YOUR PLAN",
        "hook":    "START\nTODAY",
        "bullets": [
            "List daily tasks — spot the repetitive ones AI can handle.",
            "Protect time for human judgment — build those skills deliberately.",
            "Try one AI tool this week. See what it does well and where it fails.",
            "Measure tasks, pilot carefully, and keep the human skills that matter.",
        ],
        "sub":     None,
        "date":    None,
        "cta":     "Subscribe for weekly AI insights.",
    },
    # ── SLIDE 11 — Branding Outro ─────────────────────────────────────────────
    {
        "type":    "outro",
        "bg":      None,   # generated programmatically
        "label":   None,
        "hook":    None,
        "bullets": [],
        "sub":     None,
        "date":    None,
        "cta":     None,
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _ft(bold, size):
    for n in (["arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold
              else ["arial.ttf", "DejaVuSans.ttf"]):
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            pass
    return ImageFont.load_default()


def wrap(text, font, max_w, draw):
    """Word-wrap text to fit within max_w pixels."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def auto_font_size(text, bold, max_w, draw, size_max=92, size_min=36):
    """Auto-pick font size so text fits within max_w on one line."""
    for size in range(size_max, size_min - 1, -2):
        f = _ft(bold, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
    return _ft(bold, size_min)


def apply_scrim(img, left_alpha=200, right_alpha=20, pct=0.60):
    """
    Dark gradient scrim over background image.
    Higher left_alpha = stronger contrast for text readability.
    """
    arr = np.array(img.convert("RGB")).astype(np.float32)
    w   = img.width
    sw  = int(w * pct)
    for x in range(w):
        if x < sw:
            a = left_alpha + (right_alpha - left_alpha) * (x / sw) ** 0.55
        else:
            a = right_alpha * max(0, 1 - (x - sw) / (w - sw))
        arr[:, x, :] = np.clip(arr[:, x, :] * (1 - a / 255), 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def load_bg(slide: dict) -> Image.Image:
    """Load background image or generate a solid dark fallback."""
    if slide.get("bg"):
        bg_path = GRAPHICS / slide["bg"]
        if bg_path.exists():
            bg_raw = Image.open(bg_path).convert("RGB")
            bw, bh = bg_raw.size
            ratio  = bw / bh
            if ratio > W / H:
                nh = H; nw = int(ratio * H)
            else:
                nw = W; nh = int(W / ratio)
            bg_raw = bg_raw.resize((nw, nh), Image.LANCZOS)
            left = (nw - W) // 2; top = (nh - H) // 2
            return bg_raw.crop((left, top, left + W, top + H))
    # Fallback: dark gradient
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        v = int(8 + (y / H) * 12)
        arr[y, :] = [v, v + 4, v + 20]
    return Image.fromarray(arr)


def load_logo(size=72):
    path = ASSETS / "logo.png"
    if path.exists():
        return Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
    return None


def load_avatar(target_h=280):
    path = ASSETS / "avatar.png"
    if path.exists():
        av = Image.open(path).convert("RGBA")
        target_w = int(target_h * av.width / av.height)
        return av.resize((target_w, target_h), Image.LANCZOS)
    return None


def add_cyan_glow(img, intensity=0.20):
    """Subtle cyan glow on the left edge for brand consistency."""
    arr = np.array(img).astype(np.float32)
    ys, xs = np.ogrid[:H, :W]
    dist = np.sqrt(xs.astype(np.float32) ** 2 + ((ys - H // 2)).astype(np.float32) ** 2)
    mask = np.clip(1.0 - dist / 950, 0, 1) * intensity
    arr[:, :, 0] = np.clip(arr[:, :, 0] + mask * CYAN[0], 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] + mask * CYAN[1], 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] + mask * CYAN[2], 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT CONSTANTS — auto-computed from slide height
# ══════════════════════════════════════════════════════════════════════════════

TOP_BAR_H  = 74
BOT_BAR_H  = 62
PAD        = 66
TEXT_COL_W = int(W * 0.52)   # left text zone width
AVATAR_H   = H // 4           # ~270px


# ══════════════════════════════════════════════════════════════════════════════
# STANDARD SLIDE RENDERER
# ══════════════════════════════════════════════════════════════════════════════

def render_slide(slide: dict, path: Path):
    # ── 1. Background ──────────────────────────────────────────────────────────
    bg = load_bg(slide)
    bg = apply_scrim(bg, left_alpha=200, right_alpha=18, pct=0.62)
    bg = add_cyan_glow(bg, intensity=0.20)
    canvas = bg.convert("RGBA")
    d = ImageDraw.Draw(canvas)

    # ── 2. TOP BAR ────────────────────────────────────────────────────────────
    d.rectangle([0, 0, W, TOP_BAR_H], fill=(*BLACK, 230))
    d.rectangle([0, TOP_BAR_H, W, TOP_BAR_H + 3], fill=(*CYAN, 255))

    logo = load_logo(54)
    if logo:
        canvas.paste(logo, (14, (TOP_BAR_H - 54) // 2), logo)
        brand_x = 80
    else:
        brand_x = PAD

    # Show name in top bar — two-line to fit "THE AI CHRONICLE: EDITORS VIEW"
    d.text((brand_x, 10), "THE AI CHRONICLE",
           font=_ft(True, 26), fill=(*WHITE, 255))
    d.text((brand_x, 38), "EDITORS VIEW",
           font=_ft(True, 22), fill=(*CYAN, 240))

    # Date top-right (intro slide uses date box below; others get small top-right date)
    if slide.get("date") is None:
        d.text((W - 200, 22), "APR 2026",
               font=_ft(True, 22), fill=(*LGRAY, 180))

    # ── 3. SECTION LABEL ──────────────────────────────────────────────────────
    if slide.get("label"):
        label_y = TOP_BAR_H + 20
        d.text((PAD, label_y), slide["label"],
               font=_ft(True, 28), fill=(*CYAN, 255))
        lw = int(d.textlength(slide["label"], font=_ft(True, 28)))
        d.rectangle([PAD, label_y + 37, PAD + lw, label_y + 40],
                    fill=(*CYAN, 200))
    else:
        label_y = TOP_BAR_H

    # ── 4. HOOK HEADLINE — auto-sized, positioned below label ─────────────────
    if slide.get("hook"):
        hook_y  = label_y + 56
        lines   = slide["hook"].split("\n")
        # Larger font for fewer lines
        base_sz = 96 if len(lines) <= 2 else 82 if len(lines) == 3 else 70
        f_hook  = _ft(True, base_sz)
        for i, line in enumerate(lines):
            # Cyan highlight on first line for contrast
            col = CYAN if i == 0 else WHITE
            d.text((PAD + 3, hook_y + 3), line, font=f_hook, fill=(*BLACK, 170))
            d.text((PAD, hook_y), line, font=f_hook, fill=(*col, 255))
            hook_y += int(f_hook.size * 1.08)
        content_y = hook_y + 18
    else:
        content_y = label_y + 80

    # ── 5. BULLETS — auto-wrapped, auto-spaced to avoid bottom bar overlap ────
    if slide.get("bullets"):
        f_bul    = _ft(True, 42)
        line_h   = int(f_bul.size * 1.20)
        max_y    = H - BOT_BAR_H - AVATAR_H - 20   # leave room for avatar
        bullet_y = content_y

        for bullet in slide["bullets"]:
            if bullet_y + line_h > max_y:
                break  # stop before overflowing
            d.ellipse([PAD, bullet_y + 13, PAD + 14, bullet_y + 27],
                      fill=(*CYAN, 255))
            bx = PAD + 26
            wrapped = wrap(bullet, f_bul, TEXT_COL_W - 36, d)
            for wline in wrapped:
                if bullet_y + line_h > max_y:
                    break
                d.text((bx, bullet_y), wline, font=f_bul, fill=(*WHITE, 255))
                bullet_y += line_h
            bullet_y += 4

        content_y = bullet_y

    # ── 6. SUB / EXTRA TEXT ───────────────────────────────────────────────────
    if slide.get("sub"):
        max_sub_y = H - BOT_BAR_H - AVATAR_H - 10
        if content_y + 42 < max_sub_y:
            sub_y = content_y + 10
            f_sub = _ft(False, 33)
            for line in slide["sub"].split("\n"):
                for wl in wrap(line, f_sub, TEXT_COL_W, d):
                    if sub_y + 40 > max_sub_y:
                        break
                    d.text((PAD, sub_y), wl, font=f_sub, fill=(*LGRAY, 220))
                    sub_y += int(f_sub.size * 1.28)

    # ── 7. DATE BOX (intro slide only) ────────────────────────────────────────
    if slide.get("date"):
        db_y = H - BOT_BAR_H - AVATAR_H - 74
        db_w = 280
        d.rectangle([PAD, db_y, PAD + db_w, db_y + 58], fill=(*CYAN, 255))
        d.rectangle([PAD, db_y, PAD + 8, db_y + 58], fill=(*WHITE, 255))
        d.text((PAD + 18, db_y + 10), slide["date"],
               font=_ft(True, 34), fill=(*BLACK, 255))

    # ── 8. CTA BOX ────────────────────────────────────────────────────────────
    if slide.get("cta"):
        cta_y = H - BOT_BAR_H - AVATAR_H - 80
        f_cta = _ft(True, 46)
        cta_w = int(d.textlength(slide["cta"], font=f_cta)) + 48
        d.rectangle([PAD - 6, cta_y - 10, PAD + cta_w, cta_y + 58],
                    fill=(*CYAN, 35), outline=(*CYAN, 220), width=3)
        d.text((PAD + 16, cta_y), slide["cta"], font=f_cta, fill=(*WHITE, 255))

    # ── 9. AVATAR (bottom-left, above bottom bar) ─────────────────────────────
    avatar = load_avatar(target_h=AVATAR_H)
    if avatar:
        av_y = H - AVATAR_H - BOT_BAR_H
        d.rectangle([0, av_y, avatar.width + 12, H - BOT_BAR_H],
                    fill=(*BLACK, 130))
        d.rectangle([0, av_y, 5, H - BOT_BAR_H], fill=(*CYAN, 210))
        canvas.paste(avatar, (5, av_y), avatar)

    # ── 10. BOTTOM BAR ────────────────────────────────────────────────────────
    bar_y = H - BOT_BAR_H
    d.rectangle([0, bar_y, W, H], fill=(*BLACK, 235))
    d.rectangle([0, bar_y, W, bar_y + 3], fill=(*CYAN, 200))

    logo_s = load_logo(44)
    if logo_s:
        canvas.paste(logo_s, (14, bar_y + (BOT_BAR_H - 44) // 2), logo_s)
        bl_x = 70
    else:
        bl_x = PAD
    d.text((bl_x, bar_y + 14), "@theaichronicle007",
           font=_ft(False, 26), fill=(*WHITE, 225))
    d.text((W - 580, bar_y + 14), "#AI   #FutureOfWork   #AIChronicle",
           font=_ft(False, 23), fill=(*LGRAY, 190))

    canvas.convert("RGB").save(str(path), quality=96)


# ══════════════════════════════════════════════════════════════════════════════
# OUTRO SLIDE RENDERER — "That's a Wrap" branding screen
# ══════════════════════════════════════════════════════════════════════════════

def render_outro(path: Path):
    import random
    rng = random.Random(99)

    # ── Deep dark navy base ───────────────────────────────────────────────────
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        v = int(6 + (y / H) * 10)
        arr[y, :] = [v, v + 2, v + 18]

    # ── Particle constellation ────────────────────────────────────────────────
    for _ in range(320):
        px = rng.randint(0, W - 1)
        py = rng.randint(0, H - 1)
        brightness = rng.randint(60, 200)
        r = rng.randint(1, 3)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if 0 <= py + dy < H and 0 <= px + dx < W:
                    arr[py + dy, px + dx] = [brightness // 4, brightness // 3, brightness]

    # Subtle constellation lines
    nodes = [(rng.randint(100, W - 100), rng.randint(100, H - 100)) for _ in range(18)]
    img = Image.fromarray(arr)
    dl  = ImageDraw.Draw(img)
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            nx1, ny1 = nodes[i]
            nx2, ny2 = nodes[j]
            dist = math.hypot(nx2 - nx1, ny2 - ny1)
            if dist < 320:
                alpha = int(30 * (1 - dist / 320))
                dl.line([(nx1, ny1), (nx2, ny2)], fill=(alpha, alpha * 2, alpha * 6), width=1)
    for nx, ny in nodes:
        dl.ellipse([nx - 3, ny - 3, nx + 3, ny + 3], fill=(40, 80, 180, 160))

    canvas = img.convert("RGBA")
    d = ImageDraw.Draw(canvas)

    # ── "THAT'S A WRAP" ───────────────────────────────────────────────────────
    f_wrap = _ft(True, 108)
    wrap_text = "THAT'S A WRAP"
    tw = int(d.textlength(wrap_text, font=f_wrap))
    tx = (W - tw) // 2
    ty = int(H * 0.14)
    # Shadow
    d.text((tx + 4, ty + 4), wrap_text, font=f_wrap, fill=(*BLACK, 160))
    d.text((tx, ty), wrap_text, font=f_wrap, fill=(*WHITE, 255))

    # ── Show name ─────────────────────────────────────────────────────────────
    f_show = _ft(True, 36)
    show1  = "THE AI CHRONICLE: EDITORS VIEW"
    sw1    = int(d.textlength(show1, font=f_show))
    d.text(((W - sw1) // 2, ty + 130), show1, font=f_show, fill=(*WHITE, 220))

    f_ep   = _ft(False, 30)
    ep_txt = "Will AI Take My Job?"
    ew     = int(d.textlength(ep_txt, font=f_ep))
    d.text(((W - ew) // 2, ty + 178), ep_txt, font=f_ep, fill=(*LGRAY, 200))

    # ── Channel handle ────────────────────────────────────────────────────────
    f_handle = _ft(True, 72)
    handle   = "@theaichronicle007"
    hw       = int(d.textlength(handle, font=f_handle))
    hx       = (W - hw) // 2
    hy       = int(H * 0.42)
    d.text((hx + 3, hy + 3), handle, font=f_handle, fill=(*BLACK, 140))
    d.text((hx, hy), handle, font=f_handle, fill=(*CYAN, 255))

    # ── Tagline ───────────────────────────────────────────────────────────────
    f_tag  = _ft(False, 28)
    tagline = "Weekly insights on AI and the future of work."
    tgw    = int(d.textlength(tagline, font=f_tag))
    d.text(((W - tgw) // 2, hy + 90), tagline, font=f_tag, fill=(*LGRAY, 190))

    # ── Logo centred below tagline ────────────────────────────────────────────
    logo = load_logo(120)
    if logo:
        lx = (W - 120) // 2
        ly = hy + 136
        canvas.paste(logo, (lx, ly), logo)
        next_y = ly + 140
    else:
        next_y = hy + 160

    # ── Avatar (bottom-right) ─────────────────────────────────────────────────
    avatar = load_avatar(target_h=int(H * 0.30))
    if avatar:
        av_x = W - avatar.width - 60
        av_y = H - avatar.height - 80
        # Subtle backing circle
        d.ellipse([av_x - 10, av_y - 10,
                   av_x + avatar.width + 10, av_y + avatar.height + 10],
                  fill=(*DARK, 180))
        canvas.paste(avatar, (av_x, av_y), avatar)
        # "Editors View" label next to avatar
        f_ev   = _ft(True, 26)
        ev_txt = "Editors View"
        evw    = int(d.textlength(ev_txt, font=f_ev))
        d.text((av_x + (avatar.width - evw) // 2, av_y - 36),
               ev_txt, font=f_ev, fill=(*CYAN, 220))

    # ── SUBSCRIBE NOW button ──────────────────────────────────────────────────
    f_cta  = _ft(True, 44)
    cta_t  = "SUBSCRIBE NOW"
    ctw    = int(d.textlength(cta_t, font=f_cta)) + 60
    ctx    = (W - ctw) // 2
    cty    = next_y + 16
    d.rounded_rectangle([ctx, cty, ctx + ctw, cty + 68],
                        radius=12, fill=(*RED_CTA, 255))
    d.text((ctx + 30, cty + 10), cta_t, font=f_cta, fill=(*WHITE, 255))

    # ── Bottom action bar ─────────────────────────────────────────────────────
    bar_y = H - 72
    d.rectangle([0, bar_y, W, H], fill=(*BLACK, 240))
    d.rectangle([0, bar_y, W, bar_y + 3], fill=(*CYAN, 200))

    btn_specs = [
        (80,  (0, 180, 220),  "LIKE"),
        (260, (80, 80, 80),   "SHARE"),
        (430, (*RED_CTA, 255), "SUBSCRIBE"),
    ]
    f_btn = _ft(True, 26)
    for bx_, bfill, btxt in btn_specs:
        bw2 = int(d.textlength(btxt, font=f_btn)) + 36
        d.rounded_rectangle([bx_, bar_y + 10, bx_ + bw2, bar_y + 58],
                            radius=8, fill=bfill)
        d.text((bx_ + 18, bar_y + 18), btxt, font=f_btn, fill=(*WHITE, 255))

    logo_s = load_logo(42)
    if logo_s:
        canvas.paste(logo_s, (W - 240, bar_y + (72 - 42) // 2), logo_s)
    d.text((W - 190, bar_y + 18), "@theaichronicle007",
           font=_ft(False, 24), fill=(*WHITE, 210))

    canvas.convert("RGB").save(str(path), quality=96)


# ══════════════════════════════════════════════════════════════════════════════
# FFMPEG COMPOSER
# ══════════════════════════════════════════════════════════════════════════════

def compose_video(slide_paths, durations, audio, music, output):
    tmp_dir  = Path(tempfile.mkdtemp())
    concat_f = tmp_dir / "concat.txt"
    with open(concat_f, "w") as fh:
        for path, dur in zip(slide_paths, durations):
            fh.write(f"file '{path.as_posix()}'\n")
            fh.write(f"duration {dur}\n")
        fh.write(f"file '{slide_paths[-1].as_posix()}'\n")

    audio_exists = audio.exists()
    music_exists = music.exists()

    if audio_exists and music_exists:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_f),
            "-i", str(audio),
            "-i", str(music),
            "-filter_complex",
            "[2:a]volume=0.16[music];[1:a][music]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-vf", "scale=1920:1080,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(output),
        ]
    elif audio_exists:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_f),
            "-i", str(audio),
            "-map", "0:v", "-map", "1:a",
            "-vf", "scale=1920:1080,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(output),
        ]
    else:
        # No audio — slides only
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_f),
            "-vf", "scale=1920:1080,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            str(output),
        ]

    print("\nRunning FFmpeg ...")
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stderr[-2000:])
        raise RuntimeError("FFmpeg failed")
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"Saved: {output.name}  ({output.stat().st_size / 1_048_576:.1f} MB)")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    slides_dir = OUT_DIR / "slides_rendered"
    slides_dir.mkdir(exist_ok=True)
    slide_paths = []

    print(f"\nRendering {len(SLIDES)} slides ...")
    for i, slide in enumerate(SLIDES):
        out_path = slides_dir / f"slide_{i:02d}.png"
        if slide["type"] == "outro":
            render_outro(out_path)
        else:
            render_slide(slide, out_path)
        slide_paths.append(out_path)
        print(f"  [{i + 1}/{len(SLIDES)}] {slide.get('bg') or 'outro'}")

    print(f"\nComposing: {OUT_FILE.name}")
    compose_video(slide_paths, DURATIONS, AUDIO, MUSIC, OUT_FILE)
    print("\nDone.")
