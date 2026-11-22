from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import measure_home_bgm as measure
from build_theme_pkg import PackageBuildError


class MeasureHomeBgmTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.at9 = self.root / "bgm_home.at9"
        self.at9.write_bytes(b"fixture-at9")
        self.tool_dir = self.root / "tools"
        self.tool_dir.mkdir()
        self.tool = self.tool_dir / "orbis-pub-cmd"
        self.tool.write_bytes(b"stub")
        ext = self.tool_dir / "ext"
        ext.mkdir()
        for name in ("sc.exe", "di.exe", "libatrac9.dll"):
            (ext / name).write_bytes(b"stub")

    def tearDown(self):
        self.temp.cleanup()

    def runner_with(self, output, code=0):
        commands = []

        def run(command, **kwargs):
            commands.append(command)
            return SimpleNamespace(returncode=code, stdout=output, stderr="")
        return run, commands

    def test_parses_measured_lkfs_value(self):
        runner, commands = self.runner_with("Integrated loudness: -23.47 LKFS")
        report = measure.measure_loudness(self.at9, self.tool, runner=runner)
        self.assertEqual(report["loudness_lkfs"], -23.47)
        self.assertEqual(report["metadata_argument"], "-23.47")
        self.assertEqual(commands[0][1], "file_calc_loudness")

    def test_missing_loudness_output_is_rejected(self):
        runner, _ = self.runner_with("measurement unavailable")
        with self.assertRaisesRegex(PackageBuildError, "did not report an LKFS"):
            measure.measure_loudness(self.at9, self.tool, runner=runner)

    def test_out_of_range_loudness_is_rejected(self):
        runner, _ = self.runner_with("loudness: 2.00 LKFS")
        with self.assertRaisesRegex(PackageBuildError, "outside the supported range"):
            measure.measure_loudness(self.at9, self.tool, runner=runner)

    def test_nonzero_tool_exit_is_rejected(self):
        runner, _ = self.runner_with("error", code=4)
        with self.assertRaisesRegex(PackageBuildError, "exit code 4"):
            measure.measure_loudness(self.at9, self.tool, runner=runner)

    def test_missing_atrac_library_is_rejected(self):
        (self.tool_dir / "ext" / "libatrac9.dll").unlink()
        with self.assertRaisesRegex(PackageBuildError, "libatrac9.dll"):
            measure.measure_loudness(self.at9, self.tool)

    def test_wrong_input_extension_is_rejected(self):
        wav = self.root / "bgm.wav"
        wav.write_bytes(b"wav")
        with self.assertRaisesRegex(PackageBuildError, "existing .at9"):
            measure.measure_loudness(wav, self.tool)


if __name__ == "__main__":
    unittest.main()
