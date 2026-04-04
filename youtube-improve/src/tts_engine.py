#!/usr/bin/env python3
"""
THE AI CHRONICLE — Improved TTS Engine
Converts story tts_script to SSML and generates MP3 via edge-tts.
Voice: en-IN-PrabhatNeural @ +15% rate, +5Hz pitch.
Handles <emphasis> and <break> tags in the tts_script field.
"""

import asyncio
import logging
import re
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

TTS_VOICE = "en-IN-PrabhatNeural"
TTS_RATE  = "-5%"    # Passed as edge_tts constructor param (not via SSML prosody)
TTS_PITCH = "+5Hz"


# ─────────────────────────────────────────────
# TEXT CLEANING
# ─────────────────────────────────────────────

def strip_markup(text: str) -> str:
    """Strip all XML/SSML markup tags, return clean plain text."""
    return re.sub(r'<[^>]+>', '', text).strip()


# ─────────────────────────────────────────────
# ASYNC GENERATION
# ─────────────────────────────────────────────

async def _generate_async(plain_text: str, out_mp3: Path) -> Path:
    """Generate TTS MP3 using edge-tts with rate/pitch as constructor params."""
    import edge_tts
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    # Pass rate and pitch as constructor params — edge_tts applies these
    # via its own internal SSML prosody wrapper. Do NOT pass full SSML as text,
    # as edge_tts ignores rate/pitch params when text starts with <speak>.
    communicate = edge_tts.Communicate(plain_text, TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH)
    await communicate.save(str(out_mp3))
    return out_mp3


def _gtts_fallback(plain_text: str, out_mp3: Path) -> Path:
    """Fallback TTS using gTTS when edge-tts is unavailable."""
    from gtts import gTTS
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    tts = gTTS(text=plain_text, lang="en", slow=False)
    tts.save(str(out_mp3))
    logger.info(f"[TTS] gTTS fallback generated: {out_mp3.name}")
    return out_mp3


async def generate_tts(text: str, out_mp3: Path) -> Path:
    """
    Async: strip markup from text, generate MP3 at target rate/pitch.
    Falls back to gTTS if edge-tts connection fails.
    Returns path to the generated MP3.
    """
    plain = strip_markup(text)
    try:
        await _generate_async(plain, out_mp3)
        logger.info(f"[TTS] Generated: {out_mp3.name}")
        return out_mp3
    except Exception as e:
        logger.warning(f"[TTS] edge-tts failed ({type(e).__name__}) — trying gTTS fallback")
        try:
            return _gtts_fallback(plain, out_mp3)
        except Exception as e2:
            logger.error(f"[TTS] gTTS fallback also failed: {e2}")
            raise


# ─────────────────────────────────────────────
# SYNC WRAPPER
# ─────────────────────────────────────────────

def generate_tts_sync(text: str, out_mp3: Path) -> Path:
    """
    Synchronous wrapper. Strips any <emphasis>/<break> markup, then generates MP3.
    Returns path to generated MP3.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, generate_tts(text, out_mp3))
                return future.result()
        else:
            return loop.run_until_complete(generate_tts(text, out_mp3))
    except RuntimeError:
        return asyncio.run(generate_tts(text, out_mp3))


def generate_story_tts(story: dict, out_mp3: Path) -> Path:
    """
    Generate TTS for a story dict using its tts_script field.
    Returns path to MP3.
    """
    script = story.get("tts_script", story.get("summary", story.get("headline", "")))
    logger.info(f"[TTS] Generating TTS for: {story.get('headline', '?')}")
    return generate_tts_sync(script, out_mp3)


# ─────────────────────────────────────────────
# AUDIO DURATION
# ─────────────────────────────────────────────

# ffmpeg path
_WINGET_FFPROBE = (
    Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-7.1-full_build/bin/ffprobe.exe"
)
_WINGET_FFPROBE2 = (
    Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-8.1-full_build/bin/ffprobe.exe"
)

def _get_ffprobe() -> str:
    for p in (_WINGET_FFPROBE, _WINGET_FFPROBE2):
        if p.exists():
            return str(p)
    return "ffprobe"


def get_audio_duration(mp3_path: Path) -> float:
    """
    Get duration of an MP3 file in seconds using ffprobe.
    Falls back to estimating from file size if ffprobe unavailable.
    """
    try:
        ffprobe = _get_ffprobe()
        result = subprocess.run(
            [
                ffprobe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(mp3_path),
            ],
            capture_output=True, text=True, timeout=15,
        )
        duration = float(result.stdout.strip())
        logger.debug(f"[TTS] Duration of {mp3_path.name}: {duration:.2f}s")
        return duration
    except Exception as e:
        logger.warning(f"[TTS] ffprobe failed ({e}), estimating duration from file size")
        try:
            size_kb = mp3_path.stat().st_size / 1024
            # Rough estimate: ~16KB/s for 128kbps MP3
            return max(5.0, size_kb / 16.0)
        except Exception:
            return 15.0  # safe default


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    test_script = (
        "The AI that outperforms human experts just went live. "
        "<break time=\"400ms\"/> Over at <emphasis>OpenAI</emphasis>, "
        "<emphasis>GPT-5</emphasis> just scored <emphasis>96 percent</emphasis> "
        "on the MMLU benchmark. Enterprise API access opens this week."
    )
    out = Path("test_tts_output.mp3")
    result = generate_tts_sync(test_script, out)
    print(f"Generated: {result}")
    duration = get_audio_duration(result)
    print(f"Duration: {duration:.2f}s")
