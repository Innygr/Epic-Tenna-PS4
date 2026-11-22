from __future__ import annotations

import sys
import tempfile
import unittest
import wave
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from analyze_home_bgm import analyze
from generate_home_bgm import RATE, render


class AnalyzeHomeBgmTests(unittest.TestCase):
    def test_generated_master_passes_quality_report(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "bgm_home.wav"
            render(source)
            report = analyze(source)

        self.assertTrue(report["passed"], report["checks"])
        self.assertTrue(all(report["checks"].values()))
        self.assertGreater(report["combined"]["mean_absolute_channel_delta"], 10)
        self.assertEqual(report["combined"]["clipped_samples"], 0)
        self.assertLess(abs(report["left"]["dc_offset"]), 100)
        self.assertLess(abs(report["right"]["dc_offset"]), 100)

    def test_rejects_mono_input(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "mono.wav"
            with wave.open(str(source), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(RATE)
                wav.writeframes(array("h", [0] * RATE).tobytes())
            with self.assertRaisesRegex(ValueError, "expected stereo"):
                analyze(source)


if __name__ == "__main__":
    unittest.main()
