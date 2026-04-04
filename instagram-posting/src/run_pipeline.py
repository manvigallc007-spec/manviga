#!/usr/bin/env python3
"""
THE AI CHRONICLE — Instagram Daily Pipeline
Runs once at 9 AM. Fetches 10 geo-balanced AI stories (RSS, free).
Generates and uploads 10 posts: 3 USA · 3 India · 2 China · 2 ROW.
"""

import sys
import time
import logging
import threading
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

ROOT_ENV  = Path(__file__).parent.parent.parent / ".env"
LOCAL_ENV = Path(__file__).parent.parent / ".env"
load_dotenv(ROOT_ENV)
load_dotenv(LOCAL_ENV)

ROOT    = Path(__file__).parent.parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


class UTFStreamHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(
            open(sys.stdout.fileno(), mode='w', encoding='utf-8',
                 errors='replace', closefd=False)
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

UPLOAD_DELAY_SECS = 90   # wait between uploads to avoid Instagram rate limits


def main():
    parser = argparse.ArgumentParser(description="The AI Chronicle — Instagram Pipeline")
    parser.add_argument(
        "--generate-only", action="store_true",
        help="Generate content only — skip Instagram upload"
    )
    args, _ = parser.parse_known_args()
    generate_only = args.generate_only

    # Run-level timestamped output directory (all posts for this run go inside it)
    run_ts = datetime.now().strftime("%A_%Y-%m-%d_%H%M%S")
    ROOT = Path(__file__).parent.parent
    run_output_dir = ROOT / "instagram-output" / run_ts
    run_output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("\n" + "=" * 65)
    logger.info("THE AI CHRONICLE — DAILY INSTAGRAM PIPELINE")
    logger.info(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("10 geo-balanced AI stories | 3 USA · 3 India · 2 China · 2 ROW")
    if generate_only:
        logger.info("Mode: GENERATE ONLY (no upload)")
    logger.info(f"Output dir: instagram-output/{run_ts}/")
    logger.info("=" * 65)

    sys.path.insert(0, str(SRC))

    # ── Step 1: Fetch 10 geo-balanced stories ─────────────────────
    logger.info("\n[STEP 1] Fetching 10 geo-balanced AI stories from RSS feeds...")
    try:
        from news_fetcher import fetch_geo_balanced_stories, FALLBACK_STORIES
        stories = fetch_geo_balanced_stories(n=10, save_dedup=not generate_only)
        if not stories:
            logger.warning("[WARN] No stories returned — using fallback")
            stories = FALLBACK_STORIES[:10]
    except Exception as e:
        logger.error(f"[FAIL] News fetch error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            from news_fetcher import FALLBACK_STORIES
            stories = FALLBACK_STORIES[:10]
        except Exception:
            logger.error("[FAIL] Could not load fallback stories")
            sys.exit(1)

    if len(stories) < 1:
        logger.error("[FAIL] No stories available")
        sys.exit(1)

    stories = stories[:10]
    logger.info(f"[OK] {len(stories)} stories ready")

    # ── Step 2: Generate + upload each post ───────────────────────
    logger.info("\n[STEP 2] Generating and uploading posts...")

    import master_post_v2
    # Redirect all post output to the run-level timestamped directory
    master_post_v2.OUTPUT_DIR = run_output_dir
    from master_post_v2 import generate_post, generate_audio, generate_reel, create_caption

    if generate_only:
        upload_enabled = False
        logger.info("[INFO] Upload skipped (--generate-only mode)")
    else:
        from instagram_uploader import validate_credentials, test_api_connection, upload_reel

        # Validate credentials once before starting
        if not validate_credentials():
            logger.error("[FAIL] Instagram credentials missing — posts will be generated but not uploaded")
            upload_enabled = False
        elif not test_api_connection():
            logger.error("[FAIL] Instagram API connection failed — posts will be generated but not uploaded")
            upload_enabled = False
        else:
            upload_enabled = True
            logger.info("[OK] Instagram API connected")

    results = []
    for i, story in enumerate(stories, 1):
        logger.info(f"\n{'─' * 65}")
        region_flag = story.get('region', '')
        logger.info(f"[POST {i:02d}/10] {region_flag} {story['company']} — {story['headline']}")
        logger.info(f"{'─' * 65}")

        try:
            # Generate image
            result   = generate_post(story)
            slug     = result['slug']
            post_dir = result['post_dir']

            # Generate audio (edge-tts)
            audio_path = generate_audio(story, post_dir, slug)

            # Generate video reel
            reel_path = generate_reel(result['png'], audio_path, post_dir, slug)

            # Build and save caption
            caption = create_caption(story)
            cap_file = Path(post_dir) / f"{slug}_caption.txt"
            cap_file.write_text(caption, encoding="utf-8")

            post_result = {
                "index":    i,
                "story":    story["headline"],
                "region":   story.get("region_name", "?"),
                "company":  story["company"],
                "post_dir": post_dir,
                "reel":     reel_path,
                "caption":  caption,
                "uploaded": False,
                "reel_id":  None,
            }

            # Upload
            if upload_enabled and reel_path:
                logger.info(f"[UPLOAD] Uploading post {i}/10 to Instagram...")
                reel_id = upload_reel(Path(reel_path), caption)
                if reel_id:
                    post_result["uploaded"] = True
                    post_result["reel_id"]  = reel_id
                    logger.info(f"[OK] Post {i}/10 live: https://www.instagram.com/reel/{reel_id}/")
                else:
                    logger.error(f"[FAIL] Upload failed for post {i}/10")

                # Wait between uploads to respect Instagram rate limits
                if i < len(stories):
                    logger.info(f"[WAIT] Pausing {UPLOAD_DELAY_SECS}s before next upload...")
                    time.sleep(UPLOAD_DELAY_SECS)
            else:
                logger.info(f"[SKIP] Upload disabled — post saved to {Path(post_dir).name}")

            results.append(post_result)

        except Exception as e:
            logger.error(f"[FAIL] Post {i}/10 failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            results.append({
                "index": i, "story": story["headline"],
                "region": story.get("region_name", "?"),
                "company": story["company"],
                "error": str(e), "uploaded": False,
            })

    # ── Summary ───────────────────────────────────────────────────
    uploaded  = [r for r in results if r.get("uploaded")]
    generated = [r for r in results if "reel" in r]
    failed    = [r for r in results if "error" in r]

    logger.info("\n" + "=" * 65)
    logger.info("DAILY PIPELINE COMPLETE — SUMMARY")
    logger.info("=" * 65)
    logger.info(f"Date      : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"Generated : {len(generated)}/10")
    logger.info(f"Uploaded  : {len(uploaded)}/10")
    logger.info(f"Failed    : {len(failed)}")
    logger.info("")

    # Geo breakdown
    geo = {}
    for r in results:
        reg = r.get("region", "?")
        geo[reg] = geo.get(reg, 0) + 1
    logger.info("Geographic breakdown:")
    for region, count in sorted(geo.items()):
        logger.info(f"  {region.upper():6s}: {'█' * count} ({count})")

    logger.info("")
    logger.info("Posts:")
    for r in results:
        status = "OK" if r.get("uploaded") else ("GEN" if "reel" in r else "ERR")
        hl = r['story'].encode('ascii', errors='replace').decode('ascii')
        logger.info(f"  [{status}] [{r.get('region','?'):6s}] {r.get('company','?'):<20} {hl}")

    logger.info("")
    logger.info(f"Log : {LOG_FILE}")
    logger.info("=" * 65)

    # ── Step 3: Schedule Google Drive transfer in 5 minutes ───────
    generated_dirs = [
        Path(r["post_dir"]) for r in results if "post_dir" in r
    ]
    if generated_dirs:
        logger.info(f"\n[GDRIVE] Transfer scheduled in 5 minutes for "
                    f"{len(generated_dirs)} directories...")

        def _run_gdrive_transfer():
            transfer_logger = logging.getLogger("gdrive_transfer")
            transfer_logger.info("[GDRIVE] Starting scheduled Google Drive transfer...")
            try:
                from google_drive_uploader import transfer_post_directory
                transferred, failed = 0, 0
                for d in generated_dirs:
                    # Re-resolve path in case it was renamed to transferred_*
                    actual = d if d.exists() else d.parent / f"transferred_{d.name}"
                    if actual.exists() and not actual.name.startswith("transferred_"):
                        ok = transfer_post_directory(actual)
                        if ok:
                            transferred += 1
                        else:
                            failed += 1
                transfer_logger.info(
                    f"[GDRIVE] Complete: {transferred} transferred, {failed} failed"
                )
            except FileNotFoundError as e:
                transfer_logger.error(str(e))
            except Exception as e:
                transfer_logger.error(f"[GDRIVE] Transfer error: {e}")
                import traceback
                transfer_logger.error(traceback.format_exc())

        timer = threading.Timer(300, _run_gdrive_transfer)   # 300s = 5 minutes
        timer.daemon = True
        timer.start()
        logger.info("[GDRIVE] Timer started — transfer will begin at "
                    f"{datetime.now().strftime('%H:%M:%S')} + 5 min")


if __name__ == "__main__":
    main()
