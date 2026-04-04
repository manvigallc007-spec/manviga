#!/usr/bin/env python3
"""
THE AI CHRONICLE — YouTube Data API v3 Uploader
Uploads MP4 as a YouTube Short with title, description, tags, and thumbnail.
Uses OAuth 2.0 with persistent token refresh.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

ROOT_ENV = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ROOT_ENV)

PROJECT_ROOT     = Path(__file__).parent.parent
CREDENTIALS_DIR  = PROJECT_ROOT / "credentials"
CLIENT_SECRET    = CREDENTIALS_DIR / "client_secret.json"
TOKEN_FILE       = CREDENTIALS_DIR / "token.json"
OUTPUT_DIR       = PROJECT_ROOT / "output"
LOG_DIR          = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"youtube_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

CATEGORY_SCIENCE_TECH = "28"   # Science & Technology


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
    if not CREDENTIALS_DIR.exists():
        CREDENTIALS_DIR.mkdir(parents=True)

    if not CLIENT_SECRET.exists():
        logger.error("[FAIL] client_secret.json not found.")
        logger.error(f"[FIX]  Place your OAuth credentials at: {CLIENT_SECRET}")
        logger.error("[FIX]  Steps:")
        logger.error("[FIX]  1. Go to console.cloud.google.com")
        logger.error("[FIX]  2. Create project → Enable YouTube Data API v3")
        logger.error("[FIX]  3. Credentials → Create OAuth 2.0 Client ID (Desktop app)")
        logger.error("[FIX]  4. Download JSON → rename to client_secret.json")
        logger.error(f"[FIX]  5. Place at: {CLIENT_SECRET}")
        return False
    return True


# ─────────────────────────────────────────────
# OAUTH
# ─────────────────────────────────────────────

def get_youtube_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        logger.info("[AUTH] Loaded saved credentials")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("[AUTH] Refreshing expired token...")
            creds.refresh(Request())
            logger.info("[AUTH] Token refreshed")
        else:
            logger.info("[AUTH] Starting OAuth flow — browser will open...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
            logger.info("[AUTH] OAuth completed")

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        logger.info(f"[AUTH] Token saved: {TOKEN_FILE}")

    return build("youtube", "v3", credentials=creds)


# ─────────────────────────────────────────────
# AUTO-DISCOVER LATEST POST
# ─────────────────────────────────────────────

def find_latest_post() -> dict | None:
    dirs = sorted([d for d in OUTPUT_DIR.iterdir() if d.is_dir()], reverse=True)
    if not dirs:
        logger.error("[FAIL] No post subdirectories in output/")
        return None

    post_dir = dirs[0]
    logger.info(f"[OK] Latest post: {post_dir.name}")

    mp4   = next(post_dir.glob("*.mp4"),           None)
    thumb = next(post_dir.glob("*_thumbnail.png"), None)
    title_file = next(post_dir.glob("*_title.txt"),       None)
    desc_file  = next(post_dir.glob("*_description.txt"), None)
    meta_file  = next(post_dir.glob("*_metadata.json"),   None)

    if not mp4:
        logger.error(f"[FAIL] No MP4 found in {post_dir.name}")
        return None

    title = title_file.read_text(encoding="utf-8").strip() if title_file else post_dir.name
    desc  = desc_file.read_text(encoding="utf-8").strip()  if desc_file  else ""
    tags  = []
    if meta_file:
        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)
        tags = meta.get("youtube_tags", [])

    for label, f in [("MP4", mp4), ("Thumbnail", thumb)]:
        if f:
            logger.info(f"[OK] {label}: {f.name} ({f.stat().st_size / 1024:.1f} KB)")
        else:
            logger.warning(f"[WARN] {label}: not found")

    return {
        "dir":   post_dir,
        "mp4":   mp4,
        "thumb": thumb,
        "title": title,
        "desc":  desc,
        "tags":  tags,
    }


# ─────────────────────────────────────────────
# UPLOAD VIDEO
# ─────────────────────────────────────────────

def upload_video(youtube, mp4_path: Path, title: str, description: str, tags: list) -> str | None:
    from googleapiclient.http import MediaFileUpload

    logger.info("\n" + "=" * 60)
    logger.info("Uploading to YouTube")
    logger.info("=" * 60)
    logger.info(f"Title: {title}")

    # Ensure #Shorts is in description for YouTube Short classification
    if "#Shorts" not in description:
        description += "\n\n#Shorts"
    if "Shorts" not in tags:
        tags = tags + ["Shorts"]

    body = {
        "snippet": {
            "title":       title[:100],       # YouTube limit
            "description": description[:5000], # YouTube limit
            "tags":        tags[:500],         # YouTube limit
            "categoryId":  CATEGORY_SCIENCE_TECH,
        },
        "status": {
            "privacyStatus":             "public",
            "selfDeclaredMadeForKids":   False,
            "madeForKids":               False,
        }
    }

    media = MediaFileUpload(
        str(mp4_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=8 * 1024 * 1024,   # 8 MB chunks
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
        logger.info(f"[OK] Uploaded! Video ID: {video_id}")
        logger.info(f"[OK] URL: https://www.youtube.com/shorts/{video_id}")
    else:
        logger.error(f"[FAIL] Upload response missing ID: {response}")
    return video_id


# ─────────────────────────────────────────────
# SET THUMBNAIL
# ─────────────────────────────────────────────

def set_thumbnail(youtube, video_id: str, thumb_path: Path):
    from googleapiclient.http import MediaFileUpload
    try:
        media = MediaFileUpload(str(thumb_path), mimetype="image/png")
        youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
        logger.info(f"[OK] Thumbnail set for video {video_id}")
    except Exception as e:
        logger.warning(f"[WARN] Thumbnail upload failed: {e}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main() -> bool:
    logger.info("\n" + "=" * 60)
    logger.info("THE AI CHRONICLE — YOUTUBE UPLOADER")
    logger.info("=" * 60)

    if not check_credentials():
        return False

    post = find_latest_post()
    if not post:
        return False

    try:
        youtube = get_youtube_service()
    except Exception as e:
        logger.error(f"[FAIL] Auth failed: {e}")
        return False

    video_id = upload_video(
        youtube,
        post["mp4"],
        post["title"],
        post["desc"],
        post["tags"],
    )

    if not video_id:
        return False

    if post["thumb"]:
        set_thumbnail(youtube, video_id, post["thumb"])

    # Save result
    result = {
        "timestamp":  datetime.now().isoformat(),
        "video_id":   video_id,
        "url":        f"https://www.youtube.com/shorts/{video_id}",
        "title":      post["title"],
    }
    result_file = post["dir"] / "upload_result.json"
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"[OK] Result saved: {result_file}")
    logger.info("\n" + "=" * 60)
    logger.info("DONE")
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    try:
        ok = main()
        sys.exit(0 if ok else 1)
    except Exception as e:
        logger.error(f"[FAIL] {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
