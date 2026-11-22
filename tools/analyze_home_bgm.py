#!/usr/bin/env python3
"""Analyze a generated TV TIME WAV master using only the Python standard library.

This is a source-master quality report, not a substitute for listening or
measuring the final ATRAC9 encode on the target playback chain.
"""
from __future__ import annotations

import argparse
import json
import math
import wave
from array import array
from pathlib import Path
from typing import Any


def dbfs(value: float) -> float | None:
    if value <= 0:
        return None
    return round(20.0 * math.log10(value / 32768.0), 2)


def analyze(path: Path) -> dict[str, Any]:
    source = path.expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".wav":
        raise ValueError("input must be an existing .wav file")

    with wave.open(str(source), "rb") as wav:
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        rate = wav.getframerate()
        frames = wav.getnframes()
        if channels != 2 or width != 2:
            raise ValueError(f"expected stereo 16-bit PCM, got {channels} channels / {width * 8}-bit")
        raw = wav.readframes(frames)
        if len(raw) != frames * channels * width:
            raise ValueError("WAV frame data is truncated")

    samples = array("h")
    samples.frombytes(raw)
    left = samples[0::2]
    right = samples[1::2]
    if not left:
        raise ValueError("WAV contains no audio frames")

    def channel_stats(values: array) -> dict[str, Any]:
        peak = max(abs(value) for value in values)
        mean = sum(values) / len(values)
        rms = math.sqrt(sum(value * value for value in values) / len(values))
        return {
            "peak": peak,
            "peak_dbfs": dbfs(float(peak)),
            "rms": round(rms, 2),
            "rms_dbfs": dbfs(rms),
            "dc_offset": round(mean, 3),
            "clipped_samples": sum(value in (-32768, 32767) for value in values),
        }

    l_stats = channel_stats(left)
    r_stats = channel_stats(right)
    l_rms = float(l_stats["rms"])
    r_rms = float(r_stats["rms"])
    denominator = math.sqrt(sum(x * x for x in left) * sum(y * y for y in right))
    correlation = (sum(x * y for x, y in zip(left, right)) / denominator) if denominator else 0.0
    delta = sum(abs(x - y) for x, y in zip(left, right)) / len(left)
    peak = max(int(l_stats["peak"]), int(r_stats["peak"]))
    ratio = l_rms / r_rms if r_rms else math.inf
    report = {
        "file": source.name,
        "bytes": source.stat().st_size,
        "sample_rate_hz": rate,
        "channels": channels,
        "sample_width_bits": width * 8,
        "duration_seconds": round(frames / rate, 3) if rate else 0,
        "left": l_stats,
        "right": r_stats,
        "combined": {
            "peak_dbfs": dbfs(float(peak)),
            "mean_absolute_channel_delta": round(delta, 2),
            "channel_correlation": round(correlation, 5),
            "left_right_rms_ratio": round(ratio, 5) if math.isfinite(ratio) else None,
            "clipped_samples": int(l_stats["clipped_samples"]) + int(r_stats["clipped_samples"]),
        },
        "checks": {
            "stereo_48khz_16bit": channels == 2 and width == 2 and rate == 48000,
            "duration_32_seconds": 31.9 <= frames / rate <= 32.1 if rate else False,
            "non_silent": peak > 1000,
            "no_full_scale_clipping": l_stats["clipped_samples"] == 0 and r_stats["clipped_samples"] == 0,
            "distinct_stereo_content": delta > 10,
            "balanced_channel_rms": 0.75 <= ratio <= 1.25 if math.isfinite(ratio) else False,
        },
    }
    report["passed"] = all(report["checks"].values())
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path)
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    args = parser.parse_args()
    try:
        report = analyze(args.wav)
    except (OSError, ValueError, wave.Error) as exc:
        parser.error(str(exc))
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Report: {args.output}")
    if not report["passed"]:
        print("FAIL: one or more source-master quality checks did not pass")
        return 1
    print("PASS: source-master quality checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
