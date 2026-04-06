# Will AI Take My Job? — Video Production Package

**Brand:** The AI Chronicle  
**Platform:** YouTube Long-Form  
**Runtime:** ~5:50  
**Status:** Ready for generation

---

## Directory Structure

```
will-ai-take-my-job/
├── config/
│   ├── project.json          # Runtime, voice, visual, audio settings
│   └── metadata.json         # YouTube title, description, tags, provenance
├── script/
│   └── narration.md          # Full narration with timestamps + emphasis markers
├── audio/
│   └── tts_clean.txt         # Plain text TTS input (no markdown, no symbols)
├── slides/
│   └── scene_plan.md         # Slide-by-slide layout: hook, bullets, on-screen text
├── graphics/
│   └── broll_prompts.md      # Image generation prompts for each scene + thumbnail
├── thumbnail/
│   └── thumbnail_spec.md     # 1280×720 thumbnail layout, text layers, variants A/B
└── output/                   # Generated files go here (video, audio, images)
```

---

## Generation Order

1. **Images** — Run `graphics/broll_prompts.md` prompts through image generator (Midjourney / SD / DALL-E)
2. **Thumbnail** — Run `thumbnail/thumbnail_spec.md` background prompt; overlay text in post
3. **Audio** — Feed `audio/tts_clean.txt` to edge-tts with American Indian voice parameter
4. **Slides** — Build slides from `slides/scene_plan.md` layout specs (1920×1080)
5. **Video** — Compose slides + audio + music bed using FFmpeg or video generator
6. **Upload** — Use `config/metadata.json` for YouTube title, description, tags

---

## Quick Reference

| Asset | File | Status |
|---|---|---|
| Narration script | `script/narration.md` | Ready |
| TTS plain text | `audio/tts_clean.txt` | Ready |
| Scene layout | `slides/scene_plan.md` | Ready |
| B-roll prompts | `graphics/broll_prompts.md` | Ready |
| Thumbnail spec | `thumbnail/thumbnail_spec.md` | Ready |
| YouTube metadata | `config/metadata.json` | Draft |
| Generated output | `output/` | Pending |

---

## Voice Settings (edge-tts)

```python
import edge_tts
tts = edge_tts.Communicate(
    text=open("audio/tts_clean.txt").read(),
    voice="en-IN-NeerjaNeural",  # American Indian English, female — calm
    rate="+0%",
    pitch="+0Hz"
)
```

Alternative voices: `en-IN-PrabhatNeural` (male), `en-IN-NeerjaExpressiveNeural`

---

## Provenance

- Source: `prepare-prompt.txt` briefing
- Quoted verbatim: "This remains the #1 query." / "In 2026, the global conversation..."
- No speculative claims included
- Safety check: run before publishing
