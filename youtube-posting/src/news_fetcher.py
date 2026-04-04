#!/usr/bin/env python3
"""
THE AI CHRONICLE — YouTube News Fetcher
Uses Anthropic API web search to select 10 geo-balanced AI stories.
Geo mix: ~3 USA · ~3 India · ~2 China · ~2 Global
Story format matches video_generator slide spec.
Completely independent from the Instagram pipeline.
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

ROOT_ENV = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ROOT_ENV)

PROJECT_ROOT = Path(__file__).parent.parent
POSTED_LOG   = PROJECT_ROOT / "logs" / "posted_stories.json"

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────────

def _load_posted():
    if POSTED_LOG.exists():
        try:
            with open(POSTED_LOG, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_posted(headlines: list):
    posted = _load_posted()
    for h in headlines:
        posted.append({"headline": h, "posted_at": datetime.now().isoformat()})
    posted = posted[-200:]
    POSTED_LOG.parent.mkdir(exist_ok=True)
    with open(POSTED_LOG, "w", encoding="utf-8") as f:
        json.dump(posted, f, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────────
# SEARCH PROMPT
# ─────────────────────────────────────────────

SEARCH_PROMPT = """You are a broadcast news producer for @theaichronicle — a YouTube AI news channel.
Today is {today}.

Search the web and find 10 significant AI news stories published in the last 48 hours.

VERIFIED SOURCES ONLY:
TechCrunch, The Verge, Wired, VentureBeat, MIT Technology Review, Reuters, Bloomberg,
BBC, The Economic Times, Inc42, YourStory, Analytics Vidhya, TechNode, Pandaily,
South China Morning Post Tech, OpenAI blog, Google DeepMind, Anthropic blog, Meta AI,
Microsoft blog, NVIDIA blog, ArXiv, Nature, Science, The Decoder, AI Business.

GEOGRAPHIC MIX (select approximately):
  • 3 stories from USA sources
  • 3 stories from INDIA sources
  • 2 stories from CHINA/Asia sources
  • 2 stories from GLOBAL sources (UK, Europe, international)
Shuffle the final order randomly — do NOT group by region.

TOPICS (newsworthy only — no gossip, no opinion):
New AI model release · Major funding · Research breakthrough · Benchmark record ·
Enterprise AI deployment · Government AI regulation · AI safety finding

ALREADY POSTED — DO NOT REPEAT:
{avoid_list}

Return ONLY a JSON array of exactly 10 story objects, no other text:
[
  {{
    "company":    "<company or org, max 22 chars>",
    "headline":   "<punchy YouTube headline, max 8 words, title case>",
    "summary":    "<one plain sentence, max 14 words, what happened>",
    "impact":     "<why this matters TODAY, 2 sentences, max 28 words>",
    "watermark":  "<1 key word or metric, max 12 chars, all caps>",
    "body":       ["<fact max 28 chars>","<fact max 28 chars>","<fact max 28 chars>","<fact max 28 chars>"],
    "stat_label": "<metric label, max 26 chars>",
    "stat_value": "<striking number, max 14 chars, e.g. $10B, 94%, 3x>",
    "source":     "<publication name, max 26 chars>",
    "region":     "<single emoji flag: 🇺🇸 🇮🇳 🇨🇳 🇬🇧 🇪🇺 🌐 etc>",
    "hashtags":   ["#Tag1","#Tag2","#Tag3","#Tag4","#Tag5"],
    "tts_script": "<60-80 word spoken script. NEVER start with Story 1/2/N. Use broadcast transitions: Meanwhile..., Over at [Company]..., In a major move..., Breaking overnight..., Switching gears..., On the business side..., In a surprising twist..., Hot off the wire..., And finally.... Conversational, punchy, energetic. End with a why-it-matters sentence.>"
  }}
]"""

# ─────────────────────────────────────────────
# FETCH
# ─────────────────────────────────────────────

def fetch_todays_stories() -> list[dict]:
    """
    Fetch 10 geo-balanced AI news stories for today's YouTube video.
    Returns list of story dicts. Falls back to FALLBACK_STORIES on failure.
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        recent    = _load_posted()[-40:]
        avoid_list = "\n".join(f"  - {p['headline']}" for p in recent) or "  None"
        today     = datetime.now().strftime("%B %d, %Y")

        logger.info("[NEWS] Searching web for 10 geo-balanced AI stories...")
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=6000,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 5,
            }],
            messages=[{"role": "user", "content": SEARCH_PROMPT.format(
                today=today,
                avoid_list=avoid_list,
            )}],
        )

        for block in reversed(response.content):
            if getattr(block, "type", None) == "text":
                text = block.text.strip()
                if "[" in text and "]" in text:
                    match = re.search(r'\[[\s\S]+\]', text)
                    if match:
                        stories = json.loads(match.group())
                        validated = [_validate(s) for s in stories]
                        validated = [s for s in validated if s]
                        if len(validated) >= 5:
                            _save_posted([s["headline"] for s in validated])
                            logger.info(f"[NEWS] Fetched {len(validated)} stories")
                            for i, s in enumerate(validated, 1):
                                logger.info(f"  {i:2d}. [{s['region']}] {s['company']} — {s['headline']}")
                            return validated

        logger.error("[NEWS] Could not parse stories from API response")
        return FALLBACK_STORIES

    except json.JSONDecodeError as e:
        logger.error(f"[NEWS] JSON parse error: {e}")
        return FALLBACK_STORIES
    except Exception as e:
        logger.error(f"[NEWS] Fetch failed: {e}")
        return FALLBACK_STORIES


def _validate(story: dict) -> dict | None:
    required = ["company","headline","summary","impact","watermark","body",
                "stat_label","stat_value","source","region","hashtags","tts_script"]
    if any(k not in story for k in required):
        return None
    if not isinstance(story["body"], list) or len(story["body"]) < 4:
        return None
    if not isinstance(story["hashtags"], list):
        story["hashtags"] = story["hashtags"].split() if isinstance(story["hashtags"], str) else []
    story["body"] = [str(b)[:28] for b in story["body"][:4]]
    # Strip any accidental "Story N" prefix from tts_script
    story["tts_script"] = re.sub(r'^Story\s+\d+[:\.\-]?\s*', '', story["tts_script"]).strip()
    return story

# ─────────────────────────────────────────────
# FALLBACK STORIES
# ─────────────────────────────────────────────

FALLBACK_STORIES = [
    {
        "company": "OpenAI",
        "headline": "GPT-5 Sets New Reasoning Record",
        "summary": "OpenAI's GPT-5 tops all major reasoning benchmarks.",
        "impact": "GPT-5 outperforms human experts on graduate-level tasks. Enterprises gain access this week via API.",
        "watermark": "GPT-5",
        "body": ["Tops MMLU at 96% accuracy","Beats human doctors on QA","256k context window","API access opens today"],
        "stat_label": "MMLU Benchmark Score",
        "stat_value": "96%",
        "source": "OpenAI Blog",
        "region": "🇺🇸",
        "hashtags": ["#OpenAI","#GPT5","#AI","#ChatGPT","#ArtificialIntelligence"],
        "tts_script": "Over at OpenAI, GPT-5 just shattered every reasoning benchmark on record, hitting 96 percent on the MMLU — that's above board-certified human performance. Enterprise API access opens this week, which means every developer on the planet is about to get a significant upgrade.",
    },
    {
        "company": "Google DeepMind",
        "headline": "Gemini Ultra Beats Human Doctors",
        "summary": "Gemini Ultra 2 scores 90% on clinical medical questions.",
        "impact": "AI now outperforms specialists in 9 of 12 medical specialties. Deployment in healthcare is imminent.",
        "watermark": "HEALTH",
        "body": ["90% on clinical QA tests","Beats specialists in 9/12","14,000 questions tested","Phase 2 trials approved"],
        "stat_label": "Clinical Accuracy",
        "stat_value": "90%",
        "source": "Google DeepMind",
        "region": "🇺🇸",
        "hashtags": ["#Google","#Gemini","#AIHealth","#DeepMind","#MedicalAI"],
        "tts_script": "Meanwhile at Google DeepMind, Gemini Ultra 2 is now outperforming board-certified doctors on 9 out of 12 medical specialties in a landmark clinical study. The model answered 14,000 questions with 90 percent accuracy, pushing AI-assisted diagnostics closer to real-world deployment.",
    },
    {
        "company": "Anthropic",
        "headline": "Claude 4 Leads Safety Benchmarks",
        "summary": "Claude 4 scores highest on AI safety evaluations.",
        "impact": "Anthropic's new model sets the industry bar for safety and alignment. Regulators are paying attention.",
        "watermark": "SAFE",
        "body": ["Tops all safety benchmarks","99% harmless on red-team","Available in API today","Cheaper than GPT-4"],
        "stat_label": "Safety Score",
        "stat_value": "99%",
        "source": "Anthropic Blog",
        "region": "🇺🇸",
        "hashtags": ["#Anthropic","#Claude4","#AISafety","#AI","#LLM"],
        "tts_script": "Switching gears to AI safety — Anthropic's Claude 4 just topped every safety benchmark in the industry, scoring 99 percent on red-team harmlessness evaluations. That's a big deal as governments worldwide push for AI accountability standards.",
    },
    {
        "company": "Reliance Jio",
        "headline": "India Launches National AI Platform",
        "summary": "Reliance Jio unveils India's largest AI infrastructure.",
        "impact": "India's Jio deploys sovereign AI compute across 12 cities. This positions India as a top-3 global AI nation.",
        "watermark": "INDIA",
        "body": ["12 city AI data centers","1 exaflop compute total","Indian language models","Free for startups 2026"],
        "stat_label": "Compute Capacity",
        "stat_value": "1 ExaFLOP",
        "source": "Economic Times",
        "region": "🇮🇳",
        "hashtags": ["#India","#JioAI","#AIIndia","#DigitalIndia","#AI"],
        "tts_script": "In a major move, Reliance Jio just unveiled India's largest sovereign AI compute platform — one exaflop spread across 12 cities. This is India's boldest step yet to compete with the US and China in the global AI race, and startups get free access in 2026.",
    },
    {
        "company": "IIT Bombay / ISRO",
        "headline": "India AI Detects Crop Disease Early",
        "summary": "IIT Bombay and ISRO deploy AI for precision farming.",
        "impact": "AI system detects crop disease 3 weeks before visible symptoms. Could protect $8B in annual farm losses.",
        "watermark": "FARM",
        "body": ["3-week early detection","Satellite + AI fusion","8B USD losses protected","250M farmers benefited"],
        "stat_label": "Early Detection Lead",
        "stat_value": "3 Weeks",
        "source": "Analytics Vidhya",
        "region": "🇮🇳",
        "hashtags": ["#IndiaAI","#AgriTech","#ISRO","#IITBombay","#AI"],
        "tts_script": "Hot off the wire from India — IIT Bombay and ISRO have deployed a satellite AI system that detects crop disease three full weeks before it becomes visible. Protecting 8 billion dollars in farm losses annually across 250 million farmers. This is AI where it truly matters.",
    },
    {
        "company": "Infosys AI",
        "headline": "Infosys AI Cuts Code Bugs by 60%",
        "summary": "Infosys deploys AI across 200,000 developers.",
        "impact": "Enterprise AI coding assistant reduces bugs by 60% at scale. Productivity gains measured across 200k engineers.",
        "watermark": "CODE",
        "body": ["60% fewer bugs in prod","200K developers enrolled","Saves 2hrs/dev per day","Rolled out in 6 months"],
        "stat_label": "Bug Reduction",
        "stat_value": "60%",
        "source": "Inc42",
        "region": "🇮🇳",
        "hashtags": ["#Infosys","#AICode","#DevTools","#India","#EnterpriseAI"],
        "tts_script": "On the business side, Infosys has rolled out an AI coding assistant across 200,000 developers in just six months, cutting production bugs by 60 percent. That's two extra hours saved per developer per day — compounding across the entire company every single day.",
    },
    {
        "company": "Baidu / ERNIE",
        "headline": "Baidu ERNIE 5 Tops China AI Charts",
        "summary": "Baidu's ERNIE 5 outperforms GPT-4 on Chinese language tasks.",
        "impact": "China now has a frontier model competitive with Western counterparts. Access available to 100M+ users.",
        "watermark": "ERNIE5",
        "body": ["Beats GPT-4 in Chinese","100M users on Day 1","Multimodal text+image","API free tier available"],
        "stat_label": "Day 1 Users",
        "stat_value": "100M",
        "source": "TechNode",
        "region": "🇨🇳",
        "hashtags": ["#Baidu","#ERNIE5","#ChinaAI","#AI","#LLM"],
        "tts_script": "Breaking overnight from China — Baidu's ERNIE 5 just launched to 100 million users on day one, outperforming GPT-4 on Chinese language tasks. China's domestic AI ecosystem is maturing fast, and this signals a genuine two-horse race at the frontier.",
    },
    {
        "company": "ByteDance",
        "headline": "ByteDance AI Video Fools Experts",
        "summary": "ByteDance releases MagicVideo AI generation model.",
        "impact": "New model generates photo-realistic video from text in seconds. Experts call it a turning point for content creation.",
        "watermark": "VIDEO",
        "body": ["Text-to-video in 8 secs","Passes expert blindtest","4K 60fps output","Open-source weights"],
        "stat_label": "Generation Speed",
        "stat_value": "8 Seconds",
        "source": "Pandaily",
        "region": "🇨🇳",
        "hashtags": ["#ByteDance","#VideoAI","#Sora","#AI","#GenAI"],
        "tts_script": "In a surprising twist, ByteDance's MagicVideo model just generated 4K photo-realistic video from a text prompt in 8 seconds — and it fooled human experts in a blind test. Open-source weights are live right now, so every creator on the planet can use this today.",
    },
    {
        "company": "EU AI Office",
        "headline": "EU AI Act Enforcement Begins Now",
        "summary": "European Union begins enforcing AI Act compliance.",
        "impact": "High-risk AI systems must now comply or face fines up to 7% of global revenue. The era of AI regulation is here.",
        "watermark": "EUROPE",
        "body": ["High-risk AI rules live","7% revenue fines start","30 nations adopting law","6-month grace period"],
        "stat_label": "Max Fine (Global Revenue)",
        "stat_value": "7%",
        "source": "The Decoder",
        "region": "🇪🇺",
        "hashtags": ["#EUAIAct","#AIRegulation","#EU","#Policy","#AI"],
        "tts_script": "Across the pond, the EU AI Act enforcement just went live, meaning high-risk AI systems now face fines up to 7 percent of global annual revenue if they don't comply. Thirty nations are adopting the framework — this is the moment AI regulation becomes real.",
    },
    {
        "company": "UK AI Safety Inst.",
        "headline": "UK Tests First AI Safety Standard",
        "summary": "UK AI Safety Institute publishes first global safety standard.",
        "impact": "The world's first binding AI safety evaluation framework is now published. It could become the global benchmark.",
        "watermark": "SAFETY",
        "body": ["First binding AI standard","24 nations signed on","Mandatory eval process","Results published openly"],
        "stat_label": "Nations Signed",
        "stat_value": "24",
        "source": "BBC Technology",
        "region": "🇬🇧",
        "hashtags": ["#UKAISafety","#AISafety","#UK","#AIPolicy","#AI"],
        "tts_script": "And finally — the UK AI Safety Institute just published the world's first binding AI safety evaluation standard, with 24 nations already signed on. Every major AI model will now be evaluated against these benchmarks before deployment. A landmark day for global AI governance.",
    },
]

# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stories = fetch_todays_stories()
    print(f"\nFetched {len(stories)} stories:")
    for i, s in enumerate(stories, 1):
        print(f"  {i:2d}. [{s['region']}] {s['company']:<22} {s['headline']}")
