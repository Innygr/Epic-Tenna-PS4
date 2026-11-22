#!/usr/bin/env python3
"""Convert the TV TIME WAV master to the PS4 theme ATRAC9 music slot.

Requires a user-supplied Sony at9tool executable. The proprietary encoder is
not downloaded, bundled, or redistributed by this project.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import wave
from pathlib import Path


MAX_OUTPUT_BYTES = 2 * 1024 * 1024
EXPECTED_RATE = 48_000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("build/tv-time/sound/bgm_home.wav"),
        help="48 kHz stereo PCM WAV source master",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/tv-time/sound/bgm_home.at9"),
        help="destination AT9 file",
    )
    parser.add_argument(
        "--at9tool",
        default="at9tool",
        help="path to a compatible Sony at9tool executable",
    )
    args = parser.parse_args()

    source = args.input
    if not source.is_file():
        parser.error(f"input WAV does not exist: {source}")

    try:
        with wave.open(str(source), "rb") as audio:
            params = audio.getparams()
            duration = audio.getnframes() / audio.getframerate()
            if audio.getnchannels() != 2:
                raise SystemExit(f"FAIL: expected stereo WAV, got {params}")
            if audio.getsampwidth() != 2:
                raise SystemExit(f"FAIL: expected 16-bit PCM WAV, got {params}")
            if audio.getframerate() != EXPECTED_RATE:
                raise SystemExit(f"FAIL: expected 48000 Hz WAV, got {params}")
            if not 0 < duration <= 240:
                raise SystemExit(f"FAIL: duration must be between 0 and 240 seconds, got {duration:.2f}")
    except wave.Error as exc:
        raise SystemExit(f"FAIL: input is not a readable PCM WAV: {exc}") from exc

    executable = shutil.which(args.at9tool)
    if executable is None and Path(args.at9tool).is_file():
        executable = str(Path(args.at9tool).resolve())
    if executable is None:
        raise SystemExit(
            "FAIL: at9tool was not found. Supply --at9tool with your own "
            "compatible encoder; this repository does not bundle proprietary tools."
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise SystemExit(f"FAIL: refusing to overwrite existing output: {args.output}")

    command = [
        executable, "-e", "-br", "144", "-wholeloop",
        str(source.resolve()), str(args.output.resolve()),
    ]
    print("Encoding stereo 48 kHz WAV as looped 144 kbps ATRAC9...")
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        args.output.unlink(missing_ok=True)
        raise SystemExit(f"FAIL: at9tool exited with status {result.returncode}")
    if not args.output.is_file() or args.output.stat().st_size == 0:
        raise SystemExit("FAIL: encoder did not produce a non-empty AT9 file")
    output_size = args.output.stat().st_size
    if output_size > MAX_OUTPUT_BYTES:
        args.output.unlink(missing_ok=True)
        raise SystemExit(
            f"FAIL: AT9 output exceeds the 2 MiB PS4 theme music limit "
            f"({output_size} bytes)"
        )

    print(f"PASS: created {args.output} ({args.output.stat().st_size} bytes)")
    print("NOTE: encoder success and size are checked; console playback still requires testing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
