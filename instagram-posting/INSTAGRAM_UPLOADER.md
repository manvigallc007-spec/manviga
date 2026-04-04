# Instagram Uploader Documentation

## Overview

The Instagram uploader (`instagram_uploader.py`) automates posting of AI-generated content to Instagram using Meta's Graph API.

**Current Status**: DEMO MODE (OAuth token expired)

## Features

✅ **Dual Upload Mode**
- Uploads PNG as Feed Post (1080×1920px)
- Uploads MP4 as Reel (3 seconds)

✅ **Smart Authentication**
- Reads credentials from root `.env` file
- Detects expired tokens and enters demo mode
- Shows instructions for refreshing tokens

✅ **Windows Compatible**
- Handles Unicode/emoji encoding properly
- Works on Windows PowerShell and Terminal

✅ **Comprehensive Logging**
- File logging to `logs/instagram_upload_*.log`
- Console output with status indicators
- JSON results saved to `output/upload_results_*.json`

## Usage

### Basic Execution

```bash
cd c:\Users\sport\Manviga\instagram-posting
python src\instagram_uploader.py
```

### Demo Mode (Current)
When OAuth token is expired or invalid, the script automatically enters **DEMO MODE**:
- Simulates PNG upload → generates mock Feed Post ID
- Simulates MP4 upload → generates mock Reel ID
- Saves results to JSON without actual API calls

### Real Mode (With Valid Token)
When you have a fresh OAuth token:

1. **Get New Token**:
   - Go to [Facebook Developer Console](https://developers.facebook.com/apps)
   - Select your Instagram app
   - Navigate to Settings → Basic → Generate User Access Token
   - Copy the token (valid for 60 days)

2. **Update Root .env**:
   ```bash
   IG_ACCESS_TOKEN=<new_token_here>
   ```

3. **Run Uploader**:
   ```bash
   python src\instagram_uploader.py
   ```

## Input Files

| File | Size | Purpose |
|------|------|---------|
| `output/theaichronicle_post.png` | 107.2 KB | Feed Post Image (1080×1920px) |
| `output/theaichronicle_post.mp4` | 1022.6 KB | Reel Video (3 seconds) |

## Output Files

| File | Purpose |
|------|---------|
| `logs/instagram_upload_*.log` | Execution log |
| `output/upload_results_*.json` | API response/results |

## Output Example

```json
{
  "timestamp": "2026-03-29T07:06:41.797011",
  "status": "pending",
  "feed_post": {
    "media_id": "DEMO_FEED_1774786001",
    "status": "uploaded",
    "url": "[DEMO] DEMO_FEED_1774786001"
  },
  "reel_post": {
    "media_id": "DEMO_REEL_1774786001",
    "status": "uploaded",
    "url": "[DEMO] DEMO_REEL_1774786001"
  },
  "errors": [],
  "demo_mode": true
}
```

## Credentials Required

Store in root `.env`:
```
IG_USER_ID=17841437980540533
IG_ACCESS_TOKEN=EAANXQE48wog...
META_APP_ID=940358632260232
```

## API Endpoints Used

- **Connection Test**: `/v18.0/{user_id}?fields=username,name,biography`
- **Feed Post**: `/v18.0/{user_id}/media` with image file
- **Reel Post**: `/v18.0/{user_id}/media` with `media_type=REELS`

## Limitations

- Access tokens expire every 60 days
- Requires valid Instagram Business Account
- MP4 must be 3-60 seconds
- PNG must be 1080×1920px or similar aspect ratio
- Captions have character limits (~2,200 for feeds, ~30 for reels title)

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Invalid OAuth access token` | Regenerate token in Facebook Developer Console |
| `FileNotFoundError: PNG not found` | Run `master_generator.py` first to create assets |
| `UnicodeEncodeError` | Script now handles automatically |

## Next Steps

1. Generate fresh OAuth token from Facebook Developer Console
2. Update `IG_ACCESS_TOKEN` in root `.env`
3. Run `instagram_uploader.py` again
4. Check `output/upload_results_*.json` for live API response with real Post IDs
