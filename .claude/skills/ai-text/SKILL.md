---
name: ai-text
description: This skill should be used when the user asks to write a summary, create a social caption, generate metadata, write a description, produce tags or keywords, write a title, create a short-form text post, or mentions "text content" or "copy" for The AI Chronicle.
version: 1.0.0
---

# AI Text Content — The AI Chronicle

Handles all short-form text content: summaries, captions, metadata, titles, descriptions, and social copy.

## Brand Rules
- Factual, concise, neutral — no drama, hype, or emotional framing
- No clickbait titles — lead with the fact
- No speculation, unverified claims, or opinions
- No hashtags unless explicitly requested
- No filler ("This is huge", "You won't believe", "Game-changing")

## Inputs
- Topic or AI news story
- Platform (YouTube / Instagram / Facebook / TikTok / newsletter)
- Content type (summary / caption / title / description / tags / metadata)
- Tone (neutral / educational / authoritative) — default: neutral
- Length constraint (optional)

## Outputs

### YouTube Title
```
Format: [Key Entity]: [What Happened] — [Year if relevant]
Max: 70 characters
Examples:
  "OpenAI Updates GPT-4: Faster Reasoning and Lower Latency"
  "Google DeepMind Releases New Dataset Labeling Tool"
Rules:
  - No ALL CAPS
  - No questions as titles
  - No "SHOCKING" / "INSANE" / "BREAKING"
```

### YouTube Description
```
Paragraph 1 (2–3 sentences): What happened + who is involved
Paragraph 2 (2–3 sentences): Why it matters + impact
Paragraph 3 (1 sentence): What to expect next (hedge: "may", "could")

Subscribe line: "Subscribe to The AI Chronicle for daily AI updates."
Tags block: comma-separated, 10–15 tags, specific to story
```

### Instagram Caption
```
3 bullet points max, one fact per bullet
Format:
  • [Fact 1]
  • [Fact 2]
  • [Fact 3]
Optional CTA: "Follow for daily AI updates"
Max length: 150 characters per bullet
```

### Facebook Post
```
Intro sentence (1 line): what happened
Body (2–4 sentences): context + why it matters
Close (1 sentence): broader implication (no speculation)
No hashtags unless requested
```

### Metadata Block
```yaml
title: "..."           # max 70 chars, no clickbait
description: "..."     # 150–300 chars, factual summary
tags: [tag1, tag2]     # 10–15 items, specific + general
category: "Science & Technology"
```

## Decision Rules
- IF platform = YouTube → title (70 chars) + description (3 paragraphs) + tags
- IF platform = Instagram → 3-bullet caption, punchy, 150 chars max per bullet
- IF platform = Facebook → slightly longer, no hashtags, professional tone
- IF content_type = tags → mix specific (model name, company) + general (AI, machine learning)
- IF story involves a product → include product name in title
- IF story involves a company → include company name in first sentence

## Style Constraints
- Sentence length: max 20 words for social copy; max 30 words for descriptions
- Avoid repeating the same phrase in title + description
- Always use full brand name on first mention: "The AI Chronicle"
- Numbers: use numerals in titles ("10 Stories"), words in body ("ten companies")
