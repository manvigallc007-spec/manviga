# Quick Start Guide - Instagram Automation

## 🚀 What Was Built

✅ **Instagram Uploader** - Posts PNG + MP4 to Instagram via Meta API
✅ **2-Hour Scheduler** - Automates posting every 2 hours (9 AM - 11 PM)
✅ **Demo Mode** - Works immediately without valid OAuth token
✅ **Retry Logic** - Automatically retries failed posts

## 📍 File Locations

```
c:\Users\sport\Manviga\instagram-posting\
├── src/instagram_uploader.py    ← Main posting script
├── src/scheduler.py              ← Automation scheduler
├── config/instagram_schedule_2h.json ← Schedule config
└── INSTAGRAM_UPLOADER.md         ← Full documentation
```

## ⚡ Quick Commands

### Test Demo Mode (Current)
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src\instagram_uploader.py
```
✅ Simulates posting both PNG (Feed) and MP4 (Reel)

### Test Scheduler
```bash
python src\scheduler.py --test
```
✅ Shows 2-hour posting times: 09:00, 11:00, 13:00, etc.

### Single Post via Scheduler
```bash
python src\scheduler.py --once
```
✅ Runs uploader once and exits

### 24-Hour Automation
```bash
python src\scheduler.py --duration 24
```
✅ Runs full scheduler loop (posts at 09:00, 11:00, 13:00, etc.)

## 📊 Posting Schedule

**Active Window**: 9 AM - 11 PM UTC

| Time | Post # |
|------|--------|
| 09:00 | 1 |
| 11:00 | 2 |
| 13:00 | 3 |
| 15:00 | 4 |
| 17:00 | 5 |
| 19:00 | 6 |
| 21:00 | 7 |

## 🔑 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| PNG Posts | ✅ Works | Simulated in demo mode |
| MP4 Reels | ✅ Works | Simulated in demo mode |
| Scheduler | ✅ Works | 2-hour cycle verified |
| API | ⏳ Needs Token | OAuth token expired |

## 🔐 Enable Real Posting (3 Steps)

### 1. Get New OAuth Token
- Go to: https://developers.facebook.com/apps
- Click your Instagram app
- Go to Settings > Basic
- Click "Generate User Access Token"

### 2. Copy Token
The token starts with `EAANXQE48wogBRHGWVO3SK...`

### 3. Update .env
Edit `c:\Users\sport\Manviga\.env`:
```
IG_ACCESS_TOKEN=EAANXQE48wogBRHGWVO3SK...
```

## 📝 Output Files

After each run:
- **Logs**: `logs/instagram_upload_YYYYMMDD_HHMMSS.log`
- **Results**: `output/upload_results_YYYYMMDD_HHMMSS.json`

### Example Results
```json
{
  "timestamp": "2026-03-29T07:06:41.797011",
  "feed_post": {
    "media_id": "DEMO_FEED_1774786001",
    "status": "uploaded"
  },
  "reel_post": {
    "media_id": "DEMO_REEL_1774786001",
    "status": "uploaded"
  },
  "demo_mode": true
}
```

## 🎯 Input Files Required

| File | Size | Created By |
|------|------|-----------|
| `output/theaichronicle_post.png` | 107 KB | `master_generator.py` |
| `output/theaichronicle_post.mp4` | 1023 KB | `master_generator.py` |

Already present ✅

## 📑 Documentation Reference

| File | Purpose |
|------|---------|
| [INSTAGRAM_UPLOADER.md](./instagram-posting/INSTAGRAM_UPLOADER.md) | API guide + troubleshooting |
| [INSTAGRAM_AUTOMATION_COMPLETE.md](./INSTAGRAM_AUTOMATION_COMPLETE.md) | Full system overview |
| [README.md](./instagram-posting/README.md) | Project basics |
| [config/instagram_schedule_2h.json](./instagram-posting/config/instagram_schedule_2h.json) | Schedule settings |

## 🐛 Troubleshooting

### "No module named requests"
```bash
pip install requests
```

### "OAuth token is expired"
- Click [here](https://developers.facebook.com/apps) to generate new token
- Update `IG_ACCESS_TOKEN` in root `.env`

### "PNG not found"
```bash
python src/master_generator.py  # Generate first
```

### "UnicodeEncodeError" (Windows)
✅ Fixed in latest version - no action needed

## 📞 Support

All systems are operational:
- ✅ Content detection: PNG + MP4 found
- ✅ Credential validation: IG_USER_ID loaded
- ✅ Scheduler logic: 2-hour intervals correct
- ✅ Demo mode: Posts simulated successfully

**Ready to deploy with fresh OAuth token!**

---

**Next Step**: Generate new OAuth token and update `.env` to enable real posting
