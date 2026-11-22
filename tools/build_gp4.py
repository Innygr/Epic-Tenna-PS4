#!/usr/bin/env python3
"""Generate a PS4 theme GP4 project description from a validated Image0 tree.

The output is plain XML consumed by a compatible package-building utility. This
script does not call that utility and does not create or sign a PKG.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

from build_param_sfo import ParamSfoError, validate_param_sfo
from build_theme_descriptor import validate_theme_xml

DEFAULT_PASSCODE = "0" * 32
PASSCODE_RE = re.compile(r"^[A-Za-z0-9]{32}$")
CONTENT_ID_RE = re.compile(r"^[A-Z0-9]{6}-[A-Z]{4}[0-9]{5}_00-[A-Z0-9]{16}$")
DEFAULT_OUTPUT = Path("build/tv-time/package-input/tv-time.gp4")


class Gp4Error(ValueError):
    """Invalid theme staging tree or GP4 project description."""


def _safe_target(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise Gp4Error(f"unsafe package target path: {value!r}")
    if "\\" in value or ":" in value:
        raise Gp4Error(f"package target must use relative POSIX path syntax: {value!r}")
    if any(not re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in path.parts):
        raise Gp4Error(f"package target contains unsupported characters: {value!r}")
    return path.as_posix()


def _validate_timestamp(value: str) -> str:
    try:
        parsed = dt.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError) as exc:
        raise Gp4Error("timestamp must use YYYY-MM-DD HH:MM:SS") from exc
    if parsed.strftime("%Y-%m-%d %H:%M:%S") != value:
        raise Gp4Error("timestamp must use YYYY-MM-DD HH:MM:SS")
    return value


def _directory_tree(targets: list[str]) -> dict:
    tree: dict = {}
    for target in targets:
        node = tree
        for part in PurePosixPath(target).parts[:-1]:
            node = node.setdefault(part, {})
    return tree


def _append_directories(parent: ET.Element, tree: dict) -> None:
    for name in sorted(tree):
        node = ET.SubElement(parent, "dir", {"targ_name": name})
        _append_directories(node, tree[name])


def build_gp4_xml(
    staging_dir: Path,
    *,
    passcode: str = DEFAULT_PASSCODE,
    timestamp: str | None = None,
) -> str:
    """Return a theme-mode GP4 XML project for the supplied validated staging tree."""
    root_dir = staging_dir.resolve()
    if not root_dir.is_dir():
        raise Gp4Error(f"staging directory does not exist: {root_dir}")
    if root_dir.name != "Image0":
        raise Gp4Error("the staging directory must be named Image0")
    if not PASSCODE_RE.fullmatch(passcode or ""):
        raise Gp4Error("passcode must be exactly 32 alphanumeric characters")

    theme_path = root_dir / "theme.xml"
    manifest_path = root_dir / "STAGING-MANIFEST.json"
    sfo_path = root_dir / "sce_sys" / "param.sfo"
    if not theme_path.is_file() or not manifest_path.is_file() or not sfo_path.is_file():
        raise Gp4Error("staging tree must contain theme.xml, STAGING-MANIFEST.json, and sce_sys/param.sfo")

    try:
        validate_theme_xml(theme_path.read_text(encoding="utf-8"))
        sfo_binary = sfo_path.read_bytes()
        sfo_values = validate_param_sfo(sfo_binary)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (ValueError, ParamSfoError, json.JSONDecodeError) as exc:
        raise Gp4Error(f"staging metadata failed validation: {exc}") from exc
    if manifest.get("status") != "theme-staging-only; not an installable package":
        raise Gp4Error("staging manifest does not identify a theme staging tree")
    package_meta = manifest.get("package_metadata", {})
    if package_meta.get("included") is not True or package_meta.get("path") != "sce_sys/param.sfo":
        raise Gp4Error("staging manifest does not declare the supplied binary param.sfo")
    if package_meta.get("bytes") != len(sfo_binary):
        raise Gp4Error("staging manifest param.sfo byte count does not match")
    if package_meta.get("sha256") != hashlib.sha256(sfo_binary).hexdigest():
        raise Gp4Error("staging manifest param.sfo SHA-256 does not match")
    content_id = sfo_values.get("CONTENT_ID", "")
    if package_meta.get("content_id") != content_id or package_meta.get("title_id") != sfo_values.get("TITLE_ID"):
        raise Gp4Error("staging manifest package identity does not match param.sfo")
    if not CONTENT_ID_RE.fullmatch(content_id):
        raise Gp4Error("staged param.sfo does not contain a valid theme CONTENT_ID")
    if sfo_values.get("CATEGORY") != "ac" or sfo_values.get("IRO_TAG") != "2":
        raise Gp4Error("staged param.sfo is not marked as PS4 theme content")

    targets = []
    for path in sorted(root_dir.rglob("*")):
        if path.is_symlink():
            raise Gp4Error(f"symlinks are not allowed in package staging: {path}")
        if path.is_file() and path.name != "STAGING-MANIFEST.json":
            targets.append(_safe_target(path.relative_to(root_dir).as_posix()))
    if not targets:
        raise Gp4Error("staging tree contains no files")
    if len(targets) != len(set(targets)):
        raise Gp4Error("staging tree contains duplicate target paths")
    if "theme.xml" not in targets or "sce_sys/param.sfo" not in targets:
        raise Gp4Error("staging tree is missing a required theme package file")

    stamp = _validate_timestamp(timestamp or dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    project = ET.Element("psproject", {"fmt": "gp4", "version": "1000"})
    volume = ET.SubElement(project, "volume")
    ET.SubElement(volume, "volume_type").text = "pkg_ps4_theme"
    ET.SubElement(volume, "volume_id").text = ""
    ET.SubElement(volume, "volume_ts").text = stamp
    ET.SubElement(volume, "package", {"content_id": content_id, "passcode": passcode})

    files_node = ET.SubElement(project, "files", {"img_no": "0"})
    for target in targets:
        windows_path = target.replace("/", "\\")
        origin = f"{root_dir.name}\\{windows_path}"
        ET.SubElement(files_node, "file", {"targ_path": target, "orig_path": origin})

    root_node = ET.SubElement(project, "rootdir")
    _append_directories(root_node, _directory_tree(targets))
    ET.indent(project, space="  ")
    body = ET.tostring(project, encoding="unicode", short_empty_elements=True)
    return '\ufeff<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n' + body + "\n"


def validate_gp4_xml(
    xml_text: str,
    *,
    staging_dir: Path,
    expected_content_id: str | None = None,
) -> dict[str, object]:
    """Parse project XML and confirm it describes every file in the staging tree."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise Gp4Error(f"GP4 project is not valid XML: {exc}") from exc
    if root.tag != "psproject" or root.attrib != {"fmt": "gp4", "version": "1000"}:
        raise Gp4Error("GP4 root must be <psproject fmt='gp4' version='1000'>")
    volume = root.find("volume")
    if volume is None or volume.findtext("volume_type") != "pkg_ps4_theme":
        raise Gp4Error("GP4 volume must use pkg_ps4_theme")
    package = volume.find("package")
    if package is None:
        raise Gp4Error("GP4 project is missing its package element")
    content_id = package.get("content_id", "")
    passcode = package.get("passcode", "")
    if not CONTENT_ID_RE.fullmatch(content_id):
        raise Gp4Error("GP4 package has an invalid content ID")
    if not PASSCODE_RE.fullmatch(passcode):
        raise Gp4Error("GP4 package has an invalid passcode")
    _validate_timestamp(volume.findtext("volume_ts", ""))

    files_node = root.find("files")
    if files_node is None or files_node.get("img_no") != "0":
        raise Gp4Error("GP4 project is missing files img_no=0")
    actual_targets = []
    origins = set()
    for item in files_node.findall("file"):
        target = _safe_target(item.get("targ_path", ""))
        origin = item.get("orig_path", "")
        expected_origin = f"{staging_dir.name}\\{target.replace('/', chr(92))}"
        if origin != expected_origin:
            raise Gp4Error(f"GP4 origin path does not match target {target}")
        if target in actual_targets or origin in origins:
            raise Gp4Error("GP4 contains duplicate file targets or origins")
        actual_targets.append(target)
        origins.add(origin)
    if actual_targets != sorted(actual_targets):
        raise Gp4Error("GP4 file targets are not sorted")

    expected_targets = sorted(
        _safe_target(path.relative_to(staging_dir).as_posix())
        for path in staging_dir.rglob("*")
        if path.is_file() and not path.is_symlink() and path.name != "STAGING-MANIFEST.json"
    )
    if actual_targets != expected_targets:
        raise Gp4Error("GP4 file list does not exactly match the staging directory")
    if expected_content_id is not None and content_id != expected_content_id:
        raise Gp4Error("GP4 content ID does not match the expected value")
    if "theme.xml" not in actual_targets or "sce_sys/param.sfo" not in actual_targets:
        raise Gp4Error("GP4 file list is missing theme.xml or sce_sys/param.sfo")
    if root.find(".//chunk_info") is not None:
        raise Gp4Error("theme GP4 projects must not contain application chunk_info")

    return {
        "content_id": content_id,
        "passcode": passcode,
        "file_count": len(actual_targets),
        "targets": actual_targets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, default=Path("build/tv-time/Image0"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--passcode", default=DEFAULT_PASSCODE)
    parser.add_argument("--timestamp", help="reproducible GP4 timestamp: YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--force", action="store_true", help="replace an existing GP4 file")
    args = parser.parse_args()

    staging = args.staging.resolve()
    output = args.output.resolve()
    try:
        output.relative_to(staging)
    except ValueError:
        pass
    else:
        parser.error("GP4 output must be outside the Image0 staging directory")

    xml_text = build_gp4_xml(staging, passcode=args.passcode, timestamp=args.timestamp)
    validate_gp4_xml(xml_text, staging_dir=staging)
    if output.exists() and not args.force:
        parser.error(f"{output} already exists; pass --force to replace it")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(xml_text, encoding="utf-8", newline="\n")
    result = validate_gp4_xml(output.read_text(encoding="utf-8"), staging_dir=staging)
    print(f"PASS: wrote theme GP4 project to {output}")
    print(f"CONTENT_ID: {result['content_id']}")
    print(f"Files described: {result['file_count']}")
    print("NOTE: this is a GP4 project description only; no PKG was built.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
