---
name: ai-video
description: This skill should be used when the user asks to generate a video, write a YouTube script, create a video pipeline, produce a scene breakdown, list b-roll, write on-screen text, create a reel, or mentions "video content" for The AI Chronicle.
version: 1.0.0
---

# AI Video Content — The AI Chronicle

Handles all video content generation for The AI Chronicle across YouTube long-form, YouTube Shorts, and Instagram Reels.

## Brand Rules
- Factual, neutral, professional — no drama, hype, or sensationalism
- No clickbait hooks — lead with the fact, not emotion
- Futuristic, minimal, clean visual aesthetic
- Tone: calm, informative, authoritative

## Inputs
- Topic or AI news story
- Platform (YouTube long-form / YouTube Shorts / Instagram Reel)
- Audience (general / technical)
- Duration target (optional)

## Outputs

### YouTube Long-Form (~6 min, 10 stories)
Structure per story slide:
```
Hook:           ALL CAPS headline (1 line, factual)
What Happened:  3 bullet points (concise, verified facts)
Why It Matters: 1–2 sentences
What's Next:    1 sentence (no speculation — state as possibility only)
```
Also produce:
- Intro slide copy (list of all stories)
- Outro CTA: "Subscribe for daily AI updates"
- On-screen text suggestions per scene
- B-roll description per scene (futuristic visuals, no faces)

### YouTube Shorts (10–25 sec)
```
Line 1: Hook fact (1 sentence, no clickbait)
Line 2: Core detail (1 sentence)
Line 3: Why it matters (1 sentence)
Optional on-screen text: key stat or name
```

### Instagram Reel (30–60 sec)
```
Hook (first 3 sec): bold factual statement
Body: 3–5 punchy lines, one fact per line
CTA: "Follow for daily AI updates"
```

## Decision Rules
- IF platform = YouTube long-form → use full Hook/What Happened/Why/Next structure
- IF platform = YouTube Shorts → max 3 lines, no filler
- IF platform = Instagram Reel → hook-first, punchy, no background context
- IF audience = technical → include model names, benchmarks, API details
- IF audience = general → use plain language, no jargon
- IF story is speculative → label as "reportedly" or "according to [source]"

## Style Constraints
- Video resolution: 1920×1080 (slides), 1080×1920 (Shorts/Reels)
- Font hierarchy: Hook = Arial Bold large, Body = Georgia Bold 44px, Secondary = Georgia 40px
- No transition effects described — keep scene notes purely content-focused
- B-roll must be AI-themed, futuristic — no real people, no political imagery
