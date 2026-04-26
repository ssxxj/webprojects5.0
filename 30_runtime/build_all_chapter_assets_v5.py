#!/usr/bin/env python3
"""
projects5.0 全课程章节资产批量编排脚本

输入：
1. 章节主配置目录 `30_runtime/chapter_master_configs/*.yaml`

输出：
1. 各章 profile
2. 各章 assignment pack
3. 各章 lesson_script_input_v5.yaml
4. 各章课堂实施方案
5. 全课程批量构建摘要 `all_chapters_build_manifest_v5.json`
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

import build_chapter_assets_v5 as single  # type: ignore  # noqa: E402
from project_paths_v5 import project_relative  # noqa: E402


def discover_configs(root: Path, chapter_filters: list[str]) -> list[Path]:
    paths = sorted(path for path in root.glob("chapter*.yaml") if path.is_file())
    if not chapter_filters:
        return paths
    selected: list[Path] = []
    for path in paths:
        stem = path.stem
        if any(token in stem for token in chapter_filters):
            selected.append(path)
    return selected


def process_config(config_path: Path, validate_only: bool) -> dict[str, Any]:
    data = single.load_master_config(config_path)
    chapter_id = single.ensure_str(data.get("chapter_id")) or config_path.stem
    errors = single.validate_master_config(data)
    profile_path = PROJECT_ROOT / "40_evaluation" / "runtime" / "chapter_profiles" / f"{chapter_id}.json"
    lesson_dir = PROJECT_ROOT / "50_assets" / "课堂实施方案" / chapter_id
    lesson_input_path = lesson_dir / "lesson_script_input_v5.yaml"
    manifest_path = config_path.with_name(f"{single.normalize_filename(chapter_id)}_build_manifest_v5.json")

    if errors:
        return {
            "chapter_id": chapter_id,
            "config_file": project_relative(config_path, PROJECT_ROOT),
            "status": "error",
            "validation_errors": errors,
        }

    preview = single.build_manifest(config_path, chapter_id, profile_path, lesson_input_path, {}, {})
    preview["status"] = "ok"
    preview["validation_errors"] = []

    if validate_only:
        return preview

    profile_payload = single.build_profile_payload(data)
    lesson_payload = single.build_lesson_input_payload(data)
    assignment_dir = PROJECT_ROOT / "50_assets" / "assignment_packs" / chapter_id

    single.write_profile(profile_payload, profile_path)
    single.write_lesson_input(lesson_payload, lesson_input_path)
    assignment_settings = single.resolve_assignment_settings(data, profile_path)
    assignment_files = single.generate_assignment_assets(profile_path, assignment_dir, assignment_settings)
    lesson_files = single.generate_lesson_assets(lesson_payload, lesson_input_path, lesson_dir)

    manifest = single.build_manifest(
        config_path,
        chapter_id,
        profile_path,
        lesson_input_path,
        assignment_files,
        lesson_files,
    )
    manifest["status"] = "ok"
    manifest["validation_errors"] = []
    manifest["chapter_manifest"] = project_relative(manifest_path, PROJECT_ROOT)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def build_summary(root: Path, chapter_filters: list[str], validate_only: bool, results: list[dict[str, Any]]) -> dict[str, Any]:
    success = sum(1 for item in results if item.get("status") == "ok")
    failed = sum(1 for item in results if item.get("status") != "ok")
    return {
        "schema_version": "v5.0",
        "generator": "build_all_chapter_assets_v5.py",
        "generated_at": str(date.today()),
        "root": project_relative(root, PROJECT_ROOT),
        "chapter_filters": chapter_filters,
        "validate_only": validate_only,
        "total": len(results),
        "success": success,
        "failed": failed,
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量根据章节主配置重建全课程资产。")
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
    parser.add_argument("--validate-only", action="store_true", help="仅校验主配置，不写任何产物")
    parser.add_argument(
        "--summary",
        type=Path,
        help="批量构建摘要 JSON 路径；默认写到 root/all_chapters_build_manifest_v5.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    configs = discover_configs(root, args.chapters)
    if not configs:
        print(
            json.dumps(
                {
                    "schema_version": "v5.0",
                    "generator": "build_all_chapter_assets_v5.py",
                    "generated_at": str(date.today()),
                    "root": project_relative(root, PROJECT_ROOT),
                    "chapter_filters": args.chapters,
                    "validate_only": args.validate_only,
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "results": [],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    results = [process_config(config_path, args.validate_only) for config_path in configs]
    summary = build_summary(root, args.chapters, args.validate_only, results)
    summary_path = (
        args.summary.expanduser().resolve()
        if args.summary
        else root / "all_chapters_build_manifest_v5.json"
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
