#!/usr/bin/env python3
"""
projects5.0 课程维护入口

统一封装：
1. 批量重建全课程资产
2. 漂移检查

适用场景：
1. 教师日常维护
2. CI 校验
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUNTIME_ROOT.parent
sys.path.insert(0, str(RUNTIME_ROOT))

import build_all_chapter_assets_v5 as build_all  # type: ignore  # noqa: E402
import check_all_chapter_asset_drift_v5 as drift_check  # type: ignore  # noqa: E402


def run_build(root: Path, chapter_filters: list[str], validate_only: bool) -> dict[str, Any]:
    configs = build_all.discover_configs(root, chapter_filters)
    results = [build_all.process_config(config_path, validate_only) for config_path in configs]
    return build_all.build_summary(root, chapter_filters, validate_only, results)


def run_drift(root: Path, chapter_filters: list[str], diff_lines: int) -> dict[str, Any]:
    configs = drift_check.discover_configs(root, chapter_filters)
    results = [drift_check.process_config(config_path, diff_lines) for config_path in configs]
    return drift_check.build_summary(root, chapter_filters, diff_lines, results)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="projects5.0 课程维护入口：统一执行批量重建与漂移检查。")
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT / "30_runtime" / "chapter_master_configs",
        help="章节主配置目录；默认使用 30_runtime/chapter_master_configs",
    )
    parser.add_argument(
        "--chapters",
        nargs="*",
        default=[],
        help="仅处理指定章节；按 chapter_id 片段匹配，如 chapter02 chapter05",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "check", "rebuild", "validate"],
        default="full",
        help="full=先重建再检查；check=只做漂移检查；rebuild=只重建；validate=只校验主配置",
    )
    parser.add_argument(
        "--diff-lines",
        type=int,
        default=12,
        help="漂移报告中每个文件保留的 diff 预览行数；默认 12",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="统一维护报告 JSON 路径；默认写到 root/projects5_maintenance_report_v5.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()

    build_summary: dict[str, Any] | None = None
    drift_summary: dict[str, Any] | None = None

    if args.mode in {"full", "rebuild", "validate"}:
        build_summary = run_build(root, args.chapters, validate_only=(args.mode == "validate"))

    if args.mode in {"full", "check"}:
        drift_summary = run_drift(root, args.chapters, args.diff_lines)

    report = {
        "schema_version": "v5.0",
        "generator": "maintain_projects5_v5.py",
        "generated_at": str(date.today()),
        "root": str(root),
        "chapter_filters": args.chapters,
        "mode": args.mode,
        "build": build_summary,
        "drift": drift_summary,
    }

    summary_path = (
        args.summary.expanduser().resolve()
        if args.summary
        else root / "projects5_maintenance_report_v5.json"
    )
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.mode in {"rebuild", "validate"}:
        return 0 if build_summary and build_summary.get("failed", 0) == 0 else 1
    if args.mode == "check":
        return 0 if drift_summary and drift_summary.get("drift", 0) == 0 and drift_summary.get("error", 0) == 0 else 1

    build_ok = build_summary is not None and build_summary.get("failed", 0) == 0
    drift_ok = drift_summary is not None and drift_summary.get("drift", 0) == 0 and drift_summary.get("error", 0) == 0
    return 0 if build_ok and drift_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
