#!/usr/bin/env python3
"""
projects5.0 全课程章节资产漂移检查脚本

目标：
1. 以 `chapter_master_configs/*.yaml` 为单一来源
2. 检查当前落盘的 profile / assignment pack / lesson input / 课堂实施方案
3. 判断哪些文件已经与主配置不一致
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml


RUNTIME_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUNTIME_ROOT.parent
sys.path.insert(0, str(RUNTIME_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "40_evaluation" / "runtime"))
sys.path.insert(0, str(PROJECT_ROOT / "50_assets" / "课堂实施方案" / "runtime"))

import build_chapter_assets_v5 as orchestrator  # type: ignore  # noqa: E402
import generate_assignment_pack_v5 as assignment_gen  # type: ignore  # noqa: E402
import generate_lesson_script_v5 as lesson_gen  # type: ignore  # noqa: E402


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip() + "\n"


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


def preview_diff(expected: str, actual: str, max_lines: int) -> list[str]:
    diff = list(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile="expected",
            tofile="actual",
            lineterm="",
            n=1,
        )
    )
    return diff[:max_lines]


def build_profile_object(payload: dict[str, Any]) -> assignment_gen.ChapterProfile:
    return assignment_gen.ChapterProfile(
        course_name=payload["course_name"],
        chapter_name=payload["chapter_name"],
        chapter_mainline=payload["chapter_mainline"],
        capability_goals=payload.get("capability_goals", []),
        tasks=[assignment_gen.TaskRule(**task) for task in payload.get("tasks", [])],
        relation_item_name=payload["relation_item_name"],
        relation_item_score=float(payload["relation_item_score"]),
        self_eval_score=float(payload["self_eval_score"]),
        redlines=[assignment_gen.RedlineRule(**item) for item in payload.get("redlines", [])],
        professional_checks=payload.get("professional_checks", []),
        default_tags=payload.get("default_tags", []),
    )


def resolve_expected_assignment_texts(data: dict[str, Any], profile_path: Path) -> dict[str, str]:
    profile_payload = orchestrator.build_profile_payload(data)
    profile_obj = build_profile_object(profile_payload)
    settings = orchestrator.resolve_assignment_settings(data, profile_path)
    return {
        "profile": json.dumps(profile_payload, ensure_ascii=False, indent=2),
        "teacher_pack": assignment_gen.build_teacher_pack(
            profile=profile_obj,
            profile_path=profile_path,
            environment=settings["environment"],
            boundary=settings["boundary"],
            submission_format=settings["submission_format"],
            duration=settings["duration"],
            naming=settings["naming"],
        ),
        "student_sheet": assignment_gen.build_student_sheet(
            profile=profile_obj,
            environment=settings["environment"],
            boundary=settings["boundary"],
            submission_format=settings["submission_format"],
            duration=settings["duration"],
            naming=settings["naming"],
        ),
        "teacher_acceptance": assignment_gen.build_teacher_acceptance(profile_obj),
        "feedback_template": assignment_gen.build_feedback_template(profile_obj),
        "score_summary": assignment_gen.build_score_summary(profile_obj),
    }


def resolve_expected_lesson_texts(data: dict[str, Any]) -> dict[str, str]:
    lesson_payload = orchestrator.build_lesson_input_payload(data)
    return {
        "lesson_input": yaml.safe_dump(lesson_payload, allow_unicode=True, sort_keys=False),
        "lesson_script": lesson_gen.render_markdown(lesson_payload),
    }


def expected_paths(chapter_id: str, chapter_title: str) -> dict[str, Path]:
    profile_path = PROJECT_ROOT / "40_evaluation" / "runtime" / "chapter_profiles" / f"{chapter_id}.json"
    lesson_dir = PROJECT_ROOT / "50_assets" / "课堂实施方案" / chapter_id
    assignment_dir = PROJECT_ROOT / "50_assets" / "assignment_packs" / chapter_id
    safe_title = assignment_gen.normalize_filename(chapter_title)
    return {
        "profile": profile_path,
        "lesson_input": lesson_dir / "lesson_script_input_v5.yaml",
        "lesson_script": lesson_dir / f"{safe_title}_课堂实施方案_v5.0.md",
        "teacher_pack": assignment_dir / f"{safe_title}_教师端作业包_v5.0.md",
        "student_sheet": assignment_dir / f"{safe_title}_学生版作业说明单_v5.0.md",
        "teacher_acceptance": assignment_dir / f"{safe_title}_教师验收表_v5.0.md",
        "feedback_template": assignment_dir / f"{safe_title}_班级级教学反馈模板_v5.0.md",
        "score_summary": assignment_dir / f"{safe_title}_任务分值与红线摘要_v5.0.md",
    }


def compare_file(path: Path, expected_text: str, diff_lines: int) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "path": str(path), "diff_preview": []}
    actual = path.read_text(encoding="utf-8")
    expected_norm = normalize_text(expected_text)
    actual_norm = normalize_text(actual)
    if expected_norm == actual_norm:
        return {"status": "clean", "path": str(path), "diff_preview": []}
    return {
        "status": "drift",
        "path": str(path),
        "diff_preview": preview_diff(expected_norm, actual_norm, diff_lines),
    }


def process_config(config_path: Path, diff_lines: int) -> dict[str, Any]:
    data = orchestrator.load_master_config(config_path)
    chapter_id = orchestrator.ensure_str(data.get("chapter_id")) or config_path.stem
    chapter_title = orchestrator.ensure_str(data.get("chapter_title"))
    validation_errors = orchestrator.validate_master_config(data)
    if validation_errors:
        return {
            "chapter_id": chapter_id,
            "config_file": str(config_path),
            "status": "error",
            "validation_errors": validation_errors,
            "drifted_files": [],
        }

    paths = expected_paths(chapter_id, chapter_title)
    expected_assignment = resolve_expected_assignment_texts(data, paths["profile"])
    expected_lesson = resolve_expected_lesson_texts(data)
    expected_map = {
        "profile": expected_assignment["profile"],
        "teacher_pack": expected_assignment["teacher_pack"],
        "student_sheet": expected_assignment["student_sheet"],
        "teacher_acceptance": expected_assignment["teacher_acceptance"],
        "feedback_template": expected_assignment["feedback_template"],
        "score_summary": expected_assignment["score_summary"],
        "lesson_input": expected_lesson["lesson_input"],
        "lesson_script": expected_lesson["lesson_script"],
    }

    files: dict[str, dict[str, Any]] = {}
    drifted_files: list[str] = []
    missing_files: list[str] = []
    for key, path in paths.items():
        result = compare_file(path, expected_map[key], diff_lines)
        files[key] = result
        if result["status"] == "drift":
            drifted_files.append(key)
        elif result["status"] == "missing":
            missing_files.append(key)

    status = "clean"
    if drifted_files or missing_files:
        status = "drift"

    return {
        "chapter_id": chapter_id,
        "config_file": str(config_path),
        "status": status,
        "validation_errors": [],
        "drifted_files": drifted_files,
        "missing_files": missing_files,
        "files": files,
    }


def build_summary(root: Path, chapter_filters: list[str], diff_lines: int, results: list[dict[str, Any]]) -> dict[str, Any]:
    clean = sum(1 for item in results if item.get("status") == "clean")
    drift = sum(1 for item in results if item.get("status") == "drift")
    error = sum(1 for item in results if item.get("status") == "error")
    return {
        "schema_version": "v5.0",
        "generator": "check_all_chapter_asset_drift_v5.py",
        "generated_at": str(date.today()),
        "root": str(root),
        "chapter_filters": chapter_filters,
        "diff_lines": diff_lines,
        "total": len(results),
        "clean": clean,
        "drift": drift,
        "error": error,
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查现有章节资产是否已与主配置发生漂移。")
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
        help="漂移检查摘要 JSON 路径；默认写到 root/all_chapters_drift_report_v5.json",
    )
    parser.add_argument(
        "--diff-lines",
        type=int,
        default=12,
        help="每个漂移文件保留的 diff 预览行数；默认 12",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    configs = discover_configs(root, args.chapters)
    if not configs:
        summary = build_summary(root, args.chapters, args.diff_lines, [])
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    results = [process_config(config_path, args.diff_lines) for config_path in configs]
    summary = build_summary(root, args.chapters, args.diff_lines, results)
    summary_path = (
        args.summary.expanduser().resolve()
        if args.summary
        else root / "all_chapters_drift_report_v5.json"
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["drift"] == 0 and summary["error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
