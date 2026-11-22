from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import build_theme_pkg as maker
from audit_package_inputs import PackageAuditError


class BuildThemePkgTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.staging = self.root / "Image0"
        self.staging.mkdir()
        self.gp4 = self.root / "tv-time.gp4"
        self.gp4.write_text("<psproject />", encoding="utf-8")

        self.package_files = [
            {"path": "sce_sys/param.sfo", "bytes": 64, "sha256": "a"},
            {"path": "sce_sys/icon0.png", "bytes": 64, "sha256": "b"},
            {"path": "sce_sys/pic1.png", "bytes": 64, "sha256": "c"},
            {"path": "theme.xml", "bytes": 64, "sha256": "d"},
            {"path": "texture/background/homescreen.png", "bytes": 64, "sha256": "e"},
        ]
        for record in self.package_files:
            target = self.staging / record["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"fixture")

        self.tool_dir = self.root / "packager"
        self.tool_dir.mkdir()
        self.tool = self.tool_dir / "orbis-pub-cmd"
        self.tool.write_bytes(b"stub")
        (self.tool_dir / "ext").mkdir()

        self.output = self.root / "out" / "TV-TIME.pkg"
        self.content_id = "UP9000-CUSA12345_00-TVTIME0000000000"
        self.audit = {
            "package": {
                "title_id": "CUSA12345",
                "content_id": self.content_id,
                "ci_fixture_identity": False,
            },
            "gp4": {"sha256": "fixture"},
            "package_files": self.package_files,
        }
        self.gp4_info = {
            "content_id": self.content_id,
            "passcode": "0" * 32,
        }

    def tearDown(self):
        self.temp.cleanup()

    def _patched_inputs(self):
        return (
            patch.object(maker, "build_package_audit", return_value=self.audit),
            patch.object(maker, "validate_gp4_xml", return_value=self.gp4_info),
        )

    def _successful_runner(self, *, omit_entry=None, bad_magic=False, create_exit=0):
        expected = maker.expected_pkg_entries(self.package_files)
        if omit_entry:
            expected = [entry for entry in expected if entry != omit_entry]
        commands = []

        def run(command, **kwargs):
            commands.append(command)
            if command[1] == "img_create":
                if create_exit:
                    return SimpleNamespace(returncode=create_exit, stdout="", stderr="build failed")
                output_dir = Path(command[-1])
                package = output_dir / f"{self.content_id}.pkg"
                magic = b"NOPE" if bad_magic else maker.PKG_MAGIC
                package.write_bytes(magic + (b"\0" * (1024 * 1024 - 4)))
                return SimpleNamespace(returncode=0, stdout="created", stderr="")
            if command[1] == "img_file_list":
                listing = "\n".join(expected)
                return SimpleNamespace(returncode=0, stdout=listing, stderr="")
            raise AssertionError(f"unexpected tool command: {command}")

        return run, commands

    def test_builds_pkg_and_checks_every_staged_target(self):
        run, commands = self._successful_runner()
        with self._patched_inputs()[0], self._patched_inputs()[1]:
            report = maker.build_theme_pkg(
                self.staging,
                self.gp4,
                self.output,
                self.tool,
                runner=run,
            )

        self.assertTrue(self.output.is_file())
        self.assertEqual(self.output.read_bytes()[:4], maker.PKG_MAGIC)
        self.assertEqual(report["package"]["content_id"], self.content_id)
        self.assertEqual(report["checks"]["required_package_entries"], len(self.package_files))
        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[0][1], "img_create")
        self.assertIn("--oformat", commands[0])
        self.assertEqual(commands[0][commands[0].index("--oformat") + 1], "pkg")
        self.assertEqual(commands[1][1], "img_file_list")
        self.assertEqual(commands[1][commands[1].index("--passcode") + 1], "0" * 32)

    def test_theme_metadata_is_mapped_to_sc0(self):
        mapped = maker.expected_pkg_entries(self.package_files)
        self.assertIn("Sc0/param.sfo", mapped)
        self.assertIn("Sc0/icon0.png", mapped)
        self.assertIn("Sc0/pic1.png", mapped)
        self.assertIn("Image0/theme.xml", mapped)
        self.assertNotIn("Image0/sce_sys/param.sfo", mapped)

    def test_missing_package_entry_fails_without_publishing_output(self):
        run, _ = self._successful_runner(omit_entry="Image0/theme.xml")
        with self._patched_inputs()[0], self._patched_inputs()[1]:
            with self.assertRaisesRegex(maker.PackageBuildError, "missing required theme entries"):
                maker.build_theme_pkg(
                    self.staging, self.gp4, self.output, self.tool, runner=run
                )
        self.assertFalse(self.output.exists())

    def test_bad_pkg_magic_is_rejected(self):
        run, _ = self._successful_runner(bad_magic=True)
        with self._patched_inputs()[0], self._patched_inputs()[1]:
            with self.assertRaisesRegex(maker.PackageBuildError, "header magic"):
                maker.build_theme_pkg(
                    self.staging, self.gp4, self.output, self.tool, runner=run
                )
        self.assertFalse(self.output.exists())

    def test_packager_failure_is_reported(self):
        run, _ = self._successful_runner(create_exit=7)
        with self._patched_inputs()[0], self._patched_inputs()[1]:
            with self.assertRaisesRegex(maker.PackageBuildError, "exit code 7"):
                maker.build_theme_pkg(
                    self.staging, self.gp4, self.output, self.tool, runner=run
                )
        self.assertFalse(self.output.exists())

    def test_prebuild_audit_failure_stops_before_external_tool(self):
        run, commands = self._successful_runner()
        with patch.object(maker, "build_package_audit", side_effect=PackageAuditError("fixture ID")):
            with self.assertRaisesRegex(maker.PackageBuildError, "pre-build package audit failed"):
                maker.build_theme_pkg(
                    self.staging, self.gp4, self.output, self.tool, runner=run
                )
        self.assertEqual(commands, [])
        self.assertFalse(self.output.exists())

    def test_output_must_be_pkg(self):
        with self.assertRaisesRegex(maker.PackageBuildError, "end in .pkg"):
            maker.build_theme_pkg(
                self.staging, self.gp4, self.root / "out" / "wrong.zip", self.tool
            )

    def test_existing_output_requires_force(self):
        self.output.parent.mkdir(parents=True)
        self.output.write_bytes(b"existing")
        run, _ = self._successful_runner()
        with self._patched_inputs()[0], self._patched_inputs()[1]:
            with self.assertRaisesRegex(maker.PackageBuildError, "already exists"):
                maker.build_theme_pkg(
                    self.staging, self.gp4, self.output, self.tool, runner=run
                )
        self.assertEqual(self.output.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
