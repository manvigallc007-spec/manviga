# Post AI News Roundup to Instagram

Generate a 3-story AI news roundup with female TTS narration and post to Instagram automatically.

## Steps

1. Run the roundup generator (fetches news, generates TTS, renders video, posts to Instagram):
```bash
cd "c:/Users/sport/Manviga" && .venv/Scripts/python.exe news_roundup_generator.py
```

2. Report the result — show:
   - The 3 story headlines
   - TTS voice used
   - Video duration
   - Instagram Post ID
   - Any errors

The output is saved to `~/ai-reels/roundup/` (separate from regular posts).
