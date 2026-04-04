# The AI Chronicle - Complete Instagram Automation System

## Project Overview

**The AI Chronicle** is a fully automated Instagram posting system that:
1. Generates AI news content with geographic distribution
2. Creates professional PNG images (1080×1920px) and MP4 videos (3 seconds)
3. Automatically posts to Instagram Feed and Reels every 2 hours
4. Manages scheduling and retries intelligently

## Architecture

```
instagram-posting/
├── src/
│   ├── main.py                    ← Project entry point
│   ├── generate.py                ← Story generation (10 stories)
│   ├── render.py                  ← PNG + MP4 rendering
│   ├── master_generator.py        ← Professional design system
│   ├── instagram_uploader.py      ← API posting (NEW)
│   └── scheduler.py               ← 2-hour automation (NEW)
├── config/
│   ├── settings.json              ← Project settings
│   ├── geographic_mix.json        ← Geographic distribution
│   └── instagram_schedule_2h.json ← Posting schedule (NEW)
├── output/
│   ├── generated_stories_*.json
│   ├── post_*.png                 ← Feed images
│   ├── reel_*.mp4                 ← Reel videos
│   └── upload_results_*.json      ← API results (NEW)
├── logs/
│   ├── generation_*.log
│   ├── rendering_*.log
│   ├── instagram_upload_*.log     ← API logs (NEW)
│   └── scheduler_*.log            ← Scheduler logs (NEW)
└── Documentation
    ├── README.md
    ├── INSTAGRAM_UPLOADER.md      ← API guide (NEW)
    ├── .prompt.md
    ├── MASTER_PROMPT.md
    └── SCHEDULE_SETUP.md
```

## Workflow

### 1. Content Generation
```bash
python src/generate.py
→ Creates 10 geo-balanced stories (USA 30%, India 30%, China 20%, ROW 20%)
→ Output: output/generated_stories_*.json
```

### 2. Content Rendering
```bash
python src/render.py
→ Generates PNG (1080×1920px, color-coded by region)
→ Generates MP4 (3 seconds, H.264 + AAC)
→ Output: output/post_*.png, output/reel_*.mp4
```

### 3. Professional Post Generation (Optional)
```bash
python src/master_generator.py
→ Creates high-quality post with 24 themes + 11 backgrounds
→ Synthesizes 64 unique music tracks
→ Output: output/theaichronicle_post.png, .mp4, .wav
```

### 4. Automated Instagram Posting
```bash
# Single execution
python src/instagram_uploader.py
→ Uploads PNG as Feed Post
→ Uploads MP4 as Reel
→ Output: output/upload_results_*.json

# Scheduled (2-hour cycle)
python src/scheduler.py
→ Runs uploader every 2 hours (9 AM - 11 PM UTC)
→ Posting times: 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, 21:00
```

## Instagram API Integration

### Current Mode: DEMO
- **Status**: ✅ Fully operational
- **Token**: Expired (expected, test account)
- **Behavior**: Simulates uploads without API calls
- **Output**: Mock Media IDs, results logged to JSON

### Real Mode Setup
1. Go to [Facebook Developer Console](https://developers.facebook.com/apps)
2. Select your Instagram app
3. Generate new User Access Token (Settings > Basic)
4. Update `IG_ACCESS_TOKEN` in root `.env`
5. Run uploader → Posts go live to Instagram

### API Endpoints
- **Connection Test**: `GET /v18.0/{user_id}?fields=username,name,biography`
- **Feed Post**: `POST /v18.0/{user_id}/media` with `image` parameter
- **Reel Post**: `POST /v18.0/{user_id}/media` with `media_type=REELS`

## Scheduling

### 2-Hour Cycle (Default)
```
09:00 ─ Post #1 (3 USA + 3 India + 2 China + 2 ROW stories)
11:00 ─ Post #2
13:00 ─ Post #3
15:00 ─ Post #4
17:00 ─ Post #5
19:00 ─ Post #6
21:00 ─ Post #7
Next day at 09:00 ─ Post #8
```

### Configuration
- File: `config/instagram_schedule_2h.json`
- Interval: 2 hours
- Active window: 09:00-23:00 UTC
- Retries: 3 attempts, 60-second delay between retries

## Content Generation

### Geographic Mix (Each Post)
- **USA**: 30% (3 stories)
- **India**: 30% (3 stories)
- **China**: 20% (2 stories)
- **Rest of World**: 20% (2 stories)

### Image Specs
- **Format**: PNG (RGB or RGBA)
- **Dimensions**: 1080×1920px (9:16 aspect ratio)
- **Size**: ~100-150 KB
- **Colors**: Region-specific (USA Blue, India Orange, China Crimson, ROW Green)

### Video Specs
- **Format**: MP4 (H.264 + AAC)
- **Duration**: 3 seconds
- **Resolution**: 1080×1920px (vertical)
- **Audio**: 192kbps AAC
- **Size**: ~1-2 MB

## Master Generator (Professional Posts)

### Features
- **24 Color Themes**: 12 dark + 12 light gradients (forest, ocean, sunset, etc.)
- **11 Background Styles**: neural networks, grids, bars, stars, waves, etc.
- **64 Music Tracks**: Unique combinations (BPM × keys × scales × waveforms)
- **9-Zone Layout**: Header → Pills → Headline → Body → Stats → Signature → Footer
- **Deterministic**: Same story always generates same design

### Output
- **PNG**: 1080×1080 @ 300 DPI (high quality)
- **MP4**: H.264 + synthesized audio (3 seconds)
- **WAV**: Audio track (5+ MB, 44.1kHz stereo)

## Error Handling

### API Connection
- OAuth token validation
- Automatic demo mode fallback
- Clear error messages with recovery instructions

### Retry Logic
- Up to 3 attempts per post
- 60-second delay between retries
- Exponential backoff (future enhancement)

### File Validation
- Project root verification
- Content file existence checks
- API response parsing

## Logging

### Log Files
- `logs/generation_*.log` - Story generation
- `logs/rendering_*.log` - Image/video creation
- `logs/instagram_upload_*.log` - API posting
- `logs/scheduler_*.log` - Scheduling events

### Log Format
```
2026-03-29 07:06:41,619 - INFO - [OK] PNG file found: theaichronicle_post.png (107.2 KB)
2026-03-29 07:06:41,794 - WARNING - [WARN] OAuth token is expired or invalid
2026-03-29 07:06:41,798 - INFO - [DEMO] File: theaichronicle_post.png
```

## Dependencies

### Python Packages
- `pillow` (12.1.1) - Image generation
- `numpy` (2.4.3) - Numerical operations
- `scipy` (1.17.1) - Audio generation
- `requests` - HTTP API calls
- `python-dotenv` - Environment configuration

### External Tools
- `FFmpeg` - Video encoding (H.264, MP4)

## Security

### Credential Management
- API keys stored in `.env` files (git-ignored)
- Tokens never logged or printed
- Separate .env for each project (isolation)

### Token Rotation
- OAuth tokens expire after 60 days
- Console prompts for token refresh
- Instructions provided in INSTAGRAM_UPLOADER.md

## Monitoring & Debugging

### Test Commands
```bash
# Test uploader (demo mode)
python src/instagram_uploader.py

# Test scheduler calculation
python src/scheduler.py --test

# Single execution via scheduler
python src/scheduler.py --once

# Full scheduler loop (24 hours)
python src/scheduler.py --duration 24
```

### Result Inspection
```bash
# View latest upload results
cat output/upload_results_*.json

# View latest logs
Get-Content logs/instagram_upload_*.log -Tail 50

# Check IG account
@theaichronicle on Instagram
```

## Deployment

### Local Development
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src\instagram_uploader.py     # Single post
python src\scheduler.py              # 24-hour automation
```

### Production (Scheduled Task / CRON)
```bash
# Windows Task Scheduler
python src\scheduler.py --duration 24

# Linux/Mac crontab
0 9 * * * /path/to/venv/bin/python /path/to/scheduler.py --duration 24
```

## Future Enhancements

1. **Multi-Account**: Support multiple Instagram accounts
2. **Analytics**: Track engagement, impressions, saves
3. **A/B Testing**: Test different captions/images
4. **Comments**: Monitor and respond to comments
5. **Story Mode**: Post to Instagram Stories (24-hr expiry)
6. **Cross-Posting**: YouTube, TikTok, LinkedIn integration
7. **AI Optimization**: ML-based optimal posting times
8. **Database**: Store results in MongoDB/PostgreSQL

## Support

### Common Issues

**Q: OAuth Token Expired**
- **A**: Run 2-hour scheduler and post was simulated, not sent
- **Action**: Generate new token in Facebook Developer Console

**Q: PNG Not Found**
- **A**: Need to run `master_generator.py` first
- **Action**: `python src/master_generator.py`

**Q: Windows Console Encoding Error**
- **A**: Fixed in latest version
- **Action**: Update `instagram_uploader.py`

### Troubleshooting
- Check logs: `cat logs/instagram_upload_*.log`
- Verify credentials: `grep IG_ACCESS_TOKEN root/.env`
- Test PNG/MP4: `python src/render.py`

## Credits

- **Content Generation**: AI-powered storytelling
- **Design System**: THE AI CHRONICLE master generator
- **Automation**: Production-ready scheduler
- **Integration**: Meta/Instagram Graph API v18.0
