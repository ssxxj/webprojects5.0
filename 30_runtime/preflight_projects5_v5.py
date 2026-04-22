#!/usr/bin/env python3
"""
projects5.0 发布前检查入口

特点：
1. 复用现有主配置校验与 drift check
2. 只输出高层摘要
3. 适合发布前人工检查与 CI 快速判定
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

RUNTIME_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUNTIME_ROOT.parent
sys.path.insert(0, str(RUNTIME_ROOT))

import build_all_chapter_assets_v5 as build_all  # type: ignore  # noqa: E402
import check_all_chapter_asset_drift_v5 as drift_check  # type: ignore  # noqa: E402


LECTURE_ROOT = PROJECT_ROOT / "50_assets" / "章节讲义"


def run_validation(root: Path, chapter_filters: list[str]) -> dict[str, Any]:
    configs = build_all.discover_configs(root, chapter_filters)
    results = [build_all.process_config(config_path, True) for config_path in configs]
    return build_all.build_summary(root, chapter_filters, True, results)


def run_drift(root: Path, chapter_filters: list[str], diff_lines: int) -> dict[str, Any]:
    configs = drift_check.discover_configs(root, chapter_filters)
    results = [drift_check.process_config(config_path, diff_lines) for config_path in configs]
    return drift_check.build_summary(root, chapter_filters, diff_lines, results)


def _load_master_config(config_path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"章节主配置不是对象结构：{config_path}")
    return raw


def _lecture_expected_paths(chapter_id: str, chapter_title: str) -> dict[str, Path]:
    lecture_dir = LECTURE_ROOT / chapter_id
    return {
        "lecture_dir": lecture_dir,
        "teacher_lecture": lecture_dir / f"{chapter_title}_教师版讲义_v5.0.md",
        "student_lecture": lecture_dir / f"{chapter_title}_学生预习版讲义_v5.0.md",
        "migration_manifest": lecture_dir / f"{chapter_title}_讲义迁移清单_v5.0.json",
        "alignment_table": lecture_dir / f"{chapter_title}_4.0讲义到5.0讲义到5.0作业包对照表.md",
    }


def _read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def process_lecture_governance(config_path: Path) -> dict[str, Any]:
    try:
        config = _load_master_config(config_path)
    except Exception as exc:
        return {
            "chapter_id": config_path.stem,
            "chapter_title": "",
            "status": "error",
            "issues": [f"master_config_unreadable: {exc}"],
        }

    chapter_id = str(config.get("chapter_id", config_path.stem))
    chapter_title = str(config.get("chapter_title", "")).strip()
    expected = _lecture_expected_paths(chapter_id, chapter_title)
    issues: list[str] = []

    for key, path in expected.items():
        if key == "lecture_dir":
            if not path.is_dir():
                issues.append(f"missing_lecture_dir: {path}")
            continue
        if not path.exists():
            issues.append(f"missing_{key}: {path}")

    heading_marker = f"# {chapter_title}"
    for key in ("teacher_lecture", "student_lecture"):
        path = expected[key]
        if path.exists():
            text = _read_text_if_exists(path)
            if heading_marker not in text:
                issues.append(f"{key}_title_mismatch: expected heading containing `{heading_marker}`")

    alignment_table = expected["alignment_table"]
    if alignment_table.exists():
        text = _read_text_if_exists(alignment_table)
        if chapter_title not in text:
            issues.append("alignment_table_title_mismatch")

    manifest_path = expected["migration_manifest"]
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(f"migration_manifest_unreadable: {exc}")
            manifest = {}

        if manifest:
            if manifest.get("chapter_id") != chapter_id:
                issues.append("migration_manifest_chapter_id_mismatch")
            if manifest.get("chapter_name") != chapter_title:
                issues.append("migration_manifest_chapter_name_mismatch")

            upstream = manifest.get("upstream_5_0", {})
            if not isinstance(upstream, dict):
                issues.append("migration_manifest_upstream_invalid")
            else:
                for key in ("profile", "assignment_pack"):
                    target = upstream.get(key)
                    if not target:
                        issues.append(f"migration_manifest_missing_upstream_{key}")
                    elif not Path(str(target)).exists():
                        issues.append(f"migration_manifest_upstream_{key}_not_found")

            generated_assets = manifest.get("generated_assets", [])
            if not isinstance(generated_assets, list) or not generated_assets:
                issues.append("migration_manifest_generated_assets_missing")
            else:
                missing_generated = [item for item in generated_assets if not Path(str(item)).exists()]
                if missing_generated:
                    issues.append(f"migration_manifest_generated_assets_not_found: {len(missing_generated)}")

    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter_title,
        "status": "ok" if not issues else "issue",
        "issues": issues,
        "checked_files": {key: str(path) for key, path in expected.items() if key != "lecture_dir"},
    }


def run_lecture_governance(root: Path, chapter_filters: list[str]) -> dict[str, Any]:
    configs = build_all.discover_configs(root, chapter_filters)
    results = [process_lecture_governance(config_path) for config_path in configs]
    issue_count = sum(1 for item in results if item.get("status") != "ok")
    return {
        "schema_version": "v5.0",
        "generator": "preflight_projects5_v5.py",
        "root": str(LECTURE_ROOT),
        "chapter_filters": chapter_filters,
        "total": len(results),
        "clean": len(results) - issue_count,
        "issue": issue_count,
        "results": results,
    }


def summarize_validation(summary: dict[str, Any]) -> dict[str, Any]:
    failed = [
        {
            "chapter_id": item.get("chapter_id"),
            "validation_errors": item.get("validation_errors", []),
        }
        for item in summary.get("results", [])
        if item.get("status") != "ok"
    ]
    return {
        "total": summary.get("total", 0),
        "success": summary.get("success", 0),
        "failed": summary.get("failed", 0),
        "failed_chapters": failed,
    }


def summarize_drift(summary: dict[str, Any]) -> dict[str, Any]:
    drifted = []
    errored = []
    for item in summary.get("results", []):
        status = item.get("status")
        if status == "drift":
            drifted.append(
                {
                    "chapter_id": item.get("chapter_id"),
                    "drifted_files": item.get("drifted_files", []),
                    "missing_files": item.get("missing_files", []),
                }
            )
        elif status == "error":
            errored.append(
                {
                    "chapter_id": item.get("chapter_id"),
                    "validation_errors": item.get("validation_errors", []),
                }
            )
    return {
        "total": summary.get("total", 0),
        "clean": summary.get("clean", 0),
        "drift": summary.get("drift", 0),
        "error": summary.get("error", 0),
        "drift_chapters": drifted,
        "error_chapters": errored,
    }


def summarize_lecture_governance(summary: dict[str, Any]) -> dict[str, Any]:
    issues = [
        {
            "chapter_id": item.get("chapter_id"),
            "issues": item.get("issues", []),
        }
        for item in summary.get("results", [])
        if item.get("status") != "ok"
    ]
    return {
        "total": summary.get("total", 0),
        "clean": summary.get("clean", 0),
        "issue": summary.get("issue", 0),
        "issue_chapters": issues,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="projects5.0 发布前检查入口：只输出高层摘要。")
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
        help="仅检查指定章节；按 chapter_id 片段匹配，如 chapter02 chapter05",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="轻量摘要 JSON 路径；默认写到 root/projects5_preflight_report_v5.json",
    )
    parser.add_argument(
        "--diff-lines",
        type=int,
        default=0,
        help="内部 drift 检查使用的 diff 预览行数；preflight 默认不需要详细 diff，故默认 0",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()

    validation_summary = run_validation(root, args.chapters)
    drift_summary = run_drift(root, args.chapters, args.diff_lines)
    lecture_summary = run_lecture_governance(root, args.chapters)

    validation_compact = summarize_validation(validation_summary)
    drift_compact = summarize_drift(drift_summary)
    lecture_compact = summarize_lecture_governance(lecture_summary)

    release_ready = (
        validation_compact["failed"] == 0
        and drift_compact["drift"] == 0
        and drift_compact["error"] == 0
        and lecture_compact["issue"] == 0
    )

    report = {
        "schema_version": "v5.0",
        "generator": "preflight_projects5_v5.py",
        "generated_at": str(date.today()),
        "root": str(root),
        "chapter_filters": args.chapters,
        "release_ready": release_ready,
        "config_validation": validation_compact,
        "asset_consistency": drift_compact,
        "lecture_governance": lecture_compact,
        "next_action": (
            "可发布"
            if release_ready
            else "先修复主配置、核心资产或讲义层轻量一致性问题，再重新执行 preflight"
        ),
    }

    summary_path = (
        args.summary.expanduser().resolve()
        if args.summary
        else root / "projects5_preflight_report_v5.json"
    )
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if release_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
