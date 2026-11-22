#!/usr/bin/env python3
"""Generate and validate the TV TIME PS4 theme.xml descriptor.

The selected values use the documented PS4 theme descriptor shape:
red system theme colour, yellow focus accent, warm-white text, and transparent
background dimmers. Home music is enabled only when a converted AT9 is staged.
"""
from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

FORMAT_VERSION = "4.0"
THEME_COLOR_RED = 2
FONT_COLOR = "#FFFFF0DC"
FONT_SHADOW_COLOR = "#FF000000"
FOCUS_COLOR_YELLOW = "#FFFFD400"
TRANSPARENT = "#00FFFFFF"
ARGB_RE = re.compile(r"^#[0-9A-Fa-f]{8}$")
LABEL_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def sanitize_label(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", (value or "").strip())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned[:64] or "TV-TIME"


def build_theme_xml(
    *,
    label: str = "TV-TIME",
    themecolor: int = THEME_COLOR_RED,
    homebgm_enabled: bool = False,
) -> str:
    try:
        color = int(themecolor)
    except (TypeError, ValueError) as exc:
        raise ValueError("themecolor must be an integer from 0 to 7") from exc
    if not 0 <= color <= 7:
        raise ValueError("themecolor must be between 0 and 7")
    safe_label = sanitize_label(label)
    rows = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<theme>",
        f"    <format-version>{FORMAT_VERSION}</format-version>",
        f"    <themecolor>{color}</themecolor>",
        f"    <label>{safe_label}</label>",
        f"    <fontcolor>{FONT_COLOR}</fontcolor>",
        f"    <fontshadowcolor>{FONT_SHADOW_COLOR}</fontshadowcolor>",
        f"    <focuscolor>{FOCUS_COLOR_YELLOW}</focuscolor>",
        f"    <homescreen-dimmer>{TRANSPARENT}</homescreen-dimmer>",
        f"    <functionscreen-dimmer>{TRANSPARENT}</functionscreen-dimmer>",
        f"    <titlename-dimmer>{TRANSPARENT}</titlename-dimmer>",
        f"    <homebgm-enable>{'True' if homebgm_enabled else 'False'}</homebgm-enable>",
        "</theme>",
        "",
    ]
    xml_text = "\n".join(rows)
    validate_theme_xml(xml_text)
    return xml_text


def validate_theme_xml(xml_text: str) -> dict[str, object]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"theme.xml is not valid XML: {exc}") from exc
    if root.tag != "theme":
        raise ValueError("theme.xml root element must be <theme>")
    required = (
        "format-version", "themecolor", "label", "fontcolor",
        "fontshadowcolor", "focuscolor", "homescreen-dimmer",
        "functionscreen-dimmer", "titlename-dimmer", "homebgm-enable",
    )
    values = {}
    for tag in required:
        node = root.find(tag)
        if node is None or node.text is None:
            raise ValueError(f"theme.xml is missing <{tag}>")
        values[tag] = node.text.strip()
    if values["format-version"] != FORMAT_VERSION:
        raise ValueError("unsupported TV TIME theme.xml format-version")
    if not LABEL_RE.fullmatch(str(values["label"])):
        raise ValueError("theme label contains unsupported characters")
    try:
        color = int(str(values["themecolor"]))
    except ValueError as exc:
        raise ValueError("theme themecolor is not an integer") from exc
    if not 0 <= color <= 7:
        raise ValueError("theme themecolor must be between 0 and 7")
    for tag in ("fontcolor", "fontshadowcolor", "focuscolor",
                "homescreen-dimmer", "functionscreen-dimmer", "titlename-dimmer"):
        if not ARGB_RE.fullmatch(str(values[tag])):
            raise ValueError(f"<{tag}> must be an eight-digit ARGB colour")
    bgm = str(values["homebgm-enable"])
    if bgm not in ("True", "False"):
        raise ValueError("<homebgm-enable> must be True or False")
    return {
        "format_version": str(values["format-version"]),
        "themecolor": color,
        "label": str(values["label"]),
        "homebgm_enabled": bgm == "True",
        "focuscolor": str(values["focuscolor"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/tv-time/Image0/theme.xml"))
    parser.add_argument("--label", default="TV-TIME")
    parser.add_argument("--homebgm-enabled", action="store_true")
    args = parser.parse_args()
    xml_text = build_theme_xml(label=args.label, homebgm_enabled=args.homebgm_enabled)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(xml_text, encoding="utf-8", newline="\n")
    result = validate_theme_xml(xml_text)
    print(f"PASS: wrote {args.output} (theme colour {result['themecolor']}, "
          f"home music {'enabled' if result['homebgm_enabled'] else 'disabled'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
