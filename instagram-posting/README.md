# Instagram Posting Project

## Overview
This project automates the creation and posting of geographic-balanced AI news reels to Instagram. It generates fresh content with a specific geographic distribution mix and posts them automatically or on a schedule.

## Project Structure
```
instagram-posting/
├── src/
│   └── main.py                 # Main entry point
├── config/
│   ├── settings.json           # General project settings
│   └── geographic_mix.json     # Geographic content distribution
├── output/                     # Generated posts, images, videos
├── logs/                       # Application logs
├── schedules/                  # Scheduled task configurations
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables
```

## Geographic Mix Requirement
All Instagram posts must follow this geographic distribution (hard requirement):

| Region | Percentage | Target Count |
|--------|-----------|--------------|
| USA | 30% | 3 |
| India | 30% | 3 |
| China | 20% | 2 |
| Rest of World | 20% | 2 |
| **Total** | **100%** | **10 stories** |

## Configuration Files

### `.env` - Environment Variables
- `PROJECT_NAME`: Project identifier (instagram-posting)
- `API_KEY`: Instagram API credentials
- `OUTPUT_DIR`: Directory for generated files (./output)
- `LOG_DIR`: Directory for log files (./logs)
- `SCHEDULE_DIR`: Directory for schedule configurations (./schedules)
- `CONFIG_DIR`: Directory for config files (./config)

### `config/settings.json` - Project Settings
```json
{
  "project": "instagram-posting",
  "api_endpoint": "https://api.instagram.com",
  "max_retries": 3,
  "timeout": 30,
  "output_format": "json"
}
```

### `config/geographic_mix.json` - Geographic Distribution
Configuration defining the geographic breakdown for content generation.

## Workflow

### Step 1: Generate Content
Generate a fresh AI news reel with geo-balanced content:
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src/main.py
```

This will:
- Fetch live AI news from APIs
- Ensure geographic mix compliance (USA 30%, India 30%, China 20%, ROW 20%)
- Render PNG images and MP4 videos
- Generate 10-story reel
- Log results to Excel in `output/`

### Step 2: Post to Instagram
Upload generated reels to Instagram (auto-approval mode):
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src/poster.py
```

This will:
- Upload pending reels
- Auto-approve posts
- Return Post ID and captions
- Log geographic breakdown

### Step 3: Schedule Continuous Posting
Configure automated posting every 2 hours (no manual approval):
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src/scheduler.py
```

This will:
- Create scheduled tasks
- Run generation every 2 hours
- Auto-post to Instagram
- Maintain geographic mix
- Log all activities

## Logging
All logs are stored in `logs/` with timestamps:
- `instagram_20260329_143022.log` - Application logs
- `geographic_breakdown.log` - Geographic distribution tracking

## Output Files
Generated files are stored in `output/`:
- `posts_*.png` - Generated post images
- `reels_*.mp4` - Generated video reels
- `instagram_posts_*.xlsx` - Posting logs and statistics
- `geo_breakdown_*.json` - Geographic distribution records

## Schedule Configuration
Scheduled tasks are stored in `schedules/`:
- `instagram_schedule_2h.json` - 2-hour interval schedule
- `instagram_schedule_manual.json` - Manual execution schedule

## Error Handling
- If YouTube OAuth fails (EOF error): Reel and Excel log still created successfully
- If no pending reels found: Logs "No unposted reels found — nothing to do." and exits
- All errors logged to `logs/` directory with full traceback

## Requirements
See `requirements.txt` for Python dependencies:
- requests
- python-dotenv
- google-auth-oauthlib
- google-auth-httplib2

## Running the Project

### Development Mode
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src/main.py --debug
```

### Production with Scheduling
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src/scheduler.py --interval 2h
```

### Manual Execution
```bash
cd c:\Users\sport\Manviga\instagram-posting
python src/main.py --now
```

## Troubleshooting

### Files not appearing in output/
- Check that you're running from `instagram-posting/` directory
- Verify `.env` file has correct `OUTPUT_DIR` path
- Check logs for error messages

### Geographic mix not balanced
- Verify `config/geographic_mix.json` is loaded correctly
- Check Claude prompt includes geographic constraints
- Review logs for distribution breakdown

### Schedule not running
- Verify `config/settings.json` schedule is enabled
- Check system task scheduler configuration
- Review logs in `logs/` directory

## Support
For issues or questions, check the logs in `logs/` directory first. All operations are logged with full context.
