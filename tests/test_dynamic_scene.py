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

    def test_scene_xml_uses_one_shared_plane_and_loops(self):
        root = ET.fromstring(dynamic.scene_xml(12))
        self.assertEqual(root.tag, "raf")
        model = root.find("model")
        self.assertEqual(model.attrib, {"id": "plane", "file": "plane.fbx"})
        self.assertEqual(len(root.findall("material")), 12)
        self.assertEqual(len(root.findall("actor")), 12)
        cases = root.find("sequence").findall("case")
        self.assertEqual(len(cases), 12)
        self.assertEqual(cases[0].attrib["wait"], "0.12")
        self.assertEqual(cases[-1].findall("actor")[0].attrib["id"], "f11")
        self.assertEqual(cases[-1].findall("actor")[1].attrib["id"], "f00")
        self.assertTrue(all(a.attrib["model"] == "plane" for a in root.findall("actor")))
        self.assertNotIn("target", root.find("sequence").attrib)

    def test_plane_model_has_validated_xdm_structure(self):
        data = dynamic.plane_model_bytes()
        self.assertTrue(data.startswith(b"XDM.00.1MSP\\x00" + b"\\x00" * 4))
        result = dynamic.validate_plane_model(data)
        self.assertEqual(result["vertices"], 4)
        self.assertEqual(result["vertex_stride"], 14)
        self.assertGreater(result["bytes"], 128)

    def test_plane_geometry_matches_camera_aspect(self):
        half_w, half_h = dynamic.plane_half_size()
        self.assertAlmostEqual(half_w / half_h, 16 / 9, places=6)
        self.assertGreater(half_w, half_h)

    def test_frame_render_dimensions(self):
        frame = dynamic.render_frame(0)
        self.assertEqual(frame.size, (640, 360))
        self.assertEqual(frame.mode, "RGB")


if __name__ == "__main__":
    unittest.main()
