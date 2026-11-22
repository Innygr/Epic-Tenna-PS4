import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_dynamic_scene as dynamic


class DynamicSceneTests(unittest.TestCase):
    def test_dds_header_and_payload(self):
        from PIL import Image
        image = Image.new("RGB", (8, 8), (220, 30, 20))
        data = dynamic.dds_file(image)
        self.assertEqual(data[:4], b"DDS ")
        self.assertEqual(len(data), 128 + (8 * 8 // 2))
        self.assertEqual(data[84:88], b"DXT1")

    def test_scene_xml_has_looping_frame_sequence(self):
        xml_text = dynamic.scene_xml(12)
        root = ET.fromstring(xml_text)
        self.assertEqual(root.tag, "raf")
        self.assertEqual(len(root.findall("material")), 12)
        self.assertEqual(len(root.findall("actor")), 12)
        cases = root.find("sequence").findall("case")
        self.assertEqual(len(cases), 12)
        self.assertIn('id="bg11"', ET.tostring(cases[-1], encoding="unicode"))
        self.assertIn('id="bg00"', ET.tostring(cases[-1], encoding="unicode"))

    def test_frame_render_dimensions(self):
        frame = dynamic.render_frame(0)
        self.assertEqual(frame.size, (640, 360))
        self.assertEqual(frame.mode, "RGB")


if __name__ == "__main__":
    unittest.main()
