#!/usr/bin/env python3
"""Audit static TV TIME package inputs without creating an installable PKG."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from build_gp4 import Gp4Error, validate_gp4_xml
from build_param_sfo import ParamSfoError, validate_param_sfo
from build_theme_descriptor import validate_theme_xml

CI_FIXTURE_TITLE_ID = "CUSA00000"


class PackageAuditError(ValueError):
    """Package inputs failed the pre-build audit."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _package_files(staging: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(staging.rglob("*")):
        if path.is_symlink():
            raise PackageAuditError(f"symlinks are not allowed in package staging: {path}")
        if not path.is_file() or path.name == "STAGING-MANIFEST.json":
            continue
        relative = path.relative_to(staging).as_posix()
        records.append({
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return records


def build_package_audit(
    staging_dir: Path,
    gp4_path: Path,
    *,
    allow_ci_fixture: bool = False,
) -> dict[str, Any]:
    """Validate Image0 + GP4 and return a machine-readable pre-package audit."""
    staging = staging_dir.resolve()
    gp4_file = gp4_path.resolve()
    if not staging.is_dir() or staging.name != "Image0":
        raise PackageAuditError("staging must be an existing directory named Image0")
    if not gp4_file.is_file():
        raise PackageAuditError(f"GP4 project does not exist: {gp4_file}")
    if _inside(gp4_file, staging):
        raise PackageAuditError("the GP4 project must be stored outside the Image0 directory")

    manifest_path = staging / "STAGING-MANIFEST.json"
    theme_path = staging / "theme.xml"
    sfo_path = staging / "sce_sys" / "param.sfo"
    for required in (manifest_path, theme_path, sfo_path):
        if not required.is_file():
            raise PackageAuditError(f"required staging input is missing: {required.relative_to(staging)}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        theme_meta = manifest.get("theme_descriptor", {})
        if manifest.get("status") != "theme-staging-only; not an installable package":
            raise PackageAuditError("staging manifest does not identify a theme staging tree")
        if "installable .pkg" not in manifest.get("not_generated", []):
            raise PackageAuditError("manifest must explicitly record that no installable .pkg was generated")
        if theme_meta.get("path") != "theme.xml":
            raise PackageAuditError("manifest does not describe theme.xml")
        if theme_meta.get("bytes") != theme_path.stat().st_size:
            raise PackageAuditError("theme.xml byte count differs from the staging manifest")
        if theme_meta.get("sha256") != sha256_file(theme_path):
            raise PackageAuditError("theme.xml SHA-256 differs from the staging manifest")
        theme = validate_theme_xml(theme_path.read_text(encoding="utf-8"))
        sfo_bytes = sfo_path.read_bytes()
        sfo_values = validate_param_sfo(sfo_bytes)
    except PackageAuditError:
        raise
    except (OSError, ValueError, json.JSONDecodeError, ParamSfoError) as exc:
        raise PackageAuditError(f"staging metadata validation failed: {exc}") from exc

    if theme.get("themecolor") != 2 or theme.get("focuscolor") != "#FFFFD400":
        raise PackageAuditError("theme descriptor does not match the TV TIME red/yellow palette")

    metadata = manifest.get("package_metadata", {})
    if metadata.get("included") is not True or metadata.get("path") != "sce_sys/param.sfo":
        raise PackageAuditError("manifest does not declare the staged binary param.sfo")
    if metadata.get("bytes") != len(sfo_bytes) or metadata.get("sha256") != hashlib.sha256(sfo_bytes).hexdigest():
        raise PackageAuditError("param.sfo bytes or SHA-256 differ from the staging manifest")
    title_id = sfo_values.get("TITLE_ID", "")
    content_id = sfo_values.get("CONTENT_ID", "")
    if title_id != metadata.get("title_id") or content_id != metadata.get("content_id"):
        raise PackageAuditError("param.sfo package identity differs from the staging manifest")
    if sfo_values.get("CATEGORY") != "ac" or sfo_values.get("IRO_TAG") != "2":
        raise PackageAuditError("param.sfo is not marked as PS4 theme content")
    is_ci_fixture = title_id == CI_FIXTURE_TITLE_ID
    if is_ci_fixture and not allow_ci_fixture:
        raise PackageAuditError(
            "CUSA00000 is reserved in this project for CI fixtures; use a non-conflicting production TITLE_ID"
        )

    audio_path = staging / "sound" / "bgm_home.at9"
    audio_included = audio_path.is_file()
    audio_meta = manifest.get("optional_audio", {})
    if bool(audio_meta.get("included")) != audio_included:
        raise PackageAuditError("staged AT9 presence differs from optional_audio manifest metadata")
    if bool(theme.get("homebgm_enabled")) != audio_included:
        raise PackageAuditError("homebgm-enable does not match staged AT9 presence")
    if audio_included:
        audio_bytes = audio_path.stat().st_size
        if not 0 < audio_bytes <= 2 * 1024 * 1024:
            raise PackageAuditError("staged AT9 must be non-empty and no larger than 2 MiB")
        if audio_meta.get("bytes") != audio_bytes:
            raise PackageAuditError("staged AT9 byte count differs from its manifest")

    try:
        gp4_text = gp4_file.read_text(encoding="utf-8-sig")
        gp4_result = validate_gp4_xml(
            gp4_text,
            staging_dir=staging,
            expected_content_id=content_id,
        )
    except (OSError, Gp4Error) as exc:
        raise PackageAuditError(f"GP4 validation failed: {exc}") from exc

    files = _package_files(staging)
    if len(files) != gp4_result["file_count"]:
        raise PackageAuditError("audited package file count differs from the GP4 project")
    return {
        "schema_version": 1,
        "status": "fixture-only-inputs-audited" if is_ci_fixture else "production-inputs-audited",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "package": {
            "kind": "ps4-theme",
            "installable_pkg_created": False,
            "installable": False,
            "title_id": title_id,
            "content_id": content_id,
            "ci_fixture_identity": is_ci_fixture,
        },
        "theme": {
            "descriptor": "theme.xml",
            "system_colour": "red",
            "focus_accent": "#FFFFD400",
            "home_music_at9_included": audio_included,
        },
        "gp4": {
            "file": gp4_file.name,
            "bytes": gp4_file.stat().st_size,
            "sha256": sha256_file(gp4_file),
            "file_count": gp4_result["file_count"],
        },
        "package_files": files,
        "remaining_gates": [
            "Build an installable theme PKG using a verified and legitimate toolchain.",
            "Install and test the static theme on a compatible console.",
            "Verify home music playback on-console if an AT9 file is included.",
        ],
        "notice": "This report validates package inputs only. It is not a PKG and does not establish console compatibility.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, default=Path("build/tv-time/production/Image0"))
    parser.add_argument("--gp4", type=Path, default=Path("build/tv-time/package-input/tv-time.gp4"))
    parser.add_argument("--output", type=Path, default=Path("build/tv-time/package-input/package-input-audit.json"))
    parser.add_argument("--allow-ci-fixture", action="store_true", help="explicitly permit the CUSA00000 CI-only fixture identity")
    parser.add_argument("--force", action="store_true", help="replace an existing audit report")
    args = parser.parse_args()

    output = args.output.resolve()
    staging = args.staging.resolve()
    if _inside(output, staging):
        parser.error("audit output must be outside the Image0 staging directory")
    if output.exists() and not args.force:
        parser.error(f"{output} already exists; pass --force to replace it")

    try:
        report = build_package_audit(
            staging,
            args.gp4,
            allow_ci_fixture=args.allow_ci_fixture,
        )
    except (PackageAuditError, OSError) as exc:
        parser.error(str(exc))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: package inputs audited ({report['gp4']['file_count']} files)")
    print(f"TITLE_ID: {report['package']['title_id']}")
    print(f"Audit report: {output}")
    print("NOTE: no installable PKG was created; console compatibility remains untested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
