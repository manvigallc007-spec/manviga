"""
test_template.py — Render slide PNGs from hardcoded test stories.

Usage (from youtube-improve/ directory):
    python test_template.py

Outputs PNG slides to:  output/test_slides/
  00_intro.png
  01_story_openai.png
  02_story_google.png
  ... (one per story)
  11_outro.png

No TTS, no FFmpeg, no API calls required.
Stories are the same ones shown in the reference news template screenshot.
"""

import sys
from pathlib import Path
from datetime import datetime

# ── Ensure src/ is on the path ─────────────────────────────────────────────
SRC = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC))

from video_generator import (
    load_fonts,
    render_thumbnail_slide,
    render_intro_slide,
    render_slide,
    render_outro_slide,
    STORY_THEMES,
)
from thumbnail_generator import generate_thumbnail_a, generate_thumbnail_b

# ── Output directory ────────────────────────────────────────────────────────
OUT_DIR = Path(__file__).parent / "output" / "test_slides"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Test date (matches reference screenshot) ────────────────────────────────
DATE_STR = "March 29, 2026"

# ── 10 hardcoded test stories (matching reference screenshot) ───────────────
TEST_STORIES = [
    {
        "company": "OpenAI",
        "headline": "GPT-5 Sets New Reasoning Record",
        "hook": "GPT-5 SETS NEW REASONING RECORD",
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
        "titles": ["OpenAI GPT-5 Just Broke Every AI Benchmark", "GPT-5 Is Here: What You Need To Know", "The AI That Beats Human Experts Is Now Live"],
        "tts_script": "The AI that outperforms human experts across every discipline just went live for everyone.",
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
        "titles": ["Google's AI Now Outperforms Human Doctors", "Gemini Ultra 2 Aces Medical Exams Worldwide", "AI vs Doctors: Google Just Won"],
        "tts_script": "An AI just outperformed board-certified doctors — and it's ready for real-world deployment.",
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
        "titles": ["Anthropic's Claude 4 Is The World's Safest AI", "99% Safety Score: Claude 4 Sets New Standard", "The AI Regulator's Dream Model Just Launched"],
        "tts_script": "Anthropic's Claude 4 just topped every safety benchmark in the industry.",
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
        "titles": ["India Just Built Its Own AI Superpower Platform", "Jio Launches National AI Infrastructure Worth Billions", "Why India's New AI Platform Changes Everything"],
        "tts_script": "India just made its boldest declaration of AI independence.",
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
        "titles": ["India's Satellite AI Detects Crop Disease Early", "IIT Bombay AI Protects $8B in Farming Each Year", "How India Is Using AI To Feed 250 Million People"],
        "tts_script": "IIT Bombay and ISRO deployed a satellite AI that detects crop disease three weeks before it's visible.",
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
        "titles": ["Infosys AI Cuts Bugs 60%: The Largest Dev Rollout", "200,000 Developers Get AI Upgrade at Infosys", "How Infosys Used AI To Transform Software Quality"],
        "tts_script": "Infosys completed the world's largest enterprise AI coding rollout with 200,000 developers.",
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
        "titles": ["Baidu ERNIE 5 Surpasses GPT-4 In China", "China's AI Hits 100 Million Users In 24 Hours", "The Other AI Superpower Just Made Its Move"],
        "tts_script": "China's Baidu just launched ERNIE 5 with 100 million sign-ups on day one.",
        "score": {"impact": 8, "novelty": 7, "relevance": 8, "virality": 8, "total": 31},
    },
    {
        "company": "Huawei / Ascend",
        "headline": "Huawei Ascend 920 Rivals Nvidia H100",
        "hook": "CHINA'S AI CHIP CLOSES THE GAP",
        "what_happened": [
            "Ascend 920 delivers 800 TFLOPS — 90% of H100 performance",
            "Mass production begins immediately, bypassing US export bans",
            "Priced 40% lower than equivalent Nvidia hardware",
        ],
        "why_it_matters": "A domestic chip at 90% of H100 performance effectively breaks the US semiconductor containment strategy. China's AI supply chain is now self-sufficient.",
        "whats_next": "Ascend 920 will power ERNIE 6 training clusters launching mid-year.",
        "keywords": ["Ascend", "800", "Nvidia"],
        "summary": "Huawei's Ascend 920 chip matches Nvidia H100 at 40% lower cost.",
        "impact": "Huawei's Ascend 920 hits 90% of H100 performance in mass production. US chip sanctions now have a credible domestic alternative.",
        "watermark": "CHIPS",
        "body": ["800 TFLOPS compute", "90% H100 performance", "40% cheaper than Nvidia", "Mass production now"],
        "stat_label": "H100 Performance Match",
        "stat_value": "90%",
        "source": "South China Morning Post",
        "region": "🇨🇳",
        "region_name": "china",
        "hashtags": ["#Huawei", "#Ascend920", "#AIChips", "#ChinaAI", "#Semiconductors"],
        "titles": ["Huawei's AI Chip Now Rivals Nvidia At 40% Less Cost", "China Breaks US Chip Sanctions With Ascend 920", "The Chip That Changes The AI Race"],
        "tts_script": "Huawei's Ascend 920 chip matches 90% of Nvidia H100 performance at 40% lower cost.",
        "score": {"impact": 9, "novelty": 8, "relevance": 8, "virality": 8, "total": 33},
    },
    {
        "company": "EU AI Office",
        "headline": "EU Passes First AI Liability Law",
        "hook": "EUROPE FORCES AI FIRMS TO PAY DAMAGES",
        "what_happened": [
            "EU AI Liability Directive passes 421-to-89 in Parliament",
            "Companies face unlimited fines if AI systems cause harm",
            "Law takes effect for all EU-operating AI firms by 2027",
        ],
        "why_it_matters": "The EU just made AI liability legally enforceable for the first time anywhere in the world. Every AI product sold in Europe must now carry legal risk insurance.",
        "whats_next": "US and UK are expected to table similar legislation by year end following EU precedent.",
        "keywords": ["liability", "EU", "fines"],
        "summary": "EU Parliament passes the world's first binding AI liability directive.",
        "impact": "EU holds AI companies legally liable for harm caused by their systems. This reshapes global AI product risk frameworks overnight.",
        "watermark": "LAW",
        "body": ["421-89 Parliament vote", "Unlimited fines for harm", "Covers all EU AI firms", "Effective 2027"],
        "stat_label": "Parliament Vote Margin",
        "stat_value": "421–89",
        "source": "Euractiv",
        "region": "🇪🇺",
        "region_name": "row",
        "hashtags": ["#EUAIAct", "#AILaw", "#TechPolicy", "#Europe", "#AI"],
        "titles": ["EU Just Made AI Companies Pay For Harm", "World's First AI Liability Law Just Passed", "Europe Rewrites The Rules For AI Products"],
        "tts_script": "Europe just passed the world's first binding AI liability law by a massive 421 to 89 vote.",
        "score": {"impact": 9, "novelty": 9, "relevance": 9, "virality": 8, "total": 35},
    },
    {
        "company": "DeepSeek",
        "headline": "DeepSeek V3 Runs On a Laptop",
        "hook": "FRONTIER AI NOW FITS IN YOUR POCKET",
        "what_happened": [
            "DeepSeek V3 quantized model runs fully on M3 MacBook Pro",
            "Matches GPT-4 on coding tasks at 1/100th the compute cost",
            "Open-weight release triggers immediate global downloads",
        ],
        "why_it_matters": "Running a GPT-4-class model locally ends cloud AI dependency for developers. Privacy-first AI at zero inference cost is now real.",
        "whats_next": "Community fine-tunes of DeepSeek V3 for medical and legal tasks are already underway.",
        "keywords": ["laptop", "open", "V3"],
        "summary": "DeepSeek V3 open weights run GPT-4 class AI on consumer hardware.",
        "impact": "DeepSeek V3 runs GPT-4-level AI locally on a MacBook. Open weights release democratizes frontier AI for every developer on earth.",
        "watermark": "LOCAL",
        "body": ["Runs on M3 MacBook Pro", "Matches GPT-4 on code", "1/100th cloud cost", "Open weights released"],
        "stat_label": "Cost vs Cloud Inference",
        "stat_value": "1/100th",
        "source": "HuggingFace Blog",
        "region": "🌐",
        "region_name": "row",
        "hashtags": ["#DeepSeek", "#OpenSource", "#LocalAI", "#AI", "#LLM"],
        "titles": ["DeepSeek V3 Is GPT-4 That Runs On Your Laptop", "Open Source AI Just Beat The Cloud Giants", "The Model That Changes Everything Just Dropped"],
        "tts_script": "DeepSeek V3 runs GPT-4 class intelligence locally on a MacBook at 1/100th the cloud cost.",
        "score": {"impact": 9, "novelty": 9, "relevance": 9, "virality": 10, "total": 37},
    },
]


def main():
    print(f"Loading fonts...")
    fonts = load_fonts()

    # Render first 3 story slides to check layout
    for i in range(3):
        story = TEST_STORIES[i]
        theme = STORY_THEMES[i % len(STORY_THEMES)]
        slug  = story["company"].lower().replace(" ", "_").replace("/", "_")[:12]
        out   = OUT_DIR / f"story_{i+1:02d}_{slug}.png"
        render_slide(story, theme, fonts, DATE_STR, i + 1,
                     len(TEST_STORIES), all_stories=TEST_STORIES, story_idx=i).save(str(out))
        print(f"[DONE] {out.name}")


if __name__ == "__main__":
    main()
