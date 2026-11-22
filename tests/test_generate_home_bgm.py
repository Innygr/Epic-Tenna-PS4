from __future__ import annotations

import math
import sys
import tempfile
import unittest
import wave
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from generate_home_bgm import RATE, render


class GenerateHomeBgmTests(unittest.TestCase):
    def test_render_is_stereo_48khz_16bit_and_loop_edges_are_smooth(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "bgm_home.wav"
            render(output)

            with wave.open(str(output), "rb") as wav:
                self.assertEqual(wav.getnchannels(), 2)
                self.assertEqual(wav.getsampwidth(), 2)
                self.assertEqual(wav.getframerate(), RATE)
                self.assertAlmostEqual(wav.getnframes() / RATE, 32.0, places=3)
                samples = array("h")
                samples.frombytes(wav.readframes(wav.getnframes()))
                if sys.byteorder != "little":
                    samples.byteswap()

            self.assertEqual(samples[0], 0)
            self.assertEqual(samples[-1], 0)
            self.assertLess(abs(samples[1] - samples[0]), 100)
            self.assertLess(abs(samples[-1] - samples[-2]), 100)
            self.assertLess(max(abs(x) for x in samples), 32767)
            self.assertGreater(max(abs(x) for x in samples), 1000)

            # Both edge fades should be quieter than the adjacent interior.
            edge_frames = round(0.005 * RATE)
            edge_samples = 2 * edge_frames
            first_edge = samples[:edge_samples]
            first_inner = samples[edge_samples : 2 * edge_samples]
            last_inner = samples[-2 * edge_samples : -edge_samples]
            last_edge = samples[-edge_samples:]
            rms = lambda block: math.sqrt(sum(x * x for x in block) / len(block))
            self.assertLess(rms(first_edge), rms(first_inner))
            self.assertLess(rms(last_edge), rms(last_inner))


if __name__ == "__main__":
    unittest.main()
