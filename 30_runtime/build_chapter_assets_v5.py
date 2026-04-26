#!/usr/bin/env python3
"""
projects5.0 章节资产编排脚本

单一来源：
1. 章节主配置 YAML/JSON

统一生成：
1. chapter profile JSON
2. assignment pack
3. lesson_script_input_v5.yaml
4. 课堂实施方案 markdown
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT_RUNTIME = PROJECT_ROOT / "40_evaluation" / "runtime"
LESSON_RUNTIME = PROJECT_ROOT / "50_assets" / "课堂实施方案" / "runtime"

sys.path.insert(0, str(ASSIGNMENT_RUNTIME))
sys.path.insert(0, str(LESSON_RUNTIME))

import generate_assignment_pack_v5 as assignment_gen  # type: ignore  # noqa: E402
import generate_lesson_script_v5 as lesson_gen  # type: ignore  # noqa: E402
from project_paths_v5 import project_relative, relativize_mapping  # noqa: E402


def ensure_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_master_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        raw = yaml.safe_load(text)
    elif path.suffix.lower() == ".json":
        raw = json.loads(text)
    else:
        raise ValueError(f"不支持的主配置格式：{path.suffix}")
    if not isinstance(raw, dict):
        raise ValueError("主配置顶层必须是对象/映射。")
    return raw


def normalize_filename(name: str) -> str:
    safe = re.sub(r"[\\/:*?\"<>|]", "_", name).strip()
    return safe or "chapter_asset"


def validate_profile_section(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scalar_keys = ["chapter_mainline", "relation_item_name", "relation_item_score", "self_eval_score"]
    for key in scalar_keys:
        if key in {"relation_item_score", "self_eval_score"}:
            if profile.get(key) in (None, ""):
                errors.append(f"profile.{key} 缺失")
        elif not ensure_str(profile.get(key)):
            errors.append(f"profile.{key} 缺失")

    if not ensure_list(profile.get("capability_goals")):
        errors.append("profile.capability_goals 不能为空")
    if not ensure_list(profile.get("tasks")):
        errors.append("profile.tasks 不能为空")
    if not ensure_list(profile.get("redlines")):
        errors.append("profile.redlines 不能为空")
    if not ensure_list(profile.get("professional_checks")):
        errors.append("profile.professional_checks 不能为空")
    if not ensure_list(profile.get("default_tags")):
        errors.append("profile.default_tags 不能为空")

    for index, task in enumerate(ensure_list(profile.get("tasks")), start=1):
        if not isinstance(task, dict):
            errors.append(f"profile.tasks[{index}] 必须是对象")
            continue
        for key in ["name", "score", "required"]:
            if task.get(key) in (None, ""):
                errors.append(f"profile.tasks[{index}].{key} 缺失")
        if not ensure_list(task.get("semantic_requirements")):
            errors.append(f"profile.tasks[{index}].semantic_requirements 不能为空")

    for index, item in enumerate(ensure_list(profile.get("redlines")), start=1):
        if not isinstance(item, dict):
            errors.append(f"profile.redlines[{index}] 必须是对象")
            continue
        for key in ["name", "description", "action"]:
            if not ensure_str(item.get(key)):
                errors.append(f"profile.redlines[{index}].{key} 缺失")

    return errors


def validate_master_config(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["schema_version", "generator_target", "course", "chapter_id", "chapter_title", "owner", "updated"]:
        if not ensure_str(data.get(key)):
            errors.append(f"缺少主配置字段：{key}")
    schema_version = ensure_str(data.get("schema_version"))
    if schema_version and schema_version != "v5.0":
        errors.append(f"不支持的 schema_version：{schema_version}；当前脚本只接受 v5.0。")

    profile = data.get("profile")
    if not isinstance(profile, dict):
        errors.append("缺少对象字段：profile")
    else:
        errors.extend(validate_profile_section(profile))

    lesson = data.get("lesson")
    if not isinstance(lesson, dict):
        errors.append("缺少对象字段：lesson")
    else:
        lesson_payload = build_lesson_input_payload(data)
        errors.extend(lesson_gen.validate_input(lesson_payload))

    assignment = data.get("assignment")
    if assignment is not None and not isinstance(assignment, dict):
        errors.append("assignment 必须是对象")

    return errors


def build_profile_payload(data: dict[str, Any]) -> dict[str, Any]:
    profile = dict(data["profile"])
    return {
        "schema_version": ensure_str(data["schema_version"]),
        "course_name": ensure_str(data["course"]),
        "chapter_name": ensure_str(data["chapter_title"]),
        "chapter_mainline": ensure_str(profile["chapter_mainline"]),
        "capability_goals": ensure_list(profile.get("capability_goals")),
        "tasks": ensure_list(profile.get("tasks")),
        "relation_item_name": ensure_str(profile["relation_item_name"]),
        "relation_item_score": float(profile["relation_item_score"]),
        "self_eval_score": float(profile["self_eval_score"]),
        "redlines": ensure_list(profile.get("redlines")),
        "professional_checks": ensure_list(profile.get("professional_checks")),
        "default_tags": ensure_list(profile.get("default_tags")),
    }


def build_lesson_input_payload(data: dict[str, Any]) -> dict[str, Any]:
    lesson = dict(data["lesson"])
    return {
        "schema_version": ensure_str(data["schema_version"]),
        "generator_target": "chapter_lesson_script",
        "course": ensure_str(data["course"]),
        "chapter_id": ensure_str(data["chapter_id"]),
        "chapter_title": ensure_str(data["chapter_title"]),
        "duration_minutes": lesson.get("duration_minutes"),
        "owner": ensure_str(data["owner"]),
        "updated": ensure_str(data["updated"]),
        "chapter_type": ensure_str(lesson.get("chapter_type")),
        "core_spine": ensure_str(lesson.get("core_spine")),
        "chapter_goals": ensure_list(lesson.get("chapter_goals")),
        "prerequisites": ensure_list(lesson.get("prerequisites")),
        "boundary_rules": ensure_list(lesson.get("boundary_rules")),
        "class_baseline": ensure_str(lesson.get("class_baseline")),
        "environment": ensure_str(lesson.get("environment")),
        "authorized_scope": ensure_list(lesson.get("authorized_scope")),
        "sensitive_fields_to_mask": ensure_list(lesson.get("sensitive_fields_to_mask")),
        "pace_blocks": ensure_list(lesson.get("pace_blocks")),
        "omdm_map": lesson.get("omdm_map"),
        "board_skeleton": ensure_list(lesson.get("board_skeleton")),
        "key_questions": lesson.get("key_questions"),
        "served_tasks": ensure_list(lesson.get("served_tasks")),
        "required_relation_graph": ensure_list(lesson.get("required_relation_graph")),
        "ai_review_prompt": ensure_list(lesson.get("ai_review_prompt")),
        "formative_assessment": lesson.get("formative_assessment"),
        "high_freq_misconceptions": ensure_list(lesson.get("high_freq_misconceptions")),
        "step9_min_observations": ensure_list(lesson.get("step9_min_observations")),
        "after_class_bridge": lesson.get("after_class_bridge"),
    }


def numbered_lines(items: list[Any]) -> str:
    return "\n".join(f"{idx}. {ensure_str(item)}" for idx, item in enumerate(items, start=1))


def resolve_assignment_settings(data: dict[str, Any], profile_path: Path) -> dict[str, Any]:
    assignment = data.get("assignment") or {}
    profile_payload = build_profile_payload(data)
    profile_obj = assignment_gen.load_profile(profile_path)
    lesson = data["lesson"]
    boundary_rules = ensure_list(lesson.get("boundary_rules"))
    return {
        "submission_format": ensure_str(assignment.get("submission_format")) or "PDF",
        "duration": ensure_str(assignment.get("suggested_duration")) or assignment_gen.infer_duration(len(profile_payload["tasks"])),
        "naming": ensure_str(assignment.get("naming")) or assignment_gen.default_submission_name(profile_obj),
        "environment": ensure_str(lesson.get("environment")) or "DVWA + 本机浏览器 + 教师授权实验环境",
        "boundary": numbered_lines(boundary_rules) if boundary_rules else assignment_gen.infer_boundary(profile_obj),
    }


def write_profile(profile_payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile_payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_lesson_input(lesson_payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(lesson_payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def generate_assignment_assets(profile_path: Path, outdir: Path, settings: dict[str, Any]) -> dict[str, str]:
    profile = assignment_gen.load_profile(profile_path)
    outdir.mkdir(parents=True, exist_ok=True)
    base = assignment_gen.normalize_filename(profile.chapter_name)
    files = {
        "teacher_pack": outdir / f"{base}_教师端作业包_v5.0.md",
        "student_sheet": outdir / f"{base}_学生版作业说明单_v5.0.md",
        "teacher_acceptance": outdir / f"{base}_教师验收表_v5.0.md",
        "feedback_template": outdir / f"{base}_班级级教学反馈模板_v5.0.md",
        "score_summary": outdir / f"{base}_任务分值与红线摘要_v5.0.md",
        "manifest": outdir / f"{base}_生成清单_v5.0.json",
    }

    assignment_gen.write_text(
        files["teacher_pack"],
        assignment_gen.build_teacher_pack(
            profile=profile,
            profile_path=profile_path,
            environment=settings["environment"],
            boundary=settings["boundary"],
            submission_format=settings["submission_format"],
            duration=settings["duration"],
            naming=settings["naming"],
        ),
    )
    assignment_gen.write_text(
        files["student_sheet"],
        assignment_gen.build_student_sheet(
            profile=profile,
            environment=settings["environment"],
            boundary=settings["boundary"],
            submission_format=settings["submission_format"],
            duration=settings["duration"],
            naming=settings["naming"],
        ),
    )
    assignment_gen.write_text(files["teacher_acceptance"], assignment_gen.build_teacher_acceptance(profile))
    assignment_gen.write_text(files["feedback_template"], assignment_gen.build_feedback_template(profile))
    assignment_gen.write_text(files["score_summary"], assignment_gen.build_score_summary(profile))
    manifest = assignment_gen.build_manifest(
        profile,
        {key: project_relative(path, PROJECT_ROOT) for key, path in files.items() if key != "manifest"},
        argparse.Namespace(**settings),
    )
    files["manifest"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {key: project_relative(value, PROJECT_ROOT) for key, value in files.items()}


def generate_lesson_assets(lesson_payload: dict[str, Any], lesson_input_path: Path, chapter_dir: Path) -> dict[str, str]:
    chapter_dir.mkdir(parents=True, exist_ok=True)
    chapter_title = ensure_str(lesson_payload["chapter_title"])
    safe_title = lesson_gen.normalize_filename(chapter_title)
    output_path = chapter_dir / f"{safe_title}_课堂实施方案_v5.0.md"
    manifest_path = chapter_dir / f"{safe_title}_课堂实施方案_生成清单_v5.0.json"
    markdown = lesson_gen.render_markdown(lesson_payload)
    output_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
    manifest = lesson_gen.build_manifest(
        lesson_input_path,
        output_path,
        ensure_str(lesson_payload["chapter_id"]),
        chapter_title,
        [],
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "lesson_script": project_relative(output_path, PROJECT_ROOT),
        "lesson_manifest": project_relative(manifest_path, PROJECT_ROOT),
    }


def build_manifest(
    input_path: Path,
    chapter_id: str,
    profile_path: Path,
    lesson_input_path: Path,
    assignment_files: dict[str, str],
    lesson_files: dict[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": "v5.0",
        "generator": "build_chapter_assets_v5.py",
        "generated_at": str(date.today()),
        "input_file": project_relative(input_path, PROJECT_ROOT),
        "chapter_id": chapter_id,
        "profile_file": project_relative(profile_path, PROJECT_ROOT),
        "lesson_input_file": project_relative(lesson_input_path, PROJECT_ROOT),
        "assignment_outputs": relativize_mapping(assignment_files, PROJECT_ROOT),
        "lesson_outputs": relativize_mapping(lesson_files, PROJECT_ROOT),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据章节主配置统一生成 profile、assignment pack、lesson input 和课堂实施方案。")
    parser.add_argument("--input", required=True, type=Path, help="章节主配置 YAML/JSON 路径")
    parser.add_argument("--validate-only", action="store_true", help="仅校验，不写文件")
    parser.add_argument("--manifest", type=Path, help="自定义总 manifest 输出路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input.expanduser().resolve()
    data = load_master_config(input_path)
    errors = validate_master_config(data)
    chapter_id = ensure_str(data.get("chapter_id"))
    if errors:
        print(json.dumps({"chapter_id": chapter_id, "validation_errors": errors}, ensure_ascii=False, indent=2))
        return 1

    profile_payload = build_profile_payload(data)
    lesson_payload = build_lesson_input_payload(data)
    profile_path = PROJECT_ROOT / "40_evaluation" / "runtime" / "chapter_profiles" / f"{chapter_id}.json"
    lesson_dir = PROJECT_ROOT / "50_assets" / "课堂实施方案" / chapter_id
    lesson_input_path = lesson_dir / "lesson_script_input_v5.yaml"
    assignment_dir = PROJECT_ROOT / "50_assets" / "assignment_packs" / chapter_id
    manifest_path = (
        args.manifest.expanduser().resolve()
        if args.manifest
        else input_path.with_name(f"{normalize_filename(chapter_id)}_build_manifest_v5.json")
    )

    if args.validate_only:
        preview = build_manifest(input_path, chapter_id, profile_path, lesson_input_path, {}, {})
        preview["validation_errors"] = []
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0

    write_profile(profile_payload, profile_path)
    write_lesson_input(lesson_payload, lesson_input_path)
    assignment_settings = resolve_assignment_settings(data, profile_path)
    assignment_files = generate_assignment_assets(profile_path, assignment_dir, assignment_settings)
    lesson_files = generate_lesson_assets(lesson_payload, lesson_input_path, lesson_dir)
    manifest = build_manifest(input_path, chapter_id, profile_path, lesson_input_path, assignment_files, lesson_files)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
