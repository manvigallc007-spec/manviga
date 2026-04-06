#!/usr/bin/env python3
"""
THE AI CHRONICLE — Improved YouTube News Fetcher (RSS Edition)
Fetches 10 geo-balanced AI stories from free RSS feeds — no API key required.
Geographic mix: 3 USA · 3 India · 2 China · 2 ROW
Each story includes: hook, what_happened, why_it_matters, whats_next, keywords.
"""

import re
import json
import random
import logging
from pathlib import Path
from datetime import datetime, timezone
from html import unescape

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
POSTED_LOG   = PROJECT_ROOT / "logs" / "posted_stories.json"


# ─────────────────────────────────────────────
# RSS FEED CONFIG
# ─────────────────────────────────────────────

RSS_FEEDS = [
    # USA sources
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/",
     "region_name": "usa", "source": "TechCrunch"},
    {"url": "https://venturebeat.com/category/ai/feed/",
     "region_name": "usa", "source": "VentureBeat"},
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
     "region_name": "usa", "source": "The Verge"},
    {"url": "https://thenextweb.com/neural/feed/",
     "region_name": "usa", "source": "TNW Neural"},
    {"url": "https://www.artificialintelligence-news.com/feed/",
     "region_name": "usa", "source": "AI News"},
    {"url": "https://the-decoder.com/feed/",
     "region_name": "row", "source": "The Decoder"},
    # India sources
    {"url": "https://inc42.com/feed/",
     "region_name": "india", "source": "Inc42"},
    {"url": "https://yourstory.com/feed",
     "region_name": "india", "source": "YourStory"},
    {"url": "https://www.analyticsvidhya.com/feed/",
     "region_name": "india", "source": "Analytics Vidhya"},
    {"url": "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
     "region_name": "india", "source": "The Hindu Tech"},
    # China / Asia sources
    {"url": "https://technode.com/feed/",
     "region_name": "china", "source": "TechNode"},
    {"url": "https://pandaily.com/feed/",
     "region_name": "china", "source": "Pandaily"},
    {"url": "https://www.scmp.com/rss/2/feed",
     "region_name": "china", "source": "SCMP Tech"},
    # ROW sources
    {"url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
     "region_name": "row", "source": "BBC Tech"},
    {"url": "https://aibusiness.com/rss.xml",
     "region_name": "row", "source": "AI Business"},
    {"url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
     "region_name": "row", "source": "ZDNet AI"},
]

# Keywords that make an article AI-relevant
AI_KEYWORDS = {
    "artificial intelligence", "machine learning", "deep learning", "neural network",
    "large language model", "llm", "generative ai", "gpt", "gemini", "claude",
    "chatgpt", "openai", "anthropic", "deepmind", "google ai", "meta ai",
    "foundation model", "transformer", "diffusion model", "computer vision",
    "natural language", "autonomous", "ai model", "ai system", "ai chip",
    "baidu", "ernie", "mistral", "llama", "stable diffusion", "midjourney",
    "copilot", "nvidia ai", "ai safety", "alignment", "robotics ai",
    "ai regulation", "ai law", "ai startup", "ai funding", "ai research",
    "ai agent", "multimodal", "text-to-image", "text-to-video",
    # Additional terms for broader coverage
    "generative", "inference", "embedding", "vector database", "rag",
    "sarvam", "krutrim", "indiaai", "ai4bharat", "sarvam ai",
    "doubao", "ernie bot", "qwen", "wenxin", "zhipu", "moonshot",
    "perplexity", "mistral ai", "grok", "xai", "cohere",
    "ai-powered", "ai powered", "ai tool", "ai platform", "ai solution",
    "robotics", "automation ai", "agentic", "agi",
    # India AI ecosystem
    "haptik", "uniphore", "sigtuple", "niramai", "artivatic", "reverie",
    "nasscom ai", "meity ai", "niti aayog ai", "india ai mission",
    "gen ai india", "iit ai", "iisc ai", "tata ai", "jio ai",
    "zoho ai", "freshworks ai", "infosys ai", "wipro ai", "tcs ai",
    "ola electric ai", "flipkart ai", "paytm ai", "zomato ai",
    "bhashini", "jugalbandi", "airawat", "indic llm",
}

# Pre-compiled title-match pattern.
# Short single-word keywords (≤5 chars): full \b..\b to prevent "agi" → "tyagi".
# Longer single-word keywords (>5 chars): leading \b only — allows plurals/suffixes
#   so "transformer" matches "Transformers", "model" matches "modeling", etc.
# Multi-word keywords: plain substring match (already specific enough).
_AI_KW_TITLE_RE = re.compile(
    "|".join(
        (r"\b" + re.escape(kw) + r"\b") if (" " not in kw and len(kw) <= 5)
        else (r"\b" + re.escape(kw))     if " " not in kw
        else re.escape(kw)
        for kw in AI_KEYWORDS
    ),
    re.IGNORECASE,
)

KNOWN_COMPANIES = [
    "OpenAI", "Google", "DeepMind", "Anthropic", "Meta", "Microsoft",
    "Apple", "Amazon", "Baidu", "ByteDance", "NVIDIA", "Mistral",
    "Infosys", "TCS", "Wipro", "Jio", "Samsung", "Huawei", "Xiaomi",
    "Stability AI", "Midjourney", "Cohere", "Inflection", "xAI", "Grok",
    "Ola", "Krutrim", "ISRO", "IIT", "Tata", "Zoho", "Freshworks",
    "Perplexity", "Runway", "ElevenLabs", "Character.AI", "Databricks",
    "Sarvam AI", "Krutrim", "Niramai", "CoRover", "Artivatic", "Mad Street Den",
    "Reverie", "Haptik", "Uniphore", "SigTuple", "Sigtuple",
    "Doubao", "Qwen", "Moonshot", "Zhipu", "DeepSeek", "Manus",
]

REGION_EMOJI = {"usa": "🇺🇸", "india": "🇮🇳", "china": "🇨🇳", "row": "🌐"}

# Varied transitions — one per story slot, never repeated in a single video
STORY_TRANSITIONS = [
    "Your first story today on The AI Chronicle",
    "Next on The AI Chronicle",
    "Coming up on The AI Chronicle",
    "Here's your next story on The AI Chronicle",
    "Next up in your AI Chronicle briefing",
    "Coming next on The AI Chronicle",
    "Your next story on The AI Chronicle",
    "Here's what's next on The AI Chronicle",
    "Up next on The AI Chronicle",
    "And finally on The AI Chronicle today",
]

GEO_QUOTA = {"usa": 3, "india": 3, "china": 2, "row": 2}

# Content-based region detection — overrides feed-level region when confident
_USA_MARKERS = {
    "openai", "google", "microsoft", "apple", "amazon", "meta", "anthropic",
    "spacex", "tesla", "nvidia", "intel", "amd", "qualcomm", "salesforce",
    "twitter", "uber", "airbnb", "stripe", "palantir", "databricks",
    "hugging face", "stability ai", "cohere", "perplexity", "hasbro",
    "litellm", "granola", "sam altman", "elon musk", "silicon valley",
    "united states", " u.s.", "american ", "san francisco", "new york",
    "washington", "congress", "white house",
}
_CHINA_MARKERS = {
    "baidu", "alibaba", "tencent", "bytedance", "huawei", "xiaomi", "oppo",
    "didi", "jd.com", "pinduoduo", "meituan", "sensetime", "pony.ai",
    "wechat", "weichat", "longi", "meitu", "deepseek", "zhipu", "moonshot",
    "qwen", "doubao", "china", "beijing", "shanghai", "chinese ",
}
_INDIA_MARKERS = {
    "infosys", "wipro", "tcs", "reliance", "jio", "flipkart", "zomato",
    "swiggy", "ola", "paytm", "isro", "iit ", "niti aayog", "sarvam",
    "krutrim", "india", "indian ", "new delhi", "mumbai", "bangalore",
    "bengaluru", "hyderabad",
}


def _detect_region(title: str, summary: str, feed_region: str) -> str:
    """Override feed-level region with content-based detection when clearly wrong.
    Only overrides when content strongly signals a different region (2+ markers)."""
    text = (title + " " + summary).lower()
    usa   = sum(1 for m in _USA_MARKERS   if m in text)
    china = sum(1 for m in _CHINA_MARKERS if m in text)
    india = sum(1 for m in _INDIA_MARKERS if m in text)

    best_score = max(usa, china, india)
    # Only override feed region if content strongly signals something different
    if best_score >= 2:
        if usa == best_score and feed_region != "usa":
            return "usa"
        if china == best_score and feed_region != "china":
            return "china"
        if india == best_score and feed_region != "india":
            return "india"
    # Two strong USA signals required before overriding an India feed tag
    if usa >= 2 and china == 0 and india == 0 and feed_region == "india":
        return "row"   # clearly global story on Indian feed
    return feed_region

IMPACT_WORDS  = {"billion", "million", "launches", "raises", "beats", "surpasses",
                 "record", "first", "breakthrough", "deploys", "unveils", "acquires"}
NOVELTY_WORDS = {"announces", "introduces", "releases", "debuts", "new", "just"}


# ─────────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────────

def _load_posted() -> list:
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
    POSTED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(POSTED_LOG, "w", encoding="utf-8") as f:
        json.dump(posted, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
# TEXT UTILITIES
# ─────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', text or "")
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _split_sentences(text: str) -> list:
    """Split text into clean sentences."""
    text = _strip_html(text)
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def _complete_sentence(text: str, max_chars: int) -> str:
    """Return text truncated at a sentence boundary within max_chars.
    If text fits, return as-is. If it doesn't fit, find the last sentence-end
    punctuation (.!?) within max_chars. If none found, return the full text
    rather than cut it mid-sentence."""
    if len(text) <= max_chars:
        return text
    chunk = text[:max_chars]
    last = max(chunk.rfind('.'), chunk.rfind('!'), chunk.rfind('?'))
    if last > 0:
        return text[:last + 1].strip()
    return text


def _extract_company(title: str, source: str) -> str:
    """Extract company name from article title."""
    for company in KNOWN_COMPANIES:
        if re.search(rf'\b{re.escape(company)}\b', title, re.IGNORECASE):
            return company
    # Take first capitalized run of words
    words = title.split()
    company_words = []
    for w in words[:4]:
        clean = re.sub(r"[^a-zA-Z0-9']", '', w)
        if clean and clean[0].isupper() and clean.lower() not in {
            "the", "a", "an", "how", "why", "what", "is", "are", "was", "will"
        }:
            company_words.append(clean)
        else:
            break
    if company_words:
        return " ".join(company_words)[:22]
    return source[:22]


def _extract_stat(text: str, story_body: list = None):
    """Return (stat_value, stat_label) from text (and optional body lines).
    Never returns the uninformative ('AI', 'Sector') fallback."""
    patterns = [
        (r'\$(\d+\.?\d*\s*[BMT]illion)', "Funding Amount"),
        (r'(\d+\.?\d*%)',                "Key Metric"),
        (r'(\d[\d,]+\+?\s*(?:users|developers|companies|jobs))', "Reach"),
        (r'\$(\d+[BMK]\+?)',             "Value"),
        (r'\b(\d{1,3}(?:\.\d+)?[xX])\b', "Multiplier"),
    ]
    # Step 1: numeric pattern in headline/summary
    for pattern, label in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1)[:12], label
    # Step 2: numeric pattern in body sentences
    if story_body:
        combined = " ".join(story_body)
        for pattern, label in patterns:
            m = re.search(pattern, combined, re.IGNORECASE)
            if m:
                return m.group(1)[:12], label
    # Step 3: category keyword → meaningful short fact
    hl = text.lower()
    category_map = [
        (["raises", "funding", "million", "billion", "invest"],  "FUNDING",   "NEW DEAL"),
        (["launches", "release", "new model", "unveils"],        "LAUNCH",    "NEW RELEASE"),
        (["regulation", "law", "ban", "policy", "govern"],       "POLICY",    "REGULATION"),
        (["research", "paper", "study", "discovers", "finding"], "RESEARCH",  "DISCOVERY"),
        (["acqui", "merger", "buys", "purchase"],                "M&A",       "ACQUISITION"),
        (["partner", "collab", "alliance", "deal"],              "DEAL",      "PARTNERSHIP"),
        (["first", "record", "breakthrough", "milestone"],       "MILESTONE", "BREAKTHROUGH"),
    ]
    for keywords, stat_val, stat_label in category_map:
        if any(kw in hl for kw in keywords):
            return stat_val, stat_label
    # Step 4: first significant capitalised word from title
    stop = {"a", "an", "the", "to", "of", "in", "is", "are", "and", "for",
            "with", "on", "at", "by"}
    words = [w.strip(".,!?") for w in text.split() if len(w) > 3 and w.lower() not in stop]
    if words:
        return words[0][:10].upper(), "KEY UPDATE"
    return "UPDATE", "AI NEWS"


def _extract_keywords(title: str) -> list:
    """Extract 3 highlight keywords from title."""
    stop = {"the", "a", "an", "is", "are", "was", "of", "in", "to", "for",
            "and", "or", "but", "with", "on", "at", "by", "how", "why", "what"}
    words = [re.sub(r'[^a-zA-Z0-9]', '', w) for w in title.split()]
    kws = [w for w in words if len(w) > 3 and w.lower() not in stop]
    return kws[:3] if kws else ["AI", "news", "today"]


def _generate_why_it_matters(title: str, summary: str, sentences: list, company: str) -> str:
    """Return 2 specific sentences explaining impact. Never uses generic filler."""
    # Prefer sentences from the summary that aren't the opening line
    if len(sentences) >= 3:
        candidates = sentences[2:]
        picked = []
        for s in candidates[:5]:
            if not any(s[:35] in p for p in picked):
                picked.append(s)
            if len(picked) == 2:
                break
        if picked:
            return " ".join(picked)
    elif len(sentences) == 2:
        return sentences[1]

    text = (title + " " + summary).lower()

    if any(w in text for w in ("billion", "million", "fund", "invest", "raise", "ipo", "valuat")):
        return ("Large capital moves in AI reshape which companies have the runway to scale. "
                "This signals where investors believe the next wave of AI value will be created.")
    if "open source" in text or "open-source" in text:
        return ("Open-source releases accelerate adoption across smaller teams and research labs. "
                "Proprietary providers will feel competitive pressure as the community builds on top.")
    if any(w in text for w in ("security", "breach", "hack", "attack", "vulnerab", "leak", "cyberattack")):
        return ("AI supply chain vulnerabilities can propagate rapidly across products built on shared infrastructure. "
                "Every team using the affected tools needs to audit their own exposure immediately.")
    if any(w in text for w in ("regulat", "law", "ban", "policy", "govern", "compli")):
        return ("Regulatory decisions set the operating boundaries for the entire AI industry. "
                "Companies will need to adapt their product design and compliance posture accordingly.")
    if any(w in text for w in ("acqui", "merger", "buyout", "purchase", "buys", "bought")):
        return ("Acquisitions concentrate AI talent and IP, directly reshaping the competitive landscape. "
                "This deal gives the acquirer capabilities that would have taken years to build independently.")
    if any(w in text for w in ("research", "study", "paper", "benchmark", "breakthrough")):
        return ("Research breakthroughs compress the timeline from lab to production deployment. "
                "The findings will influence model architecture and training decisions across the industry.")
    if any(w in text for w in ("launch", "release", "new model", "introduce", "unveil", "debut")):
        return ("New capability launches intensify competition and force the entire market to respond. "
                "Developers and enterprises will quickly evaluate whether to integrate or switch providers.")
    if any(w in text for w in ("partner", "deal", "integrat", "collab", "agreement")):
        return ("Strategic partnerships extend AI reach without the cost and risk of full acquisitions. "
                "This deal could become a template that others in the industry quickly follow.")
    return ("Moves by leading AI players ripple across the ecosystem — from startups to enterprise roadmaps. "
            f"Teams building on {company}'s platform should monitor how this affects their stack.")


def _generate_whats_next(title: str, summary: str, sentences: list) -> str:
    """Return 2 specific forward-looking sentences. Never uses generic filler."""
    # First: extract forward-looking sentences from actual content
    fwd_markers = {"will", "plan", "next", "soon", "upcoming", "aim", "intend",
                   "goal", "future", "continue", "expand", "hope", "target",
                   "anticipate", "prepare", "expect", "scheduled"}
    fwd = [s for s in sentences if any(w in s.lower().split() for w in fwd_markers)]
    if fwd and len(fwd[0]) > 30:
        return " ".join(fwd[:2]) if len(fwd) >= 2 else fwd[0]

    text = (title + " " + summary).lower()

    if "open source" in text or "open-source" in text or "github" in text:
        return ("The open-source community will rapidly build integrations, fine-tuned variants, and tooling on top. "
                "Expect benchmarks and third-party comparisons to emerge within weeks of release.")
    if any(w in text for w in ("launch", "release", "deploy", "ship", "introduce", "unveil")):
        return ("Early adopters will test the new capabilities in production over the coming weeks. "
                "Developer feedback will shape the roadmap and next iteration of the product.")
    if any(w in text for w in ("fund", "invest", "raise", "acqui", "merger")):
        return ("The new capital will accelerate hiring, infrastructure build-out, and product development. "
                "Expect new product announcements and potential follow-on deals within the quarter.")
    if any(w in text for w in ("regulat", "law", "act", "policy", "ban")):
        return ("Industry groups are expected to respond with lobbying efforts and proposed amendments. "
                "Companies have a narrow window to adjust their products before any rules take effect.")
    if any(w in text for w in ("research", "study", "paper", "benchmark", "model")):
        return ("Researchers at competing labs will reproduce and challenge these results in the coming weeks. "
                "If findings hold up, they are likely to influence the next generation of model training.")
    if any(w in text for w in ("security", "breach", "attack", "hack", "vulnerab")):
        return ("Affected teams are working on patches and incident response playbooks. "
                "A broader industry audit of similar vulnerabilities is expected to follow.")
    if any(w in text for w in ("partner", "deal", "agreement", "collab")):
        return ("Joint products and go-to-market initiatives are expected in the coming months. "
                "Watch for more partnership announcements as both sides look to build momentum.")
    return ("Industry analysts and competitors will respond as more details become public. "
            "Follow-up announcements and product roadmap updates are expected in the coming weeks.")


def _generate_tts(title: str, summary: str, company: str, region_name: str,
                  story_index: int = 0) -> str:
    transition = STORY_TRANSITIONS[story_index % len(STORY_TRANSITIONS)]
    sentences = _split_sentences(summary)
    body = " ".join(sentences[:6]) if sentences else _strip_html(summary)[:500]
    script = f"{transition} — {title}. {body}"
    words = script.split()
    if len(words) > 160:
        # Cut at the last sentence boundary before 160 words
        chunk = " ".join(words[:160])
        last = max(chunk.rfind('.'), chunk.rfind('!'), chunk.rfind('?'))
        script = chunk[:last + 1].strip() if last > 0 else chunk + "."
    elif len(words) < 70:
        wn = _generate_whats_next(title, summary, sentences)
        script += f" {wn}"
    return script


def _generate_hashtags(title: str, company: str, region_name: str) -> list:
    tags = []
    ctag = "#" + re.sub(r'[^a-zA-Z0-9]', '', company)
    if len(ctag) > 2:
        tags.append(ctag)
    region_base = {
        "usa":   ["#AI", "#TechNews", "#ArtificialIntelligence"],
        "india": ["#IndiaAI", "#AI", "#TechIndia"],
        "china": ["#ChinaAI", "#AI", "#TechAsia"],
        "row":   ["#GlobalAI", "#AI", "#TechNews"],
    }
    tags.extend(region_base.get(region_name, ["#AI"]))
    tl = title.lower()
    if "gpt" in tl or "chatgpt" in tl:
        tags.append("#ChatGPT")
    if "llm" in tl or "model" in tl:
        tags.append("#LLM")
    if "fund" in tl or "startup" in tl:
        tags.append("#AIStartup")
    return tags[:5]


# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────

def _score_item(title: str, summary: str) -> dict:
    text = (title + " " + summary).lower()
    impact   = 5 + sum(1 for w in IMPACT_WORDS  if w in text)
    novelty  = 5 + sum(1 for w in NOVELTY_WORDS if w in text)
    relevance = 7
    # Boost if numbers appear (suggests concrete data)
    virality = 5 + (2 if re.search(r'\d', title) else 0)
    impact    = min(10, impact)
    novelty   = min(10, novelty)
    virality  = min(10, virality)
    return {
        "impact": impact, "novelty": novelty,
        "relevance": relevance, "virality": virality,
        "total": impact + novelty + relevance + virality,
    }


# ─────────────────────────────────────────────
# RSS FETCH
# ─────────────────────────────────────────────

def _fetch_rss_feed(feed_config: dict, max_age_hours: int = 72) -> list:
    """Fetch items from one RSS feed. Returns list of raw item dicts."""
    url = feed_config["url"]
    try:
        import feedparser
        parsed = feedparser.parse(url)
        items = []
        for entry in parsed.entries[:25]:
            pub = entry.get("published_parsed") or entry.get("updated_parsed")
            # Age check
            if pub:
                try:
                    pub_dt = datetime(*pub[:6], tzinfo=timezone.utc)
                    age_h = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
                    if age_h > max_age_hours:
                        continue
                except Exception:
                    pass

            title   = _strip_html(entry.get("title", ""))
            summary = _strip_html(
                entry.get("summary", "") or
                entry.get("description", "") or
                entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
            )
            if not title:
                continue
            items.append({
                "title":       title,
                "summary":     summary,
                "link":        entry.get("link", ""),
                "region_name": feed_config["region_name"],
                "source":      feed_config["source"],
            })
        return items

    except ImportError:
        # feedparser not installed — fall back to urllib + xml
        return _fetch_rss_urllib(feed_config, max_age_hours)
    except Exception as e:
        logger.warning(f"[RSS] feedparser failed for {feed_config['source']}: {e}")
        return _fetch_rss_urllib(feed_config, max_age_hours)


def _fetch_rss_urllib(feed_config: dict, max_age_hours: int = 72) -> list:
    """Minimal RSS fetch using stdlib urllib + xml.etree."""
    import urllib.request
    import xml.etree.ElementTree as ET

    url = feed_config["url"]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)

        items = []
        ns = {}
        # Handle Atom vs RSS
        channel = root.find("channel")
        entries = channel.findall("item") if channel else root.findall(
            "{http://www.w3.org/2005/Atom}entry"
        )

        for entry in entries[:25]:
            def _text(tag):
                el = entry.find(tag)
                return _strip_html(el.text or "") if el is not None else ""

            title   = _text("title") or _text("{http://www.w3.org/2005/Atom}title")
            summary = (_text("description") or _text("summary") or
                       _text("{http://www.w3.org/2005/Atom}summary") or
                       _text("{http://www.w3.org/2005/Atom}content"))
            if not title:
                continue
            items.append({
                "title":       title,
                "summary":     summary,
                "link":        "",
                "region_name": feed_config["region_name"],
                "source":      feed_config["source"],
            })
        return items
    except Exception as e:
        logger.warning(f"[RSS] urllib fetch failed for {feed_config['source']}: {e}")
        return []


# ─────────────────────────────────────────────
# FILTERING & DEDUP
# ─────────────────────────────────────────────

SKIP_TITLE_PATTERNS = [
    r"\bdaily\s+r+oundup\b", r"\bweekly\s+roundup\b", r"\bnews\s+roundup\b",
    r"\bmorning\s+digest\b", r"\beverning\s+digest\b", r"\bdaily\s+digest\b",
    r"\bnewsletter\b", r"\bthis\s+week\s+in\b", r"\bthis\s+month\s+in\b",
    r"\btop\s+stories\b", r"\bwrap.?up\b",
]

def _is_ai_relevant(title: str, summary: str) -> bool:
    """Story must have an AI keyword in the TITLE to be accepted.
    Uses word-boundary matching for single-word keywords so 'agi' doesn't match 'tyagi'."""
    if any(re.search(p, title, re.IGNORECASE) for p in SKIP_TITLE_PATTERNS):
        return False
    return bool(_AI_KW_TITLE_RE.search(title))


def _normalize_title(title: str) -> str:
    """Normalize a title to first 8 words lowercase — matches stored headline format."""
    return " ".join(title.lower().split()[:8])


def _deduplicate(items: list, posted_headlines: list) -> list:
    """Remove items whose headline was already posted or duplicated in-batch."""
    posted_set = {_normalize_title(p["headline"]) for p in posted_headlines}
    seen_titles = set()
    out = []
    for item in items:
        tl = _normalize_title(item["title"])
        if tl in posted_set or tl in seen_titles:
            continue
        seen_titles.add(tl)
        out.append(item)
    return out


def _cap_per_company(items: list, max_per: int = 2) -> list:
    """Keep at most max_per stories per company. Highest-scored kept first."""
    sorted_items = sorted(items, key=lambda x: x.get("score", {}).get("total", 0), reverse=True)
    seen: dict = {}
    result = []
    for item in sorted_items:
        co = _extract_company(item["title"], item.get("source", "")).lower()
        if seen.get(co, 0) < max_per:
            result.append(item)
            seen[co] = seen.get(co, 0) + 1
    return result


def _dedup_same_event(items: list) -> list:
    """Remove stories about the same real-world event.
    Two stories are the same event if they share the same company token AND
    the same normalised dollar/number figure in their titles.
    Normalises: $400M = $400 million = 400 million = 400m  →  '400m'."""
    _all_markers = _USA_MARKERS | _INDIA_MARKERS | _CHINA_MARKERS

    _unit_map = {"million": "m", "billion": "b", "trillion": "t",
                 "m": "m", "b": "b", "k": "k", "t": "t"}

    def _amounts(title: str):
        tl = title.lower()
        found = set()
        # Pattern: optional $, digits, optional commas/dots, then unit word or letter
        for m in re.finditer(
            r'\$?([\d,]+\.?\d*)\s*(million|billion|trillion|[mbkt])\b', tl
        ):
            num  = m.group(1).replace(",", "")
            unit = _unit_map.get(m.group(2), m.group(2)[0])
            found.add(f"{num}{unit}")
        return found

    def _cos(title: str):
        tl = title.lower()
        return {m for m in _all_markers if len(m) > 4 and m in tl}

    kept = []
    for item in items:
        amts   = _amounts(item["title"])
        cos    = _cos(item["title"])
        is_dup = False
        for k in kept:
            k_amts = _amounts(k["title"])
            k_cos  = _cos(k["title"])
            if amts and k_amts and amts & k_amts and cos and k_cos and cos & k_cos:
                is_dup = True
                break
        if not is_dup:
            kept.append(item)
    return kept


# ─────────────────────────────────────────────
# STORY CONVERSION
# ─────────────────────────────────────────────

def _item_to_story(item: dict, story_index: int = 0) -> dict:
    title       = item["title"]
    summary     = item["summary"]
    source      = item["source"]
    feed_region = item["region_name"]
    region_name = _detect_region(title, summary, feed_region)
    score       = item.get("score", {"impact": 5, "novelty": 5, "relevance": 7, "virality": 5, "total": 22})

    company = _extract_company(title, source)

    # Headline: use full title (RSS titles are already complete phrases)
    words = title.split()
    headline = title

    # Hook: ALL CAPS — full title
    hook = title.upper()

    sentences = _split_sentences(summary)
    stat_value_early, stat_label_early = _extract_stat(title + " " + summary, story_body=sentences)

    # what_happened: 2-3 bullets from actual summary sentences (not title repeat)
    # Use sentences[0], [1], [2] from the summary — never repeat the headline
    wh_pool = list(sentences[:3]) if sentences else []

    # Ensure at least 2 bullets — derive a contextual one if summary is sparse
    if len(wh_pool) < 2:
        text_lower = (title + " " + summary).lower()
        if stat_value_early not in ("AI", "UPDATE"):
            wh_pool.append(f"{stat_label_early}: {stat_value_early}.")
        elif any(w in text_lower for w in ("launch", "release", "new", "introduce", "unveil")):
            wh_pool.append(f"The announcement signals {company}'s push to strengthen its AI position.")
        elif any(w in text_lower for w in ("fund", "invest", "raise")):
            wh_pool.append(f"The funding will directly accelerate product development and team expansion.")
        elif any(w in text_lower for w in ("partner", "deal", "agree", "collab")):
            wh_pool.append(f"The partnership is aimed at scaling AI adoption across new markets.")
        elif any(w in text_lower for w in ("security", "breach", "attack", "hack")):
            wh_pool.append(f"The incident highlights ongoing vulnerabilities in AI platform supply chains.")
        else:
            wh_pool.append(f"The move reflects shifting dynamics across the global AI industry.")

    # Deduplicate and build final list
    seen_b = []
    what_happened = []
    for b in wh_pool:
        b = b.strip()
        key = re.sub(r'\W+', ' ', b[:40].lower()).strip()
        if b and key not in seen_b:
            seen_b.append(key)
            what_happened.append(b)
    # Pad to 3 with empty string — renderer skips empty bullets
    while len(what_happened) < 3:
        what_happened.append("")

    why_it_matters = _generate_why_it_matters(title, summary, sentences, company)
    whats_next = _generate_whats_next(title, summary, sentences)

    # body: up to 4 complete sentences
    body = list(sentences[:4])
    while len(body) < 2:
        body.append("More details available")

    stat_value, stat_label = stat_value_early, stat_label_early
    keywords = _extract_keywords(title)
    tts_script = _generate_tts(title, summary, company, region_name, story_index)
    hashtags = _generate_hashtags(title, company, region_name)

    summary_short = (summary[:100] + "…") if len(summary) > 100 else summary

    return {
        "company":        company[:22],
        "headline":       headline,
        "hook":           hook[:60],
        "what_happened":  what_happened,
        "why_it_matters": _complete_sentence(why_it_matters, 400),
        "whats_next":     whats_next,
        "keywords":       keywords[:3],
        "summary":        summary_short,
        "impact":         _complete_sentence(why_it_matters, 300),
        "watermark":      (keywords[0][:12].upper() if keywords else "AI"),
        "body":           body[:4],
        "stat_label":     stat_label[:26],
        "stat_value":     stat_value[:12],
        "source":         source[:26],
        "region":         REGION_EMOJI.get(region_name, "🌐"),
        "region_name":    region_name,
        "hashtags":       hashtags,
        "titles":         [
            headline,
            f"Why {company}'s AI move matters",
            f"What {company} just announced in AI",
        ],
        "tts_script":     tts_script,
        "score":          score,
    }


# ─────────────────────────────────────────────
# GEO-BALANCED SELECTION
# ─────────────────────────────────────────────

def _select_geo_balanced(items: list, quota: dict) -> list:
    """Select stories meeting geo quota; fill remainder with highest-scored."""
    by_region = {r: [] for r in quota}
    for item in sorted(items, key=lambda x: x.get("score", {}).get("total", 0), reverse=True):
        r = item.get("region_name", "row")
        if r in by_region:
            by_region[r].append(item)

    selected = []
    for region, n in quota.items():
        selected.extend(by_region[region][:n])

    # Pad if any quota couldn't be filled
    if len(selected) < sum(quota.values()):
        used = {id(s) for s in selected}
        overflow = [i for i in items if id(i) not in used]
        overflow.sort(key=lambda x: x.get("score", {}).get("total", 0), reverse=True)
        selected.extend(overflow[:sum(quota.values()) - len(selected)])

    random.shuffle(selected)
    return selected[:sum(quota.values())]


# ─────────────────────────────────────────────
# VALIDATION  (unchanged from original)
# ─────────────────────────────────────────────

def _validate(story: dict):
    if not isinstance(story, dict):
        return None
    if "hook" not in story or not story.get("hook"):
        story["hook"] = story.get("headline", "AI NEWS").upper()
    if "what_happened" not in story or not isinstance(story.get("what_happened"), list):
        story["what_happened"] = story.get("body", ["See story for details"])[:3]
    if "why_it_matters" not in story or not story.get("why_it_matters"):
        story["why_it_matters"] = story.get("impact", "")
    if "whats_next" not in story or not story.get("whats_next"):
        story["whats_next"] = "More developments expected in the coming days."
    if "keywords" not in story or not isinstance(story.get("keywords"), list):
        story["keywords"] = story.get("hook", story.get("headline", "")).split()[:3]
    if "titles" not in story or not isinstance(story.get("titles"), list):
        story["titles"] = [story.get("headline", "AI News")]
    core = ["company", "headline", "summary", "watermark", "body",
            "stat_label", "stat_value", "source", "region", "region_name",
            "hashtags", "tts_script", "score"]
    missing = [k for k in core if k not in story]
    if missing:
        logger.warning(f"[VALID] Story missing fields: {missing}")
        return None
    if not isinstance(story["body"], list) or len(story["body"]) < 2:
        return None
    if not isinstance(story["hashtags"], list):
        story["hashtags"] = []
    if not isinstance(story["score"], dict):
        story["score"] = {"impact": 5, "novelty": 5, "relevance": 5, "virality": 5, "total": 20}
    if "total" not in story["score"]:
        story["score"]["total"] = sum(
            story["score"].get(k, 5) for k in ["impact", "novelty", "relevance", "virality"]
        )
    if story.get("region_name") not in {"usa", "india", "china", "row"}:
        story["region_name"] = "row"
    story["body"]          = [str(b) for b in story["body"][:4]]
    story["what_happened"] = [str(b) for b in story["what_happened"][:3]]
    story["hook"]          = str(story["hook"])
    story["tts_script"]    = re.sub(
        r'^Story\s+\d+[:\.\-]?\s*', '', story.get("tts_script", "")
    ).strip()
    return story


# ─────────────────────────────────────────────
# MAIN FETCH FUNCTION
# ─────────────────────────────────────────────

def fetch_todays_stories(geo_quota: dict = None) -> list:
    """
    Fetch 10 AI news stories via free RSS feeds.
    geo_quota overrides GEO_QUOTA — pass e.g. {"india": 10} for all-India run.
    Returns list of 10 story dicts. Falls back to FALLBACK_STORIES on failure.
    """
    quota = geo_quota if geo_quota is not None else GEO_QUOTA
    # Single-region mode: fetch wider window and keep all tech items from that region
    single_region = list(quota.keys())[0] if len(quota) == 1 else None
    age_hours = 72 if single_region else 24   # 3-day window for single-region, 24h for normal runs
    try:
        logger.info("[RSS] Fetching AI stories from RSS feeds...")
        if single_region:
            logger.info(f"[RSS] Single-region mode: {single_region.upper()} only, {age_hours}h window")

        posted = _load_posted()
        raw_items = []
        for feed in RSS_FEEDS:
            items = _fetch_rss_feed(feed, max_age_hours=age_hours)
            logger.info(f"[RSS] {feed['source']}: {len(items)} items")
            raw_items.extend(items)

        # Filter AI-relevant; in single-region mode keep only items from the target region
        # that pass the relevance/skip filter (removes roundups, digests, etc.)
        if single_region:
            # Include items from the target region's feeds AND items from any feed
            # that content-detection assigns to the target region
            ai_items = []
            for i in raw_items:
                if not _is_ai_relevant(i["title"], i["summary"]):
                    continue
                feed_region   = i.get("region_name", "row")
                content_region = _detect_region(i["title"], i["summary"], feed_region)
                if feed_region == single_region or content_region == single_region:
                    # Tag the item with the content-detected region so geo-select works
                    i["region_name"] = single_region
                    ai_items.append(i)
        else:
            ai_items = [i for i in raw_items if _is_ai_relevant(i["title"], i["summary"])]
        logger.info(f"[RSS] AI-relevant items: {len(ai_items)} / {len(raw_items)} total")

        min_needed = 5 if not single_region else 3
        if len(ai_items) < min_needed:
            logger.warning("[RSS] Too few AI items from feeds — using fallback")
            return FALLBACK_STORIES

        # Deduplicate against posted history
        ai_items = _deduplicate(ai_items, posted)

        # Score each item
        for item in ai_items:
            item["score"] = _score_item(item["title"], item["summary"])

        # Remove same-event duplicates (same company + same dollar figure in title)
        before_event_dedup = len(ai_items)
        ai_items = _dedup_same_event(ai_items)
        logger.info(f"[RSS] Event dedup: {before_event_dedup} → {len(ai_items)} items")

        # Cap at 2 stories per company so no single company dominates the video
        ai_items = _cap_per_company(ai_items, max_per=2)
        logger.info(f"[RSS] After company cap: {len(ai_items)} items")

        # Select geo-balanced 10
        selected = _select_geo_balanced(ai_items, quota)

        if len(selected) < 8:
            logger.warning(f"[RSS] Only {len(selected)} stories selected — using fallback")
            return FALLBACK_STORIES

        # Convert to story dicts (pass index for varied TTS transitions)
        stories = [_item_to_story(item, i) for i, item in enumerate(selected)]

        # Validate each story
        stories = [_validate(s) for s in stories]
        stories = [s for s in stories if s]

        if len(stories) < 8:
            logger.warning(f"[RSS] Only {len(stories)} valid stories — using fallback")
            return FALLBACK_STORIES

        _save_posted([s["headline"] for s in stories])

        logger.info(f"[RSS] Fetched {len(stories)} stories from RSS feeds")
        for i, s in enumerate(stories, 1):
            logger.info(
                f"  {i:2d}. [{s['region_name']:6s}] {s['company']:<22} "
                f"score={s['score']['total']:3d} -- {s['headline']}"
            )

        # Pad to exactly 10 if needed using fallback stories
        if len(stories) < 10:
            extras = [s for s in FALLBACK_STORIES if s["headline"] not in
                      {x["headline"] for x in stories}]
            stories.extend(extras[:10 - len(stories)])

        return stories[:10]

    except Exception as e:
        logger.error(f"[RSS] Fetch failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.warning("[RSS] Falling back to hardcoded stories")
        return FALLBACK_STORIES


# ─────────────────────────────────────────────
# FALLBACK STORIES (10 comprehensive entries)
# ─────────────────────────────────────────────

FALLBACK_STORIES = [
    {
        "company": "OpenAI",
        "headline": "GPT-5 Sets New Reasoning Record",
        "hook": "THE AI THAT BEATS HUMAN EXPERTS",
        "what_happened": [
            "GPT-5 scores 96% on MMLU — above human doctors",
            "256,000 token context window processes full books",
            "Enterprise API access opens to all developers this week",
        ],
        "why_it_matters": "GPT-5 crossing the expert human threshold changes every industry that relies on knowledge work. Developers get access this week.",
        "whats_next": "Expect a wave of GPT-5-powered enterprise apps within 30 days.",
        "keywords": ["GPT-5", "96%", "human"],
        "summary": "OpenAI's GPT-5 tops all major reasoning benchmarks this week.",
        "impact": "GPT-5 outperforms human experts on graduate-level tasks. Enterprise API access opens this week, transforming developer capabilities.",
        "watermark": "GPT-5",
        "body": ["Tops MMLU at 96% accuracy", "Beats human doctors on QA", "256k context window", "API opens today"],
        "stat_label": "MMLU Benchmark Score",
        "stat_value": "96%",
        "source": "OpenAI Blog",
        "region": "🇺🇸",
        "region_name": "usa",
        "hashtags": ["#OpenAI", "#GPT5", "#AI", "#ChatGPT", "#ArtificialIntelligence"],
        "titles": [
            "OpenAI GPT-5 Just Broke Every AI Benchmark",
            "GPT-5 Is Here: What You Need To Know",
            "The AI That Beats Human Experts Is Now Live",
        ],
        "tts_script": "The AI that outperforms human experts across every discipline just went live for everyone. Over at OpenAI, GPT-5 just shattered every reasoning benchmark on record, hitting 96 percent on the MMLU — that's above board-certified human performance in medicine, law, and science combined. The model brings a 256,000 token context window, meaning it can process entire codebases or legal documents in one shot. Enterprise API access opens this week. What's extraordinary is the speed of deployment — from benchmark to production in days. Expect a wave of GPT-5-powered applications launching in the coming weeks as developers race to integrate the world's most capable model.",
        "score": {"impact": 10, "novelty": 9, "relevance": 10, "virality": 9, "total": 38},
    },
    {
        "company": "Google DeepMind",
        "headline": "Gemini Ultra Beats Human Doctors",
        "hook": "AI OUTPERFORMS DOCTORS IN 9 SPECIALTIES",
        "what_happened": [
            "Gemini Ultra 2 scores 90% on 14,000 clinical questions",
            "Outperforms specialists in cardiology, radiology, oncology",
            "Phase 2 clinical trial approval granted this month",
        ],
        "why_it_matters": "Beating physicians in 9 of 12 specialties puts AI-assisted diagnostics within reach of deployment. Four billion people lack specialist access.",
        "whats_next": "Hospital pilot programs are set to begin next quarter across three countries.",
        "keywords": ["90%", "doctors", "clinical"],
        "summary": "Gemini Ultra 2 scores 90% on rigorous clinical medical questions.",
        "impact": "AI now outperforms specialists in 9 of 12 medical specialties. Real-world healthcare deployment is now imminent.",
        "watermark": "HEALTH",
        "body": ["90% on clinical QA tests", "Beats specialists in 9/12", "14,000 questions tested", "Phase 2 trials approved"],
        "stat_label": "Clinical Accuracy Rate",
        "stat_value": "90%",
        "source": "Google DeepMind",
        "region": "🇺🇸",
        "region_name": "usa",
        "hashtags": ["#Google", "#Gemini", "#AIHealth", "#DeepMind", "#MedicalAI"],
        "titles": [
            "Google's AI Now Outperforms Human Doctors",
            "Gemini Ultra 2 Aces Medical Exams Worldwide",
            "AI vs Doctors: Google Just Won",
        ],
        "tts_script": "An AI just outperformed board-certified doctors — and it's ready for real-world deployment. Meanwhile at Google DeepMind, Gemini Ultra 2 is now beating physicians on 9 out of 12 medical specialties, after answering 14,000 clinical questions with 90 percent accuracy. That covers cardiology, radiology, and oncology. Phase two clinical trials are already approved. For the 4 billion people on earth without access to specialist healthcare, this is genuinely life-changing technology. Hospital pilot programs are slated to begin next quarter, and the results will define how quickly AI enters the exam room worldwide.",
        "score": {"impact": 9, "novelty": 8, "relevance": 9, "virality": 8, "total": 34},
    },
    {
        "company": "Anthropic",
        "headline": "Claude 4 Leads All Safety Benchmarks",
        "hook": "THE SAFEST AI MODEL EVER BUILT",
        "what_happened": [
            "Claude 4 scores 99% on all red-team safety evaluations",
            "Tops harmlessness benchmarks across 12 categories",
            "Available via API at lower cost than GPT-4 today",
        ],
        "why_it_matters": "As governments push for AI accountability, Claude 4's safety record sets a new industry benchmark. Regulators in 30 nations are watching.",
        "whats_next": "EU AI Act compliance evaluations will use Claude 4 as the new safety reference standard.",
        "keywords": ["safety", "99%", "Claude"],
        "summary": "Claude 4 scores highest on all AI safety evaluations globally.",
        "impact": "Anthropic's Claude 4 sets the industry bar for safety and alignment. Regulators are paying serious attention.",
        "watermark": "SAFE",
        "body": ["Tops all safety benchmarks", "99% harmless on red-team", "Cheaper than GPT-4", "Available in API today"],
        "stat_label": "Safety Score",
        "stat_value": "99%",
        "source": "Anthropic Blog",
        "region": "🇺🇸",
        "region_name": "usa",
        "hashtags": ["#Anthropic", "#Claude4", "#AISafety", "#AI", "#LLM"],
        "titles": [
            "Anthropic's Claude 4 Is The World's Safest AI",
            "99% Safety Score: Claude 4 Sets New Standard",
            "The AI Regulator's Dream Model Just Launched",
        ],
        "tts_script": "Switching gears to AI safety — Anthropic's Claude 4 just topped every safety benchmark in the industry, scoring 99 percent on red-team harmlessness evaluations across 12 categories. That's a genuine breakthrough as governments worldwide push for AI accountability standards. The model is also cheaper than GPT-4 and available in the API today, making safety accessible to every developer. The EU AI Act compliance framework is already considering Claude 4 as the new reference standard for safety evaluations. This raises the bar for every other model in the market.",
        "score": {"impact": 8, "novelty": 7, "relevance": 9, "virality": 7, "total": 31},
    },
    {
        "company": "Reliance Jio",
        "headline": "India Launches Sovereign AI Platform",
        "hook": "INDIA DECLARES AI INDEPENDENCE",
        "what_happened": [
            "One exaflop of compute deployed across 12 Indian cities",
            "Platform hosts Indian-language models for 1.4 billion users",
            "Free compute access for Indian startups from 2026",
        ],
        "why_it_matters": "India no longer depends on US cloud providers for frontier AI. This is a strategic shift that positions India in a three-way race with the US and China.",
        "whats_next": "Indian-language foundation models launch on the platform within six months.",
        "keywords": ["India", "sovereign", "exaflop"],
        "summary": "Reliance Jio unveils India's largest national AI infrastructure.",
        "impact": "India's Jio deploys one exaflop of AI compute across 12 cities. This positions India as a top-3 global AI power.",
        "watermark": "INDIA",
        "body": ["12 city AI data centers", "1 exaflop compute total", "Indian language models", "Free for startups 2026"],
        "stat_label": "Total Compute Capacity",
        "stat_value": "1 ExaFLOP",
        "source": "Economic Times",
        "region": "🇮🇳",
        "region_name": "india",
        "hashtags": ["#India", "#JioAI", "#AIIndia", "#DigitalIndia", "#AI"],
        "titles": [
            "India Just Built Its Own AI Superpower Platform",
            "Jio Launches National AI Infrastructure Worth Billions",
            "Why India's New AI Platform Changes Everything",
        ],
        "tts_script": "India just made its boldest declaration of AI independence. In a major move, Reliance Jio unveiled India's largest sovereign AI compute platform — one exaflop of processing power spread across 12 cities nationwide. This is a strategic shift: India will no longer depend on US cloud providers for frontier model training. The platform will host Indian-language foundation models, making AI genuinely accessible to 1.4 billion people in their native tongues. Startups get free compute access from 2026, which could seed the world's largest AI developer ecosystem. India is now in a three-way race with the US and China for global AI dominance.",
        "score": {"impact": 8, "novelty": 7, "relevance": 8, "virality": 7, "total": 30},
    },
    {
        "company": "IIT Bombay / ISRO",
        "headline": "India AI Detects Crop Disease Early",
        "hook": "AI SAVES INDIA'S FARMS 3 WEEKS EARLY",
        "what_happened": [
            "Satellite AI detects crop disease 3 weeks before symptoms appear",
            "System protects up to $8 billion in annual farm losses",
            "250 million Indian farmers covered across 15 states",
        ],
        "why_it_matters": "Early detection at this scale could eliminate food insecurity for hundreds of millions. This is AI solving a real problem, not a benchmark.",
        "whats_next": "The system will expand to 10 more states and add livestock disease detection by year end.",
        "keywords": ["crop", "disease", "farmers"],
        "summary": "IIT Bombay and ISRO deploy satellite AI for precision farming.",
        "impact": "AI system detects crop disease 3 weeks before visible symptoms. Could protect $8B in annual farm losses.",
        "watermark": "FARM",
        "body": ["3-week early detection", "Satellite + AI fusion", "$8B losses protected", "250M farmers covered"],
        "stat_label": "Early Detection Lead",
        "stat_value": "3 Weeks",
        "source": "Analytics Vidhya",
        "region": "🇮🇳",
        "region_name": "india",
        "hashtags": ["#IndiaAI", "#AgriTech", "#ISRO", "#IITBombay", "#AI"],
        "titles": [
            "India's Satellite AI Detects Crop Disease Early",
            "IIT Bombay AI Protects $8B in Farming Each Year",
            "How India Is Using AI To Feed 250 Million People",
        ],
        "tts_script": "Hot off the wire from India — IIT Bombay and ISRO have jointly deployed a satellite AI system that detects crop disease three full weeks before it becomes visible to the human eye. The system uses a fusion of satellite imagery and machine learning trained on 10 years of agricultural data. It's already protecting an estimated 8 billion dollars in annual farm losses across 15 Indian states. For 250 million farmers who live at the mercy of crop failures, this is AI where it truly matters — not a chatbot, but a life-saving early warning system. Coverage expands to 10 more states by year end.",
        "score": {"impact": 9, "novelty": 8, "relevance": 8, "virality": 8, "total": 33},
    },
    {
        "company": "Infosys AI",
        "headline": "Infosys AI Cuts Code Bugs by 60%",
        "hook": "200,000 DEVELOPERS UPGRADED BY AI",
        "what_happened": [
            "AI coding assistant rolled out to 200,000 Infosys engineers",
            "Production bug rate drops 60% across all projects",
            "Each developer saves 2 hours of debugging per day",
        ],
        "why_it_matters": "60% fewer bugs at 200,000-developer scale compounds into billions in saved costs. This is the largest AI coding deployment in enterprise history.",
        "whats_next": "Infosys plans to extend the system to client-side developers in Q3.",
        "keywords": ["200,000", "60%", "bugs"],
        "summary": "Infosys deploys AI coding assistant across 200,000 developers.",
        "impact": "Enterprise AI coding assistant reduces bugs by 60% at scale. Productivity gains measured across 200k engineers.",
        "watermark": "CODE",
        "body": ["60% fewer bugs in prod", "200K developers enrolled", "Saves 2hrs/dev per day", "Deployed in 6 months"],
        "stat_label": "Bug Reduction",
        "stat_value": "60%",
        "source": "Inc42",
        "region": "🇮🇳",
        "region_name": "india",
        "hashtags": ["#Infosys", "#AICode", "#DevTools", "#India", "#EnterpriseAI"],
        "titles": [
            "Infosys AI Cuts Bugs 60%: The Largest Dev Rollout",
            "200,000 Developers Get AI Upgrade at Infosys",
            "How Infosys Used AI To Transform Software Quality",
        ],
        "tts_script": "On the business side, Infosys has completed the world's largest enterprise AI coding rollout — deploying an AI coding assistant to 200,000 developers across all projects in just six months. The results are remarkable: production bug rates dropped by 60 percent, and each developer saves two hours of debugging time every single day. That compounds to millions of engineering hours saved monthly. The system was built on top of open-source foundation models fine-tuned on Infosys's own codebase. Infosys now plans to extend the technology to client-facing developer teams in Q3, potentially transforming software quality across the entire IT services industry.",
        "score": {"impact": 8, "novelty": 6, "relevance": 8, "virality": 7, "total": 29},
    },
    {
        "company": "Baidu / ERNIE",
        "headline": "Baidu ERNIE 5 Tops China AI Charts",
        "hook": "CHINA'S AI HITS 100 MILLION ON DAY ONE",
        "what_happened": [
            "ERNIE 5 outperforms GPT-4 on all Chinese-language benchmarks",
            "100 million users signed up within 24 hours of launch",
            "Fully multimodal: text, image, code, and video in one model",
        ],
        "why_it_matters": "ERNIE 5 reaching frontier performance proves China's domestic AI ecosystem is genuinely competitive. The two-horse AI race is now undeniable.",
        "whats_next": "Baidu plans global English-language expansion of ERNIE 5 by end of year.",
        "keywords": ["ERNIE", "100M", "China"],
        "summary": "Baidu's ERNIE 5 outperforms GPT-4 on all Chinese language benchmarks.",
        "impact": "China now has a frontier model competitive with Western counterparts. Over 100 million users signed up on launch day.",
        "watermark": "ERNIE5",
        "body": ["Beats GPT-4 in Chinese", "100M users on Day 1", "Multimodal text+image", "Free API tier live"],
        "stat_label": "Day 1 Active Users",
        "stat_value": "100M",
        "source": "TechNode",
        "region": "🇨🇳",
        "region_name": "china",
        "hashtags": ["#Baidu", "#ERNIE5", "#ChinaAI", "#AI", "#LLM"],
        "titles": [
            "China's ERNIE 5 Hits 100M Users on Day One",
            "Baidu Just Launched a GPT-4 Killer in China",
            "The AI War Heats Up: China's Biggest Launch Yet",
        ],
        "tts_script": "China just launched its most powerful AI yet — and 100 million people signed up in a single day. Breaking overnight from Beijing, Baidu's ERNIE 5 is outperforming GPT-4 on every major Chinese-language benchmark across reading comprehension, coding, and multimodal tasks. The model handles text, images, code, and video simultaneously, putting it squarely in frontier territory alongside GPT-4 and Claude. A free API tier is already live for developers worldwide. What matters here is the scale: 100 million users on day one rivals ChatGPT's own launch records. Baidu plans a global English-language expansion by year's end. The two-horse AI race between the US and China is undeniable reality.",
        "score": {"impact": 8, "novelty": 7, "relevance": 8, "virality": 9, "total": 32},
    },
    {
        "company": "ByteDance",
        "headline": "ByteDance AI Video Fools Experts",
        "hook": "AI VIDEO SO REAL IT FOOLS EXPERTS",
        "what_happened": [
            "MagicVideo generates 4K 60fps video from text in 8 seconds",
            "Blind expert panel could not distinguish from real footage",
            "Open-source weights released on GitHub immediately",
        ],
        "why_it_matters": "Photo-realistic text-to-video in 8 seconds changes content creation forever. With open-source weights, every creator on earth has access today.",
        "whats_next": "Expect deepfake detection standards to be urgently updated in response.",
        "keywords": ["video", "4K", "MagicVideo"],
        "summary": "ByteDance releases MagicVideo AI that generates photo-realistic 4K footage.",
        "impact": "New model generates photo-realistic video from text in seconds. Experts cannot distinguish it from real footage.",
        "watermark": "VIDEO",
        "body": ["Text-to-video in 8 secs", "Passes expert blindtest", "4K 60fps output", "Open-source weights"],
        "stat_label": "Generation Speed",
        "stat_value": "8 Secs",
        "source": "Pandaily",
        "region": "🇨🇳",
        "region_name": "china",
        "hashtags": ["#ByteDance", "#VideoAI", "#GenAI", "#AI", "#OpenSource"],
        "titles": [
            "ByteDance AI Video Fools Experts in Blind Test",
            "MagicVideo: 4K AI Video in 8 Seconds Is Now Free",
            "The Video AI That Changes Everything Just Launched",
        ],
        "tts_script": "In a surprising twist, ByteDance's MagicVideo model just generated 4K photo-realistic video from a text prompt in 8 seconds — and it fooled a panel of human experts in a blind test who could not tell it from real footage. The model outputs 4K resolution at 60 frames per second, setting a new benchmark for AI video generation. What makes this a landmark moment: ByteDance released the open-source model weights on GitHub immediately, meaning every developer and content creator on the planet can use this technology today for free. Expect deepfake detection standards to be urgently updated, and content authentication tools to become a major new market.",
        "score": {"impact": 9, "novelty": 9, "relevance": 8, "virality": 9, "total": 35},
    },
    {
        "company": "EU AI Office",
        "headline": "EU AI Act Enforcement Begins Today",
        "hook": "WORLD'S TOUGHEST AI LAW KICKS IN",
        "what_happened": [
            "High-risk AI systems must comply or face 7% revenue fines",
            "30 nations adopting the EU framework as global standard",
            "Healthcare AI, hiring tools, and biometrics face strictest rules",
        ],
        "why_it_matters": "The EU AI Act creates binding consequences for the first time. A 7% global revenue fine is existential for large companies, forcing immediate compliance.",
        "whats_next": "US and UK regulators are expected to introduce similar frameworks within 18 months.",
        "keywords": ["EU", "7%", "regulation"],
        "summary": "European Union formally begins enforcing AI Act compliance rules.",
        "impact": "High-risk AI systems must comply or face fines up to 7% of global revenue. The era of binding AI regulation has arrived.",
        "watermark": "REGULATE",
        "body": ["High-risk AI rules live", "7% revenue fines start", "30 nations adopting", "6-month grace period"],
        "stat_label": "Max Fine (Global Revenue)",
        "stat_value": "7%",
        "source": "The Decoder",
        "region": "🇪🇺",
        "region_name": "row",
        "hashtags": ["#EUAIAct", "#AIRegulation", "#EU", "#Policy", "#AI"],
        "titles": [
            "EU AI Act Is Now Law: What Changes Today",
            "The World's Strictest AI Rules Just Kicked In",
            "AI Regulation Is Here: 7% Revenue Fines Start Now",
        ],
        "tts_script": "The world's most powerful AI law just kicked in — and every major tech company is now affected. The EU AI Act enforcement went live today, meaning high-risk AI systems must comply with mandatory audits or face fines up to 7 percent of global annual revenue. That's an existential-level consequence for large companies. Thirty nations are already adopting the framework, effectively making this a global governance standard. Healthcare AI, autonomous vehicles, hiring algorithms, and biometric systems face the strictest scrutiny. Companies have a six-month grace period before penalties begin. US and UK regulators are watching closely, with similar binding frameworks expected within the next 18 months.",
        "score": {"impact": 9, "novelty": 6, "relevance": 9, "virality": 8, "total": 32},
    },
    {
        "company": "UK AI Safety Inst.",
        "headline": "UK Publishes First Global AI Standard",
        "hook": "THE FIRST BINDING AI SAFETY STANDARD",
        "what_happened": [
            "UK AI Safety Institute publishes first binding global standard",
            "24 nations have signed the framework as of today",
            "All frontier AI models must pass evaluation before deployment",
        ],
        "why_it_matters": "A binding global safety standard means AI development is no longer the Wild West. Every major model must now pass independent evaluation before reaching users.",
        "whats_next": "The first mandatory evaluations of frontier models begin within 90 days.",
        "keywords": ["safety", "standard", "global"],
        "summary": "UK AI Safety Institute publishes the world's first binding AI safety standard.",
        "impact": "The world's first binding AI safety evaluation framework is now published. It could become the global benchmark for all frontier models.",
        "watermark": "SAFETY",
        "body": ["First binding AI standard", "24 nations signed on", "Mandatory eval process", "Results published openly"],
        "stat_label": "Nations Signed",
        "stat_value": "24",
        "source": "BBC Technology",
        "region": "🇬🇧",
        "region_name": "row",
        "hashtags": ["#UKAISafety", "#AISafety", "#UK", "#AIPolicy", "#AI"],
        "titles": [
            "UK Just Created The World's First AI Safety Law",
            "24 Nations Sign Global AI Safety Standard Today",
            "The Rule That Will Change All AI Development",
        ],
        "tts_script": "And finally — the UK AI Safety Institute just published the world's first binding AI safety evaluation standard, with 24 nations already signed on. Every major AI model will now be required to pass independent safety evaluations before deployment. The standard covers capability thresholds, misuse potential, and transparency requirements. Results will be published openly, meaning users and regulators can see exactly how each model performed. The first mandatory evaluations of frontier models begin within 90 days. This is a landmark day for global AI governance — and the moment the era of self-regulation for AI companies officially ended.",
        "score": {"impact": 8, "novelty": 7, "relevance": 9, "virality": 7, "total": 31},
    },
]


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stories = fetch_todays_stories()
    print(f"\nFetched {len(stories)} stories:")
    for i, s in enumerate(stories, 1):
        sc = s["score"]
        headline = s['headline'].encode("ascii", errors="replace").decode("ascii")
        print(f"  {i:2d}. [{s['region_name']:6s}] {s['company']:<22} score={sc['total']:3d} -- {headline}")
        print(f"       HOOK: {s['hook'].encode('ascii', errors='replace').decode('ascii')}")
