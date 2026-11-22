#!/usr/bin/env python3
"""Offline tests for the TV TIME home-music conversion wrapper."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONVERTER = ROOT / "tools" / "convert_home_bgm.py"


def make_wav(path: Path, *, channels: int = 2, rate: int = 48_000) -> None:
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"\0\0" * channels * rate)


def make_encoder(path: Path, *, exit_code: int = 0, output_bytes: int = 64) -> Path:
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        f"payload = b'X' * {output_bytes}\n"
        "pathlib.Path(sys.argv[-1]).write_bytes(payload)\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | 0o111)
    return path


class ConvertHomeBgmTests(unittest.TestCase):
    def run_converter(self, source: Path, output: Path, encoder: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable, str(CONVERTER),
                "--input", str(source),
                "--output", str(output),
                "--at9tool", str(encoder),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_success_creates_nonempty_at9(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source, output = folder / "source.wav", folder / "bgm_home.at9"
            make_wav(source)
            encoder = make_encoder(folder / "at9tool")
            result = self.run_converter(source, output, encoder)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), b"X" * 64)
            self.assertIn("144 kbps", result.stdout)

    def test_rejects_non_stereo_input_before_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source, output = folder / "source.wav", folder / "bgm_home.at9"
            make_wav(source, channels=1)
            encoder = make_encoder(folder / "at9tool")
            result = self.run_converter(source, output, encoder)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected stereo WAV", result.stderr)
            self.assertFalse(output.exists())

    def test_refuses_to_overwrite_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source, output = folder / "source.wav", folder / "bgm_home.at9"
            make_wav(source)
            output.write_bytes(b"keep")
            encoder = make_encoder(folder / "at9tool")
            result = self.run_converter(source, output, encoder)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), b"keep")

    def test_removes_partial_output_when_encoder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source, output = folder / "source.wav", folder / "bgm_home.at9"
            make_wav(source)
            encoder = make_encoder(folder / "at9tool", exit_code=2)
            result = self.run_converter(source, output, encoder)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_removes_output_over_two_mib(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source, output = folder / "source.wav", folder / "bgm_home.at9"
            make_wav(source)
            encoder = make_encoder(folder / "at9tool", output_bytes=2 * 1024 * 1024 + 1)
            result = self.run_converter(source, output, encoder)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exceeds the 2 MiB", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
