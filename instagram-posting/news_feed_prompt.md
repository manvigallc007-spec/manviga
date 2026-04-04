# News Feed Prompts — The AI Chronicle
## Ready-made prompts for Claude Code (Last updated: 2026-03-29)

Paste any of these prompts directly into Claude Code to manage the pipeline.

---

## PROMPT: Check Pipeline Health

```
Check the health of The AI Chronicle Instagram pipeline at c:/Users/sport/Manviga/instagram-posting/

1. List the 5 most recent output subdirectories in output/
2. Read the most recent pipeline_*.log in logs/
3. Read logs/posted_stories.json — show the last 5 posted headlines and timestamps
4. Check Windows Task Scheduler:
   powershell -Command "Get-ScheduledTask -TaskName 'TheAIChronicle_HourlyPost' | Select-Object TaskName,State,Triggers"
5. Show the first 40 chars of IG_ACCESS_TOKEN from c:/Users/sport/Manviga/.env (do not show full token)
6. Summarise pipeline status in 5 bullet points: last post, next scheduled run, any errors, token status
```

---

## PROMPT: Run Pipeline Now (On Demand)

```
Run the full Instagram pipeline immediately for The AI Chronicle:

  python c:/Users/sport/Manviga/instagram-posting/src/run_pipeline.py

This will:
1. Search the web for today's #1 AI news story (verified sources only)
2. Generate PNG + MP3 + MP4 + caption
3. Upload the reel to @theaichronicle007

Report the headline of the story posted and the Instagram post ID.
```

---

## PROMPT: Post a Specific Story Now

```
I want to post this specific AI news story to Instagram immediately.

Story details:
  Headline: [PASTE HEADLINE]
  Source URL: [PASTE URL]
  Key stat: [e.g. "$5B funding" or "94% accuracy"]
  Summary: [2-3 sentence summary]

Please:
1. Format this into a valid story dict matching the structure in
   c:/Users/sport/Manviga/instagram-posting/src/master_post_v2.py (AI_NEWS_STORIES format)
2. Read news_fetcher.py and add a fetch_override(story) function that returns this story directly
3. In master_post_v2.py main(), call fetch_override() before the live fetch so this story is used
4. Run: python c:/Users/sport/Manviga/instagram-posting/src/run_pipeline.py
5. After successful upload, remove the override and restore normal live-fetch behaviour
```

---

## PROMPT: Add Fallback Stories

```
Add 5 new fallback stories to The AI Chronicle pipeline at:
  c:/Users/sport/Manviga/instagram-posting/src/master_post_v2.py

The AI_NEWS_STORIES list is the fallback used when live web search fails.

Please:
1. Search the web for 5 significant AI news stories from the past 30 days.
   Sources: TechCrunch, The Verge, Wired, VentureBeat, MIT TR, Reuters, Bloomberg,
   OpenAI/DeepMind/Anthropic/Meta blogs, ArXiv, Nature, WSJ.
   Topics: model releases, funding, benchmarks, research breakthroughs, regulation.
   No gossip or speculation.

2. Format each as:
   {
       "company":    "Company / Topic",
       "headline":   "Max Six Word Title",
       "watermark":  "KEYWORD",
       "body":       ["Line 1", "Line 2", "Line 3", "Line 4"],
       "stat_label": "Metric label",
       "stat_value": "VALUE",
       "source":     "Org / Publication",
       "hashtags":   "#Tag1 #Tag2 #Tag3",
       "reference":  "https://url"
   }

3. Read AI_NEWS_STORIES in master_post_v2.py.
   Append the 5 new stories. Do NOT remove existing ones. Do NOT duplicate headlines.
4. Confirm total story count.
```

---

## PROMPT: Renew Instagram Access Token

```
The Instagram access token for The AI Chronicle pipeline needs renewal.
App ID: 4129428227192830

1. Remind me of the exact steps to get a new token:
   - Go to: developers.facebook.com/tools/explorer
   - Select app 4129428227192830
   - Required permissions: instagram_basic, instagram_content_publish, pages_show_list
   - Generate User Access Token

2. Once I paste the new token here, update IG_ACCESS_TOKEN in c:/Users/sport/Manviga/.env

3. Verify the token works by running:
   python -c "
   import requests, os
   from dotenv import load_dotenv
   from pathlib import Path
   load_dotenv(Path('c:/Users/sport/Manviga/.env'))
   token = os.getenv('IG_ACCESS_TOKEN')
   ig_id = os.getenv('IG_USER_ID')
   r = requests.get(f'https://graph.facebook.com/v18.0/{ig_id}?fields=username,name&access_token={token}')
   print(r.json())
   "

4. Confirm token is valid and shows @theaichronicle007
```

---

## PROMPT: Fix News Fetcher Issues

```
The news fetcher at c:/Users/sport/Manviga/instagram-posting/src/news_fetcher.py
is having issues. Please diagnose and fix.

1. Read news_fetcher.py
2. Test it standalone:
   cd c:/Users/sport/Manviga/instagram-posting/src && python news_fetcher.py
3. Check logs/posted_stories.json for recent entries
4. Common issues to check:
   - Rate limit (429): model should be claude-sonnet-4-6, NOT claude-opus-4-6
   - JSON parse failure: look for malformed response in last pipeline log
   - Missing ANTHROPIC_API_KEY: check c:/Users/sport/Manviga/.env
5. Fix the root cause and confirm fetcher returns a valid story dict
```

---

## PROMPT: View Recent Posts

```
Show me a summary of the last 10 posts made by The AI Chronicle pipeline.

1. Read c:/Users/sport/Manviga/instagram-posting/logs/posted_stories.json
2. List each entry: timestamp, headline
3. List the last 10 output subdirectories in c:/Users/sport/Manviga/instagram-posting/output/
4. For each, read the upload_result.json and show instagram_reel post ID
5. Format as a table: Date | Headline | Instagram Post ID
```

---

## PROMPT: Rebuild Scheduler

```
The Windows Task Scheduler job for The AI Chronicle pipeline may be missing or broken.
Rebuild it.

1. Check current state:
   powershell -Command "Get-ScheduledTask -TaskName 'TheAIChronicle_HourlyPost'"

2. If missing or broken, recreate:
   powershell -Command "
   $action = New-ScheduledTaskAction -Execute 'C:\Users\sport\Manviga\.venv\Scripts\python.exe' -Argument 'C:\Users\sport\Manviga\instagram-posting\src\run_pipeline.py'
   $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 1) -Once -At '00:07'
   $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -StartWhenAvailable
   Register-ScheduledTask -TaskName 'TheAIChronicle_HourlyPost' -Action $action -Trigger $trigger -Settings $settings -Force
   "

3. Confirm task is in Ready state.
```
