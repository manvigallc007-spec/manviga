# Post to Instagram

Generate a fresh AI news reel and post it to Instagram automatically, with a geographic content mix.

## Geographic mix target (hard requirement)
- USA: 30%
- India: 30%
- China: 20%
- Rest of World: 20%

## Steps

1. Run the reel generator to fetch geo-balanced live AI news, render PNG + MP4, and log to Excel:
```bash
cd "c:/Users/sport/Manviga" && .venv/Scripts/python.exe youtube_live_generator.py
```

2. Run the auto-poster to upload the new reel to Instagram (auto-approval mode):
```bash
cd "c:/Users/sport/Manviga" && .venv/Scripts/python.exe approval_popup.py
```

3. Confirm the result — show the story headline, Post ID, caption preview, and geo breakdown from logs.

4. Configure continuous posting every 3 hours (no manual approval):
```bash
cd "c:/Users/sport/Manviga" && .venv/Scripts/python.exe ig_scheduler_setup.py
```

## Notes
- `youtube_live_generator.py` already enforces the geographic mix in the Claude prompt:
  - ~3 USA, ~3 India, ~2 China, ~2 global in a 10-story run.
- `approval_popup.py` is configured to post immediately (automatic workflow), and uses `instagram_uploader.py`.
- `post_generator.py` now places logo top-left and removes the bottom logo footer block; font sizes in the post template are scaled up by +2 points.
- If there are no unposted reels, it logs "No unposted reels found — nothing to do." and exits.

If the generator fails due to YouTube OAuth (EOF error), ignored; the reel and Excel log are still created successfully.

If no pending reels are found in step 2, report that all reels are already posted.
