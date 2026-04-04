---
name: ai-image
description: This skill should be used when the user asks to generate an image prompt, create a background prompt, write a Midjourney or Stable Diffusion prompt, produce AI art directions, describe a visual for generation, or mentions "image generation", "background image", or "image pipeline" for The AI Chronicle.
version: 1.0.0
---

# AI Image Generation — The AI Chronicle

Handles all image generation prompts: backgrounds, thumbnails, slide images, social visuals, and brand-aligned AI art prompts.

## Brand Rules
- Futuristic, clean, minimalist aesthetic — no dystopia, no chaos
- Soft blue/white/teal lighting — no harsh red/orange tones
- No human faces unless explicitly requested
- No text in the image unless explicitly requested
- No political imagery, flags, logos, or copyrighted characters
- No violence, weapons, or disturbing content
- High-quality, cinematic depth — not cartoon or flat design

## Inputs
- Purpose (background / thumbnail / social post / carousel / slide image)
- Topic or theme (optional — used to tailor the prompt)
- Color variant (blue / purple / neutral) — default: blue
- Aspect ratio (16:9 / 1:1 / 9:16) — default: 16:9
- Engine (Midjourney / Stable Diffusion / DALL-E / Flux) — default: generic

## Base Style Block
Always include in every prompt:
```
ultra-clean futuristic AI interface, holographic elements, glowing data streams,
minimalistic tech environment, soft blue and white lighting, cinematic depth,
8k detail, no humans, no text
```

## Outputs

### Standard Prompt Format
```
[Subject/Scene description], [style modifiers], [lighting], [mood], [technical specs]

Negative prompt: humans, faces, text, watermark, logo, political symbols,
                 dystopian imagery, violence, noise, blur, low quality
```

### Background Image (16:9, 1920×1080)
```
Prompt:
  [theme-specific scene], ultra-clean futuristic AI interface, holographic 
  elements, glowing data streams, minimalistic tech environment, soft [color] 
  and white lighting, cinematic depth, 8k detail, no humans, no text,
  wide landscape composition, dark background gradient

Negative: humans, faces, text, logos, clutter, noise, blur
```

### Thumbnail Visual (16:9, 1280×720)
```
Prompt:
  [theme-specific foreground element], cinematic left-heavy composition,
  futuristic AI environment, holographic glow, [accent color] light accents,
  dark background, high contrast, ultra-sharp, no text, no faces,
  professional editorial style, 8k

Negative: humans, faces, text, cluttered background, low resolution
```

### Instagram Square (1:1, 1080×1080)
```
Prompt:
  [theme-specific scene], centered square composition, futuristic minimal design,
  [accent color] holographic accents, dark background, clean negative space,
  no text, no faces, 8k detail

Negative: humans, faces, text, busy composition, watermarks
```

### Instagram Story (9:16, 1080×1920)
```
Prompt:
  [theme-specific scene], vertical portrait composition, futuristic AI aesthetic,
  top-heavy focal point, [accent color] glow effects, dark gradient background,
  no text, no faces, 8k

Negative: humans, faces, text, horizontal composition, noise
```

## Decision Rules
- IF purpose = background → use wide landscape, dark gradient, minimal foreground
- IF purpose = thumbnail → use left-heavy composition, high contrast, strong focal point
- IF purpose = Instagram → use centered or vertical composition with clean negative space
- IF color = blue → accent with #00D2FF, soft cyan/teal lighting
- IF color = purple → accent with #D264FF, violet/magenta glow
- IF color = neutral → use white/silver/gray holographic tones
- IF engine = Midjourney → append `--ar [ratio] --v 6 --style raw`
- IF engine = Stable Diffusion → add CFG scale note, sampler (DPM++ 2M Karras)
- IF topic provided → add 1–2 topic-specific visual elements (e.g. "neural network nodes", "satellite orbiting Earth", "robotic arm in lab")

## Example Prompts

**YouTube Background (blue):**
```
abstract neural network visualization, floating holographic nodes connected by 
glowing blue lines, ultra-clean futuristic AI interface, soft cyan and white 
lighting, dark space background, cinematic depth, 8k detail, no humans, no text,
wide landscape composition
```

**Thumbnail Visual (purple):**
```
single glowing AI chip on dark surface, purple holographic light rays, cinematic 
close-up, futuristic tech environment, high contrast, ultra-sharp, no text, 
no faces, editorial style, 8k
```
