import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_param_sfx import build_param_sfx
from build_param_sfo import build_param_sfo_bytes
from build_gp4 import Gp4Error, build_gp4_xml, validate_gp4_xml


class Gp4Tests(unittest.TestCase):
    def make_staging(self, root: Path) -> Path:
        staging = root / "Image0"
        (staging / "sce_sys").mkdir(parents=True)
        (staging / "texture" / "background").mkdir(parents=True)
        (staging / "theme.xml").write_text(
            '<?xml version="1.0"?><theme><format-version>4.0</format-version>'
            '<themecolor>2</themecolor><label>TV-TIME</label>'
            '<fontcolor>#FFFFF0DC</fontcolor><fontshadowcolor>#FF000000</fontshadowcolor>'
            '<focuscolor>#FFFFD400</focuscolor><homescreen-dimmer>#00FFFFFF</homescreen-dimmer>'
            '<functionscreen-dimmer>#00FFFFFF</functionscreen-dimmer>'
            '<titlename-dimmer>#00FFFFFF</titlename-dimmer><homebgm-enable>False</homebgm-enable></theme>',
            encoding="utf-8",
        )
        sfx = build_param_sfx(
            title="TV TIME", title_id="CUSA12345",
            content_prefix="UP9000", edition="TVTIME0000000000",
            date_text="20261121",
        )
        (staging / "sce_sys" / "param.sfo").write_bytes(build_param_sfo_bytes(sfx))
        (staging / "sce_sys" / "icon0.png").write_bytes(b"png-fixture")
        (staging / "sce_sys" / "pic1.png").write_bytes(b"png-fixture")
        (staging / "texture" / "background" / "homescreen.png").write_bytes(b"png-fixture")
        (staging / "STAGING-MANIFEST.json").write_text(
            json.dumps({"status": "theme-staging-only; not an installable package"}),
            encoding="utf-8",
        )
        return staging

    def test_gp4_project_contains_theme_volume_and_all_files(self):
        with tempfile.TemporaryDirectory() as temp:
            staging = self.make_staging(Path(temp))
            xml_text = build_gp4_xml(
                staging,
                passcode="0" * 32,
                timestamp="2026-11-21 12:30:00",
            )
            result = validate_gp4_xml(
                xml_text,
                staging_dir=staging,
                expected_content_id="UP9000-CUSA12345_00-TVTIME0000000000",
            )
            self.assertEqual(result["file_count"], 6)
            self.assertEqual(result["content_id"], "UP9000-CUSA12345_00-TVTIME0000000000")
            self.assertIn("sce_sys/param.sfo", result["targets"])
            self.assertIn("texture/background/homescreen.png", result["targets"])

    def test_missing_binary_sfo_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            staging = self.make_staging(Path(temp))
            (staging / "sce_sys" / "param.sfo").unlink()
            with self.assertRaises(Gp4Error):
                build_gp4_xml(staging)

    def test_invalid_passcode_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            staging = self.make_staging(Path(temp))
            with self.assertRaises(Gp4Error):
                build_gp4_xml(staging, passcode="short")

    def test_modified_file_list_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            staging = self.make_staging(Path(temp))
            xml_text = build_gp4_xml(staging, timestamp="2026-11-21 12:30:00")
            changed = xml_text.replace("texture/background/homescreen.png", "texture/background/other.png")
            with self.assertRaises(Gp4Error):
                validate_gp4_xml(changed, staging_dir=staging)

    def test_escaped_content_paths_remain_valid_xml(self):
        with tempfile.TemporaryDirectory() as temp:
            staging = self.make_staging(Path(temp))
            xml_text = build_gp4_xml(staging, timestamp="2026-11-21 12:30:00")
            self.assertIn("orig_path=", xml_text)
            self.assertTrue(xml_text.startswith('<?xml version="1.0"'))

    def test_timestamp_format_is_enforced(self):
        with tempfile.TemporaryDirectory() as temp:
            staging = self.make_staging(Path(temp))
            with self.assertRaises(Gp4Error):
                build_gp4_xml(staging, timestamp="21/11/2026")


if __name__ == "__main__":
    unittest.main()
