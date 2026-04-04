# YouTube Pipeline — 6-Hour Automation Setup

## Overview
Your YouTube posting pipeline is now configured to **run automatically every 6 hours**, fetching top AI news, generating branded vertical videos, and uploading them to YouTube.

**Frequency:** Every 6 hours (4 runs per day)  
**Schedule:** 12:00 AM, 6:00 AM, 12:00 PM, 6:00 PM (approximate)  
**Project Root:** `C:\Users\sport\Manviga\youtube-posting\`

---

## Setup Instructions

### Step 1: Create Windows Task Scheduler Job (ONE TIME ONLY)

1. **Open PowerShell as Administrator**
   - Right-click Start Menu → Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Run the setup script**
   ```powershell
   C:\Users\sport\Manviga\youtube-posting\setup_scheduler.ps1
   ```

3. **Wait for confirmation**
   - You should see:
     ```
     ✓ Task created successfully!
     ✓ Task verification successful!
     ```

### Step 2: Verify Task Creation

Run this command to check the task status:
```powershell
C:\Users\sport\Manviga\youtube-posting\check_scheduler.ps1
```

Expected output shows:
- ✓ Task Found
- State: Ready
- Last Run Time (if it's been run)
- Next Run Time

### Step 3: Verify in Windows Task Scheduler

1. Open Task Scheduler: `taskschd.msc`
2. Look for task: **YouTubePostingPipeline**
3. Verify it shows `Ready` status
4. Check the "Triggers" tab — should show "6-hour interval"

---

## Log Files

All logs are stored in: `C:\Users\sport\Manviga\youtube-posting\logs\`

### Log Files Generated

| File | Content |
|------|---------|
| `scheduler_*.log` | Batch file execution logs (when/how it ran) |
| `pipeline_*.log` | Full pipeline execution details |
| `posted_stories.json` | Deduplication log (last 100 uploaded stories) |

### Check Recent Logs

```powershell
Get-ChildItem "C:\Users\sport\Manviga\youtube-posting\logs\" -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 10
```

---

## Manual Testing

### Run Pipeline Now

```powershell
# Option 1: Via Task Scheduler (easiest)
Run-ScheduledTask -TaskName "YouTubePostingPipeline"

# Option 2: Direct Python
cd C:\Users\sport\Manviga\youtube-posting
python src\run_pipeline.py
```

### Run Individual Steps

```powershell
cd C:\Users\sport\Manviga\youtube-posting

# 1. Fetch news only
python -c "from src.news_fetcher import fetch_todays_stories; print(fetch_todays_stories())"

# 2. Generate video (after news fetch)
python -c "from src.video_generator import generate_video; generate_video(story)"

# 3. Upload to YouTube
python -c "from src.youtube_uploader import upload_short; upload_short()"
```

---

## Troubleshooting

### Task won't run automatically

**Problem:** Task scheduled but not executing  
**Solution:**
1. Verify virtual environment is activated in batch file
2. Check `C:\Users\sport\Manviga\youtube-posting\logs\scheduler_*.log` for errors
3. Ensure API keys are set in `.env` files:
   - Root `.env`: `ANTHROPIC_API_KEY`
   - YouTube `.env`: `PROJECT_NAME=youtube-posting`

### Permission denied errors

**Problem:** "Access Denied" or "Permission Error"  
**Solution:**
1. Re-run `setup_scheduler.ps1` as **Administrator**
2. Check that YouTube credentials exist:
   - `youtube-posting/credentials/client_secret.json`
   - `youtube-posting/credentials/token.json`

### API key errors

**Problem:** "Invalid API key" or "API key not found"  
**Solution:**
1. Check root `.env`: `C:\Users\sport\Manviga\.env`
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
2. Check YouTube `.env`: `C:\Users\sport\Manviga\youtube-posting\.env`
   ```
   PROJECT_NAME=youtube-posting
   ```

### No YouTube upload

**Problem:** Pipeline runs but doesn't upload to YouTube  
**Solution:**
1. Verify OAuth credentials:
   ```
   ls C:\Users\sport\Manviga\youtube-posting\credentials\
   ```
   Should show `client_secret.json` and `token.json`
2. Check logs: `logs/youtube_upload_*.log`
3. Re-authenticate: Delete `token.json` and run pipeline manually

---

## Task Management

### Disable Automatic Scheduling (Pause)

```powershell
Disable-ScheduledTask -TaskName "YouTubePostingPipeline"
```

### Re-enable Automatic Scheduling (Resume)

```powershell
Enable-ScheduledTask -TaskName "YouTubePostingPipeline"
```

### Change Schedule Frequency

1. Open Task Scheduler: `taskschd.msc`
2. Find **YouTubePostingPipeline**
3. Right-click → Edit
4. Go to "Triggers" tab
5. Edit the trigger to change frequency (e.g., 2 hours, 12 hours, daily)
6. Click OK

### Delete Task Completely

```powershell
Unregister-ScheduledTask -TaskName "YouTubePostingPipeline" -Confirm:$false
```

---

## Expected Behavior

### Every 6 Hours, The Task Will:

1. ✅ **Activate Python venv** (2 seconds)
2. ✅ **Fetch top AI news story** (5-10 seconds)
3. ✅ **Check deduplication log** (1 second)
4. ✅ **Generate branded 1080×1920 video** (30-60 seconds)
   - PNG with AI Chronicle branding
   - MP3 narration via Google Text-to-Speech
   - MP4 video compilation
5. ✅ **Upload to YouTube** (10-20 seconds)
6. ✅ **Log results** (1 second)

**Total time per run:** ~1-2 minutes  
**Success rate target:** 95%+ (with auto-retry on failure)

---

## Output Files

Each successful run generates:

```
output/{YYYYMMDD_HHMMSS}_{story_slug}/
├── {slug}_short.png              # 1080×1920 main image
├── {slug}_thumbnail.png          # 1280×720 YouTube thumbnail
├── {slug}.mp3                    # Narration audio (Google GTTS)
├── {slug}.mp4                    # Final YouTube Short (≤58s)
├── {slug}_title.txt              # Video title
├── {slug}_description.txt        # Description + hashtags
├── {slug}_metadata.json          # Full metadata
└── upload_result.json            # YouTube video ID + URL
```

Posted stories are deduped in: `logs/posted_stories.json` (last 100)

---

## Monitoring Dashboard

Check task health regularly:

```powershell
# Status check script
C:\Users\sport\Manviga\youtube-posting\check_scheduler.ps1

# Manual log tail (last 20 lines)
Get-Content -Path "C:\Users\sport\Manviga\youtube-posting\logs\scheduler_*.log" -Tail 20 -Wait
```

---

## Files Created

| File | Purpose |
|------|---------|
| `run_scheduler.bat` | Batch wrapper that activates venv + runs pipeline |
| `run_scheduler.ps1` | PowerShell wrapper version |
| `setup_scheduler.ps1` | **RUN THIS to create the Task** |
| `check_scheduler.ps1` | Status/verification script |
| `YOUTUBE_SCHEDULE_SETUP.md` | This documentation |

---

## Questions?

If the pipeline fails:
1. **Check logs first:** `youtube-posting/logs/`
2. **Run manually:** `python youtube-posting/src/run_pipeline.py`
3. **Check API keys:** Root `.env` and project `.env`
4. **Test each step:** News → Video Gen → Upload

The pipeline is completely isolated from Instagram — no conflicts.

---

**Last Updated:** 2026-03-29  
**Schedule:** Every 6 hours (4x daily)  
**Status:** Ready for setup
