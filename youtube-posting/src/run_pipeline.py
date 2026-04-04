#!/usr/bin/env python3
"""
THE AI CHRONICLE — YouTube Pipeline Runner
Full pipeline: fetch news → generate video → upload to YouTube
Called by Windows Task Scheduler every hour.
Completely independent from the Instagram pipeline.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

ROOT_ENV = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ROOT_ENV)

PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR      = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(
            open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)
        ),
    ],
)
logger = logging.getLogger(__name__)

SRC = Path(__file__).parent


def main():
    logger.info("\n" + "=" * 60)
    logger.info(f"YOUTUBE PIPELINE START — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # ── Step 1: Fetch news ────────────────────────────────
    logger.info("\n[STEP 1] Fetching latest AI news (10 stories)...")
    try:
        sys.path.insert(0, str(SRC))
        from news_fetcher import fetch_todays_stories, FALLBACK_STORIES
        stories = fetch_todays_stories()
        if stories:
            logger.info(f"[OK] Fetched {len(stories)} live stories")
            for i, s in enumerate(stories, 1):
                logger.info(f"   {i}. {s.get('region','')} {s['headline']}")
        else:
            stories = FALLBACK_STORIES
            logger.warning(f"[WARN] Live fetch failed — using {len(stories)} fallback stories")
    except Exception as e:
        logger.error(f"[FAIL] News fetch error: {e}")
        sys.exit(1)

    # ── Step 2: Generate video ────────────────────────────
    logger.info("\n[STEP 2] Generating YouTube video...")
    try:
        from video_generator import generate
        result = generate(stories)
        logger.info(f"[OK] Video ready: {result['post_dir'].name}")
        # Read title from metadata txt (first non-empty line after "TITLE:")
        video_title = result['post_dir'].name
        try:
            meta_lines = result['metadata_txt'].read_text(encoding="utf-8").splitlines()
            for line in meta_lines:
                if line.startswith("TITLE:"):
                    video_title = line.replace("TITLE:", "").strip()
                    break
        except Exception:
            pass
        logger.info(f"[OK] Title: {video_title}")
    except Exception as e:
        logger.error(f"[FAIL] Video generation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

    # ── Step 3: Upload to YouTube ────────────────────────
    logger.info("\n[STEP 3] Uploading to YouTube...")
    try:
        from youtube_uploader import main as upload
        ok = upload()
        if not ok:
            logger.error("[FAIL] Upload returned False")
            sys.exit(1)
    except Exception as e:
        logger.error(f"[FAIL] Upload error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

    logger.info("\n" + "=" * 60)
    logger.info("YOUTUBE PIPELINE COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
