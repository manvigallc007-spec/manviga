#!/usr/bin/env python3
"""
THE AI CHRONICLE — Improved YouTube Pipeline Runner
Full pipeline: fetch + score 10 stories → select top 5 → generate 5-min video → upload.
Logs story scores, geographic distribution, and video duration summary.
Retry on video generation failure (max 2 attempts).
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load root .env then local .env
ROOT_ENV  = Path(__file__).parent.parent.parent / ".env"
LOCAL_ENV = Path(__file__).parent.parent / ".env"
load_dotenv(ROOT_ENV)
load_dotenv(LOCAL_ENV)

PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR      = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


class UTFStreamHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(
            open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)
        )
    def emit(self, record):
        try:
            super().emit(record)
        except Exception:
            pass


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        UTFStreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

SRC = Path(__file__).parent


def _log_story_summary(stories: list):
    """Print a formatted table of story scores and regions."""
    logger.info("\n" + "─" * 72)
    logger.info(f"{'#':<3} {'Region':<8} {'Score':<7} {'Company':<22} Headline")
    logger.info("─" * 72)
    for i, s in enumerate(stories, 1):
        sc = s.get("score", {})
        total = sc.get("total", "N/A")
        logger.info(
            f"{i:<3} {s.get('region_name','?'):<8} {str(total):<7} "
            f"{s.get('company','?'):<22} {s.get('headline','?')}"
        )
    logger.info("─" * 72 + "\n")


def _log_geo_distribution(stories: list):
    """Log geographic distribution of selected stories."""
    counts = {}
    for s in stories:
        r = s.get("region_name", "unknown")
        counts[r] = counts.get(r, 0) + 1

    logger.info("[GEO] Geographic distribution of selected stories:")
    for region in ("usa", "india", "china", "row"):
        count = counts.get(region, 0)
        bar   = "█" * count
        logger.info(f"      {region.upper():6s}: {bar} ({count})")


def main():
    parser = argparse.ArgumentParser(description="The AI Chronicle — YouTube Pipeline")
    parser.add_argument(
        "--generate-only", action="store_true",
        help="Generate video only — skip YouTube upload"
    )
    parser.add_argument(
        "--region", type=str, default=None,
        help="Force all stories from one region: usa | india | china | row"
    )
    args, _ = parser.parse_known_args()
    generate_only = args.generate_only
    region_override = args.region.lower().strip() if args.region else None

    logger.info("\n" + "=" * 60)
    logger.info(f"THE AI CHRONICLE — IMPROVED YOUTUBE PIPELINE")
    logger.info(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Pipeline: youtube-improve  |  10 stories  |  ~10-min video")
    if generate_only:
        logger.info("Mode: GENERATE ONLY (no upload)")
    if region_override:
        logger.info(f"Region: 100% {region_override.upper()} stories")
    logger.info("=" * 60)

    sys.path.insert(0, str(SRC))

    # ── Step 1: Fetch + score 10 stories, select top 5 ───────────
    logger.info("\n[STEP 1] Fetching 10 geo-balanced AI stories...")
    try:
        from news_fetcher import fetch_todays_stories, FALLBACK_STORIES

        geo_quota = {region_override: 10} if region_override else None
        stories = fetch_todays_stories(geo_quota=geo_quota)

        if not stories:
            logger.warning("[WARN] Live fetch returned empty — using fallback stories")
            stories = FALLBACK_STORIES[:10]

        logger.info(f"\n[OK] {len(stories)} stories selected for video:")
        _log_story_summary(stories)
        _log_geo_distribution(stories)

    except Exception as e:
        logger.error(f"[FAIL] News fetch error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.warning("[WARN] Falling back to hardcoded fallback stories...")
        try:
            from news_fetcher import FALLBACK_STORIES
            stories = FALLBACK_STORIES[:10]
        except Exception as e2:
            logger.error(f"[FAIL] Could not load fallback stories: {e2}")
            sys.exit(1)

    if len(stories) < 10:
        logger.error(f"[FAIL] Need 10 stories, only have {len(stories)}")
        sys.exit(1)

    stories = stories[:10]  # Ensure exactly 10

    # ── Step 2: Generate video (retry up to 2 times) ─────────────
    logger.info("\n[STEP 2] Generating ~10-minute YouTube video...")
    result = None
    for attempt in range(1, 3):  # max 2 attempts
        try:
            from video_generator import generate
            result = generate(stories)
            dur = result.get("duration_secs", 0)
            logger.info(f"[OK] Video generated: {result['video'].name}")
            logger.info(f"[OK] Duration: {dur:.1f}s ({dur / 60:.1f} min)")
            logger.info(f"[OK] Thumbnail A: {result['thumbnail_a'].name}")
            logger.info(f"[OK] Thumbnail B: {result['thumbnail_b'].name}")
            break  # success
        except Exception as e:
            logger.error(f"[FAIL] Video generation attempt {attempt} failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            if attempt < 2:
                logger.info("[RETRY] Retrying video generation...")
            else:
                logger.error("[FAIL] Both video generation attempts failed.")
                sys.exit(1)

    if not result:
        logger.error("[FAIL] No video result after retries.")
        sys.exit(1)

    # Read title for logging
    video_title = result["video"].stem
    try:
        lines = result["metadata_txt"].read_text(encoding="utf-8").splitlines()
        for line in lines:
            if line.startswith("TITLE:"):
                video_title = line.replace("TITLE:", "").strip()
                break
    except Exception:
        pass
    logger.info(f"[OK] Video title: {video_title}")

    # ── Step 3: Upload to YouTube ─────────────────────────────────
    if generate_only:
        logger.info("\n[STEP 3] Upload skipped (--generate-only mode)")
    else:
        logger.info("\n[STEP 3] Uploading to YouTube...")
        try:
            from youtube_uploader import main as upload
            ok = upload()
            if not ok:
                logger.error("[FAIL] Upload returned False — check credentials and retry")
                sys.exit(1)
        except Exception as e:
            logger.error(f"[FAIL] Upload error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)

    # ── Summary ───────────────────────────────────────────────────
    dur = result.get("duration_secs", 0)
    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE COMPLETE — SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Date     : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"Title    : {video_title}")
    logger.info(f"Duration : {dur:.1f}s ({dur / 60:.1f} min)")
    logger.info(f"Stories  : {len(stories)}")
    logger.info("")
    logger.info("Stories used:")
    _log_story_summary(stories)
    logger.info("Geographic breakdown:")
    _log_geo_distribution(stories)
    logger.info("")
    logger.info(f"Log file : {LOG_FILE}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
