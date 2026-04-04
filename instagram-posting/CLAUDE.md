# The AI Chronicle — Instagram Automation
## Skill File for Claude Code (Last updated: 2026-03-29)

Fully automated Instagram reel pipeline for **@theaichronicle007**.
Every hour: searches the web for the #1 AI news story → generates branded post → uploads to Instagram.

---

## Architecture

```
instagram-posting/
├── src/
│   ├── news_fetcher.py         # Live AI news via Anthropic web search
│   ├── master_post_v2.py       # Post generator: PNG + MP3 + MP4 + caption
│   ├── instagram_uploader.py   # Uploader: Meta resumable API → Instagram Reel
│   └── run_pipeline.py         # Combined runner (called by scheduler every hour)
├── output/
│   └── {YYYYMMDD_HHMMSS}_{slug}/
│       ├── {slug}.png
│       ├── {slug}.mp3
│       ├── {slug}.mp4
│       ├── {slug}_caption.txt
│       ├── {slug}_metadata.json
│       └── upload_result.json
├── logs/
│   ├── posted_stories.json     # Dedup log — last 100 posted headlines
│   ├── pipeline_*.log
│   ├── master_post_*.log
│   └── instagram_upload_*.log
├── logo.PNG                    # Brand logo: dark navy circle + teal infinity symbol
├── CLAUDE.md                   # This file
├── news_feed_prompt.md         # Ready-made prompts for Claude
└── requirements.txt
```

Root `.env` at `c:/Users/sport/Manviga/.env`:
```
ANTHROPIC_API_KEY=...
META_APP_ID=4129428227192830
META_APP_SECRET=6e46eeb535b5e45245dd70591b7251f2
IG_USER_ID=17841437980540533
IG_ACCESS_TOKEN=<user token — see Token Management below>
FB_PAGE_TOKEN=<page token — currently unused>
FB_PAGE_ID=1073260245866078
```

---

## How to Run

```bash
# Full pipeline (fetch news + generate + upload)
python instagram-posting/src/run_pipeline.py

# Generate post only
python instagram-posting/src/master_post_v2.py

# Test news fetcher only
python instagram-posting/src/news_fetcher.py

# Upload latest post only
python instagram-posting/src/instagram_uploader.py
```

---

## Scheduler

Two schedulers run the full pipeline every hour at :07:

| Scheduler | Scope | Command to check |
|---|---|---|
| Windows Task Scheduler `TheAIChronicle_HourlyPost` | Persistent, survives restarts | `powershell -Command "Get-ScheduledTask -TaskName 'TheAIChronicle_HourlyPost'"` |
| Claude session cron job `8dc011f0` | Active while Claude Code is open | Use `CronList` tool |

---

## news_fetcher.py

Uses **Anthropic API** (`claude-sonnet-4-6`) with the `web_search_20250305` tool.

**IMPORTANT:** Use `claude-sonnet-4-6`, NOT opus. Opus hits session-level rate limits (30k TPM) when Claude Code is also open and using the same API key.

**What it does:**
1. Reads `logs/posted_stories.json` — builds avoid-list of last 20 headlines
2. Sends web search prompt to Claude asking for #1 AI news from past 24h
3. Parses the JSON story dict from the response
4. Validates all required fields, saves headline to dedup log
5. Returns the story dict or `None` on failure

**Verified sources:** TechCrunch, The Verge, Wired, VentureBeat, MIT Technology Review,
Reuters, Bloomberg, BBC, OpenAI blog, Google DeepMind, Anthropic blog, Meta AI blog,
ArXiv, Nature, Science, WSJ, Financial Times.

**Story dict format:**
```python
{
    "company":    "Company / Topic",
    "headline":   "Max Six Word Title",        # punchy, title case
    "watermark":  "KEYWORD",                   # faded background text
    "body":       ["Line 1", "Line 2", "Line 3", "Line 4"],  # 4 lines, ~42 chars each
    "stat_label": "Metric label",
    "stat_value": "VALUE",                     # e.g. $10B, 94%, 3x
    "source":     "Org / Publication",
    "hashtags":   "#Tag1 #Tag2 #Tag3 #Tag4 #Tag5",
    "reference":  "https://actual-article-url"
}
```

---

## master_post_v2.py

### Story selection
1. Calls `news_fetcher.fetch_latest_ai_news()` — live web search
2. Falls back to `random.choice(AI_NEWS_STORIES)` if fetch fails

### Adding fallback stories
Add entries to `AI_NEWS_STORIES` list in `master_post_v2.py`. Used only when web fetch fails.

### Visual design
- **Canvas**: 1080×1080 px
- **Themes**: 12 dark color schemes, seeded from headline hash (deterministic per story)
- **Backgrounds**: 11 procedural patterns (neural, grid, radar, bars, stars, triangles, hexagons, circuit, waves, scatter, diagonals)
- **Fonts**: `arialbd.ttf` (bold) / `arial.ttf` (regular) — Windows paths
- **Logo**: `logo.PNG` circular-masked (76px), centered in footer
- **Footer**: logo → `@theaichronicle • Daily AI News` → `Follow for daily AI news` → `LIKE • SHARE • FOLLOW`
- **Bottom/top bars**: 8px accent color bars

### Audio & Reel
- `generate_audio()` — gTTS English narration, ~30s, saved as `{slug}.mp3`
- `generate_reel()` — ffmpeg: static PNG + audio → H.264 MP4 (1080×1080, `-shortest -t 30`)
- Audio script ends: *"For more daily AI news, like, share, and follow The AI Chronicle. Stay ahead of the curve — we'll see you in the next one."*

### Caption format
```
🚀 {headline}.

{narrative body}

{stat_label}: {stat_value}.

The AI space moves fast — stay ahead. 👇

{hashtags} #TheAIChronicle #DailyAINews #AI #ArtificialIntelligence #Tech

Source: {reference_url}
```

---

## instagram_uploader.py

Uses Meta Graph API v18.0 with resumable upload:
1. `POST /{IG_USER_ID}/media` — init session → `media_id` + `upload_url`
2. `POST {upload_url}` — raw video bytes, headers: `Authorization: OAuth {token}`, `offset: 0`, `file_size: N`
3. Poll `GET /{media_id}?fields=status_code` every 5s until `FINISHED`
4. `POST /{IG_USER_ID}/media_publish` with `creation_id`

**Facebook cross-posting is disabled** — token missing `pages_manage_posts`.

---

## Token Management

Tokens expire. Watch for `OAuthException` or `[FAIL] API 190` in logs.

**To regenerate:**
1. Go to [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)
2. Select app **4129428227192830**
3. Permissions required: `instagram_basic`, `instagram_content_publish`, `pages_show_list`
4. Generate User Token → copy → update `IG_ACCESS_TOKEN` in `c:/Users/sport/Manviga/.env`

**IG_USER_ID verification:**
```python
import requests
r = requests.get(f"https://graph.facebook.com/v18.0/1073260245866078?fields=instagram_business_account&access_token={TOKEN}")
# Should return: {"instagram_business_account": {"id": "17841437980540533"}, "id": "1073260245866078"}
```

---

## Logging

The `UTFStreamHandler` class in both `master_post_v2.py` and `instagram_uploader.py` opens stdout with `encoding='utf-8', errors='replace'` so emoji in captions never cause `UnicodeEncodeError` on Windows cp1252 terminals.

---

## Separate from YouTube

Instagram pipeline is fully independent. Do NOT mix with `youtube-posting/`. Each has its own scripts, output dirs, and schedulers.

---

## See Also

- `news_feed_prompt.md` — copy-paste prompts for managing news stories and pipeline health
