# The AI Chronicle — YouTube Automation
## Skill File for Claude Code (Last updated: 2026-03-29)

Fully automated YouTube Shorts pipeline for **@theaichronicle007**.
Every hour: searches the web for the #1 AI news story → generates a branded vertical Short → uploads to YouTube.
**Completely independent from the Instagram pipeline.**

---

## Architecture

```
youtube-posting/
├── src/
│   ├── news_fetcher.py       # Live AI news via Anthropic web search (YouTube-specific)
│   ├── video_generator.py    # 1080×1920 PNG + thumbnail + MP3 + MP4 generator
│   ├── youtube_uploader.py   # YouTube Data API v3 uploader (OAuth 2.0)
│   └── run_pipeline.py       # Combined runner — called by scheduler
├── credentials/
│   ├── client_secret.json    # OAuth app credentials (from Google Cloud Console)
│   └── token.json            # Auto-generated after first OAuth login
├── output/
│   └── {YYYYMMDD_HHMMSS}_{slug}/
│       ├── {slug}_short.png          # 1080×1920 video frame
│       ├── {slug}_thumbnail.png      # 1280×720 thumbnail
│       ├── {slug}.mp3                # narration audio
│       ├── {slug}.mp4                # YouTube Short (≤58s)
│       ├── {slug}_title.txt          # video title
│       ├── {slug}_description.txt    # video description + hashtags
│       ├── {slug}_metadata.json      # full metadata
│       └── upload_result.json        # YouTube video ID + URL
├── logs/
│   ├── posted_stories.json   # Dedup log — last 100 uploaded headlines
│   ├── pipeline_*.log
│   ├── video_gen_*.log
│   └── youtube_upload_*.log
├── logo.PNG                  # Brand logo (copy from instagram-posting if needed)
├── CLAUDE.md                 # This file
└── requirements.txt
```

Root `.env` at `c:/Users/sport/Manviga/.env`:
```
ANTHROPIC_API_KEY=...   # used by news_fetcher.py
```

Project `.env` at `youtube-posting/.env`:
```
PROJECT_NAME=youtube-posting
OUTPUT_DIR=output
LOG_DIR=logs
```

---

## How to Run

```bash
# Full pipeline (fetch + generate + upload)
cd c:/Users/sport/Manviga
python youtube-posting/src/run_pipeline.py

# Generate video only (no upload)
cd c:/Users/sport/Manviga/youtube-posting/src
python video_generator.py

# Test news fetcher only
cd c:/Users/sport/Manviga/youtube-posting/src
python news_fetcher.py

# Upload latest output only
cd c:/Users/sport/Manviga/youtube-posting/src
python youtube_uploader.py
```

---

## First-Time YouTube Setup (REQUIRED before first upload)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or select existing)
3. Enable **YouTube Data API v3** (APIs & Services → Library)
4. Go to APIs & Services → Credentials → Create Credentials → **OAuth 2.0 Client ID**
5. Application type: **Desktop app**
6. Download the JSON file
7. Rename it to `client_secret.json`
8. Place at: `c:/Users/sport/Manviga/youtube-posting/credentials/client_secret.json`
9. Run pipeline once — browser will open for Google login
10. After login, `token.json` is auto-saved — no login needed again

OAuth scopes needed:
- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube`

---

## Scheduler

| Scheduler | Scope | How to check |
|---|---|---|
| Windows Task Scheduler `TheAIChronicle_YouTube_HourlyPost` | Persistent | `powershell -Command "Get-ScheduledTask -TaskName 'TheAIChronicle_YouTube_HourlyPost'"` |
| Claude session cron | While Claude Code is open | `CronList` tool |

**NOTE:** Do NOT set up scheduler until first manual run succeeds (OAuth login required first).

---

## news_fetcher.py

- **Model:** `claude-sonnet-4-6` with `web_search_20250305` tool (max 4 uses)
- **Dedup:** `logs/posted_stories.json` — avoids last 20 headlines
- **Extra fields vs Instagram:** `extended_body` (3 extra sentences), `youtube_title`, `youtube_tags`
- **Fallback:** `FALLBACK_STORIES` list used if web search fails

---

## video_generator.py

| Property | Value |
|---|---|
| Frame size | 1080×1920 (vertical 9:16 for Shorts) |
| Thumbnail size | 1280×720 (16:9) |
| Duration | ≤58 seconds (ffmpeg `-t 58`) |
| Narration | gTTS English, includes intro + extended body + CTA |
| Font | arialbd.ttf (bold) / arial.ttf (Windows) |
| Logo | `youtube-posting/logo.PNG` → fallback to `instagram-posting/logo.PNG` |
| Themes | 12 dark color schemes, seeded deterministically from headline |
| CTA in footer | LIKE • COMMENT • SUBSCRIBE |

Audio script structure:
```
"Welcome to The AI Chronicle. Here's today's top AI story.
{headline}. {body_lines}. {extended_body}.
{stat_label}: {stat_value}. Source: {source}.
That's your AI update for now. Like, subscribe, and hit the
notification bell so you never miss a story. See you in the next one."
```

---

## youtube_uploader.py

Uses YouTube Data API v3:
1. Load OAuth credentials from `credentials/token.json`
2. Auto-refresh if expired (no user interaction needed after first login)
3. Upload MP4 via resumable upload (8 MB chunks)
4. Set video metadata: title (≤100 chars), description (≤5000 chars), tags, category (28 = Science & Technology)
5. Upload thumbnail (1280×720 PNG)
6. Save result to `upload_result.json`

`#Shorts` is automatically appended to description and tags to ensure YouTube classifies it as a Short.

Privacy: `public` — videos are live immediately on upload.

---

## Isolation from Instagram

- Separate `src/`, `output/`, `logs/`, `credentials/` directories
- Separate `posted_stories.json` dedup log
- Separate Windows Task Scheduler task name
- Separate OAuth flow (YouTube API, not Meta API)
- Separate news_fetcher.py (YouTube story has `extended_body`, `youtube_title`, `youtube_tags`)
- ANTHROPIC_API_KEY shared from root `.env` — this is intentional and safe

---

## Troubleshooting

| Error | Fix |
|---|---|
| `client_secret.json not found` | Complete First-Time Setup above |
| `Token expired` | Delete `token.json`, run pipeline once manually to re-auth |
| `quotaExceeded` | YouTube API daily quota (10,000 units) exceeded — wait 24h or increase quota in Google Cloud |
| `videoNotFound` after upload | Normal — YouTube needs a few minutes to process Shorts |
| News fetch 429 rate limit | Model is claude-sonnet-4-6 — if still hitting limits, add `time.sleep(5)` before fetch |
| ffmpeg not found | Ensure ffmpeg is in PATH — check with `ffmpeg -version` |
