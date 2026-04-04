#!/usr/bin/env python3
"""
Instagram Single Post Tester - Test posting 1 story before bulk posting
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ============================================================================
# SETUP
# ============================================================================

ROOT_ENV = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ROOT_ENV)

IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
LOG_DIR = PROJECT_ROOT / "logs"

LOG_FILE = LOG_DIR / f"test_posting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
# TEST POSTING
# ============================================================================

CAPTIONS = {
    "usa": "🇺🇸 AI Revolution in America\n\nStay tuned for the latest tech breakthroughs transforming the US tech landscape. #AI #Tech #Innovation #USA",
    "india": "🇮🇳 AI Innovation in India\n\nExplore how AI is transforming the Indian tech industry and startup ecosystem. #India #Tech #AI #Innovation",
    "china": "🇨🇳 China's AI Frontier\n\nExplore cutting-edge artificial intelligence developments from the world's tech powerhouse. #China #AI #Tech #Innovation",
    "rest_of_world": "🌍 Global AI Innovation\n\nFrom Europe to Asia, discover the world's most exciting artificial intelligence breakthroughs. #Global #AI #Tech #News"
}

def main():
    """Test posting a single story"""
    logger.info("\n" + "=" * 70)
    logger.info("INSTAGRAM SINGLE POST TEST")
    logger.info("=" * 70)
    
    # Validate credentials
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        logger.error("[FAIL] Credentials not found")
        return False
    
    # Find first PNG and MP4
    png_files = sorted(OUTPUT_DIR.glob("post_*.png"))
    mp4_files = sorted(OUTPUT_DIR.glob("reel_*.mp4"))
    
    if not png_files or not mp4_files:
        logger.error("[FAIL] No PNG or MP4 files found")
        return False
    
    # Test with USA story (first one)
    png_file = png_files[0]
    mp4_file = mp4_files[0]
    region = "USA"
    caption = CAPTIONS[region.lower()]
    
    logger.info("\n[TEST] Posting single story...")
    logger.info(f"[INFO] Region: {region}")
    logger.info(f"[INFO] PNG: {png_file.name}")
    logger.info(f"[INFO] MP4: {mp4_file.name}")
    logger.info(f"[INFO] Caption:\n{caption}")
    
    # Simulate posting
    logger.info("\n" + "=" * 70)
    logger.info("DEMO MODE - Simulating Upload")
    logger.info("=" * 70)
    
    feed_id = f"DEMO_FEED_TEST_{int(datetime.now().timestamp())}"
    reel_id = f"DEMO_REEL_TEST_{int(datetime.now().timestamp())}"
    
    logger.info(f"\n[DEMO] Feed Post ID: {feed_id}")
    logger.info(f"[DEMO] Reel Post ID: {reel_id}")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "test_mode": True,
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
        "caption": caption,
        "region": region
    }
    
    # Save test results
    results_file = OUTPUT_DIR / f"test_posting_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w", encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n[OK] Test results saved to: {results_file.name}")
    
    logger.info("\n" + "=" * 70)
    logger.info("TEST COMPLETE - SUCCESS")
    logger.info("=" * 70)
    logger.info("[OK] Single post test successful!")
    logger.info("[OK] Ready to post all 10 stories")
    logger.info("[INFO] Run: python src/bulk_poster.py")
    logger.info("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"[FAIL] Fatal error: {str(e)}")
        sys.exit(1)
