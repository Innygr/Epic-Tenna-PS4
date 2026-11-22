#!/usr/bin/env python3
"""Convert TV TIME param.sfx XML metadata into a binary PSF param.sfo file.

This writes the standard SFO container and validates it by parsing it back.
It does not create or sign a PS4 PKG.
"""
from __future__ import annotations

import argparse
import struct
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from build_param_sfx import ParamSfxError, validate_param_sfx

MAGIC = b"\x00PSF"
VERSION = 0x00000101
FORMAT_UTF8 = 0x0204
FORMAT_INT32 = 0x0404
HEADER_SIZE = 0x14
INDEX_ENTRY_SIZE = 0x10
OUTPUT_DEFAULT = Path("build/tv-time/package-input/param.sfo")


class ParamSfoError(ValueError):
    """Invalid or malformed PSF binary metadata."""


@dataclass(frozen=True)
class SfoEntry:
    key: str
    fmt: int
    data: bytes
    max_length: int


def _align4(value: int) -> int:
    return (value + 3) & ~3


def entries_from_sfx(xml_text: str) -> list[SfoEntry]:
    """Read a validated param.sfx XML document as typed SFO records."""
    try:
        values = validate_param_sfx(xml_text)
        root = ET.fromstring(xml_text)
    except (ParamSfxError, ET.ParseError) as exc:
        raise ParamSfoError(f"invalid param.sfx input: {exc}") from exc

    if root.tag != "paramsfo":
        raise ParamSfoError("param.sfx root element must be <paramsfo>")

    entries: list[SfoEntry] = []
    for node in root.findall("param"):
        key = node.attrib["key"]
        fmt_text = node.attrib["fmt"]
        value = values[key]
        if fmt_text == "utf8":
            fmt = FORMAT_UTF8
            data = value.encode("utf-8") + b"\x00"
            max_length = int(node.attrib.get("max_len", "0"))
        elif fmt_text == "int32":
            fmt = FORMAT_INT32
            try:
                integer = int(value, 10)
            except ValueError as exc:
                raise ParamSfoError(f"{key} must contain a decimal integer") from exc
            if not 0 <= integer <= 0xFFFFFFFF:
                raise ParamSfoError(f"{key} is outside the unsigned 32-bit range")
            data = struct.pack("<I", integer)
            max_length = 4
        else:
            raise ParamSfoError(f"unsupported SFO format for {key}: {fmt_text}")
        if max_length < len(data):
            raise ParamSfoError(
                f"{key} needs {len(data)} bytes but its max_len is {max_length}"
            )
        if max_length <= 0:
            raise ParamSfoError(f"{key} has an invalid max_len")
        entries.append(SfoEntry(key=key, fmt=fmt, data=data, max_length=max_length))

    if not entries:
        raise ParamSfoError("param.sfx contains no parameters")
    if len({entry.key for entry in entries}) != len(entries):
        raise ParamSfoError("param.sfx contains duplicate keys")
    return sorted(entries, key=lambda entry: entry.key)


def build_param_sfo_bytes(xml_text: str) -> bytes:
    """Serialize validated SFX values into a standard little-endian PSF file."""
    entries = entries_from_sfx(xml_text)
    key_table_offset = HEADER_SIZE + len(entries) * INDEX_ENTRY_SIZE

    key_table = bytearray()
    key_offsets: dict[str, int] = {}
    for entry in entries:
        key_offsets[entry.key] = len(key_table)
        key_table.extend(entry.key.encode("ascii") + b"\x00")

    data_table_offset = _align4(key_table_offset + len(key_table))
    data_offsets: dict[str, int] = {}
    data_cursor = 0
    for entry in entries:
        data_offsets[entry.key] = data_cursor
        data_cursor += entry.max_length

    header = struct.pack(
        "<4sIIII",
        MAGIC,
        VERSION,
        key_table_offset,
        data_table_offset,
        len(entries),
    )
    index_table = bytearray()
    data_table = bytearray()
    for entry in entries:
        index_table.extend(
            struct.pack(
                "<HHIII",
                key_offsets[entry.key],
                entry.fmt,
                len(entry.data),
                entry.max_length,
                data_offsets[entry.key],
            )
        )
        data_table.extend(entry.data)
        data_table.extend(b"\x00" * (entry.max_length - len(entry.data)))

    padding = b"\x00" * (data_table_offset - key_table_offset - len(key_table))
    binary = header + bytes(index_table) + bytes(key_table) + padding + bytes(data_table)
    parse_param_sfo(binary)
    return binary


def parse_param_sfo(binary: bytes) -> dict[str, tuple[int, str, int, int]]:
    """Parse the SFO fields and validate all table boundaries and data types."""
    if len(binary) < HEADER_SIZE:
        raise ParamSfoError("SFO file is shorter than its 20-byte header")
    magic, version, key_table_offset, data_table_offset, count = struct.unpack_from(
        "<4sIIII", binary, 0
    )
    if magic != MAGIC:
        raise ParamSfoError("SFO file has an invalid PSF magic")
    if version != VERSION:
        raise ParamSfoError(f"unsupported SFO version: {version:#x}")
    index_end = HEADER_SIZE + count * INDEX_ENTRY_SIZE
    if count == 0 or index_end > len(binary):
        raise ParamSfoError("SFO index table is empty or truncated")
    if key_table_offset < index_end or key_table_offset > data_table_offset:
        raise ParamSfoError("SFO key table offset is outside the valid range")
    if data_table_offset < key_table_offset or data_table_offset > len(binary):
        raise ParamSfoError("SFO data table offset is outside the valid range")
    if data_table_offset % 4:
        raise ParamSfoError("SFO data table is not four-byte aligned")

    parsed: dict[str, tuple[int, str, int, int]] = {}
    previous_key = ""
    for index in range(count):
        offset = HEADER_SIZE + index * INDEX_ENTRY_SIZE
        key_relative, fmt, length, max_length, data_relative = struct.unpack_from(
            "<HHIII", binary, offset
        )
        key_start = key_table_offset + key_relative
        if key_start < key_table_offset or key_start >= data_table_offset:
            raise ParamSfoError("SFO key offset points outside the key table")
        key_end = binary.find(b"\x00", key_start, data_table_offset)
        if key_end < 0:
            raise ParamSfoError("SFO key is not null-terminated")
        try:
            key = binary[key_start:key_end].decode("ascii")
        except UnicodeDecodeError as exc:
            raise ParamSfoError("SFO key contains non-ASCII bytes") from exc
        if not key or key in parsed:
            raise ParamSfoError("SFO contains an empty or duplicate key")
        if key <= previous_key:
            raise ParamSfoError("SFO keys are not sorted alphabetically")
        previous_key = key

        data_start = data_table_offset + data_relative
        data_end = data_start + length
        allocated_end = data_start + max_length
        if max_length == 0 or length == 0 or length > max_length:
            raise ParamSfoError(f"SFO field {key} has invalid length values")
        if data_start < data_table_offset or allocated_end > len(binary):
            raise ParamSfoError(f"SFO field {key} points outside the data table")
        raw = binary[data_start:data_end]
        if fmt == FORMAT_UTF8:
            if not raw.endswith(b"\x00"):
                raise ParamSfoError(f"SFO string {key} is not null-terminated")
            try:
                value = raw[:-1].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ParamSfoError(f"SFO string {key} is not valid UTF-8") from exc
        elif fmt == FORMAT_INT32:
            if length != 4 or max_length != 4:
                raise ParamSfoError(f"SFO integer {key} must use four bytes")
            value = str(struct.unpack("<I", raw)[0])
        else:
            raise ParamSfoError(f"SFO field {key} has unsupported format {fmt:#06x}")
        parsed[key] = (fmt, value, length, max_length)

    return parsed


def validate_param_sfo(binary: bytes, expected_xml: str | None = None) -> dict[str, str]:
    """Verify the binary SFO metadata values match their validated XML source."""
    parsed = parse_param_sfo(binary)
    result = {key: value for key, (_fmt, value, _length, _max_length) in parsed.items()}
    required = {
        "ATTRIBUTE", "CATEGORY", "CONTENT_ID", "CONTENT_VER", "FORMAT",
        "IRO_TAG", "PUBTOOLINFO", "TITLE", "TITLE_ID", "VERSION",
    }
    if set(result) != required:
        raise ParamSfoError("binary SFO does not contain exactly the expected TV TIME theme fields")
    if result["CATEGORY"] != "ac" or result["IRO_TAG"] != "2":
        raise ParamSfoError("binary SFO must identify this as theme content (CATEGORY=ac, IRO_TAG=2)")
    if result["FORMAT"] != "obs":
        raise ParamSfoError("binary SFO FORMAT must be obs")
    if expected_xml is not None:
        expected = validate_param_sfx(expected_xml)
        if result != expected:
            raise ParamSfoError("binary SFO values do not match the source param.sfx")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="validated param.sfx XML input")
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--force", action="store_true", help="replace an existing output file")
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"input param.sfx does not exist: {args.input}")
    xml_text = args.input.read_text(encoding="utf-8")
    binary = build_param_sfo_bytes(xml_text)
    if args.output.exists() and not args.force:
        parser.error(f"{args.output} already exists; choose another --output or pass --force")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(binary)
    values = validate_param_sfo(binary, expected_xml=xml_text)
    print(f"PASS: wrote {len(binary):,}-byte binary param.sfo to {args.output}")
    print(f"TITLE: {values['TITLE']}")
    print(f"CONTENT_ID: {values['CONTENT_ID']}")
    print("NOTE: SFO structure and values are self-validated; package and console compatibility are not yet verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
