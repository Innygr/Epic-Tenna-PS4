#!/usr/bin/env python3
"""Render TV TIME SVG masters into a reviewable PS4-theme asset staging tree.

This deliberately does not generate theme.xml, param.sfo, or a .pkg.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import cairosvg
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT_DEFAULT = ROOT / "build" / "tv-time" / "Image0"

def render_svg(source: Path, target: Path, width: int, height: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(url=str(source), write_to=str(target), output_width=width, output_height=height)

def make_glow(source: Path, target: Path, size: int = 152) -> None:
    icon = Image.open(source).convert("RGBA").resize((128, 128), Image.Resampling.LANCZOS)
    alpha = icon.getchannel("A")
    halo = alpha.filter(ImageFilter.GaussianBlur(9)).point(lambda p: int(p * 0.42))
    glow = Image.new("RGBA", (size, size), (237, 28, 36, 0))
    # Yellow-red broadcast halo; preserve the original glyph in the centre.
    halo_layer = Image.new("RGBA", (128, 128), (255, 212, 0, 0))
    halo_layer.putalpha(halo)
    glow.alpha_composite(halo_layer, ((size - 128) // 2, (size - 128) // 2))
    glow.alpha_composite(icon.resize((128, 128), Image.Resampling.LANCZOS), ((size - 128) // 2, (size - 128) // 2))
    target.parent.mkdir(parents=True, exist_ok=True)
    glow.save(target, format="PNG", optimize=True)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--force", action="store_true", help="replace the output staging directory")
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists():
        if not args.force:
            parser.error(f"{out} already exists; choose another --output or pass --force")
        shutil.rmtree(out)
    out.mkdir(parents=True)

    texture = out / "texture"
    render_svg(ROOT / "assets/tv-time-home-screen-wallpaper-v0.2.svg",
               texture / "background/homescreen.png", 1920, 1080)
    render_svg(ROOT / "assets/tv-time-system-background-red-yellow-v0.1.svg",
               texture / "background/functionscreen.png", 1920, 1080)
    render_svg(ROOT / "assets/tv-time-home-screen-wallpaper-v0.2.svg",
               texture / "preview.png", 740, 416)
    render_svg(ROOT / "assets/tv-time-theme-icon.svg", out / "sce_sys/icon0.png", 512, 512)

    mapping = {
        "setting": "settings",
        "friend": "friends",
        "message": "messages",
        "power": "power",
    }
    for slot, source_name in mapping.items():
        base = texture / "function_icon" / f"{slot}.png"
        render_svg(ROOT / f"assets/icons/{source_name}.svg", base, 128, 128)
        make_glow(base, texture / "function_icon" / f"{slot}_glow.png")

    files = []
    for path in sorted(out.rglob("*")):
        if path.is_file():
            with Image.open(path) as image:
                dimensions = list(image.size)
                mode = image.mode
            files.append({
                "path": path.relative_to(out).as_posix(),
                "width": dimensions[0],
                "height": dimensions[1],
                "mode": mode,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    manifest = {
        "project": "EPIC-TENNA-PS4 / TV TIME",
        "status": "staging-assets-only; not an installable package",
        "target_reported_firmware": "14.02",
        "generated_files": files,
        "not_generated": ["theme.xml", "sce_sys/param.sfo", "scene/background.raf", "installable .pkg"],
        "notes": [
            "Confirm exact dimensions, alpha handling, slot mapping, and XML schema against the selected theme builder.",
            "The animated SVG motion study is not converted to a RAF scene by this script.",
            "Network and Media concepts remain unmapped and are not included in the PS4 function icon slots.",
        ],
    }
    (out / "STAGING-MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(files)} PNG assets in {out}")
    print("This is an asset staging tree only; no .pkg was created.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
