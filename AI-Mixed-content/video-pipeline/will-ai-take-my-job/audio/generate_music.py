#!/usr/bin/env python3
"""
Generate ambient synth music bed for "Will AI Take My Job?"
Duration: 250s (slightly longer than voiceover to allow fade-out)
Style: Low, slow, cinematic — no percussion, no melody, pure atmosphere
Output: ../output/audio/music_bed.wav
"""

import wave, struct, math
import numpy as np
from pathlib import Path

OUT   = Path(__file__).parent.parent / "output" / "audio" / "music_bed.wav"
SR    = 44100
DUR   = 250          # seconds
N     = SR * DUR

print(f"Generating {DUR}s ambient music bed ...")

t = np.linspace(0, DUR, N, endpoint=False)

# ── Drone layer — slow evolving root + fifth ──────────────────────────────────
root   = 55.0   # A1 — deep, resonant base
fifth  = root * 1.5
octave = root * 2.0

drone  = (
    0.28 * np.sin(2 * np.pi * root   * t)
  + 0.14 * np.sin(2 * np.pi * fifth  * t)
  + 0.08 * np.sin(2 * np.pi * octave * t)
)

# Slow amplitude modulation (breathing feel, ~0.05 Hz)
drone *= 0.82 + 0.18 * np.sin(2 * np.pi * 0.05 * t)

# ── Pad layer — slow chord wash (major 7 voicing) ────────────────────────────
pad_freqs = [110.0, 138.6, 164.8, 207.6]   # A2, C#3, E3, G#3 (Amaj7)
pad = np.zeros(N)
for i, f in enumerate(pad_freqs):
    phase_offset = i * 0.3
    lfo = 0.88 + 0.12 * np.sin(2 * np.pi * 0.03 * t + phase_offset)
    pad += (0.10 / len(pad_freqs)) * np.sin(2 * np.pi * f * t) * lfo

# ── Sub bass pulse — very slow, barely audible, adds warmth ──────────────────
sub_rate = 0.08     # pulse every ~12 seconds
sub = 0.06 * np.sin(2 * np.pi * 27.5 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * sub_rate * t))

# ── High shimmer — airy overtones ────────────────────────────────────────────
shimmer_freqs = [880.0, 1046.5, 1318.5]
shimmer = np.zeros(N)
for f in shimmer_freqs:
    env = 0.5 + 0.5 * np.sin(2 * np.pi * 0.02 * t + f * 0.001)
    shimmer += (0.018 / len(shimmer_freqs)) * np.sin(2 * np.pi * f * t) * env

# ── Combine ───────────────────────────────────────────────────────────────────
mix = drone + pad + sub + shimmer

# ── Fade in (4s) / Fade out (8s) ─────────────────────────────────────────────
fade_in  = np.minimum(t / 4.0, 1.0)
fade_out = np.minimum((DUR - t) / 8.0, 1.0)
mix     *= fade_in * fade_out

# ── Soft limiter ─────────────────────────────────────────────────────────────
mix = np.tanh(mix * 1.8) * 0.72

# ── Normalise to -18 dBFS (leaves headroom for voiceover mix) ────────────────
peak    = np.max(np.abs(mix))
target  = 10 ** (-18 / 20)   # -18 dBFS
mix    *= target / peak

# ── Write stereo WAV ─────────────────────────────────────────────────────────
stereo = np.stack([mix, mix], axis=1)   # mono -> stereo
pcm    = (stereo * 32767).astype(np.int16)

OUT.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(OUT), "w") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())

size_kb = OUT.stat().st_size // 1024
print(f"Saved: {OUT.name}  ({size_kb} KB  |  {DUR}s  |  44100Hz stereo)")
