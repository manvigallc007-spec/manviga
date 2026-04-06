#!/usr/bin/env python3
"""
Generate TTS audio for "Will AI Take My Job?" — The AI Chronicle

Voices (en-IN):
  PRIMARY   en-IN-PrabhatNeural         male, calm, general
  ALT-F     en-IN-NeerjaNeural          female, calm, general
  ALT-FE    en-IN-NeerjaExpressiveNeural female, expressive

Output: ../output/audio/
  voiceover_prabhat.mp3     <- primary (male)
  voiceover_neerja.mp3      <- alt female
  voiceover_neerja_exp.mp3  <- alt female expressive

Run:
    python AI-Mixed-content/video-pipeline/will-ai-take-my-job/audio/generate_audio.py
"""

import asyncio
from pathlib import Path
import edge_tts

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE   = Path(__file__).parent
SCRIPT = HERE / "tts_clean.txt"
OUTPUT = HERE.parent / "output" / "audio"
OUTPUT.mkdir(parents=True, exist_ok=True)

# ── Script ─────────────────────────────────────────────────────────────────────
TEXT = SCRIPT.read_text(encoding="utf-8").strip()

# ── Voice configs ──────────────────────────────────────────────────────────────
VOICES = [
    {
        "id":    "en-IN-PrabhatNeural",
        "label": "primary (male, calm, slightly faster)",
        "file":  "voiceover_prabhat_v4.mp3",
        "rate":  "+12%",    # faster delivery — Editors View pacing
        "pitch": "+0Hz",
    },
]


async def generate(voice: dict):
    out_path = OUTPUT / voice["file"]
    print(f"  Generating {voice['label']} -> {voice['file']} ...")
    tts = edge_tts.Communicate(
        TEXT,
        voice["id"],
        rate=voice["rate"],
        pitch=voice["pitch"],
    )
    await tts.save(str(out_path))
    size_kb = out_path.stat().st_size // 1024
    print(f"  Saved: {voice['file']}  ({size_kb} KB)")


async def main():
    print(f"\nScript: {SCRIPT.name}  ({len(TEXT.split())} words)\n")
    for v in VOICES:
        await generate(v)
    print(f"\nDone. All audio -> {OUTPUT}\n")
    print("Recommended for production: voiceover_prabhat.mp3 (primary male voice)")


if __name__ == "__main__":
    asyncio.run(main())
