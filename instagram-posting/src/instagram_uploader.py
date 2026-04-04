#!/usr/bin/env python3
"""
Instagram Graph API Uploader — Feed Post + Reel
Auto-discovers latest post subdirectory from output/
"""

import os
import sys
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ============================================================================
# SETUP
# ============================================================================

ROOT_ENV = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ROOT_ENV)

IG_USER_ID      = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
FB_PAGE_TOKEN   = os.getenv("FB_PAGE_TOKEN")
IG_API_VERSION  = "v18.0"
IG_BASE_URL     = f"https://graph.facebook.com/{IG_API_VERSION}"

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR   = PROJECT_ROOT / "output"
LOG_DIR      = PROJECT_ROOT / "logs"

LOG_FILE = LOG_DIR / f"instagram_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        UTFStreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DISCOVER LATEST POST
# ============================================================================

def find_latest_post():
    """Find most recent timestamped post subdirectory and its files"""
    dirs = sorted(
        [d for d in OUTPUT_DIR.iterdir() if d.is_dir()],
        reverse=True
    )
    if not dirs:
        logger.error("[FAIL] No post subdirectories found in output/")
        return None

    post_dir = dirs[0]
    logger.info(f"[OK] Latest post directory: {post_dir.name}")

    png  = next(post_dir.glob("*.png"),  None)
    mp4  = next(post_dir.glob("*.mp4"),  None)
    mp3  = next(post_dir.glob("*.mp3"),  None)
    cap  = next(post_dir.glob("*_caption.txt"), None)
    meta = next(post_dir.glob("*_metadata.json"), None)

    for label, f in [("PNG", png), ("MP4", mp4), ("MP3", mp3), ("Caption", cap)]:
        if f:
            logger.info(f"[OK] {label}: {f.name} ({f.stat().st_size / 1024:.1f} KB)")
        else:
            logger.warning(f"[WARN] {label}: not found in {post_dir.name}")

    caption = cap.read_text(encoding="utf-8").strip() if cap else "The AI Chronicle — Daily AI News"

    return {
        "dir":     post_dir,
        "png":     png,
        "mp4":     mp4,
        "mp3":     mp3,
        "caption": caption,
        "meta":    meta,
    }

# ============================================================================
# API HELPERS
# ============================================================================

def validate_credentials():
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        logger.error("[FAIL] IG_USER_ID or IG_ACCESS_TOKEN missing from root .env")
        return False
    logger.info(f"[OK] IG_USER_ID: {IG_USER_ID}")
    logger.info(f"[OK] Token: {IG_ACCESS_TOKEN[:30]}...")
    return True


def test_api_connection():
    """Verify token and return account username"""
    url = (f"{IG_BASE_URL}/{IG_USER_ID}"
           f"?fields=username,name&access_token={IG_ACCESS_TOKEN}")
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if r.status_code == 200:
            logger.info(f"[OK] Connected: @{data.get('username')} — {data.get('name')}")
            return True
        err = data.get("error", {})
        logger.error(f"[FAIL] API {r.status_code}: {err.get('message', r.text)}")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Connection error: {e}")
        return False


def _wait_for_media(media_id, max_wait=120):
    """Poll until media container is FINISHED or READY"""
    url = (f"{IG_BASE_URL}/{media_id}"
           f"?fields=status_code,status&access_token={IG_ACCESS_TOKEN}")
    for _ in range(max_wait // 5):
        time.sleep(5)
        r = requests.get(url, timeout=10)
        body = r.json()
        status = body.get("status_code") or body.get("status", "")
        logger.info(f"[INFO] Media status: {status}")
        if status in ("FINISHED", "READY"):
            return True
        if status == "ERROR":
            logger.error("[FAIL] Media processing failed")
            return False
    # Attempt publish anyway after timeout
    logger.warning("[WARN] Timed out polling — attempting publish anyway")
    return True


def publish_container(media_id):
    """Publish a ready media container"""
    url = f"{IG_BASE_URL}/{IG_USER_ID}/media_publish"
    r = requests.post(url, data={
        "creation_id": media_id,
        "access_token": IG_ACCESS_TOKEN
    }, timeout=15)
    if r.status_code == 200:
        post_id = r.json().get("id")
        logger.info(f"[OK] Published! Post ID: {post_id}")
        return post_id
    logger.error(f"[FAIL] Publish failed {r.status_code}: {r.text}")
    return None

# ============================================================================
# UPLOAD: REEL to Instagram (resumable upload)
# ============================================================================

def upload_reel(mp4_path, caption):
    """Upload MP4 as Instagram Reel using resumable upload API"""
    logger.info("\n" + "=" * 60)
    logger.info("Uploading Reel")
    logger.info("=" * 60)

    file_size = mp4_path.stat().st_size

    # 1. Initialise upload session
    init_url = f"{IG_BASE_URL}/{IG_USER_ID}/media"
    r = requests.post(init_url, data={
        "media_type":   "REELS",
        "caption":      caption,
        "access_token": IG_ACCESS_TOKEN,
        "upload_type":  "resumable",
    }, timeout=15)

    if r.status_code != 200 or "id" not in r.json():
        logger.error(f"[FAIL] Init upload session {r.status_code}: {r.text}")
        return None

    media_id   = r.json()["id"]
    upload_url = r.json().get("uri") or r.json().get("upload_url")
    logger.info(f"[OK] Upload session: {media_id}")

    if not upload_url:
        logger.error("[FAIL] No upload URL returned from session init")
        return None

    # 2. Upload video bytes
    with open(mp4_path, "rb") as f:
        video_data = f.read()

    up = requests.post(upload_url, headers={
        "Authorization":         f"OAuth {IG_ACCESS_TOKEN}",
        "Content-Type":          "application/octet-stream",
        "offset":                "0",
        "file_size":             str(file_size),
    }, data=video_data, timeout=120)

    if up.status_code not in (200, 201):
        logger.error(f"[FAIL] Video upload {up.status_code}: {up.text}")
        return None
    logger.info("[OK] Video bytes uploaded")

    # 3. Wait for processing
    if not _wait_for_media(media_id):
        return None

    # 4. Publish
    post_id = publish_container(media_id)
    return post_id

# ============================================================================
# CROSS-POST: Facebook Page video upload (requires pages_manage_posts scope)
# ============================================================================

FB_PAGE_ID = os.getenv("FB_PAGE_ID")

def upload_to_facebook_page(mp4_path, caption):
    """
    Post the MP4 directly to the connected Facebook Page.
    Requires the access token to have pages_manage_posts scope.
    If missing: regenerate token at developers.facebook.com/tools/explorer
    and add pages_manage_posts permission.
    """
    logger.info("\n" + "=" * 60)
    logger.info("Cross-posting to Facebook Page")
    logger.info("=" * 60)

    with open(mp4_path, "rb") as f:
        r = requests.post(
            f"{IG_BASE_URL}/{FB_PAGE_ID}/videos",
            files={"source": ("reel.mp4", f, "video/mp4")},
            data={"description": caption, "access_token": FB_PAGE_TOKEN},
            timeout=120,
        )

    if r.status_code == 200:
        fb_id = r.json().get("id")
        logger.info(f"[OK] Facebook video published! ID: {fb_id}")
        logger.info(f"[OK] https://www.facebook.com/video/{fb_id}/")
        return fb_id

    err = r.json().get("error", {})
    if "pages_manage_posts" in err.get("message", ""):
        logger.error("[FAIL] Token missing pages_manage_posts scope.")
        logger.error("[FIX]  Regenerate token at: developers.facebook.com/tools/explorer")
        logger.error("[FIX]  Add permissions: pages_manage_posts + pages_read_engagement")
        logger.error("[FIX]  Update IG_ACCESS_TOKEN in root .env")
    else:
        logger.error(f"[FAIL] Facebook upload {r.status_code}: {r.text}")
    return None

# ============================================================================
# MAIN
# ============================================================================

def main():
    logger.info("\n" + "=" * 60)
    logger.info("THE AI CHRONICLE — INSTAGRAM UPLOADER")
    logger.info("=" * 60)

    if not validate_credentials():
        return False

    post = find_latest_post()
    if not post:
        return False

    if not test_api_connection():
        return False

    caption = post["caption"]
    results = {"timestamp": datetime.now().isoformat(), "instagram_reel": None, "facebook_video": None}

    if not post["mp4"]:
        logger.warning("[SKIP] No MP4 found")
        return False

    # 1. Instagram Reel
    reel_id = upload_reel(post["mp4"], caption)
    results["instagram_reel"] = reel_id
    if reel_id:
        logger.info(f"[OK] Instagram Reel live: https://www.instagram.com/reel/{reel_id}/")

    # Save result alongside post files
    result_file = post["dir"] / "upload_result.json"
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"[OK] Result saved: {result_file}")

    logger.info("\n" + "=" * 60)
    logger.info("DONE")
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        logger.error(f"[FAIL] {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
