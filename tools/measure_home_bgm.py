#!/usr/bin/env python3
"""Measure a staged PS4 home-music AT9 file with Publishing Tools.

The script reports the measured LKFS value; pass that exact value to
build_param_sfx.py --bgm-loudness when generating the matching SFO metadata.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any, Callable

from build_theme_pkg import PackageBuildError, _run_tool, _tool_prefix

LKFS_RE = re.compile(r"(-?(?:\d+(?:\.\d*)?|\.\d+))\s*LKFS\b", re.IGNORECASE)


def measure_loudness(
    at9_path: Path,
    tool_path: Path,
    *,
    use_wine: bool = False,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    at9 = at9_path.expanduser().resolve()
    tool = tool_path.expanduser().resolve()
    if not at9.is_file() or at9.suffix.lower() != ".at9":
        raise PackageBuildError("input must be an existing .at9 file")
    if at9.stat().st_size <= 0:
        raise PackageBuildError("AT9 input is empty")

    prefix = _tool_prefix(tool, use_wine=use_wine)
    atrac_library = tool.parent / "ext" / "libatrac9.dll"
    if not atrac_library.is_file():
        raise PackageBuildError(
            f"missing AT9 loudness helper: {atrac_library} "
            "(keep libatrac9.dll beside the other ext helpers)"
        )

    output = _run_tool(
        runner or subprocess.run,
        prefix + ["file_calc_loudness", str(at9)],
        cwd=at9.parent,
        timeout=120,
        label="file_calc_loudness",
    )
    match = LKFS_RE.search(output)
    if not match:
        raise PackageBuildError(
            "Publishing Tools did not report an LKFS measurement; "
            "check the AT9 file and tool output"
        )
    value = float(match.group(1))
    if not math.isfinite(value) or not -100.0 <= value <= 0.0:
        raise PackageBuildError(f"reported LKFS value is outside the supported range: {value}")
    return {
        "file": at9.name,
        "bytes": at9.stat().st_size,
        "loudness_lkfs": round(value, 2),
        "metadata_argument": f"{value:.2f}",
        "measurement_tool": tool.name,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--at9", type=Path, required=True)
    parser.add_argument(
        "--orbis-pub-cmd",
        type=Path,
        default=Path("tools/orbis-pub-cmd.exe"),
    )
    parser.add_argument("--wine", action="store_true")
    parser.add_argument("--output", type=Path, help="optional JSON measurement report")
    args = parser.parse_args()
    try:
        report = measure_loudness(args.at9, args.orbis_pub_cmd, use_wine=args.wine)
    except (PackageBuildError, OSError) as exc:
        parser.error(str(exc))
    print(f"PASS: measured {report['loudness_lkfs']:.2f} LKFS")
    print(f"Use: --bgm-loudness {report['metadata_argument']}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
