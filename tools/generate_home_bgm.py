#!/usr/bin/env python3
"""Generate the original TV TIME home-screen theme music as a loopable WAV.

Uses only Python's standard library. The composition and synthesis are original;
no game audio, samples, or third-party recordings are used.
"""
from __future__ import annotations

import argparse
import math
import random
import wave
from array import array
from pathlib import Path

RATE = 48_000
BPM = 120
BARS = 16
BEAT = 60.0 / BPM
DURATION = BARS * 4 * BEAT
TAU = math.tau

# F major / D minor broadcast-game-show progression.
CHORDS = [
    (174.61, 220.00, 261.63, 329.63),  # Fmaj7
    (146.83, 174.61, 220.00, 261.63),  # Dm7
    (116.54, 146.83, 174.61, 220.00),  # Bbmaj7
    (130.81, 164.81, 196.00, 233.08),  # C7
]
MELODY = [
    523.25, 659.25, 783.99, 659.25, 587.33, 659.25, 523.25, 392.00,
    440.00, 523.25, 587.33, 523.25, 493.88, 587.33, 659.25, 783.99,
]


def env(t: float, duration: float, attack: float = 0.012, release: float = 0.10) -> float:
    if t < 0 or t >= duration:
        return 0.0
    return min(1.0, t / max(attack, 1e-5), (duration - t) / max(release, 1e-5))


def osc(freq: float, t: float, bright: float = 0.0) -> float:
    phase = TAU * freq * t
    return math.sin(phase) * (1.0 - bright) + math.sin(phase * 2.0) * bright * 0.32


def render(output: Path) -> None:
    total = round(DURATION * RATE)
    rng = random.Random(24021)
    left = array("h")
    right = array("h")
    chord_events = []
    bass_events = []
    melody_events = []
    drum_events = []

    for beat_index in range(BARS * 4):
        bar = beat_index // 4
        beat_in_bar = beat_index % 4
        chord_events.append((beat_index * BEAT, CHORDS[bar % 4]))
        bass_events.append((beat_index * BEAT, CHORDS[bar % 4][0] / 2))
        if beat_in_bar in (1, 3):
            drum_events.append((beat_index * BEAT, "snare"))
        drum_events.append((beat_index * BEAT, "hat"))
    for step in range(BARS * 8):
        note = MELODY[(step + (step // 16) * 2) % len(MELODY)]
        melody_events.append((step * BEAT / 2, note))

    chord_i = bass_i = melody_i = drum_i = 0
    active_chords = []
    active_bass = []
    active_melody = []
    active_drums = []

    for n in range(total):
        t = n / RATE
        while chord_i < len(chord_events) and chord_events[chord_i][0] <= t:
            active_chords.append((chord_events[chord_i][0], chord_events[chord_i][1]))
            chord_i += 1
        while bass_i < len(bass_events) and bass_events[bass_i][0] <= t:
            active_bass.append((bass_events[bass_i][0], bass_events[bass_i][1]))
            bass_i += 1
        while melody_i < len(melody_events) and melody_events[melody_i][0] <= t:
            active_melody.append((melody_events[melody_i][0], melody_events[melody_i][1]))
            melody_i += 1
        while drum_i < len(drum_events) and drum_events[drum_i][0] <= t:
            active_drums.append((drum_events[drum_i][0], drum_events[drum_i][1], rng.random()))
            drum_i += 1

        active_chords = [(s, c) for s, c in active_chords if t - s < 0.48]
        active_bass = [(s, f) for s, f in active_bass if t - s < 0.46]
        active_melody = [(s, f) for s, f in active_melody if t - s < 0.27]
        active_drums = [(s, k, r) for s, k, r in active_drums if t - s < 0.20]

        l = r = 0.0
        for start, chord in active_chords:
            dt = t - start
            e = env(dt, 0.46, 0.025, 0.22) * 0.075
            for j, f in enumerate(chord):
                v = osc(f, dt, 0.12)
                l += v * e * (0.78 if j % 2 else 1.0)
                r += v * e * (1.0 if j % 2 else 0.78)
        for start, f in active_bass:
            dt = t - start
            v = math.sin(TAU * f * dt) * env(dt, 0.43, 0.006, 0.13) * 0.19
            l += v
            r += v
        for start, f in active_melody:
            dt = t - start
            e = env(dt, 0.245, 0.006, 0.095) * 0.13
            v = osc(f, dt, 0.30) * e
            l += v * 0.92
            r += v
        for start, kind, seed in active_drums:
            dt = t - start
            if kind == "hat":
                noise = math.sin((dt * 17311.0 + seed) * TAU) * math.sin((dt * 7919.0 + seed) * TAU)
                v = noise * math.exp(-dt * 38.0) * 0.035
            else:
                noise = math.sin((dt * 1031.0 + seed) * TAU)
                v = (noise * math.exp(-dt * 20.0) * 0.09
                     + math.sin(TAU * (105.0 - 35.0 * dt) * dt) * math.exp(-dt * 24.0) * 0.08)
            l += v * 0.96
            r += v

        # Gentle stereo width and soft clipping.
        l = math.tanh(l * 1.35) * 0.82
        r = math.tanh(r * 1.35) * 0.82
        left.append(max(-32768, min(32767, round(l * 32767))))
        right.append(max(-32768, min(32767, round(r * 32767))))

    # 25 ms equal-power-ish crossfade makes the musical loop seam unobtrusive.
    fade = round(0.025 * RATE)
    for i in range(fade):
        p = i / fade
        tail = total - fade + i
        left[tail] = round(left[tail] * (1.0 - p) + left[i] * p)
        right[tail] = round(right[tail] * (1.0 - p) + right[i] * p)

    output.parent.mkdir(parents=True, exist_ok=True)
    interleaved = array("h")
    for l, r in zip(left, right):
        interleaved.append(l)
        interleaved.append(r)
    if interleaved.itemsize != 2:
        raise RuntimeError("Expected 16-bit native samples")
    if __import__("sys").byteorder != "little":
        interleaved.byteswap()
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(interleaved.tobytes())
    print(f"Created {output}: {DURATION:.1f}s, {RATE} Hz, stereo, 16-bit PCM")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/tv-time/sound/bgm_home.wav"))
    args = parser.parse_args()
    render(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
