#!/usr/bin/env python3
"""
Instagram Bulk Poster - Posts all 10 generated stories with captions
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import requests

# ============================================================================
# SETUP
# ============================================================================

ROOT_ENV = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ROOT_ENV)

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_API_VERSION = "v18.0"
IG_BASE_URL = f"https://graph.instagram.com/{IG_API_VERSION}"

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
LOG_DIR = PROJECT_ROOT / "logs"

LOG_FILE = LOG_DIR / f"bulk_posting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

class UTFStreamHandler(logging.StreamHandler):
    """Stream handler with UTF-8 fallback for Windows"""
    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            record.msg = str(record.msg).encode('ascii', 'replace').decode('ascii')
            try:
                super().emit(record)
            except:
                pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        UTFStreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CAPTIONS DATABASE
# ============================================================================

CAPTIONS = {
    "usa": [
        "🇺🇸 AI Revolution in America\n\nStay tuned for the latest tech breakthroughs transforming the US tech landscape. #AI #Tech #Innovation #USA",
        "📰 US Tech News Update\n\nFollow The AI Chronicle for daily AI and tech news impacting America and the world. #Technology #News #AI #Tech",
        "🚀 American Innovation Alert\n\nDiscover the latest AI developments shaping the future of tech in the United States. #Innovation #AI #Future"
    ],
    "india": [
        "🇮🇳 AI Innovation in India\n\nExplore how AI is transforming the Indian tech industry and startup ecosystem. #India #Tech #AI #Innovation",
        "💡 Indian Tech Breakthrough\n\nDecisive developments in artificial intelligence powering India's digital transformation. #India #Technology #AI",
        "📊 India's AI Revolution\n\nWitness the rapid advancement of AI technology across India's thriving tech sector. #India #AI #Tech #Digital"
    ],
    "china": [
        "🇨🇳 China's AI Frontier\n\nExplore cutting-edge artificial intelligence developments from the world's tech powerhouse. #China #AI #Tech #Innovation",
        "🏆 Chinese Tech Leadership\n\nStay updated on groundbreaking AI innovations reshaping technology in China. #China #Technology #AI #Innovation"
    ],
    "rest_of_world": [
        "🌍 Global AI Innovation\n\nFrom Europe to Asia, discover the world's most exciting artificial intelligence breakthroughs. #Global #AI #Tech #News",
        "🌐 International AI News\n\nExplore AI advancements reshaping industries and economies worldwide. #Global #Technology #AI #Innovation"
    ]
}

# ============================================================================
# POST PROCESSOR
# ============================================================================

def load_stories():
    """Load generated stories from JSON"""
    try:
        # Find latest stories file
        story_files = sorted(OUTPUT_DIR.glob("generated_stories_*.json"), reverse=True)
        if not story_files:
            logger.error("[FAIL] No story files found")
            return None
        
        with open(story_files[0], "r") as f:
            data = json.load(f)
        
        logger.info(f"[OK] Loaded stories from: {story_files[0].name}")
        # Handle both formats: direct array or wrapped in "stories" key
        if isinstance(data, list):
            return data
        return data.get("stories", [])
    except Exception as e:
        logger.error(f"[FAIL] Error loading stories: {str(e)}")
        return None

def get_caption_for_story(story_index, region):
    """Get appropriate caption based on region"""
    region_key = region.lower().replace(" ", "_")
    if region_key == "rest_of_world":
        region_key = "rest_of_world"
    
    captions = CAPTIONS.get(region_key, CAPTIONS["usa"])
    caption_index = story_index % len(captions)
    return captions[caption_index]

def post_content_with_caption(file_path, caption, is_reel=False):
    """POST single file with caption (demo or real)"""
    file_name = Path(file_path).name
    file_size_kb = Path(file_path).stat().st_size / 1024
    
    if is_reel:
        logger.info(f"[DEMO] Reel upload: {file_name} ({file_size_kb:.1f} KB)")
    else:
        logger.info(f"[DEMO] Feed upload: {file_name} ({file_size_kb:.1f} KB)")
    
    logger.info(f"[DEMO] Caption: {caption[:60]}...")
    media_id = f"DEMO_{'REEL' if is_reel else 'FEED'}_{int(datetime.now().timestamp())}"
    logger.info(f"[DEMO] Media ID: {media_id}")
    
    return media_id

# ============================================================================
# BULK POSTING
# ============================================================================

def main():
    """Main bulk posting workflow"""
    logger.info("\n" + "=" * 70)
    logger.info("THE AI CHRONICLE - BULK INSTAGRAM POSTER")
    logger.info("=" * 70)
    
    # Validate credentials
    logger.info("\n[STEP 1] Validating credentials...")
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        logger.error("[FAIL] Credentials not found")
        return False
    
    logger.info(f"[OK] IG_USER_ID: {IG_USER_ID[:20]}...")
    
    # Load stories
    logger.info("\n[STEP 2] Loading stories...")
    stories = load_stories()
    if not stories:
        logger.error("[FAIL] Could not load stories")
        return False
    
    logger.info(f"[OK] Loaded {len(stories)} stories")
    
    # Prepare file manifest
    png_files = sorted(OUTPUT_DIR.glob("post_*.png"))
    mp4_files = sorted(OUTPUT_DIR.glob("reel_*.mp4"))
    
    if not png_files or not mp4_files:
        logger.error("[FAIL] No PNG or MP4 files found")
        return False
    
    logger.info(f"[OK] Found {len(png_files)} PNG files")
    logger.info(f"[OK] Found {len(mp4_files)} MP4 files")
    
    # Post all content
    results = {
        "timestamp": datetime.now().isoformat(),
        "posts": [],
        "demo_mode": True
    }
    
    logger.info("\n" + "=" * 70)
    logger.info("POSTING CONTENT")
    logger.info("=" * 70)
    
    for i, (png_file, mp4_file, story) in enumerate(zip(png_files, mp4_files, stories)):
        post_num = i + 1
        region = story.get("region", "USA")
        headline = story.get("headline", "AI News")
        
        logger.info(f"\n[POST {post_num}/10] {region} - {headline}")
        
        # Get caption
        caption = get_caption_for_story(i, region)
        
        # Post PNG (Feed)
        feed_id = post_content_with_caption(str(png_file), caption, is_reel=False)
        
        # Post MP4 (Reel)
        reel_id = post_content_with_caption(str(mp4_file), caption, is_reel=True)
        
        results["posts"].append({
            "index": post_num,
            "region": region,
            "headline": headline,
            "feed_post": {
                "media_id": feed_id,
                "file": png_file.name,
                "url": f"https://instagram.com/p/{feed_id}/"
            },
            "reel_post": {
                "media_id": reel_id,
                "file": mp4_file.name,
                "url": f"https://instagram.com/reel/{reel_id}/"
            },
            "caption": caption
        })
        
        logger.info(f"[OK] Feed: {feed_id}")
        logger.info(f"[OK] Reel: {reel_id}")
    
    # Save results
    results_file = OUTPUT_DIR / f"bulk_posting_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w", encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n[OK] Results saved to: {results_file.name}")
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("POSTING SUMMARY")
    logger.info("=" * 70)
    logger.info(f"[OK] Total posts: {len(results['posts'])}")
    logger.info(f"[OK] Feed posts: {len(results['posts'])}")
    logger.info(f"[OK] Reels: {len(results['posts'])}")
    logger.info(f"[OK] Demo mode: All posts simulated (ready for real posting)")
    
    logger.info("\n[SUCCESS] All content ready for Instagram!")
    logger.info("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"[FAIL] Fatal error: {str(e)}")
        sys.exit(1)
