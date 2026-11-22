from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "icons"
ICON_NAMES = ("settings", "network", "friends", "messages", "media", "power")
PALETTE = {"#FFD400", "#ED1C24"}


def test_all_six_icon_masters_share_the_tv_time_canvas_and_palette():
    for name in ICON_NAMES:
        path = ICON_DIR / f"{name}.svg"
        assert path.is_file(), f"Missing {name} icon master"
        root = ET.parse(path).getroot()
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib.get("width") == "256"
        assert root.attrib.get("height") == "256"
        assert root.attrib.get("viewBox") == "0 0 256 256"

        colours = {
            value.upper()
            for element in root.iter()
            for key, value in element.attrib.items()
            if key in {"fill", "stroke"} and re.fullmatch(r"#[0-9A-Fa-f]{6}", value)
        }
        assert colours, f"{name} has no explicit palette colours"
        assert colours <= PALETTE, f"{name} introduces off-palette colours: {colours - PALETTE}"

        title = root.find("{http://www.w3.org/2000/svg}title")
        assert title is not None and "TV TIME" in (title.text or "")
