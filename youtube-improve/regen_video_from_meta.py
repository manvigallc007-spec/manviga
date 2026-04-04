#!/usr/bin/env python3
"""
Regenerate video from existing yt_metadata.json — fixes TTS region mentions
and rebuilds video without re-fetching RSS news.

Usage: python regen_video_from_meta.py [path/to/yt_metadata.json]
Default: most recent output folder today.
"""
import json
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent / "src"))

from news_fetcher import (
    _generate_tts, _detect_region, _split_sentences,
    STORY_TRANSITIONS, REGION_EMOJI,
)

# ── Find metadata ────────────────────────────────────────────────────────────
if len(sys.argv) > 1:
    meta_path = Path(sys.argv[1])
else:
    out_root = Path(__file__).parent / "output"
    candidates = sorted(
        [d for d in out_root.iterdir() if d.is_dir() and (d / "yt_metadata.json").exists()],
        key=lambda d: d.name,
        reverse=True,
    )
    # Use the most recent run (skip test folders)
    meta_path = next(
        (d / "yt_metadata.json" for d in candidates if not d.name.startswith("test")),
        None,
    )
    if not meta_path:
        print("No yt_metadata.json found in output/")
        sys.exit(1)

logger.info(f"Loading: {meta_path}")
with open(meta_path, encoding="utf-8") as f:
    meta = json.load(f)

stories = meta["stories"]
date_str = meta["date_str"]

# ── Rebuild TTS scripts with correct region + varied transitions ─────────────
for i, story in enumerate(stories):
    title   = story["headline"]
    summary = story.get("summary", "")
    company = story.get("company", "")
    # Re-detect region from content
    feed_region  = story.get("region_name", "row")
    region_name  = _detect_region(title, summary, feed_region)
    story["region_name"] = region_name
    story["region"]      = REGION_EMOJI.get(region_name, "🌐")

    new_tts = _generate_tts(title, summary, company, region_name, story_index=i)
    old_tts = story.get("tts_script", "")
    story["tts_script"] = new_tts

    logger.info(f"Story {i+1}: [{region_name}] {title[:60]}")
    logger.info(f"  OLD TTS: {old_tts[:80]}...")
    logger.info(f"  NEW TTS: {new_tts[:80]}...")

# ── Regenerate video ─────────────────────────────────────────────────────────
from video_generator import generate

logger.info("\nRegenerating video...")
result = generate(stories)

logger.info(f"\nVideo : {result['video']}")
logger.info(f"Duration: {result['duration_secs']:.1f}s ({result['duration_secs']/60:.1f} min)")
logger.info(f"Thumb A: {result['thumbnail_a']}")
logger.info(f"Thumb B: {result['thumbnail_b']}")
