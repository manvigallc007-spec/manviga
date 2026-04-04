#!/usr/bin/env python3
"""
One-time YouTube OAuth setup — saves token.json for automatic future use.
Run this once, authorize in browser, then delete this file.
"""
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CREDENTIALS_DIR = Path(__file__).parent / "credentials"
CLIENT_SECRET   = CREDENTIALS_DIR / "client_secret.json"
TOKEN_FILE      = CREDENTIALS_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

print("=" * 60)
print("THE AI CHRONICLE — YouTube OAuth Setup")
print("=" * 60)
print(f"\nClient secret: {CLIENT_SECRET}")
print(f"Token will be saved to: {TOKEN_FILE}\n")

flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
creds = flow.run_local_server(port=8080, open_browser=True)

with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())

print(f"\n[OK] token.json saved to: {TOKEN_FILE}")
print("[OK] Future pipeline runs will auto-refresh — no login needed again.")

# Quick verify
youtube = build("youtube", "v3", credentials=creds)
resp = youtube.channels().list(part="snippet", mine=True).execute()
channel = resp["items"][0]["snippet"]["title"] if resp.get("items") else "unknown"
print(f"[OK] Authenticated as YouTube channel: {channel}")
print("\nSetup complete! You can now delete auth_setup.py")
