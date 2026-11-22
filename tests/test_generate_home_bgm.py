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

            # Check actual stereo content, not just the WAV channel header.
            left = samples[0::2]
            right = samples[1::2]
            mean_channel_delta = sum(abs(l - r) for l, r in zip(left, right)) / len(left)
            self.assertGreater(mean_channel_delta, 10)
            channel_rms = lambda block: math.sqrt(sum(x * x for x in block) / len(block))
            left_rms = channel_rms(left)
            right_rms = channel_rms(right)
            self.assertGreater(left_rms / right_rms, 0.75)
            self.assertLess(left_rms / right_rms, 1.25)

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

            # The four 8-second sections should have an intentional energy arc:
            # quieter intro, fuller main, quieter breakdown, stronger finale.
            section_rms = []
            frames_per_section = 8 * RATE
            for section in range(4):
                start = section * frames_per_section * 2
                end = (section + 1) * frames_per_section * 2
                section_rms.append(rms(samples[start:end]))
            self.assertGreater(section_rms[1], section_rms[0] * 1.06)
            self.assertLess(section_rms[2], section_rms[1] * 0.90)
            self.assertGreater(section_rms[3], section_rms[2] * 1.10)


if __name__ == "__main__":
    unittest.main()
