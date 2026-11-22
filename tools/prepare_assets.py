#!/usr/bin/env python3
"""Render TV TIME assets into a static PS4-theme staging tree.

The default variant preserves the Tenna home wallpaper and red/yellow
function-screen background. This does not create param.sfo or an installable PKG.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import cairosvg
from PIL import Image, ImageFilter

from build_theme_descriptor import build_theme_xml
from build_param_sfo import ParamSfoError, validate_param_sfo

ROOT = Path(__file__).resolve().parents[1]
OUT_DEFAULT = ROOT / "build" / "tv-time" / "Image0"
MAX_AT9_BYTES = 2 * 1024 * 1024


def render_svg(source: Path, target: Path, width: int, height: int) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(url=str(source), write_to=str(target), output_width=width, output_height=height)


def make_glow(source: Path, target: Path, size: int = 152) -> None:
    icon = Image.open(source).convert("RGBA").resize((128, 128), Image.Resampling.LANCZOS)
    alpha = icon.getchannel("A")
    halo = alpha.filter(ImageFilter.GaussianBlur(9)).point(lambda p: int(p * 0.42))
    glow = Image.new("RGBA", (size, size), (237, 28, 36, 0))
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
    parser.add_argument(
        "--at9",
        type=Path,
        help="optional already-converted bgm_home.at9; enables the theme's home music slot",
    )
    parser.add_argument(
        "--param-sfo",
        type=Path,
        help="optional validated binary param.sfo; copied to sce_sys/param.sfo",
    )
    args = parser.parse_args()
    out = args.output.resolve()
    if args.at9:
        if not args.at9.is_file():
            parser.error(f"AT9 input does not exist: {args.at9}")
        if args.at9.suffix.lower() != ".at9":
            parser.error("--at9 must point to an .at9 file, not a WAV source")
        if not 0 < args.at9.stat().st_size <= MAX_AT9_BYTES:
            parser.error("AT9 input must be non-empty and no larger than 2 MiB")
    param_sfo_values = None
    if args.param_sfo:
        if not args.param_sfo.is_file():
            parser.error(f"param.sfo input does not exist: {args.param_sfo}")
        if args.param_sfo.suffix.lower() != ".sfo":
            parser.error("--param-sfo must point to a binary .sfo file")
        try:
            param_sfo_values = validate_param_sfo(args.param_sfo.read_bytes())
        except ParamSfoError as exc:
            parser.error(f"invalid param.sfo input: {exc}")

    if out.exists():
        if not args.force:
            parser.error(f"{out} already exists; choose another --output or pass --force")
        shutil.rmtree(out)
    out.mkdir(parents=True)

    texture = out / "texture"
    home_svg = ROOT / "assets/tv-time-home-screen-wallpaper-v0.2.svg"
    render_svg(home_svg, texture / "background/homescreen.png", 1920, 1080)
    render_svg(ROOT / "assets/tv-time-system-background-red-yellow-v0.1.svg",
               texture / "background/functionscreen.png", 1920, 1080)
    render_svg(home_svg, texture / "preview.png", 740, 416)
    render_svg(ROOT / "assets/tv-time-theme-icon.svg", out / "sce_sys/icon0.png", 512, 512)
    render_svg(home_svg, out / "sce_sys/pic1.png", 1920, 1080)

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

    has_bgm = bool(args.at9)
    if args.at9:
        bgm_target = out / "sound" / "bgm_home.at9"
        bgm_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.at9, bgm_target)

    has_param_sfo = bool(args.param_sfo)
    if args.param_sfo:
        sfo_target = out / "sce_sys" / "param.sfo"
        sfo_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.param_sfo, sfo_target)

    theme_xml = build_theme_xml(label="TV-TIME", themecolor=2, homebgm_enabled=has_bgm)
    theme_path = out / "theme.xml"
    theme_path.write_text(theme_xml, encoding="utf-8", newline="\n")

    files = []
    for path in sorted(out.rglob("*.png")):
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
        "status": "theme-staging-only; not an installable package",
        "variant": "static-tenna-home",
        "theme_descriptor": {
            "path": "theme.xml",
            "bytes": theme_path.stat().st_size,
            "sha256": sha256(theme_path),
            "format_version": "4.0",
            "themecolor": 2,
            "focuscolor": "#FFFFD400",
            "homebgm_enabled": has_bgm,
        },
        "generated_files": files,
        "optional_audio": {
            "path": "sound/bgm_home.at9",
            "included": has_bgm,
            "bytes": (out / "sound" / "bgm_home.at9").stat().st_size if has_bgm else 0,
        },
        "package_metadata": {
            "path": "sce_sys/param.sfo",
            "included": has_param_sfo,
            "bytes": (out / "sce_sys" / "param.sfo").stat().st_size if has_param_sfo else 0,
            "sha256": sha256(out / "sce_sys" / "param.sfo") if has_param_sfo else None,
            "title_id": param_sfo_values["TITLE_ID"] if param_sfo_values else None,
            "content_id": param_sfo_values["CONTENT_ID"] if param_sfo_values else None,
        },
        "not_generated": [
            *([] if has_param_sfo else ["sce_sys/param.sfo"]),
            "scene/background.raf",
            "installable .pkg",
        ],
        "notes": [
            "This static variant keeps the Tenna home wallpaper and red/yellow function-screen background.",
            "The optional dynamic RAF candidate is separate because a RAF scene replaces both theme background screens.",
            "The theme enables home music only when a converted AT9 file is supplied with --at9.",
            "Target-console application and firmware 14.02 compatibility are not yet verified.",
        ],
    }
    (out / "STAGING-MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(files)} PNG assets and theme.xml in {out}")
    print(f"Home music slot: {'enabled' if has_bgm else 'disabled (no staged AT9)'}")
    print(f"Binary param.sfo: {'staged' if has_param_sfo else 'not supplied'}")
    print("This is a theme staging tree only; no .pkg was created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
