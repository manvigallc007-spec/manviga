---
name: ai-blog
description: This skill should be used when the user asks to write a blog post, create a long-form article, draft a newsletter, produce a written piece, write an explainer, or mentions "blog content", "article", or "newsletter" for The AI Chronicle.
version: 1.0.0
---

# AI Blog Content — The AI Chronicle

Handles all long-form written content: blog posts, articles, newsletters, and explainers.

## Brand Rules
- Factual, informative, neutral — no opinions, no editorializing
- No speculation presented as fact — hedge with "reportedly", "according to", "may"
- No drama language, no clickbait, no sensationalism
- Professional and accessible — no jargon without explanation
- No political framing, no controversy angles

## Inputs
- Topic or AI news story / concept
- Content type (news article / explainer / roundup / newsletter)
- Target length (short 300–500w / medium 600–900w / long 1000–1200w) — default: medium
- Platform (website blog / LinkedIn / Substack / email newsletter)
- Audience (general / developer / business)

## Outputs

### News Article Structure
```
Title:          Factual headline, max 70 chars, no clickbait
Intro (1 para): What happened + who is involved (2–3 sentences)
Section 1 — Background:
  What led to this? (2–4 sentences, verified context only)
Section 2 — What Happened:
  Key facts, chronological order, bullet points allowed
Section 3 — Why It Matters:
  Impact on users / developers / industry (2–4 sentences)
Section 4 — What's Next:
  Near-term developments, hedged ("may", "could", "expected to")
Conclusion (1 para):
  Brief restatement of significance, no new information
```

### Explainer Structure
```
Title:          "What Is [Topic]?" or "[Topic] Explained"
Intro:          Define the concept in plain language (2–3 sentences)
Section 1 — How It Works:
  Core mechanism, plain language, no assumed knowledge
Section 2 — Why It Matters:
  Real-world impact and use cases
Section 3 — Current State:
  Who is doing what, key players, recent developments
Section 4 — What to Watch:
  Trends or developments to follow (hedged)
```

### Newsletter Roundup Structure
```
Subject line:   Max 50 chars, factual, no clickbait
Intro (2 sentences): Frame the week/day in AI
Story 1–N:
  Headline (bold)
  2–3 sentence summary
  Source credit (if applicable)
Outro (1 sentence):
  "Stay informed with The AI Chronicle."
```

## Decision Rules
- IF content_type = news article → use News Article Structure
- IF content_type = explainer → use Explainer Structure
- IF content_type = newsletter → use Newsletter Roundup Structure
- IF audience = developer → include technical specifics (model names, APIs, benchmarks)
- IF audience = general → define all technical terms on first use
- IF audience = business → focus on industry impact, market implications
- IF length = short → use intro + why it matters + what's next only
- IF information is uncertain → state source or hedge explicitly

## Style Constraints
- Paragraph length: max 4 sentences
- Section headings: use `##` (H2) for sections, `###` (H3) for subsections
- Bullet points: use for lists of 3+ items
- Bold: use for key names, product names, key terms — not for emphasis
- No first-person ("I", "we") unless writing in newsletter voice
- No "In conclusion" — end sections directly
- Word count targets:
  - Short: 300–500 words
  - Medium: 600–900 words
  - Long: 1000–1200 words
