#!/usr/bin/env python3
"""Validate the generated TV TIME PS4-theme asset staging tree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

from PIL import Image

EXPECTED = {
    "texture/background/homescreen.png": (1920, 1080),
    "texture/background/functionscreen.png": (1920, 1080),
    "texture/preview.png": (740, 416),
    "sce_sys/icon0.png": (512, 512),
    "texture/function_icon/setting.png": (128, 128),
    "texture/function_icon/setting_glow.png": (152, 152),
    "texture/function_icon/friend.png": (128, 128),
    "texture/function_icon/friend_glow.png": (152, 152),
    "texture/function_icon/message.png": (128, 128),
    "texture/function_icon/message_glow.png": (152, 152),
    "texture/function_icon/power.png": (128, 128),
    "texture/function_icon/power_glow.png": (152, 152),
}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, default=Path("build/tv-time/Image0"))
    args = parser.parse_args()
    root = args.staging.resolve()
    manifest_path = root / "STAGING-MANIFEST.json"
    if not root.is_dir():
        parser.error(f"staging directory does not exist: {root}")
    if not manifest_path.is_file():
        parser.error(f"manifest is missing: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "staging-assets-only; not an installable package":
        raise SystemExit("FAIL: manifest does not identify this as staging-only")
    if "installable .pkg" not in manifest.get("not_generated", []):
        raise SystemExit("FAIL: manifest does not explicitly state that no .pkg was generated")

    entries = manifest.get("generated_files")
    if not isinstance(entries, list):
        raise SystemExit("FAIL: generated_files must be a list in the manifest")
    indexed = {}
    for entry in entries:
        rel = entry.get("path")
        if not isinstance(rel, str):
            raise SystemExit("FAIL: manifest entry has no string path")
        posix = PurePosixPath(rel)
        if posix.is_absolute() or ".." in posix.parts:
            raise SystemExit(f"FAIL: unsafe path in manifest: {rel}")
        if rel in indexed:
            raise SystemExit(f"FAIL: duplicate manifest path: {rel}")
        indexed[rel] = entry

    if set(indexed) != set(EXPECTED):
        missing = sorted(set(EXPECTED) - set(indexed))
        extra = sorted(set(indexed) - set(EXPECTED))
        raise SystemExit(f"FAIL: manifest file set mismatch; missing={missing}, extra={extra}")

    for rel, dimensions in EXPECTED.items():
        path = root / rel
        if not path.is_file():
            raise SystemExit(f"FAIL: required asset is missing: {rel}")
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                if image.format != "PNG":
                    raise SystemExit(f"FAIL: {rel} is {image.format}, not PNG")
                if image.size != dimensions:
                    raise SystemExit(f"FAIL: {rel} dimensions {image.size}, expected {dimensions}")
                mode = image.mode
        except Exception as exc:
            raise SystemExit(f"FAIL: cannot read {rel}: {exc}") from exc

        entry = indexed[rel]
        if entry.get("width") != dimensions[0] or entry.get("height") != dimensions[1]:
            raise SystemExit(f"FAIL: manifest dimensions disagree for {rel}")
        if entry.get("mode") != mode:
            raise SystemExit(f"FAIL: manifest colour mode disagrees for {rel}")
        if entry.get("bytes") != path.stat().st_size:
            raise SystemExit(f"FAIL: manifest byte count disagrees for {rel}")
        if entry.get("sha256") != digest(path):
            raise SystemExit(f"FAIL: SHA-256 mismatch for {rel}")

    print(f"PASS: {len(EXPECTED)} PNG assets validated; manifest hashes and dimensions match.")
    print("NOTE: validation covers staging assets only, not theme.xml, param.sfo, RAF scenes, or a PS4 package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
