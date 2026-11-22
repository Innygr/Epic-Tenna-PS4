import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from audit_package_inputs import PackageAuditError, build_package_audit
from build_gp4 import build_gp4_xml
from build_param_sfx import build_param_sfx
from build_param_sfo import build_param_sfo_bytes


class PackageAuditTests(unittest.TestCase):
    def make_inputs(self, root: Path, title_id: str = "CUSA12345") -> tuple[Path, Path]:
        staging = root / "Image0"
        (staging / "sce_sys").mkdir(parents=True)
        (staging / "texture" / "background").mkdir(parents=True)
        theme_xml = (
            '<?xml version="1.0"?><theme><format-version>4.0</format-version>'
            '<themecolor>2</themecolor><label>TV-TIME</label>'
            '<fontcolor>#FFFFF0DC</fontcolor><fontshadowcolor>#FF000000</fontshadowcolor>'
            '<focuscolor>#FFFFD400</focuscolor><homescreen-dimmer>#00FFFFFF</homescreen-dimmer>'
            '<functionscreen-dimmer>#00FFFFFF</functionscreen-dimmer>'
            '<titlename-dimmer>#00FFFFFF</titlename-dimmer><homebgm-enable>False</homebgm-enable></theme>'
        )
        theme_path = staging / "theme.xml"
        theme_path.write_text(theme_xml, encoding="utf-8")
        sfx = build_param_sfx(
            title="TV TIME",
            title_id=title_id,
            content_prefix="UP9000",
            edition="TVTIME0000000000",
            date_text="20261121",
        )
        sfo_bytes = build_param_sfo_bytes(sfx)
        sfo_path = staging / "sce_sys" / "param.sfo"
        sfo_path.write_bytes(sfo_bytes)
        (staging / "sce_sys" / "icon0.png").write_bytes(b"icon-fixture")
        (staging / "texture" / "background" / "homescreen.png").write_bytes(b"wallpaper-fixture")
        content_id = f"UP9000-{title_id}_00-TVTIME0000000000"
        manifest = {
            "status": "theme-staging-only; not an installable package",
            "not_generated": ["installable .pkg"],
            "theme_descriptor": {
                "path": "theme.xml",
                "bytes": theme_path.stat().st_size,
                "sha256": hashlib.sha256(theme_path.read_bytes()).hexdigest(),
            },
            "optional_audio": {"included": False},
            "package_metadata": {
                "path": "sce_sys/param.sfo",
                "included": True,
                "bytes": len(sfo_bytes),
                "sha256": hashlib.sha256(sfo_bytes).hexdigest(),
                "title_id": title_id,
                "content_id": content_id,
            },
        }
        (staging / "STAGING-MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        gp4 = root / "tv-time.gp4"
        gp4.write_text(
            build_gp4_xml(staging, timestamp="2026-11-21 12:30:00"),
            encoding="utf-8",
        )
        return staging, gp4

    def test_production_inputs_are_audited_and_hashed(self):
        with tempfile.TemporaryDirectory() as temp:
            staging, gp4 = self.make_inputs(Path(temp))
            report = build_package_audit(staging, gp4)
            self.assertEqual(report["status"], "production-inputs-audited")
            self.assertEqual(report["package"]["title_id"], "CUSA12345")
            self.assertFalse(report["package"]["installable_pkg_created"])
            self.assertEqual(report["gp4"]["file_count"], 4)
            self.assertEqual(
                [item["path"] for item in report["package_files"]],
                ["sce_sys/icon0.png", "sce_sys/param.sfo", "theme.xml", "texture/background/homescreen.png"],
            )
            self.assertTrue(all(len(item["sha256"]) == 64 for item in report["package_files"]))

    def test_ci_fixture_identity_is_rejected_by_default(self):
        with tempfile.TemporaryDirectory() as temp:
            staging, gp4 = self.make_inputs(Path(temp), title_id="CUSA00000")
            with self.assertRaisesRegex(PackageAuditError, "CI fixtures"):
                build_package_audit(staging, gp4)

    def test_ci_fixture_requires_explicit_override_and_is_marked(self):
        with tempfile.TemporaryDirectory() as temp:
            staging, gp4 = self.make_inputs(Path(temp), title_id="CUSA00000")
            report = build_package_audit(staging, gp4, allow_ci_fixture=True)
            self.assertEqual(report["status"], "fixture-only-inputs-audited")
            self.assertTrue(report["package"]["ci_fixture_identity"])

    def test_gp4_that_omits_a_staged_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            staging, gp4 = self.make_inputs(Path(temp))
            (staging / "texture" / "background" / "extra.png").write_bytes(b"not-in-gp4")
            with self.assertRaises(PackageAuditError):
                build_package_audit(staging, gp4)

    def test_manifest_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            staging, gp4 = self.make_inputs(Path(temp))
            theme = staging / "theme.xml"
            theme.write_text(theme.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(PackageAuditError, "SHA-256"):
                build_package_audit(staging, gp4)


if __name__ == "__main__":
    unittest.main()
