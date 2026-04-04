# YouTube Video Creator — The AI Chronicle

Generate YouTube videos for @theaichronicle. Supports four modes based on `$ARGUMENTS`:

- (no args or `daily`) — fetch live AI news and generate a fresh 1920×1080 daily news video
- `promo` — generate the ~60-second channel promo video
- `title` — generate YouTube title, description, tags, and hashtags for the most recently created video
- `create <description>` — design and build a brand-new custom video from a description

---

## Mode: `daily` (default)

Generate a fresh daily AI news video with live news, cinematic layout, and YouTube metadata.

### Steps

1. Run the live YouTube video generator:
```bash
cd "C:/Users/sport/Manviga" && .venv/Scripts/python.exe youtube_live_generator.py
```

2. After the video is created, report:
   - Full path to the MP4 file
   - Total duration
   - List of all 10 story headlines Claude selected

3. Generate YouTube upload metadata:

**Title** — punchy, under 70 chars, lead with the top 2-3 stories, include the date
**Description** — numbered list of all 10 stories covered, channel CTA (Like/Subscribe/Comment/Bell), hashtags at end
**Tags** — 20 comma-separated YouTube tags covering AI, companies mentioned, and evergreen terms
**Hashtags** — 20 hashtags with emojis grouped by: channel brand, companies, AI topics
**Playlist** — suggest the playlist name this episode belongs to

---

## Mode: `promo`

Generate the 60-second channel introduction/promo video.

### Steps

1. Run the promo generator:
```bash
cd "C:/Users/sport/Manviga" && .venv/Scripts/python.exe youtube_promo_generator.py
```

2. After the video is created, report:
   - Full path to the MP4 file
   - Total duration
   - Slide-by-slide breakdown

3. Generate YouTube upload metadata:

**Title** — channel introduction angle, include "Subscribe" CTA in title
**Description** — what the channel is about, what topics are covered, full CTA block (Like/Subscribe/Comment/Bell), hashtags
**Tags** — 20 tags: channel name, AI topics, "new YouTube channel", subscribe
**Hashtags** — brand + topic + action hashtags

---

## Mode: `title`

Generate YouTube metadata only (no video generation). Find the most recently created video and produce upload-ready metadata.

### Steps

1. Find the latest MP4 in the ai-reels folders:
```bash
ls -t ~/ai-reels/youtube-live/videos/*.mp4 ~/ai-reels/promo/videos/*.mp4 2>/dev/null | head -1
```

2. Check the live.log or promo.log for the story list from that run:
```bash
tail -60 ~/ai-reels/youtube-live/live.log 2>/dev/null || tail -60 ~/ai-reels/promo/promo.log 2>/dev/null
```

3. Based on the log content, generate:
   - YouTube **Title** (under 70 chars, punchy)
   - YouTube **Description** (story list, CTA, hashtags)
   - **Tags** (20 comma-separated)
   - **Hashtags** (20 with emojis)
   - **Default upload settings**: category = Science & Technology, language = English, audience = Not made for kids, visibility = Public

---

## Mode: `create <description>`

Design and build a brand-new custom YouTube video from a plain-English description.
The `$ARGUMENTS` after "create" is the user's description of the video they want.

Examples:
- `/youtube-video create a 90-second explainer on what GPT-5 is`
- `/youtube-video create weekly AI funding roundup with top 5 deals`
- `/youtube-video create motivational video about AI careers`

### Steps

1. **Plan the video** — based on the description, decide:
   - Total target duration (30s / 60s / 90s / 2min)
   - Number of slides (1 slide ≈ 5-7 seconds)
   - Slide types to use: `logo`, `text`, `stat`, `cta`, `split`
   - Story/content for each slide: label, headline, subtitle, stat value (if any)
   - TTS narration script per slide (spoken words at ~153 wpm after +18% speed)
   - Theme index (0-9) and pattern index (0-4) for each slide
   - Show the full plan to the user before writing any code

2. **Write the generator script** — create a new Python file at:
   `C:/Users/sport/Manviga/youtube_custom_{slug}.py`
   where `{slug}` is a short kebab-case name derived from the description.

   The script must follow the exact same structure as `youtube_promo_generator.py`:
   - Same imports, font loading, theme/pattern definitions, helper functions
   - Same `_build_bg()`, `_watermark()`, `_pill()`, `_dark_panel()`, `_channel_tag()` helpers
   - Same five render functions: `render_logo_slide`, `render_text_slide`, `render_stat_slide`,
     `render_cta_slide`, `render_split_slide`
   - A `CUSTOM_SLIDES` list with the planned slides
   - Same TTS + FFmpeg compose pipeline
   - Output to: `~/ai-reels/custom/{slug}/videos/`

3. **Run the script**:
```bash
cd "C:/Users/sport/Manviga" && .venv/Scripts/python.exe youtube_custom_{slug}.py
```

4. **Report results**:
   - File path and duration
   - Slide-by-slide summary

5. **Generate YouTube metadata**:
   - Title, description, tags, hashtags tailored to the video content

---

## Reference — Slide Types

| Type | Best for | Key fields |
|------|----------|------------|
| `logo` | Open/close, brand moments | headline, sub, label |
| `text` | Key messages, facts, topics | label (pill), headline (2 lines via \n), sub |
| `stat` | Numbers, milestones, impact | label, value (big centred), sub |
| `cta` | Like / Subscribe / Comment | label, action (big button), sub |
| `split` | Logo + text side by side | left (text), right (subtext) |

**Themes (index → colour)**:
0=gold · 1=purple · 2=red · 3=blue · 4=cyan · 5=amber · 6=green · 7=indigo · 8=pink · 9=teal

**Patterns (index → style)**:
0=rings · 1=nodes · 2=diagonal · 3=grid · 4=burst

**Voice**: `en-IN-PrabhatNeural` at `+18%` rate (Indian-English, punchy broadcast pace)

---

## Always include at the end

Remind the user:
- Video saved to: the exact file path
- To upload: open YouTube Studio → Create → Upload
- Suggest scheduling the daily video by running `/schedule`
