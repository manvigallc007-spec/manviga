#!/usr/bin/env python3
"""
THE AI CHRONICLE — Instagram News Fetcher (RSS Edition)
Fetches 10 geo-balanced AI stories once daily.
Geographic mix: 3 USA · 3 India · 2 China · 2 ROW
No API key required.
"""

import re
import json
import random
import logging
from html import unescape
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
POSTED_LOG   = PROJECT_ROOT / "logs" / "posted_stories.json"

# ─────────────────────────────────────────────
# GEO-BALANCED RSS FEEDS
# ─────────────────────────────────────────────

RSS_FEEDS = [
    # USA
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/",
     "source": "TechCrunch",        "region_name": "usa"},
    {"url": "https://venturebeat.com/category/ai/feed/",
     "source": "VentureBeat",       "region_name": "usa"},
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
     "source": "The Verge",         "region_name": "usa"},
    {"url": "https://the-decoder.com/feed/",
     "source": "The Decoder",       "region_name": "usa"},
    # India
    {"url": "https://analyticsindiamag.com/feed/",
     "source": "Analytics India",   "region_name": "india"},
    {"url": "https://inc42.com/feed/",
     "source": "Inc42",             "region_name": "india"},
    {"url": "https://yourstory.com/feed",
     "source": "YourStory",         "region_name": "india"},
    # China / Asia
    {"url": "https://technode.com/feed/",
     "source": "TechNode",          "region_name": "china"},
    {"url": "https://pandaily.com/feed/",
     "source": "Pandaily",          "region_name": "china"},
    # ROW
    {"url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
     "source": "BBC Tech",          "region_name": "row"},
    {"url": "https://aibusiness.com/rss.xml",
     "source": "AI Business",       "region_name": "row"},
]

GEO_QUOTA = {"usa": 3, "india": 3, "china": 2, "row": 2}

REGION_EMOJI = {"usa": "🇺🇸", "india": "🇮🇳", "china": "🇨🇳", "row": "🌐"}

AI_KEYWORDS = {
    "artificial intelligence", "machine learning", "deep learning", "neural network",
    "large language model", "llm", "generative ai", "gpt", "gemini", "claude",
    "chatgpt", "openai", "anthropic", "deepmind", "foundation model", "ai model",
    "baidu", "mistral", "llama", "midjourney", "copilot", "ai chip", "nvidia ai",
    "ai safety", "alignment", "ai regulation", "ai funding", "ai startup",
    "ai research", "multimodal", "autonomous", "computer vision", "natural language",
    "robotics ai", "text-to-image", "text-to-video",
}

IMPACT_WORDS = {"billion", "million", "raises", "launches", "beats", "surpasses",
                "record", "first", "breakthrough", "deploys", "unveils", "acquires",
                "ban", "law", "regulation", "funding", "open-source", "open source"}

KNOWN_COMPANIES = [
    "OpenAI", "Google", "DeepMind", "Anthropic", "Meta", "Microsoft",
    "Apple", "Amazon", "Baidu", "ByteDance", "NVIDIA", "Mistral",
    "Infosys", "TCS", "Wipro", "Jio", "Samsung", "Huawei", "Xiaomi",
    "Stability AI", "Midjourney", "Cohere", "Inflection", "xAI",
    "Perplexity", "Runway", "ElevenLabs", "Databricks", "Krutrim", "ISRO",
]


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
    POSTED_LOG.parent.mkdir(exist_ok=True)
    with open(POSTED_LOG, "w", encoding="utf-8") as f:
        json.dump(posted, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
# TEXT UTILITIES
# ─────────────────────────────────────────────

def _strip_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text or "")
    text = unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def _split_sentences(text: str) -> list:
    text = _strip_html(text)
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def _extract_company(title: str, source: str) -> str:
    for company in KNOWN_COMPANIES:
        if re.search(rf'\b{re.escape(company)}\b', title, re.IGNORECASE):
            return company
    words = title.split()
    parts = []
    for w in words[:4]:
        clean = re.sub(r"[^a-zA-Z0-9']", '', w)
        if clean and clean[0].isupper() and clean.lower() not in {
            "the", "a", "an", "how", "why", "what", "is", "are", "was"
        }:
            parts.append(clean)
        else:
            break
    return " ".join(parts)[:30] if parts else source[:30]


def _extract_stat(text: str):
    patterns = [
        (r'\$(\d+\.?\d*\s*[BMT]illion)', "Funding Amount"),
        (r'(\d+\.?\d*%)',                "Key Metric"),
        (r'\$(\d+[BMK]\+?)',             "Value"),
        (r'(\d[\d,]+\+?\s*(?:users|developers|jobs))', "Reach"),
    ]
    for pattern, label in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1)[:12], label
    return "AI", "Sector"


def _make_body_lines(sentences: list, title: str) -> list:
    """Word-wrap body text into up to 4 lines, completing sentences where possible."""
    full = " ".join(sentences[:6]) if sentences else title

    # Word-wrap at 48 chars per line
    words = full.split()
    lines, cur = [], []
    for word in words:
        test = " ".join(cur + [word])
        if len(test) <= 48:
            cur.append(word)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))

    # Take up to 4 lines; if the cut lands mid-sentence, trim back to the
    # last complete sentence so the text always ends naturally.
    candidate = lines[:4]
    last = candidate[-1].rstrip() if candidate else ""
    if last and last[-1] not in '.!?':
        joined = " ".join(candidate)
        best = -1
        for marker in ['. ', '! ', '? ']:
            pos = joined.rfind(marker)
            if pos > 0:
                best = max(best, pos + 1)
        # Only trim if a sentence end exists in the latter half of the text
        if best > len(joined) * 0.35:
            trimmed = joined[:best].strip()
            rw, cur2 = [], []
            for word in trimmed.split():
                test = " ".join(cur2 + [word])
                if len(test) <= 48:
                    cur2.append(word)
                else:
                    if cur2:
                        rw.append(" ".join(cur2))
                    cur2 = [word]
            if cur2:
                rw.append(" ".join(cur2))
            candidate = rw[:4]

    while len(candidate) < 4:
        candidate.append("")
    return [l[:50] for l in candidate[:4]]


def _score(title: str, summary: str) -> int:
    text = (title + " " + summary).lower()
    score = sum(1 for w in IMPACT_WORDS if w in text)
    if re.search(r'\d', title):
        score += 1
    return score


def _make_hashtags(title: str, company: str, region_name: str) -> str:
    region_tags = {
        "usa":   ["#AI", "#TechNews", "#AINews"],
        "india": ["#IndiaAI", "#AI", "#TechIndia"],
        "china": ["#ChinaAI", "#AI", "#AsiaAI"],
        "row":   ["#GlobalAI", "#AI", "#TechNews"],
    }
    base = region_tags.get(region_name, ["#AI", "#TechNews"])
    ctag = "#" + re.sub(r'[^a-zA-Z0-9]', '', company)
    if len(ctag) > 2:
        base = [ctag] + base
    tl = title.lower()
    if "fund" in tl or "billion" in tl:
        base.append("#AIFunding")
    if "regulat" in tl or "law" in tl:
        base.append("#AIPolicy")
    return " ".join(base[:5])


# ─────────────────────────────────────────────
# RSS FETCH
# ─────────────────────────────────────────────

def _fetch_feed(feed: dict, max_age_hours: int = 72) -> list:
    url = feed["url"]
    try:
        import feedparser
        parsed = feedparser.parse(url)
        items = []
        for entry in parsed.entries[:25]:
            pub = entry.get("published_parsed") or entry.get("updated_parsed")
            if pub:
                try:
                    pub_dt = datetime(*pub[:6], tzinfo=timezone.utc)
                    age_h = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
                    if age_h > max_age_hours:
                        continue
                except Exception:
                    pass
            title   = _strip_html(entry.get("title", ""))
            summary = _strip_html(entry.get("summary", "") or entry.get("description", ""))
            link    = entry.get("link", "")
            if title:
                items.append({
                    "title": title, "summary": summary, "link": link,
                    "source": feed["source"], "region_name": feed["region_name"],
                })
        return items
    except ImportError:
        return _fetch_urllib(feed, max_age_hours)
    except Exception as e:
        logger.warning(f"[RSS] feedparser failed for {feed['source']}: {e}")
        return _fetch_urllib(feed, max_age_hours)


def _fetch_urllib(feed: dict, max_age_hours: int = 72) -> list:
    import urllib.request, xml.etree.ElementTree as ET
    try:
        req = urllib.request.Request(feed["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        channel = root.find("channel")
        entries = channel.findall("item") if channel else \
                  root.findall("{http://www.w3.org/2005/Atom}entry")
        items = []
        for entry in entries[:25]:
            def _t(tag):
                el = entry.find(tag)
                return _strip_html(el.text or "") if el is not None else ""
            title   = _t("title") or _t("{http://www.w3.org/2005/Atom}title")
            summary = _t("description") or _t("summary") or \
                      _t("{http://www.w3.org/2005/Atom}summary")
            if title:
                items.append({
                    "title": title, "summary": summary, "link": "",
                    "source": feed["source"], "region_name": feed["region_name"],
                })
        return items
    except Exception as e:
        logger.warning(f"[RSS] urllib failed for {feed['source']}: {e}")
        return []


def _item_to_story(item: dict) -> dict:
    title       = item["title"]
    summary     = item["summary"]
    source      = item["source"]
    region_name = item["region_name"]

    company   = _extract_company(title, source)
    sentences = _split_sentences(summary)
    body      = _make_body_lines(sentences, title)
    stat_value, stat_label = _extract_stat(title + " " + summary)
    hashtags  = _make_hashtags(title, company, region_name)

    words    = title.split()
    headline = title  # full title — renderer wraps to 2 visual lines

    stop     = {"the", "a", "an", "is", "are", "was", "of", "in", "to", "for", "and"}
    wm_words = [re.sub(r'[^A-Z0-9]', '', w.upper()) for w in words
                if w.lower() not in stop and len(w) > 3]
    watermark = wm_words[0][:10] if wm_words else "AI"

    return {
        "company":    company[:30],
        "headline":   headline,
        "watermark":  watermark,
        "body":       body,
        "summary":    summary,   # full RSS summary — used for complete-sentence audio
        "stat_label": stat_label[:30],
        "stat_value": stat_value[:12],
        "source":     source[:30],
        "hashtags":   hashtags,
        "region":     REGION_EMOJI.get(region_name, "🌐"),
        "region_name": region_name,
        "reference":  item.get("link") or
                      f"https://www.google.com/search?q={'+'.join(title.split()[:5])}",
        "score":      item.get("score", 0),
    }


# ─────────────────────────────────────────────
# GEO-BALANCED SELECTION
# ─────────────────────────────────────────────

def _select_geo_balanced(items: list, quota: dict) -> list:
    by_region = {r: [] for r in quota}
    for item in sorted(items, key=lambda x: x.get("score", 0), reverse=True):
        r = item.get("region_name", "row")
        if r in by_region:
            by_region[r].append(item)

    selected = []
    for region, n in quota.items():
        selected.extend(by_region[region][:n])

    # Pad if quota not met
    if len(selected) < sum(quota.values()):
        used = {id(s) for s in selected}
        overflow = sorted(
            [i for i in items if id(i) not in used],
            key=lambda x: x.get("score", 0), reverse=True
        )
        selected.extend(overflow[:sum(quota.values()) - len(selected)])

    random.shuffle(selected)
    return selected[:sum(quota.values())]


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def fetch_geo_balanced_stories(n: int = 10, save_dedup: bool = True,
                               geo_quota: dict = None) -> list:
    """
    Fetch n geo-balanced AI stories from RSS feeds.
    Default quota: 3 USA · 3 India · 2 China · 2 ROW.
    Pass geo_quota dict to override (e.g. {"usa": 6, "india": 8, "china": 3, "row": 3}).
    Pass save_dedup=False to skip marking stories as posted (generate-only runs).
    """
    quota = geo_quota if geo_quota is not None else GEO_QUOTA
    logger.info(f"[RSS] Fetching {n} AI stories (quota: {quota})...")

    posted_set = {p["headline"].lower()[:60] for p in _load_posted()[-50:]}
    all_items  = []

    for feed in RSS_FEEDS:
        items = _fetch_feed(feed, max_age_hours=72)
        logger.info(f"[RSS] {feed['source']} ({feed['region_name']}): {len(items)} items")
        all_items.extend(items)

    # Filter AI-relevant + not posted
    candidates = []
    for item in all_items:
        text = (item["title"] + " " + item["summary"]).lower()
        if not any(kw in text for kw in AI_KEYWORDS):
            continue
        if item["title"].lower()[:60] in posted_set:
            continue
        item["score"] = _score(item["title"], item["summary"])
        candidates.append(item)

    logger.info(f"[RSS] AI candidates: {len(candidates)} / {len(all_items)} total")

    if len(candidates) < 5:
        logger.warning("[RSS] Too few candidates — using fallback stories")
        return FALLBACK_STORIES[:n]

    selected = _select_geo_balanced(candidates, quota)

    if len(selected) < 5:
        logger.warning("[RSS] Not enough geo-balanced stories — padding with fallback")
        extras = [s for s in FALLBACK_STORIES
                  if s["headline"].lower()[:60] not in posted_set]
        selected.extend(extras[:n - len(selected)])

    stories = [_item_to_story(item) for item in selected[:n]]

    # Pad to exactly n if needed
    if len(stories) < n:
        extras = [s for s in FALLBACK_STORIES if s["headline"] not in
                  {x["headline"] for x in stories}]
        stories.extend(extras[:n - len(stories)])

    if save_dedup:
        _save_posted([s["headline"] for s in stories])
    else:
        logger.info("[RSS] Dedup save skipped (generate-only mode)")

    logger.info(f"[RSS] Selected {len(stories)} stories:")
    for i, s in enumerate(stories, 1):
        logger.info(f"  {i:2d}. [{s['region_name']:6s}] {s['company']:<22} — {s['headline']}")

    return stories[:n]


def fetch_latest_ai_news() -> dict | None:
    """Legacy single-story fetch — returns top story or None."""
    stories = fetch_geo_balanced_stories(n=1)
    return stories[0] if stories else None


# ─────────────────────────────────────────────
# FALLBACK STORIES
# ─────────────────────────────────────────────

FALLBACK_STORIES = [
    {
        "company": "OpenAI", "headline": "GPT-5 Sets New Reasoning Record",
        "watermark": "GPT5",
        "body": ["GPT-5 scores 96% on MMLU,", "above human doctors.", "256k context window opens", "to all developers this week."],
        "stat_label": "MMLU Score", "stat_value": "96%",
        "source": "OpenAI Blog", "region": "🇺🇸", "region_name": "usa",
        "hashtags": "#OpenAI #AI #GPT5 #TechNews #AINews",
        "reference": "https://openai.com", "score": 10,
    },
    {
        "company": "Google DeepMind", "headline": "Gemini Ultra Beats Human Doctors",
        "watermark": "HEALTH",
        "body": ["Gemini Ultra 2 scores 90%", "on 14,000 clinical questions.", "Beats specialists in 9 of 12", "medical specialties."],
        "stat_label": "Clinical Accuracy", "stat_value": "90%",
        "source": "Google DeepMind", "region": "🇺🇸", "region_name": "usa",
        "hashtags": "#Google #Gemini #AIHealth #DeepMind #AI",
        "reference": "https://deepmind.google", "score": 9,
    },
    {
        "company": "Anthropic", "headline": "Claude 4 Leads All Safety Benchmarks",
        "watermark": "SAFE",
        "body": ["Claude 4 scores 99% on", "red-team safety evaluations.", "Tops all 12 harmlessness", "benchmark categories."],
        "stat_label": "Safety Score", "stat_value": "99%",
        "source": "Anthropic Blog", "region": "🇺🇸", "region_name": "usa",
        "hashtags": "#Anthropic #Claude #AISafety #AI #LLM",
        "reference": "https://anthropic.com", "score": 8,
    },
    {
        "company": "Reliance Jio", "headline": "India Launches Sovereign AI Platform",
        "watermark": "INDIA",
        "body": ["Jio deploys 1 exaflop of", "AI compute across 12 cities.", "Indian-language models for", "1.4 billion users."],
        "stat_label": "Compute Capacity", "stat_value": "1 ExaFLOP",
        "source": "Economic Times", "region": "🇮🇳", "region_name": "india",
        "hashtags": "#India #JioAI #AIIndia #DigitalIndia #AI",
        "reference": "https://economictimes.com", "score": 8,
    },
    {
        "company": "IIT Bombay", "headline": "India AI Detects Crop Disease Early",
        "watermark": "FARM",
        "body": ["Satellite AI spots crop disease", "3 weeks before symptoms.", "Protects $8B in annual", "farm losses across 15 states."],
        "stat_label": "Early Detection Lead", "stat_value": "3 Weeks",
        "source": "Analytics India", "region": "🇮🇳", "region_name": "india",
        "hashtags": "#IndiaAI #AgriTech #ISRO #AI #TechIndia",
        "reference": "https://analyticsindiamag.com", "score": 8,
    },
    {
        "company": "Infosys AI", "headline": "Infosys AI Cuts Code Bugs by 60%",
        "watermark": "CODE",
        "body": ["AI coding assistant rolled out", "to 200,000 Infosys engineers.", "Production bug rate drops 60%.", "Saves 2 hours per dev daily."],
        "stat_label": "Bug Reduction", "stat_value": "60%",
        "source": "Inc42", "region": "🇮🇳", "region_name": "india",
        "hashtags": "#Infosys #IndiaAI #DevTools #AI #EnterpriseAI",
        "reference": "https://inc42.com", "score": 7,
    },
    {
        "company": "Baidu / ERNIE", "headline": "Baidu ERNIE 5 Tops China AI Charts",
        "watermark": "ERNIE5",
        "body": ["ERNIE 5 outperforms GPT-4 on", "Chinese-language benchmarks.", "100 million users signed up", "within 24 hours of launch."],
        "stat_label": "Day 1 Users", "stat_value": "100M",
        "source": "TechNode", "region": "🇨🇳", "region_name": "china",
        "hashtags": "#Baidu #ERNIE5 #ChinaAI #AI #LLM",
        "reference": "https://technode.com", "score": 8,
    },
    {
        "company": "ByteDance", "headline": "ByteDance AI Video Fools Experts",
        "watermark": "VIDEO",
        "body": ["MagicVideo makes 4K 60fps video", "from text in 8 seconds.", "Experts cannot tell it", "apart from real footage."],
        "stat_label": "Generation Speed", "stat_value": "8 Secs",
        "source": "Pandaily", "region": "🇨🇳", "region_name": "china",
        "hashtags": "#ByteDance #VideoAI #ChinaAI #GenAI #OpenSource",
        "reference": "https://pandaily.com", "score": 9,
    },
    {
        "company": "EU AI Office", "headline": "EU AI Act Enforcement Begins Today",
        "watermark": "REGULATE",
        "body": ["High-risk AI must comply or", "face 7% revenue fines.", "30 nations adopting the", "EU framework as global standard."],
        "stat_label": "Max Fine", "stat_value": "7%",
        "source": "The Decoder", "region": "🇪🇺", "region_name": "row",
        "hashtags": "#EUAIAct #AIRegulation #EU #AIPolicy #AI",
        "reference": "https://the-decoder.com", "score": 8,
    },
    {
        "company": "UK AI Safety Inst.", "headline": "UK Publishes First Global AI Standard",
        "watermark": "SAFETY",
        "body": ["UK AI Safety Institute issues", "first binding global standard.", "24 nations signed on;", "frontier models must pass eval."],
        "stat_label": "Nations Signed", "stat_value": "24",
        "source": "BBC Tech", "region": "🇬🇧", "region_name": "row",
        "hashtags": "#UKAISafety #AISafety #UK #AIPolicy #GlobalAI",
        "reference": "https://bbc.co.uk/news/technology", "score": 8,
    },
]


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stories = fetch_geo_balanced_stories(10)
    print(f"\nFetched {len(stories)} stories:")
    for i, s in enumerate(stories, 1):
        hl = s['headline'].encode('ascii', errors='replace').decode('ascii')
        print(f"  {i:2d}. [{s['region_name']:6s}] {s['company']:<22} score={s['score']:2d} -- {hl}")
