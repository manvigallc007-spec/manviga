#!/usr/bin/env python3
"""
THE AI CHRONICLE — Improved YouTube Uploader (youtube-improve edition)
Uploads 5-minute MP4 as a regular YouTube video (not Shorts).
Reads credentials from youtube-improve/credentials/.
Retry logic: 3 attempts with exponential backoff (5s, 15s, 30s).
Saves both thumbnail A and B paths in upload_result.json.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load root .env (ANTHROPIC_API_KEY, etc.) then local .env
ROOT_ENV  = Path(__file__).parent.parent.parent / ".env"
LOCAL_ENV = Path(__file__).parent.parent / ".env"
load_dotenv(ROOT_ENV)
load_dotenv(LOCAL_ENV)

PROJECT_ROOT    = Path(__file__).parent.parent
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"
CLIENT_SECRET   = CREDENTIALS_DIR / "client_secret.json"
TOKEN_FILE      = CREDENTIALS_DIR / "token.json"
OUTPUT_DIR      = PROJECT_ROOT / "output"
LOG_DIR         = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"youtube_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

CATEGORY_SCIENCE_TECH = "28"  # Science & Technology

MAX_RETRIES   = 3
RETRY_BACKOFF = [5, 15, 30]   # seconds between retries


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
        UTFStreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# CREDENTIALS CHECK
# ─────────────────────────────────────────────

def check_credentials() -> bool:
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

    if not CLIENT_SECRET.exists():
        logger.error("[FAIL] client_secret.json not found in youtube-improve/credentials/")
        logger.error(f"[FIX]  Expected at: {CLIENT_SECRET}")
        logger.error("[FIX]  Steps to get credentials:")
        logger.error("[FIX]  1. Go to console.cloud.google.com")
        logger.error("[FIX]  2. Create project → Enable YouTube Data API v3")
        logger.error("[FIX]  3. Credentials → Create OAuth 2.0 Client ID (Desktop app)")
        logger.error("[FIX]  4. Download JSON → rename to client_secret.json")
        logger.error(f"[FIX]  5. Place file at: {CLIENT_SECRET}")
        logger.error("[FIX]  NOTE: This is separate from youtube-posting credentials.")
        return False
    logger.info(f"[AUTH] Found client_secret.json at {CLIENT_SECRET}")
    return True


# ─────────────────────────────────────────────
# OAUTH
# ─────────────────────────────────────────────

def get_youtube_service():
    """Authenticate with YouTube Data API v3 using OAuth 2.0."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        logger.info("[AUTH] Loaded saved OAuth credentials")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("[AUTH] Refreshing expired token...")
            creds.refresh(Request())
            logger.info("[AUTH] Token refreshed successfully")
        else:
            logger.info("[AUTH] Starting OAuth flow — browser will open...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
            logger.info("[AUTH] OAuth completed successfully")

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        logger.info(f"[AUTH] Token saved: {TOKEN_FILE}")

    return build("youtube", "v3", credentials=creds)


# ─────────────────────────────────────────────
# AUTO-DISCOVER LATEST POST
# ─────────────────────────────────────────────

def find_latest_post() -> dict | None:
    """Find the most recent output directory and extract video + metadata."""
    if not OUTPUT_DIR.exists():
        logger.error(f"[FAIL] Output directory not found: {OUTPUT_DIR}")
        return None

    dirs = sorted([d for d in OUTPUT_DIR.iterdir() if d.is_dir()
                   and not d.name.startswith(".")], reverse=True)
    if not dirs:
        logger.error("[FAIL] No post subdirectories found in output/")
        return None

    post_dir = dirs[0]
    logger.info(f"[FIND] Latest post directory: {post_dir.name}")

    # Find files
    mp4       = next(post_dir.glob("*.mp4"),               None)
    thumb_a   = next(post_dir.glob("*_thumbnail_a.png"),   None)
    thumb_b   = next(post_dir.glob("*_thumbnail_b.png"),   None)
    meta_json = next(post_dir.glob("yt_metadata.json"),    None)
    meta_txt  = next(post_dir.glob("yt_meta.txt"),         None)

    if not mp4:
        logger.error(f"[FAIL] No MP4 found in {post_dir.name}")
        return None

    # Read metadata
    title = post_dir.name
    description = ""
    tags = []
    stories = []

    if meta_txt and meta_txt.exists():
        try:
            lines = meta_txt.read_text(encoding="utf-8").splitlines()
            for line in lines:
                if line.startswith("TITLE:"):
                    title = line.replace("TITLE:", "").strip()
                    break
        except Exception as e:
            logger.warning(f"[WARN] Could not read yt_meta.txt: {e}")

    if meta_json and meta_json.exists():
        try:
            with open(meta_json, encoding="utf-8") as f:
                meta = json.load(f)
            description = meta.get("description", "")
            tags        = meta.get("youtube_tags", [])
            stories     = meta.get("stories", [])
            # Use title from JSON if better
            if meta.get("title") and len(meta["title"]) > 5:
                title = meta["title"]
        except Exception as e:
            logger.warning(f"[WARN] Could not read yt_metadata.json: {e}")

    # Log what we found
    for label, f in [("MP4", mp4), ("Thumbnail A", thumb_a), ("Thumbnail B", thumb_b)]:
        if f:
            size_kb = f.stat().st_size / 1024
            logger.info(f"[OK]   {label}: {f.name} ({size_kb:.1f} KB)")
        else:
            logger.warning(f"[WARN] {label}: not found")

    logger.info(f"[OK]   Title: {title}")

    return {
        "dir":         post_dir,
        "mp4":         mp4,
        "thumb_a":     thumb_a,
        "thumb_b":     thumb_b,
        "title":       title,
        "description": description,
        "tags":        tags,
        "stories":     stories,
    }


# ─────────────────────────────────────────────
# UPLOAD WITH RETRY
# ─────────────────────────────────────────────

def upload_video(youtube, mp4_path: Path, title: str, description: str,
                 tags: list) -> str | None:
    """
    Upload video to YouTube with retry logic (3 attempts, exponential backoff).
    This is a regular 5-minute video (NOT a Short — no #Shorts tag).
    Returns video_id on success, None on failure.
    """
    from googleapiclient.http import MediaFileUpload

    logger.info("\n" + "=" * 60)
    logger.info("Uploading to YouTube (regular video, not Shorts)")
    logger.info("=" * 60)
    logger.info(f"Title      : {title}")
    logger.info(f"File       : {mp4_path.name} ({mp4_path.stat().st_size / 1024 / 1024:.1f} MB)")
    logger.info(f"Tags       : {tags[:8]}...")

    # Build request body — do NOT add #Shorts
    body = {
        "snippet": {
            "title":       title[:100],
            "description": description[:5000],
            "tags":        tags[:500],
            "categoryId":  CATEGORY_SCIENCE_TECH,
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False,
        }
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[UPLOAD] Attempt {attempt}/{MAX_RETRIES}...")

            media = MediaFileUpload(
                str(mp4_path),
                mimetype="video/mp4",
                resumable=True,
                chunksize=8 * 1024 * 1024,  # 8 MB chunks
            )

            request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    pct = int(status.progress() * 100)
                    logger.info(f"[UPLOAD] {pct}% uploaded...")

            video_id = response.get("id")
            if video_id:
                logger.info(f"[OK] Upload successful! Video ID: {video_id}")
                logger.info(f"[OK] URL: https://www.youtube.com/watch?v={video_id}")
                return video_id
            else:
                logger.error(f"[FAIL] Upload response missing ID: {response}")
                raise ValueError(f"No video ID in response: {response}")

        except Exception as e:
            logger.error(f"[FAIL] Upload attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF[attempt - 1]
                logger.info(f"[RETRY] Waiting {wait}s before retry {attempt + 1}...")
                time.sleep(wait)
            else:
                logger.error(f"[FAIL] All {MAX_RETRIES} upload attempts exhausted.")
                return None

    return None


# ─────────────────────────────────────────────
# SET THUMBNAIL
# ─────────────────────────────────────────────

def set_thumbnail(youtube, video_id: str, thumb_path: Path) -> bool:
    """Upload and set the video thumbnail. Returns True on success."""
    from googleapiclient.http import MediaFileUpload
    try:
        media = MediaFileUpload(str(thumb_path), mimetype="image/png")
        youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
        logger.info(f"[OK] Thumbnail set: {thumb_path.name}")
        return True
    except Exception as e:
        logger.warning(f"[WARN] Thumbnail upload failed: {e}")
        logger.warning("[WARN] You can set the thumbnail manually in YouTube Studio.")
        return False


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main() -> bool:
    logger.info("\n" + "=" * 60)
    logger.info("THE AI CHRONICLE — YOUTUBE UPLOADER (youtube-improve)")
    logger.info("Regular 5-minute video  •  Category: Science & Technology")
    logger.info("=" * 60)

    if not check_credentials():
        return False

    post = find_latest_post()
    if not post:
        return False

    try:
        youtube = get_youtube_service()
    except Exception as e:
        logger.error(f"[FAIL] YouTube auth failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    # Upload video
    video_id = upload_video(
        youtube,
        post["mp4"],
        post["title"],
        post["description"],
        post["tags"],
    )

    if not video_id:
        return False

    # Set thumbnail A (primary)
    thumb_set = False
    if post["thumb_a"]:
        thumb_set = set_thumbnail(youtube, video_id, post["thumb_a"])
    elif post["thumb_b"]:
        logger.warning("[WARN] Thumbnail A not found, trying B...")
        thumb_set = set_thumbnail(youtube, video_id, post["thumb_b"])

    # Save upload result
    result = {
        "timestamp":    datetime.now().isoformat(),
        "video_id":     video_id,
        "url":          f"https://www.youtube.com/watch?v={video_id}",
        "title":        post["title"],
        "thumbnail_a":  str(post["thumb_a"]) if post["thumb_a"] else None,
        "thumbnail_b":  str(post["thumb_b"]) if post["thumb_b"] else None,
        "thumbnail_set": thumb_set,
        "pipeline":     "youtube-improve",
    }
    result_file = post["dir"] / "upload_result.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(f"\n[OK] Result saved: {result_file}")
    logger.info(f"[OK] Video URL: {result['url']}")
    logger.info("\n" + "=" * 60)
    logger.info("UPLOAD COMPLETE")
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    try:
        ok = main()
        sys.exit(0 if ok else 1)
    except Exception as e:
        logger.error(f"[FAIL] Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
