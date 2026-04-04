import os
import json
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# ============================================================================
# PROJECT INITIALIZATION & VALIDATION
# ============================================================================

# Determine project root directory
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load environment variables from project-specific .env file
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    raise FileNotFoundError(f"Project .env file not found: {ENV_FILE}")

# ============================================================================
# CONFIGURATION & PATH SETUP
# ============================================================================

PROJECT_NAME = os.getenv("PROJECT_NAME", "youtube-posting")
API_KEY = os.getenv("API_KEY", "")

# Validate project is YouTube
if PROJECT_NAME != "youtube-posting":
    raise ValueError(
        f"❌ WRONG PROJECT! Expected 'youtube-posting', got '{PROJECT_NAME}'. "
        f"Please run from the correct project directory."
    )

# Define all project directories (relative to project root)
OUTPUT_DIR = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "output")
CONFIG_DIR = PROJECT_ROOT / os.getenv("CONFIG_DIR", "config")
LOG_DIR = PROJECT_ROOT / os.getenv("LOG_DIR", "logs")
SCHEDULE_DIR = PROJECT_ROOT / os.getenv("SCHEDULE_DIR", "schedules")

# Create all directories if they don't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
SCHEDULE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# LOGGING SETUP
# ============================================================================

LOG_FILE = LOG_DIR / f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# LOAD PROJECT CONFIGURATION
# ============================================================================

# Load general settings
settings_path = CONFIG_DIR / "settings.json"
settings = {}
if settings_path.exists():
    with open(settings_path, "r") as f:
        settings = json.load(f)
    logger.info(f"Settings loaded from {settings_path}")

# Load geographic mix configuration
geographic_mix_path = CONFIG_DIR / "geographic_mix.json"
geographic_mix = {}
if geographic_mix_path.exists():
    with open(geographic_mix_path, "r") as f:
        geographic_mix = json.load(f)
    logger.info(f"Geographic mix config loaded: {geographic_mix.get('project')} project")
    logger.info(f"Geographic distribution: USA {geographic_mix['geographic_mix']['usa']['percentage']}%, "
                f"India {geographic_mix['geographic_mix']['india']['percentage']}%, "
                f"Europe {geographic_mix['geographic_mix']['europe']['percentage']}%, "
                f"Asia-Pacific {geographic_mix['geographic_mix']['asia_pacific']['percentage']}%, "
                f"ROW {geographic_mix['geographic_mix']['rest_of_world']['percentage']}%")

# ============================================================================
# VALIDATION & SAFETY CHECKS
# ============================================================================

def validate_output_path(file_path: Path) -> bool:
    """Ensure output path is within project directory to prevent cross-project contamination."""
    try:
        file_path.resolve().relative_to(PROJECT_ROOT.resolve())
        return True
    except ValueError:
        logger.error(f"❌ SECURITY ERROR: File path {file_path} is outside project root {PROJECT_ROOT}")
        return False

# ============================================================================
# PROJECT INFORMATION
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("YOUTUBE POSTING PROJECT STARTED")
    logger.info("=" * 70)
    logger.info(f"Project Name: {PROJECT_NAME}")
    logger.info(f"Project Root: {PROJECT_ROOT.resolve()}")
    logger.info(f"Output Directory: {OUTPUT_DIR.resolve()}")
    logger.info(f"Config Directory: {CONFIG_DIR.resolve()}")
    logger.info(f"Logs Directory: {LOG_DIR.resolve()}")
    logger.info(f"Schedules Directory: {SCHEDULE_DIR.resolve()}")
    logger.info(f"Log File: {LOG_FILE}")
    logger.info("=" * 70)
    
    # Display configuration
    if settings:
        logger.info(f"Settings: {json.dumps(settings, indent=2)}")
    if geographic_mix:
        logger.info(f"Geographic Mix: {geographic_mix.get('project')} - Total videos: {geographic_mix.get('total_videos')}")
    
    logger.info("=" * 70)
    
    # ========================================================================
    # MAIN YOUTUBE POSTING LOGIC GOES HERE
    # ========================================================================
    
    logger.info("Ready to execute YouTube posting tasks...")
