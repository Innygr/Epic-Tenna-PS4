#!/usr/bin/env python3
"""Build an experimental TV TIME PS4 dynamic-background scene candidate.

The output contains original DXT1 frames, a RAF scene descriptor, and a shared
XDM plane model. It is still a scene candidate, not a complete theme package.
"""
from __future__ import annotations

import argparse
import math
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "tv-time-flow-motion-study.svg"
WIDTH, HEIGHT = 640, 360
FRAME_COUNT = 12
WAIT_SECONDS = 0.12
MAX_DDS_BYTES = 6 * 1024 * 1024

# Camera/model layout follows the documented working-theme arrangement
# inspected in PS4 Ultimate Theme Creator (MIT); see THIRD_PARTY_NOTICES.md.
CAMERA_YFOV = 29.0
CAMERA_ZNEAR = 0.1
CAMERA_ZFAR = 300.0
PLANE_DEPTH = 2.146484
PLANE_SCALE = 100.0
ACTOR_Z = 9.0
ASPECT = 16 / 9

# XDM (.mdx) record/property identifiers.
MDX_MAGIC = b"XDM.00.1MSP\x00" + b"\x00" * 4
TAG_ROOT = 0x0002
TAG_MODEL = 0x0010
TAG_NODE = 0x0011
TAG_GEOMETRY = 0x0012
TAG_MESH = 0x0013
TAG_ARRAYS = 0x0014
TAG_MATERIAL = 0x0016
PROP_PARENT = 0x8440
PROP_ROTATION = 0x8444
PROP_SCALE = 0x844B
PROP_GEOMETRY_REF = 0x847F
PROP_MATERIAL_REF = 0x84C0
PROP_ARRAYS_REF = 0x84C1
PROP_INDICES = 0x84E0


def rgb565(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    return (((r * 31 + 127) // 255) << 11) | (((g * 63 + 127) // 255) << 5) | ((b * 31 + 127) // 255)


def expand565(value: int) -> tuple[int, int, int]:
    r, g, b = (value >> 11) & 31, (value >> 5) & 63, value & 31
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))


def encode_dxt1(image: Image.Image) -> bytes:
    """Small, dependency-light opaque DXT1 encoder (4x4 blocks, 8 bytes each)."""
    image = image.convert("RGB")
    width, height = image.size
    if width % 4 or height % 4:
        raise ValueError("DXT1 dimensions must be multiples of four")
    px = image.load()
    output = bytearray()
    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            block = [px[bx + x, by + y] for y in range(4) for x in range(4)]
            lo = min(block, key=lambda c: 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2])
            hi = max(block, key=lambda c: 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2])
            c0, c1 = rgb565(hi), rgb565(lo)
            if c0 <= c1:
                c0, c1 = max(c0, c1), min(c0, c1)
                if c0 == c1:
                    c0 = min(0xFFFF, c0 + 1)
            p0, p1 = expand565(c0), expand565(c1)
            palette = [p0, p1,
                       tuple((2*a+b)//3 for a,b in zip(p0,p1)),
                       tuple((a+2*b)//3 for a,b in zip(p0,p1))]
            bits = 0
            for i, color in enumerate(block):
                best = min(range(4), key=lambda k: sum((color[j]-palette[k][j])**2 for j in range(3)))
                bits |= best << (2*i)
            output.extend(struct.pack("<HHI", c0, c1, bits))
    return bytes(output)


def dds_file(image: Image.Image) -> bytes:
    width, height = image.size
    payload = encode_dxt1(image)
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000
    header = b"DDS " + struct.pack(
        "<7I44xII4s5I5I",
        124, flags, height, width, len(payload), 0, 0,
        32, 0x4, b"DXT1", 0, 0, 0, 0, 0, 0x1000, 0, 0, 0, 0
    )
    if len(header) != 128:
        raise AssertionError(f"invalid DDS header length: {len(header)}")
    return header + payload


def render_frame(index: int) -> Image.Image:
    tree = ET.parse(SOURCE)
    root = tree.getroot()
    parent_map = {child: parent for parent in root.iter() for child in parent}
    animation = next((node for node in root.iter()
                      if node.tag.endswith("animateTransform")), None)
    if animation is None:
        raise ValueError("motion study SVG has no animateTransform")
    parent = parent_map[animation]
    parent.remove(animation)
    phase = 2 * math.pi * index / FRAME_COUNT
    offset_y = round(-2 + 16 * math.sin(phase), 2)
    parent.set("transform", f"translate(0 {offset_y})")
    rendered = cairosvg.svg2png(bytestring=ET.tostring(root, encoding="utf-8"),
                                output_width=WIDTH, output_height=HEIGHT)
    from io import BytesIO
    return Image.open(BytesIO(rendered)).convert("RGB")


def plane_half_size() -> tuple[float, float]:
    """Return local half-width/half-height for the reference perspective camera."""
    world_depth = PLANE_DEPTH * PLANE_SCALE
    half_h_world = world_depth * math.tan(math.radians(CAMERA_YFOV / 2))
    half_h = half_h_world / PLANE_SCALE
    return half_h * ASPECT, half_h


def _pack_prop(pid: int, data: bytes) -> bytes:
    size = 4 + len(data)
    if size > 0xFFFF:
        raise ValueError(f"XDM property {pid:#06x} is too large")
    return struct.pack("<HH", pid, size) + data


def _pack_record(tag: int, name: str = "", children: tuple[bytes, ...] = (),
                 payload: bytes = b"") -> bytes:
    encoded_name = name.encode("ascii")
    name_field = 0 if not name else max(8, ((len(encoded_name) + 1 + 3) // 4) * 4)
    header_size = 0x10 + name_field
    body = payload + b"".join(children)
    total = header_size + len(body)
    if tag == TAG_ARRAYS:
        a, b = header_size + 12, total
    else:
        a = b = header_size
    header = struct.pack("<HHIII", tag, header_size, a, b, total)
    return header + (encoded_name.ljust(name_field, b"\x00") if name_field else b"") + body


def _vertex(x: float, y: float, z: float, u: float, v: float) -> bytes:
    # 3 IEEE-754 binary16 position values, packed normal, 2 binary16 UV values.
    return struct.pack("<3e", x, y, z) + b"\x00\x81\x00\x00" + struct.pack("<2e", u, v)


def plane_model_bytes() -> bytes:
    """Build a one-quad XDM model used by every frame actor in the RAF scene."""
    half_w, half_h = plane_half_size()
    verts = b"".join((
        _vertex(-half_w, PLANE_DEPTH, +half_h, 0.0, 0.0),
        _vertex(-half_w, PLANE_DEPTH, -half_h, 0.0, 1.0),
        _vertex(+half_w, PLANE_DEPTH, -half_h, 1.0, 1.0),
        _vertex(+half_w, PLANE_DEPTH, +half_h, 1.0, 0.0),
    ))
    arrays_payload = struct.pack("<HHII", 0x0023, 0x0490, 14, 4) + verts
    arrays = _pack_record(TAG_ARRAYS, "arrays-0", payload=arrays_payload)
    indices = struct.pack("<II8H", 3, 6, 1, 0, 0, 1, 2, 0, 2, 3)

    mesh = _pack_record(TAG_MESH, "mesh-0", children=(
        _pack_prop(PROP_MATERIAL_REF, bytes((0x00, 0x20, 0x16, 0x00))),
        _pack_prop(PROP_ARRAYS_REF, bytes((0x00, 0x10, 0x14, 0x00))),
        _pack_prop(PROP_INDICES, indices),
    ))
    geometry = _pack_record(TAG_GEOMETRY, "plane", children=(mesh, arrays))

    root2 = math.sqrt(0.5)
    rotation = struct.pack("<4f", -root2, 0.0, 0.0, root2)
    scale = struct.pack("<3f", PLANE_SCALE, PLANE_SCALE, PLANE_SCALE)
    radius = math.hypot(half_w * PLANE_SCALE, half_h * PLANE_SCALE)
    center = (0.0, 0.0, -PLANE_DEPTH * PLANE_SCALE)
    node = _pack_record(TAG_NODE, "plane", children=(
        _pack_prop(PROP_PARENT, bytes((0x00, 0x10, 0x11, 0x00))),
        _pack_prop(PROP_ROTATION, rotation),
        _pack_prop(PROP_SCALE, scale),
        _pack_prop(PROP_GEOMETRY_REF, bytes((0x00, 0x10, 0x12, 0x00))),
    ))
    model = _pack_record(TAG_MODEL, "model-0", children=(
        _pack_prop(0x8083, struct.pack("<4f", center[0], center[1], center[2], radius)),
        _pack_prop(0x8084, struct.pack("<I4f", 1, 0.0, PLANE_DEPTH, 0.0, 6.0)),
        _pack_record(TAG_NODE, "RootNode"),
        node,
        geometry,
        _pack_record(TAG_MATERIAL, "material-0"),
    ))
    return MDX_MAGIC + _pack_record(TAG_ROOT, children=(model,))


def validate_plane_model(data: bytes) -> dict[str, int]:
    """Parse the generated XDM records and reject an incomplete plane model."""
    if not data.startswith(MDX_MAGIC):
        raise ValueError("plane model is missing the XDM.00.1 header")

    def parse_records(start: int, end: int) -> list[dict]:
        records = []
        offset = start
        while offset < end:
            if offset + 4 > end:
                raise ValueError("trailing bytes in XDM record body")
            first = struct.unpack_from("<H", data, offset)[0]
            if first & 0x8000:
                pid, size = struct.unpack_from("<HH", data, offset)
                if size < 4 or offset + size > end:
                    raise ValueError(f"invalid XDM property {pid:#06x}")
                records.append({"kind": "prop", "pid": pid,
                                "data": data[offset + 4:offset + size]})
                offset += size
                continue
            if offset + 16 > end:
                raise ValueError("truncated XDM record header")
            tag, header_size, a, b, total = struct.unpack_from("<HHIII", data, offset)
            if header_size < 0x10 or total < header_size or offset + total > end:
                raise ValueError(f"invalid XDM record {tag:#06x}")
            name = ""
            if header_size > 0x10:
                name = data[offset + 0x10:offset + header_size].split(b"\x00", 1)[0].decode("ascii")
            body_start, body_end = offset + header_size, offset + total
            if tag == TAG_ARRAYS:
                payload = data[body_start:body_end]
                if len(payload) < 12:
                    raise ValueError("XDM arrays record has no vertex header")
                _flags0, _flags1, stride, count = struct.unpack_from("<HHII", payload)
                if stride <= 0 or 12 + stride * count != len(payload):
                    raise ValueError("XDM arrays vertex payload length is inconsistent")
                children = []
            else:
                payload = b""
                stride = count = 0
                children = parse_records(body_start, body_end)
            records.append({"kind": "record", "tag": tag, "name": name,
                            "a": a, "b": b, "payload": payload,
                            "stride": stride, "count": count, "children": children})
            offset += total
        return records

    tree = parse_records(len(MDX_MAGIC), len(data))
    flat = []

    def visit(items: list[dict]) -> None:
        for item in items:
            if item["kind"] == "record":
                flat.append(item)
                visit(item["children"])

    visit(tree)
    counts = {tag: sum(1 for item in flat if item["tag"] == tag)
              for tag in (TAG_ROOT, TAG_MODEL, TAG_NODE, TAG_GEOMETRY,
                          TAG_MESH, TAG_ARRAYS, TAG_MATERIAL)}
    expected = {TAG_ROOT: 1, TAG_MODEL: 1, TAG_NODE: 2, TAG_GEOMETRY: 1,
                TAG_MESH: 1, TAG_ARRAYS: 1, TAG_MATERIAL: 1}
    if counts != expected:
        raise ValueError(f"unexpected XDM record layout: {counts}")
    arrays = next(item for item in flat if item["tag"] == TAG_ARRAYS)
    if arrays["stride"] != 14 or arrays["count"] != 4:
        raise ValueError("plane model must contain four 14-byte vertices")
    mesh = next(item for item in flat if item["tag"] == TAG_MESH)
    if not any(child["kind"] == "prop" and child["pid"] == PROP_INDICES
               for child in mesh["children"]):
        raise ValueError("plane mesh has no index buffer")
    return {"bytes": len(data), "vertices": arrays["count"],
            "vertex_stride": arrays["stride"], "records": len(flat)}


def scene_xml(frame_count: int) -> str:
    """Build RAF XML with one shared plane and one material/actor per frame."""
    if frame_count < 1:
        raise ValueError("at least one frame is required")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<raf angle_unit="degree">',
        '',
        '\t<system camera_switch_mode="vertical" layer_switch_distance="0"/>',
        '',
        f'\t<camera id="camera1" type="perspective" yfov="{CAMERA_YFOV:g}"'
        f' znear="{CAMERA_ZNEAR:g}" zfar="{CAMERA_ZFAR:g}"'
        ' position="0 0 0" direction="0 0 -1" up="0 1 0"/>',
        '\t<light id="light1" type="ambient" color="1 1 1"/>',
        '',
        '\t<model id="plane" file="plane.fbx"/>',
        '',
    ]
    for index in range(frame_count):
        fid = f"f{index:02d}"
        lines += [
            f'\t<material id="{fid}" effect="pure_texture">',
            f'\t\t<texture file="{index:02d}.dds"/>',
            '\t</material>',
        ]
    lines.append('')
    for index in range(frame_count):
        fid = f"f{index:02d}"
        alpha = 1 if index == 0 else 0
        lines.append(
            f'\t<actor id="{fid}" model="plane" material="{fid}"'
            f' color="1 1 1 {alpha}" position="0 0 {ACTOR_Z:g}" zsort="back_to_front"/>'
        )
    lines += ['', '\t<sequence>']
    for index in range(frame_count):
        current, nxt = f"f{index:02d}", f"f{(index + 1) % frame_count:02d}"
        lines += [
            f'\t\t<case wait="{WAIT_SECONDS:g}">',
            f'\t\t\t<actor id="{current}" color="1 1 1 0"/>',
            f'\t\t\t<actor id="{nxt}" color="1 1 1 1"/>',
            '\t\t</case>',
        ]
    lines += ['\t</sequence>', '', '</raf>', '']
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/tv-time-dynamic"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    raf_dir = output / "scene" / "background.raf"
    if output.exists() and any(output.iterdir()) and not args.force:
        raise SystemExit(f"Refusing to overwrite non-empty output: {output} (use --force)")
    raf_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for i in range(FRAME_COUNT):
        data = dds_file(render_frame(i))
        (raf_dir / f"{i:02d}.dds").write_bytes(data)
        total += len(data)
    if total > MAX_DDS_BYTES:
        raise SystemExit(f"Frame payload exceeds conservative 6 MiB cap: {total} bytes")

    model_data = plane_model_bytes()
    model_summary = validate_plane_model(model_data)
    (raf_dir / "plane.mdx").write_bytes(model_data)
    (raf_dir / "index.xml").write_text(scene_xml(FRAME_COUNT), encoding="utf-8", newline="\n")
    (output / "DYNAMIC-SCENE-STATUS.txt").write_text(
        "EXPERIMENTAL SCENE CANDIDATE\n"
        f"Frames: {FRAME_COUNT} x {WIDTH}x{HEIGHT} DXT1\n"
        f"Frame payload: {total} bytes\n"
        f"Shared plane model: {model_summary['bytes']} bytes, {model_summary['vertices']} vertices\n"
        "The scene model, RAF XML, and DXT1 frames are generated together.\n"
        "Not installable: theme descriptor, SFO, package build, and real-console validation remain outstanding.\n",
        encoding="utf-8"
    )
    print(f"PASS: generated {FRAME_COUNT} DXT1 frames ({total:,} bytes)")
    print(f"PASS: validated shared XDM plane model ({model_summary['bytes']:,} bytes)")
    print("NOTE: theme metadata, package build, and real-console validation remain outstanding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
