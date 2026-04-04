#!/usr/bin/env python3
"""
THE AI CHRONICLE — Bulk Instagram Post Generator
Generates 20 posts: 60% global news (USA+China+ROW), 40% India news.
Uses real background images with dark scrim for text contrast.
Generate-only mode — no upload.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

ROOT_ENV = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ROOT_ENV)

PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"bulk_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


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
sys.path.insert(0, str(SRC))

# ── Config ────────────────────────────────────────────────────────────────────
TOTAL_POSTS = 20
# 40% India = 8, 60% global (6 USA + 3 China + 3 ROW) = 12
GEO_QUOTA = {"usa": 6, "india": 8, "china": 3, "row": 3}

BG_DIR  = PROJECT_ROOT / "backgrounds"
BG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".jfif"}


def _load_backgrounds() -> list:
    bgs = sorted([p for p in BG_DIR.iterdir()
                  if p.suffix.lower() in BG_EXTS and p.is_file()])
    logger.info(f"[BG] {len(bgs)} background images found in {BG_DIR.name}/")
    for b in bgs:
        logger.info(f"     {b.name}")
    return bgs


def main():
    logger.info("\n" + "=" * 65)
    logger.info("THE AI CHRONICLE — BULK INSTAGRAM POST GENERATOR")
    logger.info(f"Start : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Posts : {TOTAL_POSTS}  |  60% global / 40% India")
    logger.info(f"Quota : {GEO_QUOTA}")
    logger.info(f"Backgrounds: real images + dark scrim for text contrast")
    logger.info("=" * 65)

    # ── Step 1: Load backgrounds ──────────────────────────────────────
    backgrounds = _load_backgrounds()
    if not backgrounds:
        logger.error(f"[FAIL] No background images in {BG_DIR}")
        sys.exit(1)

    # ── Step 2: Fetch 20 stories ──────────────────────────────────────
    logger.info(f"\n[STEP 1] Fetching {TOTAL_POSTS} AI stories...")
    from news_fetcher import fetch_geo_balanced_stories
    stories = fetch_geo_balanced_stories(
        n=TOTAL_POSTS,
        save_dedup=True,
        geo_quota=GEO_QUOTA,
    )

    if len(stories) < TOTAL_POSTS:
        logger.warning(f"[WARN] Only {len(stories)} stories available "
                       f"(wanted {TOTAL_POSTS}) — continuing")

    logger.info(f"\n[OK] {len(stories)} stories fetched")

    # ── Step 3: Generate each post ────────────────────────────────────
    logger.info(f"\n[STEP 2] Generating {len(stories)} posts with background images...")
    from master_post_v2 import generate_post, generate_audio, generate_reel, create_caption

    results = []
    for i, story in enumerate(stories, 1):
        bg_path = backgrounds[(i - 1) % len(backgrounds)]
        region  = story.get("region_name", "?").upper()
        logger.info(f"\n── POST {i:02d}/{len(stories)} [{region}] "
                    f"{story['headline'][:55]}")
        logger.info(f"   BG: {bg_path.name}")
        try:
            result  = generate_post(story, bg_image_path=bg_path)
            audio   = generate_audio(story, result["post_dir"], result["slug"])
            reel    = generate_reel(result["png"], audio,
                                    result["post_dir"], result["slug"])
            caption = create_caption(story)

            cap_file = Path(result["post_dir"]) / f"{result['slug']}_caption.txt"
            cap_file.write_text(caption, encoding="utf-8")

            meta = {
                "timestamp":  datetime.now().isoformat(),
                "post_num":   i,
                "region":     story.get("region_name", "?"),
                "headline":   story["headline"],
                "company":    story["company"],
                "source":     story["source"],
                "bg_image":   str(bg_path),
                "png_file":   result["png"],
                "audio_file": audio,
                "reel_file":  reel,
                "caption":    caption,
            }
            meta_file = Path(result["post_dir"]) / f"{result['slug']}_metadata.json"
            meta_file.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            results.append(result)
            logger.info(f"   [OK] {Path(result['post_dir']).name}/")

        except Exception as e:
            import traceback
            logger.error(f"   [FAIL] Post {i} error: {e}")
            logger.error(traceback.format_exc())

    # ── Summary ───────────────────────────────────────────────────────
    logger.info("\n" + "=" * 65)
    logger.info("BULK GENERATION COMPLETE")
    logger.info("=" * 65)
    logger.info(f"Generated : {len(results)} / {len(stories)} posts")

    region_counts = {}
    for story in stories[:len(results)]:
        r = story.get("region_name", "?")
        region_counts[r] = region_counts.get(r, 0) + 1
    for r, c in sorted(region_counts.items()):
        pct = round(c / max(len(results), 1) * 100)
        logger.info(f"  {r.upper():6s}: {c:2d} posts  ({pct}%)")

    logger.info(f"\nOutput : {PROJECT_ROOT / 'instagram-output'}")
    logger.info(f"Log    : {LOG_FILE}")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
