# Instagram Posting Schedule - Setup & Execution Guide

## Overview
This schedule automation runs Instagram content generation and posting every 2 hours with zero manual intervention required.

## Schedule Configuration
File: `instagram-posting/schedules/instagram_schedule_2h.json`

### Schedule Details
- **Frequency**: Every 2 hours (interval: 120 minutes)
- **Active Hours**: 09:00 - 23:00 UTC (14 hours daily)
- **Daily Executions**: 7 cycles per day
- **Operating Days**: All 7 days (Monday-Sunday)
- **Timezone**: UTC

## Three-Step Automated Workflow

### Task 1: Generate AI News Reel (Order 1)
**Command**: `python src/main.py --generate`
- Fetches live AI news
- Ensures geographic mix: USA 30%, India 30%, China 20%, ROW 20%
- Generates 10 stories (3 USA + 3 India + 2 China + 2 ROW)
- Renders PNG images and MP4 videos
- Creates Excel log
- **Timeout**: 5 minutes
- **Status**: REQUIRED (schedule fails if this fails)
- **Output**: `output/` directory

### Task 2: Post to Instagram (Order 2)
**Command**: `python src/poster.py --auto-approve`
- Uploads pending reels to Instagram
- Auto-approves without manual intervention
- Returns Post IDs and captions
- Logs engagement metrics
- **Timeout**: 3 minutes
- **Status**: REQUIRED (on failure: log and continue)
- **Output**: `output/` directory

### Task 3: Log Geographic Breakdown (Order 3)
**Command**: `python src/logger.py --geo-breakdown`
- Records geographic distribution metrics
- Validates compliance with 30-30-20-20 mix
- Creates detailed breakdown report
- **Timeout**: 1 minute
- **Status**: OPTIONAL (won't block schedule if fails)
- **Output**: `output/` directory

## Execution Timeline

### Daily Schedule Example
```
09:00 → Cycle 1 (Generate + Post + Log)
11:00 → Cycle 2 (Generate + Post + Log)
13:00 → Cycle 3 (Generate + Post + Log)
15:00 → Cycle 4 (Generate + Post + Log)
17:00 → Cycle 5 (Generate + Post + Log)
19:00 → Cycle 6 (Generate + Post + Log)
21:00 → Cycle 7 (Generate + Post + Log)
23:00 → (Schedule stops for 10 hours)
```

## How to Start the Schedule

### Option 1: Start Immediately (Testing)
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src/scheduler.py --config schedules/instagram_schedule_2h.json --start-now
```

### Option 2: Start at Next Interval
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src/scheduler.py --config schedules/instagram_schedule_2h.json --next-cycle
```

### Option 3: Schedule as System Task (Windows)
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src/scheduler.py --config schedules/instagram_schedule_2h.json --register-task
```

## Output Files Generated

### Per Execution (2-hour cycle):
```
instagram-posting/output/
├── posts_20260329_090000.png           # Generated post image
├── reels_20260329_090000.mp4           # Generated video reel
└── instagram_log_20260329_090000.xlsx  # Execution log

instagram-posting/logs/
├── generation_20260329_090000.log      # Generation task log
├── posting_20260329_090000.log         # Posting task log
└── geo_breakdown_20260329_090000.log   # Geographic metrics
```

### Metrics (Daily):
```
instagram-posting/output/
└── metrics_20260329.json               # Day's aggregate metrics
```

## Monitoring the Schedule

### Check Current Status
```bash
python src/scheduler.py --config schedules/instagram_schedule_2h.json --status
```

### View Execution History
```bash
python src/scheduler.py --config schedules/instagram_schedule_2h.json --history
```

### View Next 10 Executions
```bash
python src/scheduler.py --config schedules/instagram_schedule_2h.json --upcoming
```

### View Latest Logs
```bash
Get-ChildItem -Path logs/ -Name | Sort-Object -Descending | Select-Object -First 10
```

## Retry Policy

If a task fails:
- **Max Retries**: 3 attempts
- **Backoff Strategy**: Exponential (delay doubles each retry)
- **Initial Delay**: 60 seconds
- **Max Delay**: 480 seconds (60 × 2 × 2 × 2)

### Retry Timeline Example (if Task 2 fails)
```
First attempt:   09:00:00 - FAILS
First retry:     09:01:00 - FAILS (60s delay)
Second retry:    09:03:00 - FAILS (120s delay)
Third retry:     09:07:00 - FAILS (240s delay)
Final failure:   System logs error and continues to next cycle
```

## Notifications & Alerts

### Success Notification
```
✅ Instagram posting cycle completed successfully
   - Generated: 10 stories ✓
   - Geographic mix: 30-30-20-20 ✓
   - Posted to Instagram ✓
   - Next cycle: 2026-03-29 11:00:00 UTC
```

### Failure Notification
```
❌ Instagram posting cycle failed - check logs
   - Failed task: [task_name]
   - Error: [error_message]
   - Retry: Scheduled in 60 seconds
   - Log file: logs/[...].log
```

## Geographic Mix Compliance

The schedule automatically validates geographic mix before posting:
- ✅ Must have exactly 3 USA stories (30%)
- ✅ Must have exactly 3 India stories (30%)
- ✅ Must have exactly 2 China stories (20%)
- ✅ Must have exactly 2 ROW stories (20%)

If compliance is not met:
- Generation task logs warning
- Proceeds with closest match possible
- Geographic breakdown report shows deviation
- Manual review recommended

## Stopping the Schedule

### Pause (Temporary)
```bash
python src/scheduler.py --config schedules/instagram_schedule_2h.json --pause
```

### Resume
```bash
python src/scheduler.py --config schedules/instagram_schedule_2h.json --resume
```

### Stop (Permanent)
```bash
python src/scheduler.py --config schedules/instagram_schedule_2h.json --stop
```

## Troubleshooting

### Schedule Not Running
1. Check if schedule is enabled: `"enabled": true` in JSON
2. Check current time is between 09:00-23:00 UTC
3. Check logs for errors: `Get-ChildItem logs/ -Name | Select-Object -Last 1`
4. Verify project directory: `c:\Users\sport\Manviga\instagram-posting`

### Tasks Not Completing
1. Check timeout values (Generation: 5m, Posting: 3m, Logging: 1m)
2. Increase timeout if tasks are timing out
3. Check API connectivity for posting failures
4. Review logs for specific error messages

### Geographic Mix Not Balanced
1. Check news API data availability by geography
2. Review `config/geographic_mix.json` settings
3. Check Claude prompt in `.prompt.md` for geographic constraints
4. Review generation logs for distribution breakdown

### Files Not Saving
1. Verify output directory exists: `output/`
2. Check disk space available
3. Verify file permissions on `output/` folder
4. Check logs for write errors

## Best Practices

✅ **DO**:
- Run schedule from `instagram-posting/` directory
- Monitor logs regularly for errors
- Review geographic compliance metrics daily
- Keep API keys updated in `.env`
- Back up output files weekly

❌ **DON'T**:
- Stop schedule while task is executing
- Manually delete files from `output/` during execution
- Change schedule settings while running
- Run multiple schedule instances simultaneously
- Modify config files without stopping schedule

## Support & Logs

All activity is logged to `logs/` directory with timestamps:
- Generation logs: `generation_*.log`
- Posting logs: `posting_*.log`
- Geographic breakdown: `geo_breakdown_*.log`
- Metrics: `metrics_*.json`

Check these logs first for troubleshooting. Each log includes:
- Timestamp
- Task name
- Status (SUCCESS/FAILURE)
- Duration
- Error details (if any)
- Geographic distribution breakdown
