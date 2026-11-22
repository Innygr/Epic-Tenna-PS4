#!/usr/bin/env python3
"""Render a red/yellow stereo waveform overview for the TV TIME music master."""
from __future__ import annotations

import argparse
import math
import sys
import wave
from array import array
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1600, 760
BG = (18, 16, 22)
PANEL = (35, 30, 37)
GRID = (77, 65, 66)
TEXT = (255, 246, 222)
MUTED = (181, 165, 151)
RED = (238, 57, 48)
YELLOW = (255, 207, 48)


def font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def read_stereo(path: Path) -> tuple[int, array, array]:
    if not path.is_file() or path.suffix.lower() != ".wav":
        raise ValueError("input must be an existing .wav file")
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 2 or wav.getsampwidth() != 2:
            raise ValueError("expected stereo 16-bit PCM WAV")
        rate = wav.getframerate()
        if rate <= 0:
            raise ValueError("WAV sample rate must be greater than zero")
        frames = wav.getnframes()
        raw = wav.readframes(frames)
        if len(raw) != frames * 4:
            raise ValueError("WAV frame data is truncated")
    samples = array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    return rate, samples[0::2], samples[1::2]


def render(wav_path: Path, output: Path) -> None:
    rate, left, right = read_stereo(wav_path)
    if not left:
        raise ValueError("WAV contains no audio frames")

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.text((64, 38), "TV TIME  /  HOME BROADCAST", font=font(34), fill=YELLOW)
    draw.text((64, 91), f"STEREO MASTER  •  {rate:,} Hz  •  {len(left) / rate:.2f} seconds",
              font=font(18), fill=MUTED)

    plot_x, plot_w = 112, WIDTH - 160
    panel_h, gap = 230, 36
    top = 160
    columns = plot_w

    for channel_index, (label, values, accent) in enumerate(
        (("LEFT CHANNEL", left, RED), ("RIGHT CHANNEL", right, YELLOW))
    ):
        y0 = top + channel_index * (panel_h + gap)
        draw.rounded_rectangle((64, y0, WIDTH - 64, y0 + panel_h), radius=18, fill=PANEL)
        draw.text((plot_x, y0 + 16), label, font=font(16), fill=TEXT)
        center = y0 + 130
        amplitude = 78
        draw.line((plot_x, center, plot_x + plot_w, center), fill=GRID, width=1)
        for fraction in (0.5, -0.5, 1.0, -1.0):
            gy = center - int(fraction * amplitude)
            draw.line((plot_x, gy, plot_x + plot_w, gy), fill=GRID, width=1)
        # Min/max envelope keeps transients visible without plotting every sample.
        total = len(values)
        for x in range(columns):
            start = x * total // columns
            end = max(start + 1, (x + 1) * total // columns)
            segment = values[start:end]
            low = min(segment)
            high = max(segment)
            y_high = center - int(high / 32768 * amplitude)
            y_low = center - int(low / 32768 * amplitude)
            draw.line((plot_x + x, y_high, plot_x + x, y_low), fill=accent, width=1)

        duration = len(values) / rate
        for tick in range(0, int(math.ceil(duration)) + 1, 4):
            x = plot_x + round(tick / duration * plot_w)
            if x <= plot_x + plot_w:
                draw.line((x, y0 + 205, x, y0 + 213), fill=MUTED, width=1)
                draw.text((x - 12, y0 + 214), f"{tick}s", font=font(11), fill=MUTED)

    draw.text((64, HEIGHT - 38),
              "Amplitude envelope preview • visual inspection aid, not a loudness or listening test",
              font=font(14), fill=MUTED)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    print(f"Created waveform overview: {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        render(args.wav, args.output)
    except (OSError, ValueError, wave.Error) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
