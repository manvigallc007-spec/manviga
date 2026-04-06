# The AI Chronicle — YouTube Improve Pipeline
## CLAUDE.md — Last updated: 2026-04-04

Automated daily AI news video pipeline for **@theaichronicle007**.
10 geo-balanced AI stories → 1920×1080 video (~6 min) → YouTube upload.
**Free RSS-based news fetch — no Anthropic API credits needed.**
**Do NOT touch `youtube-posting/` or `instagram-posting/` — this pipeline is fully independent.**

---

## Directory Structure

```
youtube-improve/
├── src/
│   ├── run_pipeline.py         # Main runner: fetch → generate → upload
│   ├── news_fetcher.py         # Free RSS news fetch (feedparser, no API key)
│   ├── video_generator.py      # 1920×1080 slide renderer + FFmpeg composer
│   ├── thumbnail_generator.py  # 1280×720 A/B YouTube thumbnail generator
│   └── youtube_uploader.py     # YouTube Data API v3 uploader (OAuth 2.0)
├── backgrounds/
│   └── *.png / *.jpg           # AI-themed background images (7 images)
├── credentials/
│   ├── client_secret.json      # OAuth app credentials (required for upload)
│   └── token.json              # Auto-generated after first OAuth login
├── output/
│   └── {YYYYMMDD_HHMMSS}_{slug}/
│       ├── {YYYYMMDD_HHMMSS}_{slug}.mp4            # Final video (~6 min)
│       ├── {YYYYMMDD_HHMMSS}_{slug}_thumbnail_a.png  # Thumbnail variant A (blue)
│       ├── {YYYYMMDD_HHMMSS}_{slug}_thumbnail_b.png  # Thumbnail variant B (purple)
│       ├── yt_meta.txt                              # Human-readable metadata
│       └── yt_metadata.json                         # Full JSON metadata
├── logs/
│   ├── posted_stories.json     # Dedup log — last 200 posted headlines
│   ├── pipeline_*.log
│   └── video_gen_*.log
├── backgrounds/README.txt      # Background image naming guide
├── CLAUDE.md                   # This file
└── requirements.txt
```

Root `.env` at `c:/Users/sport/Manviga/.env` — no keys required for this pipeline.

---

## How to Run

```bash
# Full pipeline (fetch live news + generate video + upload)
cd "c:/Users/sport/Manviga/youtube-improve"
python src/run_pipeline.py

# Test RSS news fetcher only
python src/news_fetcher.py

# Generate video with fallback stories (no network needed)
python src/video_generator.py

# Generate thumbnails only
python src/thumbnail_generator.py

# Run the visual template test (3 story slides)
python test_template.py
```

---

## Video Structure

| Slide | Duration | Content |
|---|---|---|
| Intro (news list) | ~3s | 2-column list of all 10 stories |
| Story 01–10 | ~30–35s each | Hook → What Happened → Why It Matters → What's Next |
| Outro | ~15s | Subscribe CTA |

**Total: ~6 minutes. Thumbnail slide removed — video starts with intro.**

---

## News Fetcher (RSS — Free, No API Key)

Sources (17 RSS feeds):
- **USA**: TechCrunch, VentureBeat, The Verge, TNW Neural, AI News
- **India**: Inc42, YourStory, Analytics Vidhya, The Hindu Tech
- **China/Asia**: TechNode, Pandaily, SCMP Tech
- **ROW**: BBC Tech, AI Business, The Decoder, ZDNet AI

Geographic quota enforced: **3 USA · 3 India · 2 China · 2 ROW**

Fallback: `FALLBACK_STORIES` (10 hardcoded stories) used if fewer than 8 live articles found.

**AI-only filter rules (strict):**
- Story must have ≥1 AI keyword in the **title** itself — OR ≥2 AI keywords in title+summary
- This prevents non-AI stories (sports, crime, politics) from slipping through feeds like SCMP or Inc42
- Same-event dedup: stories sharing the same company name + dollar figure are treated as one event — only the first/highest-scored kept (eliminates Anthropic $400M appearing 3×)

**India AI ecosystem terms in keyword list:**
- Haptik, Uniphore, Sarvam, Krutrim, Bhashini, AIRaWAT, Indic LLM, NASSCOM AI, MEITY AI, IIT AI, Zoho AI, TCS AI, etc.
- India feed override threshold raised to 2 USA markers (was 1) — reduces false re-assignments

Requires `feedparser>=6.0.0` — install with:
```bash
pip install -r requirements.txt
```

---

## Slide Design — Story Slides (1920×1080)

**Left column (text)**
- Hook: large ALL CAPS headline — wrapped using hero_font width (20% larger) so no word is clipped
- What Happened: up to 3 bullet points (Georgia Bold 44px)
- Why It Matters + What's Next (Georgia 40px)
- Content area bottom = Y_CTA - 10 (full height to CTA bar, not capped at Y_STRIP)

**Right column**
- Full-bleed background image card with rounded mask and dark overlay

**Fonts**
| Key | Font | Size | Use |
|---|---|---|---|
| `news_label` | Arial Bold | 40px | Section labels |
| `news_body` | Georgia Bold | 44px | Body bullets |
| `news_body_sm` | Georgia | 40px | Secondary text |
| `h44` | Georgia Bold | 44px | Hook |

---

## Thumbnail Design (1280×720)

- Full-bleed AI background image + cinematic left-heavy gradient scrim
- Top bar: logo + "THE AI CHRONICLE"
- "YOUR TOP 10 AI NEWS FROM TODAY" (accent color label)
- Auto-sized hook headline (up to 110px Arial Bold, 2 lines max)
- Decorative date box (accent-tinted, rounded border, left white bar, dot decorations)
- Bottom bar: logo + @theaichronicle007 + hashtags
- **Variant A**: electric blue `(0, 210, 255)` — bg_index=0
- **Variant B**: purple `(210, 100, 255)` — bg_index=1

---

## Background Images

Place AI-themed images in `backgrounds/`. Supported formats: `.jpg` `.jpeg` `.png` `.webp` `.jfif`

The loader scans ALL files in the folder (not just named `bg1.jpg` etc.).
Currently 7 images: `BG1.png`, `BG2.png`, `Copilot_20260331_*.png` (×5)

---

## YouTube Upload Setup (First Time)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create project → Enable **YouTube Data API v3**
3. Credentials → Create OAuth 2.0 Client ID → **Desktop app**
4. Download JSON → rename to `client_secret.json`
5. Place at: `youtube-improve/credentials/client_secret.json`
6. Run pipeline once → browser opens for Google login
7. `token.json` auto-saved — no login needed again

OAuth scopes: `youtube.upload` + `youtube`

---

## Critical Technical Notes

- `draw_glow()` returns a **new** `Image.fromarray()` object — always capture the return value
- `_ft()` always returns a truthy font (fallback to default) — never chain with `or`
- Background loader scans all extensions including `.jfif`
- Windows console: use `encode("ascii", errors="replace")` for print statements containing Unicode (₹, →, emoji)
- edge-tts rate/pitch must be passed as constructor params, NOT SSML tags (edge-tts ignores SSML prosody)

---

## Troubleshooting

| Error | Fix |
|---|---|
| `client_secret.json not found` | Complete YouTube Upload Setup above |
| `Token expired` | Delete `token.json`, run pipeline once to re-auth |
| `quotaExceeded` | YouTube API daily quota exceeded — wait 24h |
| `feedparser not found` | `pip install feedparser` |
| Too few AI stories | Feeds may be slow — fallback stories will be used automatically |
| ffmpeg not found | Install via winget: `winget install Gyan.FFmpeg` |
| UnicodeEncodeError in console | Expected on Windows cp1252 — log file has full Unicode output