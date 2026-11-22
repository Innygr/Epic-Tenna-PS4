#!/usr/bin/env python3
"""Render an illustrative PS4-style home-screen overlay over the TV TIME wallpaper.

This is a composition/readability check, not a screenshot or exact PS4 UI replica.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size: int):
    for name in ("DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wallpaper", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with Image.open(args.wallpaper) as source:
        canvas = source.convert("RGBA")
    if canvas.size != (1920, 1080):
        raise SystemExit(f"Expected 1920x1080 wallpaper, got {canvas.size}")

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    title_font = font(24)
    label_font = font(18)
    small_font = font(16)

    # Illustrative top status row.
    draw.rounded_rectangle((64, 42, 1856, 112), radius=18, fill=(8, 8, 12, 155))
    draw.text((96, 63), "TV TIME  •  HOME", font=title_font, fill=(255, 242, 196, 245))
    draw.text((1480, 67), "14:02     ◉  ONLINE", font=small_font, fill=(255, 212, 0, 240))

    # A subtle translucent shelf mimics the visual weight of the home-screen row.
    draw.rounded_rectangle((70, 645, 970, 940), radius=28, fill=(8, 5, 8, 218),
                           outline=(255, 212, 0, 95), width=2)

    apps = [
        ("TV", "TV TIME", (237, 28, 36, 235)),
        ("G", "GAMES", (45, 32, 34, 235)),
        ("M", "MEDIA", (45, 32, 34, 235)),
        ("S", "SETTINGS", (45, 32, 34, 235)),
        ("N", "NETWORK", (45, 32, 34, 235)),
    ]
    start_x, y, size, gap = 110, 685, 140, 24
    for index, (glyph, label, colour) in enumerate(apps):
        x = start_x + index * (size + gap)
        selected = index == 0
        border = (255, 212, 0, 255) if selected else (255, 246, 222, 95)
        draw.rounded_rectangle((x, y, x + size, y + size), radius=22,
                               fill=colour, outline=border, width=5 if selected else 2)
        draw.text((x + size // 2, y + 38), glyph, font=font(48),
                  fill=(255, 246, 222, 255), anchor="mm")
        draw.text((x + size // 2, y + 101), label, font=small_font,
                  fill=(255, 246, 222, 255), anchor="mm")
        if selected:
            draw.rounded_rectangle((x - 9, y - 9, x + size + 9, y + size + 9),
                                   radius=28, outline=(255, 212, 0, 210), width=3)
    draw.text((110, 895), "Illustrative overlay only — not an exact PS4 UI capture",
              font=label_font, fill=(255, 246, 222, 190))

    # Footer is deliberately understated to keep attention on UI contrast.
    draw.text((96, 1015), "TV TIME  /  BROADCAST THEME PREVIEW",
              font=small_font, fill=(255, 226, 160, 205))
    result = Image.alpha_composite(canvas, overlay).convert("RGB")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output, format="PNG", optimize=True)
    print(f"Created illustrative UI overlay preview: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
