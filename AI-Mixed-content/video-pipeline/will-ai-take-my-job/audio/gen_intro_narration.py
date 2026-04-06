#!/usr/bin/env python3
"""Generate short intro narration for cinematic intro (~15-20s)."""
import asyncio, edge_tts
from pathlib import Path

OUT = Path(__file__).parent.parent / "output" / "audio" / "intro_narration.mp3"
OUT.parent.mkdir(parents=True, exist_ok=True)

TEXT = (
    "Millions of workers are asking the same question right now. "
    "Will artificial intelligence take my job? "
    "The answer is not simple. "
    "But it is clear."
)

async def main():
    tts = edge_tts.Communicate(TEXT, voice="en-IN-PrabhatNeural", rate="+8%", pitch="+0Hz")
    await tts.save(str(OUT))
    print(f"Saved: {OUT.name}")

asyncio.run(main())
