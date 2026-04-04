---
name: youtube-improve
description: This skill should be used when the user asks to run the YouTube video pipeline, generate AI news videos, fetch RSS news, work on the youtube-improve pipeline, fix video slides, update thumbnails, modify the intro or outro, change story slide design, or mentions "the AI chronicle YouTube" in context of the improved pipeline.
version: 1.0.0
---

# YouTube Improve Pipeline — The AI Chronicle

Handles all work on the `youtube-improve/` pipeline. This is the **improved** pipeline — separate from `youtube-posting/`. Never touch `youtube-posting/` or `instagram-posting/`.

## Quick Commands

```bash
# Full pipeline (RSS news → video → upload)
cd "c:/Users/sport/Manviga/youtube-improve"
python src/run_pipeline.py

# Test RSS fetcher only
python src/news_fetcher.py

# Generate video only (uses fallback stories if no network)
python src/video_generator.py

# Generate thumbnails only
python src/thumbnail_generator.py

# Visual template test (renders 3 story slides to output/test_slides/)
python test_template.py
```

## File Map

| Task | File |
|---|---|
| Run full pipeline | `src/run_pipeline.py` |
| Fix news fetching | `src/news_fetcher.py` |
| Fix slide design / video | `src/video_generator.py` |
| Fix thumbnails | `src/thumbnail_generator.py` |
| Fix YouTube upload | `src/youtube_uploader.py` |
| Add background images | `backgrounds/` |

## Key Design Facts

- **Video**: 1920×1080, ~6 min, starts with intro slide (thumbnail slide removed)
- **Thumbnails**: 1280×720, A (blue) + B (purple) variants
- **News**: Free RSS feeds, no API key — feedparser + urllib fallback
- **Geo mix**: 3 USA · 3 India · 2 China · 2 ROW
- **Story fonts**: Georgia Bold 44px (`news_body`), Georgia 40px (`news_body_sm`), Arial Bold 40px (`news_label`)
- **Background images**: scanned from `backgrounds/` — all extensions including `.jfif`

## Common Fixes

**draw_glow() bug**: Always capture return value — it returns a new Image object:
```python
img = draw_glow(img, center, radius, color, intensity)  # CORRECT
draw_glow(img, center, radius, color, intensity)         # WRONG — img unchanged
```

**Font loading**: `_ft()` always returns truthy — never use `or` chaining:
```python
fonts["key"] = _ft("georgiab.ttf", 44)       # CORRECT
fonts["key"] = _ft("georgiab.ttf", 44) or _ft("georgia.ttf", 44)  # WRONG
```

**TTS**: Pass rate/pitch as constructor params, not SSML:
```python
edge_tts.Communicate(plain_text, voice, rate="+8%", pitch="+0Hz")  # CORRECT
```

**Windows Unicode**: Log file has full Unicode. For console print, encode to ASCII:
```python
print(text.encode("ascii", errors="replace").decode("ascii"))
```

## Output Location

```
youtube-improve/output/{YYYYMMDD_HHMMSS}_{slug}/
├── {slug}.mp4                    # Final video
├── {slug}_thumbnail_a.png        # Blue variant
├── {slug}_thumbnail_b.png        # Purple variant
├── yt_meta.txt                   # Human-readable metadata
└── yt_metadata.json              # Full JSON metadata
```

## Upload Setup (one-time)

Place `client_secret.json` (Google OAuth Desktop app) at:
`youtube-improve/credentials/client_secret.json`

Run pipeline → browser opens for login → `token.json` auto-saved.
