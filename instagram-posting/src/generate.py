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
LOG_FILE = LOG_DIR / f"generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load geographic mix configuration
with open(CONFIG_DIR / "geographic_mix.json") as f:
    geo_config = json.load(f)

logger.info("=" * 70)
logger.info("INSTAGRAM CONTENT GENERATION STARTED")
logger.info("=" * 70)

# Generate mock content following geographic mix
geo_mix = geo_config["geographic_mix"]
stories = []

# USA stories (30% - 3 stories)
for i in range(geo_mix["usa"]["target_count"]):
    stories.append({
        "id": f"usa_{i+1}",
        "region": "USA",
        "headline": f"AI Breakthrough #{i+1} from Silicon Valley",
        "content": f"USA-based AI technology news story #{i+1} focusing on latest innovations",
        "source": "https://techcrunch.com",
        "image": f"post_usa_{i+1}.png",
        "video": f"reel_usa_{i+1}.mp4"
    })

# India stories (30% - 3 stories)
for i in range(geo_mix["india"]["target_count"]):
    stories.append({
        "id": f"india_{i+1}",
        "region": "India",
        "headline": f"Indian AI Tech Innovation #{i+1}",
        "content": f"India-based AI and tech ecosystem news story #{i+1}",
        "source": "https://yourstory.com",
        "image": f"post_india_{i+1}.png",
        "video": f"reel_india_{i+1}.mp4"
    })

# China stories (20% - 2 stories)
for i in range(geo_mix["china"]["target_count"]):
    stories.append({
        "id": f"china_{i+1}",
        "region": "China",
        "headline": f"China AI Research Milestone #{i+1}",
        "content": f"China-based AI research and development news story #{i+1}",
        "source": "https://zhuanlan.zhihu.com",
        "image": f"post_china_{i+1}.png",
        "video": f"reel_china_{i+1}.mp4"
    })

# Rest of World stories (20% - 2 stories)
for i in range(geo_mix["rest_of_world"]["target_count"]):
    stories.append({
        "id": f"row_{i+1}",
        "region": "Rest of World",
        "headline": f"Global AI Trend #{i+1}",
        "content": f"International AI development news story #{i+1}",
        "source": "https://bbc.com/news",
        "image": f"post_row_{i+1}.png",
        "video": f"reel_row_{i+1}.mp4"
    })

# Save generated content
output_file = OUTPUT_DIR / f"generated_stories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, "w") as f:
    json.dump(stories, f, indent=2)

logger.info(f"✅ Generated {len(stories)} stories")
logger.info(f"   - USA: {geo_mix['usa']['target_count']} ({geo_mix['usa']['percentage']}%)")
logger.info(f"   - India: {geo_mix['india']['target_count']} ({geo_mix['india']['percentage']}%)")
logger.info(f"   - China: {geo_mix['china']['target_count']} ({geo_mix['china']['percentage']}%)")
logger.info(f"   - Rest of World: {geo_mix['rest_of_world']['target_count']} ({geo_mix['rest_of_world']['percentage']}%)")
logger.info(f"✅ Stories saved to: {output_file}")
logger.info("=" * 70)

print(json.dumps({"status": "success", "stories_generated": len(stories), "output_file": str(output_file)}, indent=2))
