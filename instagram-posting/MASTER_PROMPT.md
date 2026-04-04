# THE AI CHRONICLE — Master Instagram Post Generator Prompt

**Version 12 — Final Edition**

> Paste this entire prompt into any LLM with code execution capability to generate professional Instagram posts with original synthesized music.

---

## Overview

This is a complete, production-ready system for generating professional Instagram posts for the account **@theaichronicle** — a daily AI news channel.

The system generates **TWO files per story**:
- **(a)** A 1080×1080 PNG image at 300 DPI (static Instagram post)
- **(b)** A 1080×1080 MP4 video (H.264 + AAC 192kbps) with original synthesized music

Every post is **fully randomized but reproducible** — the same story always produces the same visual design and music track.

---

## Quick Start Guide

### Step 1: Prepare Your Story

Fill in this JSON structure with today's AI news:

```json
{
    "company":      "[COMPANY / TOPIC]",
    "headline":     "[PUNCHY HEADLINE — MAX 8 WORDS]",
    "watermark":    "[KEY STAT OR WORD, e.g. $730B or 8,000]",
    "body": [
        "[LINE 1 — MAX 30 CHARACTERS]",
        "[LINE 2 — MAX 30 CHARACTERS]",
        "[LINE 3 — MAX 30 CHARACTERS]",
        "[LINE 4 — MAX 30 CHARACTERS]"
    ],
    "stat_label":   "[METRIC NAME, e.g. Weekly Active Users]",
    "stat_value":   "[BIG NUMBER, e.g. 900M or $730B]",
    "source":       "[PUBLICATION, e.g. OpenAI / TechCrunch]"
}
```

### Step 2: Run the Python Script

Copy the entire Python code block below and paste it into:
- Claude.ai (Code Interpreter)
- ChatGPT (Code Interpreter)
- Microsoft Copilot
- Google Gemini
- Any LLM with Python execution

### Step 3: Download Files

The system generates:
- `theaichronicle_post.png` — Upload as Instagram Feed Post
- `theaichronicle_post.mp4` — Upload as Instagram Reel
- `theaichronicle_music.wav` — Optional audio reference

---

## Requirements

### Python Packages
```bash
pip install Pillow numpy scipy
```

### System Tools
- **FFmpeg** (must be installed and in PATH)
- **Logo file**: `logo.PNG` in working directory

### Fonts
- DejaVu Sans + DejaVu Serif (auto-fallback to system default)

### Compatibility
- ✅ Claude.ai Code Interpreter
- ✅ ChatGPT Code Interpreter
- ✅ Microsoft Copilot
- ✅ Google Gemini
- ✅ Any LLM with Python execution

---

## Layout Design (9 Fixed Zones)

```
┌─────────────────────────────────────────┐
│ Zone 1: 8px Top Accent Bar              │
├─────────────────────────────────────────┤
│ Zone 2: "THE AI CHRONICLE" + Divider    │
│         "D A I L Y  A I  N E W S"       │
├─────────────────────────────────────────┤
│ Zone 3: Category Pill (Company Name)    │
├─────────────────────────────────────────┤
│ Zone 4: Main Headline (2 lines max)     │
├─────────────────────────────────────────┤
│ Zone 5: 2px Divider Line                │
├─────────────────────────────────────────┤
│ Zone 6: 4-Line Body Summary             │
├─────────────────────────────────────────┤
│ Zone 7: Hero Stat Box (160px tall)      │
│         Label + Large Value (centered)  │
├─────────────────────────────────────────┤
│ Zone 8: Source Credit                   │
├─────────────────────────────────────────┤
│ Zone 9: Footer (Logo + Handle + CTA)    │
│         @theaichronicle • Daily AI News │
│         8px Bottom Accent Bar           │
└─────────────────────────────────────────┘
```

---

## Randomization System

### Per-Post Variations (Seeded by Story)
Deterministic randomization based on `headline + company`:

| Element | Options | Count |
|---------|---------|-------|
| Color Theme | 24 total (12 dark + 12 light) | 24 |
| Background Style | neural, grid, radar, bars, stars, triangles, hexagons, circuit, waves, scatter, diagonals | 11 |
| Music Track | 64 unique combinations | 64 |
| Watermark Alpha | Variable opacity | - |

**Same story = Same design + Same music** (reproducible)

### Color Themes (24 Total)

**Dark Gradient Themes:**
1. Midnight Gold — Deep black → Gold
2. Deep Cosmos — Deep purple → Light purple
3. Forest Dark — Dark green → Light green
4. Crimson Dark — Dark red → Light red
5. Deep Navy — Dark blue → Light blue
6. Dark Amber — Dark orange → Light orange
7. Dark Cobalt — Dark cyan → Light cyan
8. Deep Indigo — Dark teal → Light teal
9. Obsidian Rose — Dark pink → Light pink
10. Solar Flare — Dark orange → Light orange
11. Violet Storm — Dark purple → Light purple
12. Teal Abyss — Dark teal → Light teal

**Light Gradient Themes:**
13. Cloud White — White → Light purple
14. Warm Parchment — White → Light beige
15. Mint Fresh — White → Light green
16. Alert White — White → Light red
17. Ice Blue — White → Light blue
18. Warm Sand — White → Light yellow
19. Arctic Cyan — White → Light cyan
20. Aqua Mist — White → Light teal
21. Blush Pearl — White → Light pink
22. Lemon Zest — White → Light yellow
23. Sky Foam — White → Light blue
24. Sage Calm — White → Light green

### Background Generators (11 Styles)

1. **Neural Network** — Clusters of nodes with connecting lines
2. **Grid** — Regular geometric grid with small accent nodes
3. **Radar** — Concentric circles with radial spokes
4. **Bars** — Dancing bar chart visualization
5. **Stars** — Scattered particles with connecting trails
6. **Triangles** — Converging triangular patterns
7. **Hexagons** — Nested hexagonal rings
8. **Circuit Board** — Orthogonal circuit traces + nodes
9. **Waves** — Oscillating sine wave layers
10. **Scatter Plot** — Random dots with connecting line
11. **Diagonals** — Overlapping diagonal streaks

### Music Generation (64 Unique Tracks)

Synthesized from:
- **BPMs**: 72, 82, 88, 95, 105, 110, 118, 125, 128, 132, 138, 140 (12 options)
- **Root Keys**: C (55Hz), D♭, D, E♭, E, F, F♯, G, G♯, A, A♯, B (12 options)
- **Scale Types**: Major pentatonic, minor pentatonic, blues, 7-note scales (4 options)
- **Waveforms**: Sine, Sawtooth, Square, Triangle (4 options)

**No external music library needed** — all audio synthesized algorithmically.

---

## Example Stories

### Example 1: Funding Round
```python
story = {
    "company":      "OpenAI / Funding",
    "headline":     "OpenAI Raises $110B at $730B Valuation",
    "watermark":    "$730B",
    "body": [
        "Amazon, NVIDIA & SoftBank",
        "back OpenAI's $110B raise.",
        "A $730B valuation makes it",
        "the world's most valued AI firm."
    ],
    "stat_label":   "OpenAI Pre-Money Valuation",
    "stat_value":   "$730B",
    "source":       "OpenAI / The AI Track"
}
```

### Example 2: Model Release
```python
story = {
    "company":      "Anthropic / Models",
    "headline":     "Claude 4.2 Passes Bar Exam",
    "watermark":    "92%",
    "body": [
        "Scores 92% on US Bar Exam,",
        "up from Claude 4.1's 88%.",
        "Model now advises on legal",
        "matters with human-level accuracy."
    ],
    "stat_label":   "US Bar Exam Score",
    "stat_value":   "92%",
    "source":       "Anthropic / Legal AI Weekly"
}
```

### Example 3: Layoffs
```python
story = {
    "company":      "Meta / Restructuring",
    "headline":     "Meta Cuts 10k Jobs, Focuses on AI",
    "watermark":    "10,000",
    "body": [
        "Meta announced 10,000 layoffs",
        "to refocus on AI research.",
        "CEO Mark Zuckerberg says this",
        "positions Meta as an AI leader."
    ],
    "stat_label":   "Meta Employees Laid Off",
    "stat_value":   "10,000",
    "source":       "Meta / TechCrunch"
}
```

### Example 4: Regulation
```python
story = {
    "company":      "US Government / Policy",
    "headline":     "White House Unveils AI Framework",
    "watermark":    "2026",
    "body": [
        "The White House introduced",
        "a unified national AI framework.",
        "Replaces fragmented state-level",
        "regulation with single standard."
    ],
    "stat_label":   "US States With AI Laws",
    "stat_value":   "42",
    "source":       "White House / WBN News"
}
```

---

## Python Implementation

See [MASTER_PROMPT_CODE.py](MASTER_PROMPT_CODE.py) for the complete implementation.

Or copy the code block from the original master prompt document.

---

## Output Files

### 1. `theaichronicle_post.png`
- **Resolution**: 1080×1080px
- **DPI**: 300 (high resolution for print/sharing)
- **Format**: PNG (lossless, supports transparency)
- **Use**: Instagram Feed Post, website, email

### 2. `theaichronicle_post.mp4`
- **Resolution**: 1080×1080px
- **Codec**: H.264 video + AAC 192kbps audio
- **Duration**: 30 seconds (customizable)
- **Frame Rate**: 30fps
- **Use**: Instagram Reel

### 3. `theaichronicle_music.wav`
- **Sample Rate**: 44.1kHz
- **Bit Depth**: 16-bit stereo
- **Duration**: 30 seconds
- **Use**: Optional audio reference or editing

---

## Instagram Posting Tips

### Feed Post (PNG)
1. Upload `theaichronicle_post.png` as a standard feed post
2. Add caption with story details
3. Use 10-15 relevant hashtags in first comment
4. Post between 6–9 PM local time for peak engagement

### Reel (MP4)
1. Upload `theaichronicle_post.mp4` as a Reel
2. Keep original audio or add trending music in Instagram app
3. Write engaging copy for first few lines
4. Enable comments and sharing
5. Use trending sounds for amplification

### Engagement Strategy
- **Hour 1**: Reply to every comment to boost reach
- **Day 1**: Monitor performance and share to Stories
- **Week 1**: Repost to Threads and other platforms
- **Archive**: Save high-performing posts

### Hashtag Strategy
```
#AI #ArtificialIntelligence #Tech #Technology #News #AINews
#ML #MachineLearning #DeepLearning #DataScience #SoftwareDevelopment
#FutureOfWork #Innovation #TechNews #TheAIChronicle
```

---

## Customization Guide

### Change Post Dimensions
Edit `W` and `H` variables (currently 1080×1080):
```python
W, H = 1080, 1080  # Square (Instagram Feed/Reel)
# or
W, H = 1080, 1920  # Vertical (Instagram Story/Reel)
# or
W, H = 1920, 1080  # Landscape (YouTube thumbnail)
```

### Change Video Duration
Edit `DURATION` variable (currently 30 seconds):
```python
DURATION = 30  # seconds
# or
DURATION = 15  # for shorter Reels
# or
DURATION = 60  # for longer stories
```

### Change Output Filenames
Edit the OUTPUT variables:
```python
OUT_PNG = "theaichronicle_post.png"
OUT_MP4 = "theaichronicle_post.mp4"
OUT_WAV = "theaichronicle_music.wav"
```

### Limit Color Themes
Edit `THEMES` list to only use specific themes:
```python
# Use only light themes
THEMES = THEMES[12:]  # Indices 12-23

# Use only dark themes
THEMES = THEMES[:12]  # Indices 0-11
```

### Limit Background Styles
Edit `BG_GENS` list:
```python
BG_GENS = [bg_neural, bg_grid, bg_radar]  # Only 3 styles
```

---

## Troubleshooting

### "ImportError: No module named PIL"
```bash
pip install Pillow
```

### "FFmpeg not found"
1. Install FFmpeg: https://ffmpeg.org/download.html
2. Add to system PATH
3. Verify: `ffmpeg -version`

### "FileNotFoundError: logo.PNG"
1. Ensure `logo.PNG` exists in working directory
2. Check file extension (must be `.PNG` uppercase)
3. Verify file is readable

### "MP4 not created but PNG exists"
- Check FFmpeg error in console output
- Verify audio file was created successfully
- Try with different video codec: `libx265` or `mpeg4`

### Image looks pixelated
- Increase DPI in PNG save command (currently 300)
- Use higher quality fonts
- Ensure source logo is high-resolution

### Music sounds wrong or repetitive
- This is normal — music is randomized per story
- Different stories = Different music
- All variations are algorithmically generated

---

## Performance Metrics

Typical generation times on modern hardware:

| Task | Duration |
|------|----------|
| PNG generation | 2-3 seconds |
| Audio synthesis | 3-5 seconds |
| MP4 encoding | 8-15 seconds |
| **Total per post** | **~20-25 seconds** |

---

## Security & Privacy

- **No API calls**: All generation happens locally
- **No external data**: Fonts downloaded from system
- **No tracking**: No analytics or telemetry
- **Open source concept**: Code is transparent and auditable

---

## License & Usage

This prompt is provided as-is for creating AI news content. 

**You own all outputs** — use the generated PNG/MP4 files however you wish, including:
- ✅ Commercial use
- ✅ Social media posting
- ✅ Print and merchandise
- ✅ Redistribution
- ✅ Modification

No attribution required (but appreciated!).

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v12 (Current) | 2026 | Final production release |
| v11 | 2026 | Added 11 background generators |
| v10 | 2025 | Music synthesis system |
| v9 | 2025 | 24 color themes |
| v1 | 2024 | Initial release |

---

## Support & Questions

For issues or improvements, refer to:
- Font paths (DejaVu Sans/Serif)
- FFmpeg codec compatibility
- Python PIL/Pillow version (3.9+)
- System audio codec support

---

## One-Liner Quick Start

```
1. Fill in story dict  →  2. Paste code into LLM  →  3. Download PNG/MP4  →  4. Post to Instagram
```

Done. Your post is ready.

---

**Happy posting! 🚀**

*The AI Chronicle — Because AI waits for no one.*
