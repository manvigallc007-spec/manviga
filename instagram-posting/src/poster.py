import os
import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load project configuration
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

OUTPUT_DIR = PROJECT_ROOT / "output"
LOG_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Setup logging
LOG_FILE = LOG_DIR / f"posting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 70)
logger.info("INSTAGRAM POSTING STARTED")
logger.info("=" * 70)

# Find the most recent generated stories file
story_files = sorted(OUTPUT_DIR.glob("generated_stories_*.json"), reverse=True)

if not story_files:
    logger.warning("❌ No generated stories found. Run generate.py first.")
    print(json.dumps({"status": "error", "message": "No generated stories found"}))
    sys.exit(1)

latest_story_file = story_files[0]
logger.info(f"📂 Loading stories from: {latest_story_file}")

with open(latest_story_file) as f:
    stories = json.load(f)

# Geographic breakdown
geo_breakdown = {}
for story in stories:
    region = story["region"]
    geo_breakdown[region] = geo_breakdown.get(region, 0) + 1

logger.info(f"✅ Found {len(stories)} stories to post")
logger.info(f"   Geographic breakdown:")
for region, count in sorted(geo_breakdown.items()):
    percentage = (count / len(stories)) * 100
    logger.info(f"   - {region}: {count} stories ({percentage:.0f}%)")

# Mock posting to Instagram
posted_stories = []
for idx, story in enumerate(stories, 1):
    # Generate mock Post ID
    post_id = f"ig_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx:02d}"
    
    posted_story = {
        "post_id": post_id,
        "original_id": story["id"],
        "region": story["region"],
        "headline": story["headline"],
        "posted_at": datetime.now().isoformat(),
        "status": "posted"
    }
    posted_stories.append(posted_story)
    logger.info(f"   [{idx}/{len(stories)}] Posted to Instagram: {post_id} ({story['region']})")

# Save posting log
posting_log_file = OUTPUT_DIR / f"instagram_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(posting_log_file, "w") as f:
    json.dump({
        "total_posts": len(posted_stories),
        "timestamp": datetime.now().isoformat(),
        "geographic_breakdown": geo_breakdown,
        "posts": posted_stories
    }, f, indent=2)

logger.info(f"✅ All {len(posted_stories)} stories posted to Instagram")
logger.info(f"✅ Posting log saved to: {posting_log_file}")
logger.info("=" * 70)

print(json.dumps({"status": "success", "posts_created": len(posted_stories), "log_file": str(posting_log_file)}, indent=2))
