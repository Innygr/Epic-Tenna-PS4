import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_theme_descriptor import build_theme_xml, validate_theme_xml


class ThemeDescriptorTests(unittest.TestCase):
    def test_default_descriptor_uses_red_and_yellow_tv_time_palette(self):
        xml_text = build_theme_xml()
        root = ET.fromstring(xml_text)
        self.assertEqual(root.findtext("format-version"), "4.0")
        self.assertEqual(root.findtext("themecolor"), "2")
        self.assertEqual(root.findtext("focuscolor"), "#FFFFD400")
        self.assertEqual(root.findtext("fontcolor"), "#FFFFF0DC")
        self.assertEqual(root.findtext("homebgm-enable"), "False")
        result = validate_theme_xml(xml_text)
        self.assertEqual(result["themecolor"], 2)
        self.assertFalse(result["homebgm_enabled"])

    def test_descriptor_enables_music_only_when_requested(self):
        result = validate_theme_xml(build_theme_xml(homebgm_enabled=True))
        self.assertTrue(result["homebgm_enabled"])

    def test_label_is_sanitized(self):
        root = ET.fromstring(build_theme_xml(label="TV TIME / ON AIR"))
        self.assertEqual(root.findtext("label"), "TV-TIME-ON-AIR")

    def test_invalid_theme_colour_is_rejected(self):
        with self.assertRaises(ValueError):
            build_theme_xml(themecolor=8)

    def test_missing_required_element_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_theme_xml("<theme><format-version>4.0</format-version></theme>")


if __name__ == "__main__":
    unittest.main()
