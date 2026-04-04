---
name: ai-audio
description: This skill should be used when the user asks to generate a voiceover, write a narration script, produce TTS audio, create spoken content, write an audio script with timestamps, or mentions "audio pipeline" or "narration" for The AI Chronicle.
version: 1.0.0
---

# AI Audio Content — The AI Chronicle

Handles all spoken/audio content generation: voiceover scripts, TTS-ready narration, and audio pipeline instructions.

## Brand Rules
- Neutral, calm, professional voice — no drama, no hype
- Sentences must be short and speakable (max ~15 words per sentence)
- No filler words ("um", "so", "basically", "actually")
- Factual only — no speculation, no opinion
- Write for the ear, not the eye: avoid complex punctuation, symbols, abbreviations

## Inputs
- Topic or AI news story
- Duration target (e.g. 30s, 3 min, 6 min)
- Voice style (neutral / authoritative / calm) — default: neutral
- Platform (YouTube / Instagram / podcast)
- TTS engine (edge-tts / gtts / ElevenLabs) — default: edge-tts

## Outputs

### Voiceover Script Format
```
[00:00] Sentence one. Pause.
[00:05] Sentence two.
[00:10] Sentence three. [EMPHASIS: key term]
```

Each story segment:
```
Hook:           1 sentence — factual, direct
What Happened:  2–3 sentences
Why It Matters: 1–2 sentences
What's Next:    1 sentence (hedge with "may", "could", "reportedly")
```

### Emphasis Markers
Use inline markers for TTS guidance:
- `[EMPHASIS: word]` — stress this word
- `[PAUSE]` — insert 0.5s pause
- `[SLOW]` — reduce pace for 1 sentence
- `[BREAK]` — insert 1s break between sections

## Decision Rules
- IF engine = edge-tts → pass rate/pitch as constructor params (NOT SSML tags)
  ```python
  edge_tts.Communicate(text, voice, rate="+8%", pitch="+0Hz")  # CORRECT
  ```
- IF duration = short (≤30s) → max 3 sentences, hook only
- IF duration = medium (1–3 min) → hook + what happened + why it matters
- IF duration = long (>3 min) → full structure per story × N stories
- IF platform = Instagram → punchy, 3–5 sentences max
- IF platform = YouTube → full story structure, natural pacing
- IF abbreviation in text → spell out for TTS (e.g. "AI" → keep, "GPT-4" → "G P T 4")

## Style Constraints
- No markdown in final script output (TTS engines read it literally)
- Numbers: write as words for TTS ("three billion" not "3B")
- URLs, emails: omit entirely from spoken scripts
- Brand name: "The AI Chronicle" — always full name on first mention
- Outro: always end with "Subscribe to The AI Chronicle for daily AI updates."
