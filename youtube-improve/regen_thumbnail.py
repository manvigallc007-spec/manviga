#!/usr/bin/env python3
"""
Regenerate thumbnails for the most recent run using a specific story.
Usage: python regen_thumbnail.py
"""
import json
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Load metadata from the most recent today's output
meta_path = Path("output/20260403_045230_microsoft/yt_metadata.json")
with open(meta_path, encoding="utf-8") as f:
    meta = json.load(f)

stories = meta["stories"]
date_str = meta["date_str"]

# Print current top story (by score)
top = max(stories, key=lambda s: s.get("score", {}).get("total", 0))
print(f"Current top story (score {top['score']['total']}): {top['headline']}")
print()

# Pick a better story — "GPT reasoning models have line of sight to AGI"
# It's at index 6. Override by injecting it as the highest scorer so _top_story picks it.
override_headline = "GPT reasoning models have"
chosen = next((s for s in stories if override_headline in s["headline"]), None)
if not chosen:
    print("Story not found — available headlines:")
    for i, s in enumerate(stories):
        print(f"  [{i}] score={s['score']['total']}  {s['headline']}")
    sys.exit(1)

print(f"Override story: {chosen['headline']}")
print(f"Hook: {chosen['hook']}")
print()

# Boost its score so _top_story() picks it
for s in stories:
    s["score"]["total"] = s["score"].get("total", 0)
chosen["score"]["total"] = 999  # force it to the top

# Now regenerate thumbnails
sys.path.insert(0, str(Path(__file__).parent / "src"))
from thumbnail_generator import generate_thumbnail_a, generate_thumbnail_b

out_dir = meta_path.parent
slug = out_dir.name.split("_", 2)[-1] if "_" in out_dir.name else out_dir.name
ts   = out_dir.name.rsplit("_", 1)[0] if "_" in out_dir.name else ""

# Use the exact original paths
thumb_a = out_dir / meta["thumbnail_a"].replace("\\", "/").split("/")[-1]
thumb_b = out_dir / meta["thumbnail_b"].replace("\\", "/").split("/")[-1]

generate_thumbnail_a(stories, date_str, thumb_a)
generate_thumbnail_b(stories, date_str, thumb_b)

print(f"Saved A: {thumb_a}")
print(f"Saved B: {thumb_b}")
