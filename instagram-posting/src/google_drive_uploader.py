#!/usr/bin/env python3
"""
THE AI CHRONICLE — Google Drive Uploader
Copies post files to Google Drive. Does NOT delete local files.
Renames local directory with 'transferred_' prefix after successful copy.

Setup (one-time):
  1. console.cloud.google.com → Create project → Enable Google Drive API
  2. Credentials → OAuth 2.0 Client ID → Desktop app → Download JSON
  3. Rename to gdrive_credentials.json
  4. Place at: instagram-posting/credentials/gdrive_credentials.json
  5. First run opens browser for Google login → token.json auto-saved
"""

import json
import logging
import mimetypes
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

ROOT_ENV = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ROOT_ENV)

logger = logging.getLogger(__name__)

PROJECT_ROOT   = Path(__file__).parent.parent
CREDS_DIR      = PROJECT_ROOT / "credentials"
CREDS_FILE     = CREDS_DIR / "gdrive_credentials.json"
TOKEN_FILE     = CREDS_DIR / "gdrive_token.json"

# Google Drive folder name — will be created if it doesn't exist
DRIVE_FOLDER_NAME = os.getenv("GDRIVE_FOLDER", "TheAIChronicle_Instagram")

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# File types to upload
UPLOAD_EXTENSIONS = {".png", ".mp4", ".mp3", ".txt", ".json"}


def _get_drive_service():
    """Authenticate and return Google Drive service."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                raise FileNotFoundError(
                    f"[GDRIVE] gdrive_credentials.json not found at {CREDS_FILE}\n"
                    f"[FIX] Steps:\n"
                    f"  1. console.cloud.google.com → Enable Google Drive API\n"
                    f"  2. Credentials → OAuth 2.0 Client ID → Desktop app\n"
                    f"  3. Download JSON → rename to gdrive_credentials.json\n"
                    f"  4. Place at: {CREDS_FILE}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        logger.info("[GDRIVE] Token saved")

    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, folder_name: str, parent_id: str = None) -> str:
    """Return the Drive folder ID, creating it if it doesn't exist."""
    query = (f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
             f" and trashed=false")
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        logger.info(f"[GDRIVE] Found folder '{folder_name}': {files[0]['id']}")
        return files[0]["id"]

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    folder_id = folder["id"]
    logger.info(f"[GDRIVE] Created folder '{folder_name}': {folder_id}")
    return folder_id


def _upload_file(service, file_path: Path, parent_folder_id: str) -> str | None:
    """Upload a single file to Drive. Returns file ID or None."""
    from googleapiclient.http import MediaFileUpload

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = "application/octet-stream"

    metadata = {
        "name": file_path.name,
        "parents": [parent_folder_id],
    }

    try:
        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
        result = service.files().create(
            body=metadata, media_body=media, fields="id,name"
        ).execute()
        logger.info(f"[GDRIVE] Uploaded: {file_path.name} → {result['id']}")
        return result["id"]
    except Exception as e:
        logger.error(f"[GDRIVE] Failed to upload {file_path.name}: {e}")
        return None


def transfer_post_directory(post_dir: Path) -> bool:
    """
    Copy all files in post_dir to Google Drive.
    Creates:  TheAIChronicle_Instagram / YYYY-MM-DD / {post_dir.name} /
    Renames local dir to 'transferred_{post_dir.name}' on success.
    Returns True if all files uploaded successfully.
    """
    if not post_dir.exists():
        logger.error(f"[GDRIVE] Post dir not found: {post_dir}")
        return False

    # Skip already-transferred directories
    if post_dir.name.startswith("transferred_"):
        logger.info(f"[GDRIVE] Already transferred: {post_dir.name}")
        return True

    files_to_upload = [
        f for f in post_dir.iterdir()
        if f.is_file() and f.suffix.lower() in UPLOAD_EXTENSIONS
    ]
    if not files_to_upload:
        logger.warning(f"[GDRIVE] No uploadable files in {post_dir.name}")
        return False

    logger.info(f"[GDRIVE] Transferring {len(files_to_upload)} files from {post_dir.name}...")

    try:
        service = _get_drive_service()
    except FileNotFoundError as e:
        logger.error(str(e))
        return False
    except Exception as e:
        logger.error(f"[GDRIVE] Auth failed: {e}")
        return False

    # Root folder: TheAIChronicle_Instagram
    root_id = _get_or_create_folder(service, DRIVE_FOLDER_NAME)

    # Date sub-folder: YYYY-MM-DD
    date_folder = datetime.now().strftime("%Y-%m-%d")
    date_id = _get_or_create_folder(service, date_folder, parent_id=root_id)

    # Post sub-folder: {post_dir.name}
    post_folder_id = _get_or_create_folder(service, post_dir.name, parent_id=date_id)

    # Upload each file
    uploaded, failed = 0, 0
    for f in sorted(files_to_upload):
        fid = _upload_file(service, f, post_folder_id)
        if fid:
            uploaded += 1
        else:
            failed += 1

    logger.info(f"[GDRIVE] {post_dir.name}: {uploaded} uploaded, {failed} failed")

    if failed == 0:
        # Rename local directory with 'transferred_' prefix
        new_name = post_dir.parent / f"transferred_{post_dir.name}"
        try:
            post_dir.rename(new_name)
            logger.info(f"[GDRIVE] Renamed: {post_dir.name} -> transferred_{post_dir.name}")
        except Exception as e:
            logger.warning(f"[GDRIVE] Could not rename directory: {e}")
        return True

    return False


def transfer_all_pending(output_dir: Path) -> dict:
    """
    Transfer all post directories in output_dir that haven't been transferred yet.
    Returns summary dict.
    """
    pending = [
        d for d in sorted(output_dir.iterdir())
        if d.is_dir() and not d.name.startswith("transferred_")
    ]
    logger.info(f"[GDRIVE] Found {len(pending)} pending directories to transfer")

    results = {"transferred": 0, "failed": 0, "dirs": []}
    for post_dir in pending:
        ok = transfer_post_directory(post_dir)
        if ok:
            results["transferred"] += 1
        else:
            results["failed"] += 1
        results["dirs"].append({"dir": post_dir.name, "ok": ok})

    return results


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    output_dir = PROJECT_ROOT / "output"
    if not output_dir.exists():
        print("[FAIL] No output directory found")
        sys.exit(1)

    results = transfer_all_pending(output_dir)
    print(f"\nTransferred: {results['transferred']}, Failed: {results['failed']}")
