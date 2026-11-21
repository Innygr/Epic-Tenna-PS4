#!/usr/bin/env python3
"""Create a labelled contact sheet for reviewing TV TIME staging PNGs."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FILES = [
    ("Home screen wallpaper", "texture/background/homescreen.png", "wide"),
    ("Function screen background", "texture/background/functionscreen.png", "wide"),
    ("Theme-list icon", "sce_sys/icon0.png", "square"),
    ("Settings icon", "texture/function_icon/setting.png", "icon"),
    ("Settings focus glow", "texture/function_icon/setting_glow.png", "icon"),
    ("Friends icon", "texture/function_icon/friend.png", "icon"),
    ("Friends focus glow", "texture/function_icon/friend_glow.png", "icon"),
    ("Messages icon", "texture/function_icon/message.png", "icon"),
    ("Messages focus glow", "texture/function_icon/message_glow.png", "icon"),
    ("Power icon", "texture/function_icon/power.png", "icon"),
    ("Power focus glow", "texture/function_icon/power_glow.png", "icon"),
    ("Theme preview", "texture/preview.png", "wide"),
]

CELL_W, CELL_H = 420, 270
BG = (31, 29, 37)
TILE = (48, 44, 54)
TEXT = (255, 246, 222)


def load_font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    font = load_font(17)
    rows = (len(FILES) + 1) // 2
    sheet = Image.new("RGB", (CELL_W * 2, CELL_H * rows), BG)
    draw = ImageDraw.Draw(sheet)

    for index, (label, relative, kind) in enumerate(FILES):
        path = args.staging / relative
        if not path.is_file():
            raise SystemExit(f"Missing review image: {relative}")
        with Image.open(path) as source:
            source.load()
            image = source.convert("RGBA")

        if kind == "wide":
            image.thumbnail((CELL_W - 24, 205), Image.Resampling.LANCZOS)
        elif kind == "square":
            image.thumbnail((190, 190), Image.Resampling.LANCZOS)
        else:
            image.thumbnail((150, 150), Image.Resampling.LANCZOS)

        tile = Image.new("RGBA", (CELL_W - 16, CELL_H - 16), TILE)
        if kind == "wide":
            x = (tile.width - image.width) // 2
            y = 8 + (205 - image.height) // 2
        else:
            x = (tile.width - image.width) // 2
            y = 8 + (205 - image.height) // 2
        tile.alpha_composite(image, (x, y))

        px = (index % 2) * CELL_W + 8
        py = (index // 2) * CELL_H + 8
        sheet.paste(tile.convert("RGB"), (px, py))
        draw.text((px + 12, py + CELL_H - 43), label, font=font, fill=TEXT)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, format="PNG", optimize=True)
    print(f"Created review sheet: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
