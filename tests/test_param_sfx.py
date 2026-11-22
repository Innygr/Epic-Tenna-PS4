import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_param_sfx import ParamSfxError, build_param_sfx, validate_param_sfx


class ParamSfxTests(unittest.TestCase):
    def build(self, **kwargs):
        defaults = {
            "title": "TV TIME",
            "title_id": "CUSA12345",
            "content_prefix": "UP9000",
            "edition": "TVTIME0000000000",
            "date_text": "20261121",
        }
        defaults.update(kwargs)
        return build_param_sfx(**defaults)

    def test_theme_metadata_has_required_theme_values(self):
        xml_text = self.build()
        root = ET.fromstring(xml_text)
        params = {node.attrib["key"]: (node.attrib["fmt"], node.text) for node in root.findall("param")}
        self.assertEqual(params["CATEGORY"], ("utf8", "ac"))
        self.assertEqual(params["IRO_TAG"], ("int32", "2"))
        self.assertEqual(params["TITLE_ID"], ("utf8", "CUSA12345"))
        self.assertEqual(params["CONTENT_ID"][1], "UP9000-CUSA12345_00-TVTIME0000000000")
        self.assertEqual(params["PUBTOOLINFO"][1], "c_date=20261121")
        self.assertNotIn("APP_TYPE", params)
        self.assertNotIn("APP_VER", params)
        self.assertEqual(validate_param_sfx(xml_text)["TITLE"], "TV TIME")

    def test_optional_home_music_loudness_is_recorded(self):
        xml_text = self.build(bgm_loudness=-23.47)
        parsed = validate_param_sfx(xml_text)
        self.assertEqual(parsed["PUBTOOLINFO"], "c_date=20261121,bgmhome_loud=-23.47")

    def test_invalid_home_music_loudness_is_rejected(self):
        for value in (-101.0, 1.0, float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ParamSfxError):
                    self.build(bgm_loudness=value)

    def test_malformed_home_music_loudness_is_rejected(self):
        xml_text = self.build(bgm_loudness=-23.47).replace("bgmhome_loud=-23.47", "bgmhome_loud=very-loud")
        with self.assertRaises(ParamSfxError):
            validate_param_sfx(xml_text)

    def test_title_is_xml_escaped_and_round_trips(self):
        xml_text = self.build(title='TV TIME & "ON AIR"')
        parsed = validate_param_sfx(xml_text)
        self.assertEqual(parsed["TITLE"], 'TV TIME & "ON AIR"')

    def test_rows_are_sorted_by_key(self):
        root = ET.fromstring(self.build())
        keys = [node.attrib["key"] for node in root.findall("param")]
        self.assertEqual(keys, sorted(keys))

    def test_invalid_title_id_is_rejected(self):
        with self.assertRaises(ParamSfxError):
            self.build(title_id="BAD")

    def test_invalid_content_prefix_is_rejected(self):
        with self.assertRaises(ParamSfxError):
            self.build(content_prefix="bad")

    def test_invalid_edition_length_is_rejected(self):
        with self.assertRaises(ParamSfxError):
            self.build(edition="SHORT")

    def test_title_byte_limit_is_enforced(self):
        with self.assertRaises(ParamSfxError):
            self.build(title="é" * 65)

    def test_bad_date_is_rejected(self):
        with self.assertRaises(ParamSfxError):
            self.build(date_text="2026-11-21")

    def test_duplicate_keys_are_rejected(self):
        xml_text = self.build().replace(
            "</paramsfo>",
            '<param key="IRO_TAG" fmt="int32">2</param></paramsfo>',
        )
        with self.assertRaises(ParamSfxError):
            validate_param_sfx(xml_text)

    def test_wrong_theme_category_is_rejected(self):
        xml_text = self.build().replace(">ac</param>", ">gd</param>")
        with self.assertRaises(ParamSfxError):
            validate_param_sfx(xml_text)


if __name__ == "__main__":
    unittest.main()
