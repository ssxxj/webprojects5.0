#!/usr/bin/env python3
"""
projects5.0 Step8 逐章授课脚本生成器

输入：
1. YAML/JSON 结构化输入文件
2. 基于 `逐章授课脚本生成器输入规范_v5.0.md` 的稳定字段

输出：
1. 课堂实施方案 Markdown
2. 生成清单 manifest JSON
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


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def normalize_filename(name: str) -> str:
    safe = re.sub(r"[\\/:*?\"<>|]", "_", name).strip()
    return safe or "lesson_script"


def load_input(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        raw = yaml.safe_load(text)
    elif path.suffix.lower() == ".json":
        raw = json.loads(text)
    else:
        raise ValueError(f"不支持的输入格式：{path.suffix}")
    if not isinstance(raw, dict):
        raise ValueError("输入文件顶层必须是对象/映射。")
    return raw


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def ensure_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def validate_input(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    required_scalars = [
        "schema_version",
        "generator_target",
        "course",
        "chapter_id",
        "chapter_title",
        "duration_minutes",
        "owner",
        "updated",
        "chapter_type",
        "core_spine",
        "class_baseline",
        "environment",
    ]
    for key in required_scalars:
        if not ensure_str(data.get(key)):
            errors.append(f"缺少必填字段：{key}")

    required_lists = [
        "chapter_goals",
        "prerequisites",
        "boundary_rules",
        "authorized_scope",
        "sensitive_fields_to_mask",
        "pace_blocks",
        "board_skeleton",
        "served_tasks",
        "required_relation_graph",
        "ai_review_prompt",
        "high_freq_misconceptions",
        "step9_min_observations",
    ]
    for key in required_lists:
        if not ensure_list(data.get(key)):
            errors.append(f"缺少非空列表字段：{key}")

    omdm_map = data.get("omdm_map")
    if not isinstance(omdm_map, dict):
        errors.append("缺少对象字段：omdm_map")
    else:
        for key in ["observation", "decision", "evidence", "mechanism", "modification"]:
            node = omdm_map.get(key)
            if not isinstance(node, dict):
                errors.append(f"omdm_map.{key} 必须是对象")
                continue
            for sub in ["action", "question", "evidence"]:
                if not ensure_str(node.get(sub)):
                    errors.append(f"缺少字段：omdm_map.{key}.{sub}")

    key_questions = data.get("key_questions")
    if not isinstance(key_questions, dict):
        errors.append("缺少对象字段：key_questions")
    else:
        for key in ["forced_choice", "evidence_probe", "conditional_change"]:
            if not ensure_list(key_questions.get(key)):
                errors.append(f"缺少非空列表字段：key_questions.{key}")

    formative = data.get("formative_assessment")
    if not isinstance(formative, dict):
        errors.append("缺少对象字段：formative_assessment")
    else:
        if not ensure_str(formative.get("action")):
            errors.append("缺少字段：formative_assessment.action")
        if not ensure_list(formative.get("pass_criteria")):
            errors.append("缺少非空列表字段：formative_assessment.pass_criteria")
        if not ensure_list(formative.get("common_failures")):
            errors.append("缺少非空列表字段：formative_assessment.common_failures")

    after_class = data.get("after_class_bridge")
    if not isinstance(after_class, dict):
        errors.append("缺少对象字段：after_class_bridge")
    else:
        if not ensure_list(after_class.get("assignment")):
            errors.append("缺少非空列表字段：after_class_bridge.assignment")
        if not ensure_list(after_class.get("next_chapter")):
            errors.append("缺少非空列表字段：after_class_bridge.next_chapter")
        if not ensure_list(after_class.get("if_unbalanced_adjustment")):
            errors.append("缺少非空列表字段：after_class_bridge.if_unbalanced_adjustment")

    pace_blocks = ensure_list(data.get("pace_blocks"))
    if pace_blocks:
        required_pace_keys = ["time", "name", "goal", "teacher_action", "student_action", "evidence"]
        for index, block in enumerate(pace_blocks, start=1):
            if not isinstance(block, dict):
                errors.append(f"pace_blocks[{index}] 必须是对象")
                continue
            for key in required_pace_keys:
                if not ensure_str(block.get(key)):
                    errors.append(f"缺少字段：pace_blocks[{index}].{key}")

    misconceptions = ensure_list(data.get("high_freq_misconceptions"))
    if misconceptions:
        for index, item in enumerate(misconceptions, start=1):
            if not isinstance(item, dict):
                errors.append(f"high_freq_misconceptions[{index}] 必须是对象")
                continue
            for key in ["issue", "trigger", "correction"]:
                if not ensure_str(item.get(key)):
                    errors.append(f"缺少字段：high_freq_misconceptions[{index}].{key}")

    if len(ensure_list(data.get("step9_min_observations"))) < 3:
        errors.append("step9_min_observations 至少需要 3 条。")

    return errors


def markdown_cell(value: Any) -> str:
    return ensure_str(value).replace("|", "\\|").replace("\n", "<br>")


def numbered_lines(items: list[Any]) -> str:
    return "\n".join(f"{idx}. {ensure_str(item)}" for idx, item in enumerate(items, start=1))


def bullet_lines(items: list[Any]) -> str:
    return "\n".join(f"- {ensure_str(item)}" for item in items)


def infer_upstream_paths(chapter_id: str, chapter_title: str) -> dict[str, str]:
    safe_title = normalize_filename(chapter_title)
    return {
        "lecture": f"50_assets/章节讲义/{chapter_id}/{safe_title}_教师版讲义_v5.0.md",
        "assignment_pack": f"50_assets/assignment_packs/{chapter_id}/{safe_title}_教师端作业包_v5.0.md",
        "profile": f"40_evaluation/runtime/chapter_profiles/{chapter_id}.json",
    }


def render_pace_blocks(blocks: list[dict[str, Any]]) -> str:
    lines = ["| 时间 | 环节 | 目标 | 教师动作 | 学生活动 | 对应证据 |", "| --- | --- | --- | --- | --- | --- |"]
    for block in blocks:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(block.get("time")),
                    markdown_cell(block.get("name")),
                    markdown_cell(block.get("goal")),
                    markdown_cell(block.get("teacher_action")),
                    markdown_cell(block.get("student_action")),
                    markdown_cell(block.get("evidence")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_omdm_map(omdm_map: dict[str, dict[str, Any]]) -> str:
    label_map = {
        "observation": "Observation",
        "decision": "Decision",
        "evidence": "Evidence",
        "mechanism": "Mechanism",
        "modification": "Modification",
    }
    lines = ["| OMDM 节点 | 课堂动作 | 关键提问 | 预期证据 |", "| --- | --- | --- | --- |"]
    for key in ["observation", "decision", "evidence", "mechanism", "modification"]:
        node = omdm_map.get(key, {})
        lines.append(
            "| "
            + " | ".join(
                [
                    label_map[key],
                    markdown_cell(node.get("action")),
                    markdown_cell(node.get("question")),
                    markdown_cell(node.get("evidence")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_board_skeleton(items: list[Any]) -> str:
    return "```text\n" + "\n".join(ensure_str(item) for item in items) + "\n```"


def render_misconceptions(items: list[dict[str, Any]]) -> str:
    lines = ["| 高频误区 | 触发位置 | 纠偏动作 | 是否来自 memory |", "| --- | --- | --- | --- |"]
    for item in items:
        from_memory = "是" if bool(item.get("from_memory")) else "否"
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(item.get("issue")),
                    markdown_cell(item.get("trigger")),
                    markdown_cell(item.get("correction")),
                    from_memory,
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def render_markdown(data: dict[str, Any]) -> str:
    chapter_id = ensure_str(data["chapter_id"])
    chapter_title = ensure_str(data["chapter_title"])
    upstream = infer_upstream_paths(chapter_id, chapter_title)

    metadata = "\n".join(
        [
            "[meta]",
            "type: ClassroomPlan",
            "status: Draft",
            f"version: {ensure_str(data['schema_version'])}",
            f"chapter: {chapter_id}",
            f"owner: {ensure_str(data['owner'])}",
            f"updated: {ensure_str(data['updated'])}",
            "[/meta]",
        ]
    )

    boundary_items = ensure_list(data.get("boundary_rules"))
    if ensure_list(data.get("sensitive_fields_to_mask")) and not any(
        marker in ensure_str(item) for item in boundary_items for marker in ["脱敏", "敏感字段"]
    ):
        sensitive = "、".join(ensure_str(item) for item in ensure_list(data.get("sensitive_fields_to_mask")))
        boundary_items = boundary_items + [f"截图中的 {sensitive} 等敏感字段必须脱敏、可追溯。"]

    key_questions = data["key_questions"]
    formative = data["formative_assessment"]
    after_class = data["after_class_bridge"]

    content = [
        metadata,
        "",
        f"# {chapter_title} 课堂实施方案 v5.0",
        "",
        "## 1. 基础信息",
        "",
        f"- 课程：{ensure_str(data['course'])}",
        f"- 章节：{chapter_title}",
        f"- 课次：{ensure_str(data['duration_minutes'])} 分钟标准课",
        f"- 班级基础：{ensure_str(data['class_baseline'])}",
        f"- 环境：{ensure_str(data['environment'])}",
        "- 上游讲义：",
        f"  - `{upstream['lecture']}`",
        "- 上游 assignment pack：",
        f"  - `{upstream['assignment_pack']}`",
        "- 上游 profile：",
        f"  - `{upstream['profile']}`",
        "",
        "## 2. 本节唯一主线",
        "",
        f"`{ensure_str(data['core_spine'])}`",
        "",
        "## 3. 课堂目标",
        "",
        numbered_lines(ensure_list(data["chapter_goals"])),
        "",
        "## 4. 先修要求与环境边界",
        "",
        "### 先修要求",
        "",
        numbered_lines(ensure_list(data["prerequisites"])),
        "",
        "### 环境与边界",
        "",
        numbered_lines(boundary_items),
        "",
        "## 5. 90 分钟节奏",
        "",
        render_pace_blocks(ensure_list(data["pace_blocks"])),
        "",
        "## 6. OMDM 与课堂动作对照",
        "",
        render_omdm_map(data["omdm_map"]),
        "",
        "## 7. 板书 / 图示主骨架",
        "",
        render_board_skeleton(ensure_list(data["board_skeleton"])),
        "",
        "## 8. 关键提问设计",
        "",
        "### 强制选择题",
        "",
        numbered_lines(ensure_list(key_questions["forced_choice"])),
        "",
        "### 证据追问",
        "",
        numbered_lines(ensure_list(key_questions["evidence_probe"])),
        "",
        "### 条件变化题",
        "",
        numbered_lines(ensure_list(key_questions["conditional_change"])),
        "",
        "## 9. 形成性评估",
        "",
        "### 评估动作",
        "",
        ensure_str(formative["action"]),
        "",
        "### 通过标准",
        "",
        numbered_lines(ensure_list(formative["pass_criteria"])),
        "",
        "### 常见失败表现",
        "",
        numbered_lines(ensure_list(formative["common_failures"])),
        "",
        "## 10. 与 assignment pack 的对齐收口",
        "",
        "### 本节直接服务的任务",
        "",
        numbered_lines(ensure_list(data["served_tasks"])),
        "",
        "### 本节必须前置的关系图/关系表要求",
        "",
        numbered_lines(ensure_list(data["required_relation_graph"])),
        "",
        "### 本节应前置的 AI 输出审核提醒",
        "",
        numbered_lines(ensure_list(data["ai_review_prompt"])),
        "",
        "## 11. 高频误区与纠偏",
        "",
        render_misconceptions(ensure_list(data["high_freq_misconceptions"])),
        "",
        "## 12. Step 9 最小观察记录",
        "",
        "本节结束后至少记录：",
        "",
        numbered_lines(ensure_list(data["step9_min_observations"])),
        "",
        "## 13. 课后衔接",
        "",
        "### 作业布置",
        "",
        numbered_lines(ensure_list(after_class["assignment"])),
        "",
        "### 下节前置",
        "",
        numbered_lines(ensure_list(after_class["next_chapter"])),
        "",
        "### 若本节失衡，优先调整什么",
        "",
        numbered_lines(ensure_list(after_class["if_unbalanced_adjustment"])),
        "",
    ]
    return "\n".join(content)


def build_manifest(input_path: Path, output_path: Path, chapter_id: str, chapter_title: str, errors: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "v5.0",
        "generator": "generate_lesson_script_v5.py",
        "generated_at": str(date.today()),
        "chapter_id": chapter_id,
        "chapter_title": chapter_title,
        "input_file": str(input_path),
        "output_file": str(output_path),
        "validation_errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="projects5.0 Step8 逐章授课脚本生成器")
    parser.add_argument("--input", required=True, help="YAML/JSON 输入文件路径")
    parser.add_argument("--output", help="输出 Markdown 文件路径")
    parser.add_argument("--outdir", help="输出目录；若省略则按 chapter_id 输出到正式资产目录")
    parser.add_argument("--manifest", help="输出 manifest JSON 路径")
    parser.add_argument("--validate-only", action="store_true", help="仅校验输入，不生成文件")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    data = load_input(input_path)
    errors = validate_input(data)

    if errors:
        print(json.dumps({"validation_errors": errors}, ensure_ascii=False, indent=2))
        return 1

    chapter_id = ensure_str(data["chapter_id"])
    chapter_title = ensure_str(data["chapter_title"])
    safe_title = normalize_filename(chapter_title)

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        outdir = Path(args.outdir).expanduser().resolve() if args.outdir else PROJECT_ROOT / "50_assets" / "课堂实施方案" / chapter_id
        output_path = outdir / f"{safe_title}_课堂实施方案_v5.0.md"

    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else output_path.with_name(f"{safe_title}_课堂实施方案_生成清单_v5.0.json")

    if args.validate_only:
        print(json.dumps(build_manifest(input_path, output_path, chapter_id, chapter_title, errors), ensure_ascii=False, indent=2))
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = render_markdown(data)
    output_path.write_text(markdown, encoding="utf-8")
    manifest_path.write_text(
        json.dumps(build_manifest(input_path, output_path, chapter_id, chapter_title, errors), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"output": str(output_path), "manifest": str(manifest_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
