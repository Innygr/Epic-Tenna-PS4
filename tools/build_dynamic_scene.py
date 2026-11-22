#!/usr/bin/env python3
"""Build an experimental TV TIME PS4 dynamic-background scene candidate.

This produces DXT1 DDS frames and an RAF index.xml from the original motion
study SVG. It deliberately does NOT create the model file or a PKG: those
remain separate compatibility gates until the model format is validated.
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


def rgb565(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    return ((r * 31 + 127) // 255 << 11) | ((g * 63 + 127) // 255 << 5) | ((b * 31 + 127) // 255)


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
            # Luma extrema are stable for this deliberately limited red/gold palette.
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
    # DDS_HEADER (124 bytes), legacy DXT1 FourCC, no mipmaps.
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


def scene_xml(frame_count: int) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<raf angle_unit="degree">',
        '  <system camera_switch_mode="off" layer_switch_distance="0"/>',
        '  <camera id="camera1" type="orthographic" ymag="55.5" position="15.25 9.7 0"/>',
        '  <model id="BG" file="BG.mdx"/>',
    ]
    for i in range(frame_count):
        name = f"{i:02d}"
        lines += [f'  <material id="BG{i}" effect="pure_texture depth_0">',
                  f'    <texture file="{name}.dds"/>', '  </material>']
    for i in range(frame_count):
        alpha = 1 if i == 0 else 0
        lines.append(f'  <actor id="bg{i:02d}" model="BG" material="BG{i}" color="1 1 1 {alpha}"/>')
    lines.append('  <sequence>')
    for i in range(frame_count):
        nxt = (i + 1) % frame_count
        lines += [f'    <case wait="{WAIT_SECONDS:.6f}">',
                  f'      <actor id="bg{i:02d}" color="1 1 1 0" trans_time="0.00" trans_step="0"/>',
                  f'      <actor id="bg{nxt:02d}" color="1 1 1 1" trans_time="0.00"/>',
                  '    </case>']
    lines += ['  </sequence>', '</raf>', '']
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
        target = raf_dir / f"{i:02d}.dds"
        target.write_bytes(data)
        total += len(data)
    if total > MAX_DDS_BYTES:
        raise SystemExit(f"Frame payload exceeds conservative 6 MiB cap: {total} bytes")
    (raf_dir / "index.xml").write_text(scene_xml(FRAME_COUNT), encoding="utf-8", newline="\n")
    (output / "DYNAMIC-SCENE-STATUS.txt").write_text(
        "EXPERIMENTAL SCENE CANDIDATE\n"
        f"Frames: {FRAME_COUNT} x {WIDTH}x{HEIGHT} DXT1\n"
        f"Frame payload: {total} bytes\n"
        "Not installable: BG.mdx model, theme descriptor, SFO, package build, "
        "and real-console validation are not included.\n",
        encoding="utf-8"
    )
    print(f"PASS: generated {FRAME_COUNT} DXT1 frames ({total:,} bytes) and RAF index.xml")
    print("NOTE: BG.mdx and PS4 package validation remain outstanding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
