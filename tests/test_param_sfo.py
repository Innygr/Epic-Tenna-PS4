import sys
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_param_sfx import build_param_sfx
from build_param_sfo import (
    FORMAT_INT32,
    FORMAT_UTF8,
    MAGIC,
    VERSION,
    ParamSfoError,
    build_param_sfo_bytes,
    parse_param_sfo,
    validate_param_sfo,
)


class ParamSfoTests(unittest.TestCase):
    def make_xml(self):
        return build_param_sfx(
            title='TV TIME & "ON AIR"',
            title_id="CUSA12345",
            content_prefix="UP9000",
            edition="TVTIME0000000000",
            date_text="20261121",
        )

    def test_binary_header_and_round_trip_values(self):
        xml_text = self.make_xml()
        binary = build_param_sfo_bytes(xml_text)
        self.assertEqual(binary[:4], MAGIC)
        magic, version, key_offset, data_offset, count = struct.unpack_from("<4sIIII", binary)
        self.assertEqual(magic, MAGIC)
        self.assertEqual(version, VERSION)
        self.assertEqual(count, 10)
        self.assertEqual(key_offset, 0x14 + count * 0x10)
        self.assertEqual(data_offset % 4, 0)
        result = validate_param_sfo(binary, expected_xml=xml_text)
        self.assertEqual(result["TITLE"], 'TV TIME & "ON AIR"')
        self.assertEqual(result["TITLE_ID"], "CUSA12345")
        self.assertEqual(result["CONTENT_ID"], "UP9000-CUSA12345_00-TVTIME0000000000")
        self.assertEqual(result["CATEGORY"], "ac")
        self.assertEqual(result["IRO_TAG"], "2")

    def test_parameter_formats_and_maximum_lengths(self):
        parsed = parse_param_sfo(build_param_sfo_bytes(self.make_xml()))
        self.assertEqual(parsed["CATEGORY"], (FORMAT_UTF8, "ac", 3, 4))
        self.assertEqual(parsed["IRO_TAG"], (FORMAT_INT32, "2", 4, 4))
        self.assertEqual(parsed["TITLE_ID"], (FORMAT_UTF8, "CUSA12345", 10, 12))
        self.assertEqual(parsed["TITLE"], (FORMAT_UTF8, 'TV TIME & "ON AIR"', 19, 128))

    def test_keys_are_sorted(self):
        parsed = parse_param_sfo(build_param_sfo_bytes(self.make_xml()))
        self.assertEqual(list(parsed), sorted(parsed))

    def test_bad_magic_is_rejected(self):
        binary = bytearray(build_param_sfo_bytes(self.make_xml()))
        binary[0] = 0x01
        with self.assertRaises(ParamSfoError):
            parse_param_sfo(bytes(binary))

    def test_truncated_index_table_is_rejected(self):
        binary = build_param_sfo_bytes(self.make_xml())[:24]
        with self.assertRaises(ParamSfoError):
            parse_param_sfo(binary)

    def test_invalid_data_table_offset_is_rejected(self):
        binary = bytearray(build_param_sfo_bytes(self.make_xml()))
        struct.pack_into("<I", binary, 0x0C, len(binary) + 4)
        with self.assertRaises(ParamSfoError):
            parse_param_sfo(bytes(binary))

    def test_invalid_utf8_terminator_is_rejected(self):
        binary = bytearray(build_param_sfo_bytes(self.make_xml()))
        parsed = parse_param_sfo(bytes(binary))
        key_offset = struct.unpack_from("<I", binary, 0x08)[0]
        data_table = struct.unpack_from("<I", binary, 0x0C)[0]
        # Locate the CATEGORY record and replace its terminating NUL.
        index_count = struct.unpack_from("<I", binary, 0x10)[0]
        for i in range(index_count):
            off = 0x14 + i * 0x10
            key_rel, fmt, length, max_len, data_rel = struct.unpack_from("<HHIII", binary, off)
            key_start = key_offset + key_rel
            key_end = binary.find(b"\x00", key_start, data_table)
            key = binary[key_start:key_end].decode("ascii")
            if key == "CATEGORY":
                binary[data_table + data_rel + length - 1] = 0x41
                break
        with self.assertRaises(ParamSfoError):
            parse_param_sfo(bytes(binary))

    def test_source_xml_value_mismatch_is_rejected(self):
        xml_text = self.make_xml()
        binary = build_param_sfo_bytes(xml_text)
        changed = xml_text.replace("<IRO_TAG>2</param>", "<IRO_TAG>1</param>")
        with self.assertRaises(ParamSfoError):
            validate_param_sfo(binary, expected_xml=changed)


if __name__ == "__main__":
    unittest.main()
