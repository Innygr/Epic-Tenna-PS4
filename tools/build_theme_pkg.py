#!/usr/bin/env python3
"""Build and inspect a TV TIME PS4 theme PKG through a theme-capable img_create tool.

The proprietary Publishing Tools executable is supplied separately. This
wrapper never substitutes a game-package builder for the PS4 theme workflow.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Sequence

from audit_package_inputs import PackageAuditError, build_package_audit
from build_gp4 import Gp4Error, validate_gp4_xml

PKG_MAGIC = b"\x7fCNT"
DEFAULT_STAGING = Path("build/tv-time/production/Image0")
DEFAULT_GP4 = Path("build/tv-time/package-input/tv-time.gp4")
DEFAULT_OUTPUT = Path("build/tv-time/package-output/TV-TIME.pkg")
DEFAULT_TOOL = Path("tools/orbis-pub-cmd.exe")
DEFAULT_TIMEOUT = 30 * 60
SC0_FILES = {
    "sce_sys/param.sfo": "Sc0/param.sfo",
    "sce_sys/icon0.png": "Sc0/icon0.png",
    "sce_sys/pic1.png": "Sc0/pic1.png",
}


class PackageBuildError(RuntimeError):
    """Theme PKG build or post-build inspection failed."""


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


def expected_pkg_entries(package_files: list[dict[str, Any]]) -> list[str]:
    """Map staged Image0 paths to the locations used by PS4 theme packages."""
    result: list[str] = []
    for record in package_files:
        source = str(record.get("path", ""))
        if not source or source.startswith("/") or ".." in Path(source).parts:
            raise PackageBuildError(f"unsafe staged package path in audit: {source!r}")
        result.append(SC0_FILES.get(source, f"Image0/{source}"))
    if len(result) != len(set(result)):
        raise PackageBuildError("two staged files map to the same package entry")
    return sorted(result)


def parse_pkg_file_list(output: str) -> set[str]:
    """Extract Image0/ and Sc0/ paths from img_file_list output."""
    entries: set[str] = set()
    for line in output.splitlines():
        match = re.search(r"(?<![A-Za-z0-9_])((?:Image0|Sc0)[/\\][^\s]+)", line.strip())
        if not match:
            continue
        entry = match.group(1).replace("\\", "/").rstrip(",:;")
        entries.add(entry)
    return entries


def _tool_prefix(tool_path: Path, *, use_wine: bool) -> list[str]:
    if not tool_path.is_file():
        raise PackageBuildError(
            f"orbis-pub-cmd executable not found: {tool_path}. "
            "Supply it with --orbis-pub-cmd; the proprietary tool is not bundled."
        )
    ext_dir = tool_path.parent / "ext"
    if not ext_dir.is_dir():
        raise PackageBuildError(
            f"missing adjacent tool support directory: {ext_dir} "
            "(keep the tool's ext/ folder beside orbis-pub-cmd)"
        )
    missing_helpers = [name for name in ("sc.exe", "di.exe") if not (ext_dir / name).is_file()]
    if missing_helpers:
        raise PackageBuildError(
            "missing required Publishing Tools helper(s) in "
            f"{ext_dir}: {', '.join(missing_helpers)}"
        )

    if os.name == "nt":
        if use_wine:
            raise PackageBuildError("--wine is only valid on non-Windows systems")
        return [str(tool_path)]

    if tool_path.suffix.lower() == ".exe":
        if not use_wine:
            raise PackageBuildError(
                "the configured tool is a Windows .exe; on Linux/macOS, pass --wine "
                "to run it through an installed Wine command"
            )
        wine = shutil.which("wine")
        if not wine:
            raise PackageBuildError("--wine was supplied, but wine was not found on PATH")
        return [wine, str(tool_path)]

    if use_wine:
        raise PackageBuildError("--wine is only supported for a Windows .exe tool")
    return [str(tool_path)]


def _run_tool(
    runner: Callable[..., Any],
    command: Sequence[str],
    *,
    cwd: Path,
    timeout: int,
    label: str,
) -> str:
    try:
        completed = runner(
            list(command),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise PackageBuildError(f"{label} timed out after {timeout} seconds") from exc
    except OSError as exc:
        raise PackageBuildError(f"could not start {label}: {exc}") from exc

    stdout = getattr(completed, "stdout", "") or ""
    stderr = getattr(completed, "stderr", "") or ""
    if getattr(completed, "returncode", 1) != 0:
        details = "\n".join(part for part in (stdout, stderr) if part).strip()
        if len(details) > 2400:
            details = details[-2400:]
        suffix = f"\n{details}" if details else ""
        raise PackageBuildError(
            f"{label} failed with exit code {completed.returncode}{suffix}"
        )
    return stdout + ("\n" + stderr if stderr else "")


def build_theme_pkg(
    staging_dir: Path,
    gp4_path: Path,
    output_path: Path,
    tool_path: Path,
    *,
    use_wine: bool = False,
    timeout: int = DEFAULT_TIMEOUT,
    force: bool = False,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Build a theme PKG, then verify its header and complete staged file list."""
    if timeout < 1:
        raise PackageBuildError("timeout must be at least one second")

    staging = staging_dir.resolve()
    gp4_file = gp4_path.resolve()
    output = output_path.resolve()
    tool = tool_path.expanduser().resolve()

    if output.suffix.lower() != ".pkg":
        raise PackageBuildError("output path must end in .pkg")
    if _inside(output, staging):
        raise PackageBuildError("the final PKG must be outside the Image0 staging directory")
    if _inside(gp4_file, staging):
        raise PackageBuildError("the GP4 project must be stored outside the Image0 staging directory")
    if output.exists() and not force:
        raise PackageBuildError(f"{output} already exists; pass --force to replace it")

    try:
        audit = build_package_audit(staging, gp4_file)
    except (PackageAuditError, Gp4Error, OSError) as exc:
        raise PackageBuildError(f"pre-build package audit failed: {exc}") from exc

    try:
        gp4_text = gp4_file.read_text(encoding="utf-8-sig")
        gp4_result = validate_gp4_xml(
            gp4_text,
            staging_dir=staging,
            expected_content_id=audit["package"]["content_id"],
        )
    except (OSError, Gp4Error) as exc:
        raise PackageBuildError(f"GP4 validation failed: {exc}") from exc

    passcode = str(gp4_result.get("passcode", ""))
    if not re.fullmatch(r"[A-Za-z0-9]{32}", passcode):
        raise PackageBuildError("the GP4 project does not contain a valid 32-character passcode")

    prefix = _tool_prefix(tool, use_wine=use_wine)
    expected_entries = expected_pkg_entries(audit.get("package_files", []))
    if not expected_entries:
        raise PackageBuildError("the package audit returned an empty file list")

    output.parent.mkdir(parents=True, exist_ok=True)
    process_runner = runner or subprocess.run
    with tempfile.TemporaryDirectory(prefix=".tv-time-pkg-build-", dir=str(output.parent)) as temp_name:
        work = Path(temp_name)
        tool_temp = work / "tool-tmp"
        pkg_dir = work / "pkg-output"
        tool_temp.mkdir()
        pkg_dir.mkdir()

        create_command = prefix + [
            "img_create",
            "--no_progress_bar",
            "--tmp_path",
            str(tool_temp),
            "--oformat",
            "pkg",
            str(gp4_file),
            str(pkg_dir),
        ]
        _run_tool(
            process_runner,
            create_command,
            cwd=staging.parent,
            timeout=timeout,
            label="img_create",
        )

        built_packages = sorted(path for path in pkg_dir.glob("*.pkg") if path.is_file())
        if len(built_packages) != 1:
            raise PackageBuildError(
                f"img_create must produce exactly one .pkg; found {len(built_packages)}"
            )
        built_pkg = built_packages[0]
        if built_pkg.stat().st_size < 1024 * 1024:
            raise PackageBuildError(
                f"output PKG is unexpectedly small ({built_pkg.stat().st_size} bytes)"
            )
        with built_pkg.open("rb") as stream:
            magic = stream.read(4)
        if magic != PKG_MAGIC:
            raise PackageBuildError(
                f"output does not have the expected PS4 PKG header magic: {magic.hex()}"
            )

        list_command = prefix + [
            "img_file_list",
            "--passcode",
            passcode,
            "--oformat",
            "long",
            str(built_pkg),
        ]
        listing_output = _run_tool(
            process_runner,
            list_command,
            cwd=staging.parent,
            timeout=timeout,
            label="img_file_list",
        )
        actual_entries = parse_pkg_file_list(listing_output)
        missing = sorted(set(expected_entries) - actual_entries)
        if missing:
            raise PackageBuildError(
                "the package file listing is missing required theme entries: "
                + ", ".join(missing[:20])
            )

        forbidden_misplaced = sorted(
            f"Image0/{source}"
            for source in SC0_FILES
            if f"Image0/{source}" in actual_entries
        )
        if forbidden_misplaced:
            raise PackageBuildError(
                "theme metadata artwork was placed in Image0 instead of Sc0: "
                + ", ".join(forbidden_misplaced)
            )
        if "Image0/STAGING-MANIFEST.json" in actual_entries:
            raise PackageBuildError("the staging-only manifest must not be included in the PKG")

        output_sha256 = sha256_file(built_pkg)
        output_bytes = built_pkg.stat().st_size
        os.replace(built_pkg, output)

    return {
        "schema_version": 1,
        "status": "theme-pkg-built-and-file-list-checked",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "builder": {
            "executable": tool.name,
            "command": "img_create",
            "post_build_inspector": "img_file_list",
            "wine": bool(use_wine),
        },
        "package": {
            "kind": "ps4-system-software-theme",
            "path": str(output),
            "bytes": output_bytes,
            "sha256": output_sha256,
            "title_id": audit["package"]["title_id"],
            "content_id": audit["package"]["content_id"],
            "header_magic": PKG_MAGIC.hex(),
        },
        "inputs": {
            "gp4": gp4_file.name,
            "gp4_sha256": sha256_file(gp4_file),
            "staging_file_count": len(expected_entries),
        },
        "checks": {
            "pre_build_audit": "passed",
            "pkg_header": "passed",
            "post_build_file_listing": "passed",
            "required_package_entries": len(expected_entries),
            "actual_listed_entries": len(actual_entries),
        },
        "expected_package_entries": expected_entries,
        "actual_package_entries": sorted(actual_entries),
        "notice": (
            "The PKG header and file inventory were checked. Installation, theme application, "
            "firmware compatibility, and audio playback have not been tested on a PS4."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, default=DEFAULT_STAGING)
    parser.add_argument("--gp4", type=Path, default=DEFAULT_GP4)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--orbis-pub-cmd",
        type=Path,
        default=Path(os.environ.get("ORBIS_PUB_CMD", str(DEFAULT_TOOL))),
        help="path to a compatible orbis-pub-cmd executable (or set ORBIS_PUB_CMD)",
    )
    parser.add_argument("--wine", action="store_true", help="run the Windows .exe through Wine on Linux")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--report", type=Path, help="JSON build report (default: <output>.build.json)")
    parser.add_argument("--force", action="store_true", help="replace existing PKG and report files")
    args = parser.parse_args()

    output = args.output.resolve()
    report_path = (args.report or Path(str(output) + ".build.json")).resolve()
    staging = args.staging.resolve()
    if _inside(report_path, staging):
        parser.error("build report must be stored outside the Image0 staging directory")
    if report_path == output:
        parser.error("build report path must not be the same as the PKG output")
    if report_path.exists() and not args.force:
        parser.error(f"{report_path} already exists; pass --force to replace it")

    try:
        report = build_theme_pkg(
            staging,
            args.gp4,
            output,
            args.orbis_pub_cmd,
            use_wine=args.wine,
            timeout=args.timeout,
            force=args.force,
        )
    except (PackageBuildError, PackageAuditError, Gp4Error, OSError) as exc:
        parser.error(str(exc))

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_tmp = report_path.with_name(report_path.name + ".tmp")
    report_tmp.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(report_tmp, report_path)

    print(f"PASS: built theme PKG: {output}")
    print(f"CONTENT_ID: {report['package']['content_id']}")
    print(f"Size: {report['package']['bytes']} bytes")
    print(f"SHA-256: {report['package']['sha256']}")
    print(f"File-list report: {report_path}")
    print("NOTE: a successful build and listing check do not prove console compatibility.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
