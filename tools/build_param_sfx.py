#!/usr/bin/env python3
"""Generate the PS4 Fake PKG Tools SFO XML input (param.sfx) for TV TIME.

This creates the XML description consumed by a separately supplied
sfo_create tool. It does NOT create the binary param.sfo or a .pkg.
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

TITLE_ID_RE = re.compile(r"^[A-Z]{4}[0-9]{5}$")
PREFIX_RE = re.compile(r"^[A-Z0-9]{6}$")
EDITION_RE = re.compile(r"^[A-Z0-9]{16}$")
CONTENT_ID_RE = re.compile(r"^[A-Z0-9]{6}-[A-Z]{4}[0-9]{5}_00-[A-Z0-9]{16}$")
OUTPUT_DEFAULT = Path("build/tv-time/package-input/param.sfx")


class ParamSfxError(ValueError):
    """Invalid theme metadata for the PS4 SFO generator."""


def validate_metadata(
    *,
    title: str,
    title_id: str,
    content_prefix: str,
    edition: str,
    date_text: str,
) -> str:
    title = (title or "").strip()
    if not title:
        raise ParamSfxError("title cannot be empty")
    if len(title.encode("utf-8")) > 128:
        raise ParamSfxError("title exceeds the 128-byte UTF-8 limit")
    if not TITLE_ID_RE.fullmatch(title_id or ""):
        raise ParamSfxError("title-id must be four uppercase letters followed by five digits")
    if not PREFIX_RE.fullmatch(content_prefix or ""):
        raise ParamSfxError("content-prefix must be exactly six uppercase letters or digits")
    if not EDITION_RE.fullmatch(edition or ""):
        raise ParamSfxError("edition must be exactly 16 uppercase letters or digits")
    content_id = f"{content_prefix}-{title_id}_00-{edition}"
    if len(content_id) != 36 or not CONTENT_ID_RE.fullmatch(content_id):
        raise ParamSfxError("generated CONTENT_ID does not match the PS4 theme content-ID shape")
    try:
        parsed_date = dt.datetime.strptime(date_text, "%Y%m%d").date()
    except (TypeError, ValueError) as exc:
        raise ParamSfxError("date must use YYYYMMDD") from exc
    if parsed_date.strftime("%Y%m%d") != date_text:
        raise ParamSfxError("date must use YYYYMMDD")
    return content_id


def build_param_sfx(
    *,
    title: str,
    title_id: str,
    content_prefix: str = "UP9000",
    edition: str = "TVTIME0000000000",
    date_text: str | None = None,
    bgm_loudness: float | None = None,
) -> str:
    """Return validated param.sfx XML for a PS4 theme package."""
    date_text = date_text or dt.date.today().strftime("%Y%m%d")
    content_id = validate_metadata(
        title=title,
        title_id=title_id,
        content_prefix=content_prefix,
        edition=edition,
        date_text=date_text,
    )
    if bgm_loudness is not None:
        if not isinstance(bgm_loudness, (int, float)) or not (-100.0 <= bgm_loudness <= 0.0):
            raise ParamSfxError("bgm-loudness must be a measured LKFS value between -100 and 0")
        if not math.isfinite(float(bgm_loudness)):
            raise ParamSfxError("bgm-loudness must be a finite measured LKFS value")
    clean_title = title.strip()
    pubtoolinfo = f"c_date={date_text}"
    if bgm_loudness is not None:
        pubtoolinfo += f",bgmhome_loud={float(bgm_loudness):.2f}"
    values = [
        ("ATTRIBUTE", "int32", None, "0"),
        ("CATEGORY", "utf8", "4", "ac"),
        ("CONTENT_ID", "utf8", "48", content_id),
        ("CONTENT_VER", "utf8", "8", "01.00"),
        ("FORMAT", "utf8", "4", "obs"),
        ("IRO_TAG", "int32", None, "2"),
        ("PUBTOOLINFO", "utf8", "512", pubtoolinfo),
        ("TITLE", "utf8", "128", clean_title),
        ("TITLE_ID", "utf8", "12", title_id),
        ("VERSION", "utf8", "8", "01.00"),
    ]
    rows = ['<?xml version="1.0" encoding="utf-8" standalone="yes"?>', "<paramsfo>"]
    for key, fmt, max_len, value in sorted(values, key=lambda item: item[0]):
        max_attribute = f' max_len="{max_len}"' if max_len is not None else ""
        rows.append(
            f'  <param key="{key}" fmt="{fmt}"{max_attribute}>{escape(value)}</param>'
        )
    rows += ["</paramsfo>", ""]
    xml_text = "\n".join(rows)
    validate_param_sfx(xml_text, expected_title_id=title_id, expected_content_id=content_id)
    return xml_text


def validate_param_sfx(
    xml_text: str,
    *,
    expected_title_id: str | None = None,
    expected_content_id: str | None = None,
) -> dict[str, str]:
    """Parse and verify required theme SFO fields and reject application-only fields."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ParamSfxError(f"param.sfx is not valid XML: {exc}") from exc
    if root.tag != "paramsfo":
        raise ParamSfxError("param.sfx root element must be <paramsfo>")
    params: dict[str, tuple[str, str]] = {}
    for node in root.findall("param"):
        key = node.get("key")
        fmt = node.get("fmt")
        value = node.text or ""
        if not key or not fmt:
            raise ParamSfxError("every param entry must have key and fmt attributes")
        if key in params:
            raise ParamSfxError(f"duplicate param key: {key}")
        params[key] = (fmt, value)
    required = {
        "ATTRIBUTE", "CATEGORY", "CONTENT_ID", "CONTENT_VER", "FORMAT",
        "IRO_TAG", "PUBTOOLINFO", "TITLE", "TITLE_ID", "VERSION",
    }
    missing = required - params.keys()
    if missing:
        raise ParamSfxError(f"missing required theme params: {', '.join(sorted(missing))}")
    forbidden = {"APP_TYPE", "APP_VER", "DOWNLOAD_DATA_SIZE", "PARENTAL_LEVEL", "SYSTEM_VER"}
    present_forbidden = forbidden & params.keys()
    if present_forbidden:
        raise ParamSfxError(
            f"application-only params are not valid in this theme metadata: {', '.join(sorted(present_forbidden))}"
        )

    checks = {
        "ATTRIBUTE": ("int32", "0"),
        "CATEGORY": ("utf8", "ac"),
        "CONTENT_VER": ("utf8", "01.00"),
        "FORMAT": ("utf8", "obs"),
        "IRO_TAG": ("int32", "2"),
        "VERSION": ("utf8", "01.00"),
    }
    for key, expected in checks.items():
        if params[key] != expected:
            raise ParamSfxError(f"{key} must be {expected[1]!r} with format {expected[0]}")
    title_id = params["TITLE_ID"][1]
    content_id = params["CONTENT_ID"][1]
    if params["TITLE_ID"][0] != "utf8" or not TITLE_ID_RE.fullmatch(title_id):
        raise ParamSfxError("TITLE_ID must be a valid uppercase four-letter/five-digit ID")
    if params["CONTENT_ID"][0] != "utf8" or not CONTENT_ID_RE.fullmatch(content_id):
        raise ParamSfxError("CONTENT_ID does not match the PS4 theme content-ID shape")
    if title_id not in content_id:
        raise ParamSfxError("CONTENT_ID must contain TITLE_ID")
    if expected_title_id is not None and title_id != expected_title_id:
        raise ParamSfxError("generated TITLE_ID does not match the requested value")
    if expected_content_id is not None and content_id != expected_content_id:
        raise ParamSfxError("generated CONTENT_ID does not match the requested value")
    if params["TITLE"][0] != "utf8" or not params["TITLE"][1].strip():
        raise ParamSfxError("TITLE must be a non-empty UTF-8 value")
    if len(params["TITLE"][1].encode("utf-8")) > 128:
        raise ParamSfxError("TITLE exceeds the 128-byte UTF-8 limit")
    pubtoolinfo = params["PUBTOOLINFO"][1]
    if params["PUBTOOLINFO"][0] != "utf8" or not re.fullmatch(
        r"c_date=[0-9]{8}(?:,bgmhome_loud=-?(?:[0-9]{1,3})\\.[0-9]{2})?",
        pubtoolinfo,
    ):
        raise ParamSfxError(
            "PUBTOOLINFO must contain c_date=YYYYMMDD and optional measured bgmhome_loud=LKFS"
        )
    return {key: value for key, (_fmt, value) in params.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", default="TV TIME", help="theme title shown in metadata")
    parser.add_argument(
        "--title-id",
        required=True,
        help="your chosen nine-character title ID, e.g. CUSA12345; choose one that does not conflict",
    )
    parser.add_argument("--content-prefix", default="UP9000")
    parser.add_argument("--edition", default="TVTIME0000000000", help="16-character uppercase edition code")
    parser.add_argument("--date", help="reproducible SFO build date in YYYYMMDD form")
    parser.add_argument(
        "--bgm-loudness",
        type=float,
        help="measured home-music loudness in LKFS from file_calc_loudness; only use with a staged AT9 track",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--force", action="store_true", help="replace an existing output file")
    args = parser.parse_args()

    xml_text = build_param_sfx(
        title=args.title,
        title_id=args.title_id,
        content_prefix=args.content_prefix,
        edition=args.edition,
        date_text=args.date,
        bgm_loudness=args.bgm_loudness,
    )
    if args.output.exists() and not args.force:
        parser.error(f"{args.output} already exists; choose another --output or pass --force")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(xml_text, encoding="utf-8", newline="\n")
    parsed = validate_param_sfx(xml_text)
    print(f"PASS: wrote SFO XML input to {args.output}")
    print(f"TITLE: {parsed['TITLE']}")
    print(f"CONTENT_ID: {parsed['CONTENT_ID']}")
    print("NOTE: this is param.sfx XML input only; sfo_create must generate param.sfo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
