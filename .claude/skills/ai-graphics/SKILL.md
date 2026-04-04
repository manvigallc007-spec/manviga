---
name: ai-graphics
description: This skill should be used when the user asks to design a slide, create a carousel, produce a graphic, lay out a thumbnail, design a story card, create visual content, or mentions "graphics pipeline", "slide design", or "carousel layout" for The AI Chronicle.
version: 1.0.0
---

# AI Graphics Content — The AI Chronicle

Handles all visual/graphic content design: slides, carousels, thumbnails, story cards, and layout instructions.

## Brand Rules
- Futuristic, minimal, clean aesthetic — no clutter, no busy layouts
- High contrast — text must be legible on dark backgrounds
- Color palette: electric blue `#00D2FF`, purple `#D264FF`, white `#FFFFFF`, dark `#0A0A1A`
- No political imagery, no faces unless explicitly requested
- No copyrighted logos or characters
- No stock photo clichés (no handshakes, no lightbulbs)

## Inputs
- Content type (slide / carousel / thumbnail / story card / banner)
- Topic or headline text
- Platform (YouTube / Instagram / Facebook / TikTok)
- Color variant (blue / purple / neutral) — default: blue
- Background image available (yes/no)

## Outputs

### Video Slide (1920×1080)
```
Layout:
  Left column (60% width):
    - Section label: Arial Bold 40px, accent color
    - Hook headline: Arial Bold large, ALL CAPS, white
    - Body bullets: Georgia Bold 44px, white, 3 items
    - Secondary text: Georgia 40px, light gray

  Right column (40% width):
    - Full-bleed background image card
    - Rounded mask (radius 24px)
    - Dark overlay (opacity 0.45)
```

### YouTube Thumbnail (1280×720)
```
Layout:
  - Full-bleed AI background image
  - Left-heavy cinematic gradient scrim (left → transparent)
  - Top bar: logo left + "THE AI CHRONICLE" right (Arial Bold 36px)
  - Accent label: "YOUR TOP 10 AI NEWS FROM TODAY" (accent color, Arial Bold 28px)
  - Headline: up to 2 lines, Arial Bold 80–110px, white, auto-sized
  - Date box: rounded border, accent-tinted, left white bar, dot decorations
  - Bottom bar: logo + @theaichronicle007 + hashtags
  Variant A: electric blue #00D2FF
  Variant B: purple #D264FF
```

### Instagram Carousel Slide (1080×1080)
```
Layout:
  - Dark background (#0A0A1A or gradient)
  - Centered or left-aligned text block
  - Headline: bold, large (60–80px equivalent)
  - Body: 2–3 lines max (40–50px equivalent)
  - Bottom: branding strip — logo + @theaichronicle007
  - Accent line or border in brand color
```

### Instagram Story Card (1080×1920)
```
  - Full-bleed background
  - Top: logo
  - Center: headline + 2–3 body lines
  - Bottom: CTA + handle
```

## Decision Rules
- IF platform = YouTube → produce thumbnail spec (1280×720) + slide specs (1920×1080)
- IF platform = Instagram → produce carousel (1080×1080) or story card (1080×1920)
- IF color variant = blue → use #00D2FF as accent
- IF color variant = purple → use #D264FF as accent
- IF no background image → use dark gradient (#0A0A1A → #1A1A2E)
- IF headline > 60 chars → split across 2 lines, reduce font size

## Style Constraints
- Max 2 fonts per graphic: Arial Bold (labels/headlines) + Georgia (body)
- Text must have sufficient contrast ratio (≥4.5:1 on dark backgrounds)
- No text in image generation prompts unless explicitly requested
- Rounded corners on image cards: radius 24px
- All specs written as layout instructions — not as code
