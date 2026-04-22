#!/usr/bin/env python3
"""
projects5.0 记忆层自动回填器

输入：
1. 一个或多个 教学反馈摘要_v5.json

输出：
1. 班级教学反馈索引_v5.0.md
2. 误区库_v5.0.md
3. 案例库_v5.0.md
4. memory_snapshot_v5.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


TAG_LIBRARY: dict[str, dict[str, Any]] = {
    "T1": {
        "title": "任务字段缺失",
        "symptoms": [
            "任务存在，但查询对象、关键字段、目标或返回含义缺失。",
            "学生写了过程，却无法稳定对应评分字段。",
        ],
        "causes": [
            "学生不清楚每个任务的最小提交字段。",
            "模板中缺少字段示例或核对表前置不够。",
        ],
        "actions": ["在学生版说明单中为每个任务增加最小字段示例。"],
        "upgrade_files": [
            "`40_evaluation/学生版作业说明单模板_v5.0.md`",
            "`40_evaluation/第11步作业设计模板_v5.0.md`",
        ],
    },
    "T2": {
        "title": "任务部分完成",
        "symptoms": [
            "主体任务已写，但仍缺少一个或多个关键判断点。",
            "能做出结果，但不能把结果解释清楚。",
        ],
        "causes": [
            "学生只完成了操作层，没有完成解释层。",
            "任务说明对“完成”和“达标”区分不够清楚。",
        ],
        "actions": ["在下轮讲评中增加“已完成但未达标”的反例示范。"],
        "upgrade_files": ["`40_evaluation/教师验收表模板_v5.0.md`"],
    },
    "E1": {
        "title": "证据不清晰",
        "symptoms": [
            "截图很多，但没有标出关键字段。",
            "截图已给出，但看不出证据点在哪里。",
        ],
        "causes": [
            "学生不知道“最小证据集”是什么。",
            "模板没有把关键字段示例写在足够靠前的位置。",
        ],
        "actions": ["补讲“证据最小集”，明确各任务至少应标出哪些字段。"],
        "upgrade_files": [
            "`40_evaluation/第11步作业设计模板_v5.0.md`",
            "`40_evaluation/学生版作业说明单模板_v5.0.md`",
        ],
    },
    "E2": {
        "title": "证据与结论不对应",
        "symptoms": [
            "把线索写成证据，把端口写成漏洞，把第三方索引写成实时探测。",
            "结论明显超出截图或抓包内容本身能支持的范围。",
        ],
        "causes": ["线索、证据、主动探测三层没有真正分清。"],
        "actions": ["补讲“线索 / 证据 / 主动探测”的分层关系和边界。"],
        "upgrade_files": [
            "`40_evaluation/第11步作业设计模板_v5.0.md`",
            "`40_evaluation/runtime/chapter_profiles/`",
        ],
    },
    "M1": {
        "title": "机制解释不足",
        "symptoms": [
            "会操作，但说不清工具为什么得到这类结果。",
            "描述停留在现象层，不能回到根因或机制层。",
        ],
        "causes": ["机制模板训练不足。"],
        "actions": ["增加固定机制解释模板：结果是什么、为什么成立、边界在哪里。"],
        "upgrade_files": ["`20_skills/SK07_课后练习与章节项目生成器_v5.0.md`"],
    },
    "R1": {
        "title": "关系图/关系表缺失",
        "symptoms": ["收口项未提交，或者完全看不到关系图/关系表部分。"],
        "causes": ["学生没有意识到这是独立收口项。"],
        "actions": ["在截止前核对表中单列关系图/关系表。"],
        "upgrade_files": [
            "`40_evaluation/教师验收表模板_v5.0.md`",
            "`40_evaluation/学生版作业说明单模板_v5.0.md`",
        ],
    },
    "R2": {
        "title": "关系链不足",
        "symptoms": [
            "图/表已提交，但只列工具或概念，没有写“能说明什么 / 不能替代什么 / 下一步”。",
            "只写结果列表，没有过程或因果链。",
        ],
        "causes": [
            "教师讲评中缺少完整关系链示范。",
            "学生不清楚关系图与工具清单的区别。",
        ],
        "actions": ["增加一次关系链示范讲评，演示“现象 -> 机制 -> 控制点 -> 下一步”。"],
        "upgrade_files": [
            "`40_evaluation/学生版作业说明单模板_v5.0.md`",
            "`40_evaluation/教师验收表模板_v5.0.md`",
        ],
    },
    "B1": {
        "title": "授权边界表达不足",
        "symptoms": ["没有明确允许范围、禁止行为、脱敏或授权前提。"],
        "causes": ["授权边界提示没有前置。"],
        "actions": ["把授权边界和脱敏要求放到说明单第一页。"],
        "upgrade_files": ["`40_evaluation/学生版作业说明单模板_v5.0.md`"],
    },
    "P1": {
        "title": "防护建议泛化",
        "symptoms": [
            "建议停留在“加强管理、提高意识”层面。",
            "没有区分根因控制、暴露面控制和后果范围控制。",
        ],
        "causes": ["学生缺少防护分层框架。"],
        "actions": ["用表格示范“风险点 -> 根因 -> 控制点 -> 防护建议”。"],
        "upgrade_files": ["`40_evaluation/学生版作业说明单模板_v5.0.md`"],
    },
    "C1": {
        "title": "高度雷同待复核",
        "symptoms": ["与同班样本在多个任务上高度重复。"],
        "causes": ["存在共享答案、直接复制或模板依赖过重的风险。"],
        "actions": ["先做教师人工复核，再决定是否进入纪律处理流程。"],
        "upgrade_files": [
            "`40_evaluation/runtime/course_assignment_eval_v5.py`",
            "`40_evaluation/教师验收表模板_v5.0.md`",
        ],
    },
}


@dataclass
class FeedbackItem:
    class_name: str
    chapter_name: str
    batch_date: str
    summary_path: Path
    markdown_path: Path
    pdf_path: Path
    summary: dict[str, Any]
    avg_dimensions: dict[str, str]
    high_frequency_tags: list[dict[str, Any]]
    risk_counts: dict[str, int]
    positive_samples: list[dict[str, str]]
    suggested_actions: list[str]
    suggested_system_files: list[str]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def infer_report_paths(summary_path: Path) -> tuple[Path, Path]:
    base_name = summary_path.name.replace("_教学反馈摘要_v5.json", "")
    return (
        summary_path.with_name(f"{base_name}_教学反馈报告_v5.md"),
        summary_path.with_name(f"{base_name}_教学反馈报告_v5.pdf"),
    )


def load_feedback(path: Path) -> FeedbackItem:
    raw = load_json(path)
    markdown_path, pdf_path = infer_report_paths(path)
    return FeedbackItem(
        class_name=raw["class_name"],
        chapter_name=raw["chapter_name"],
        batch_date=raw["batch_date"],
        summary_path=path,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        summary=raw["summary"],
        avg_dimensions=raw["avg_dimensions"],
        high_frequency_tags=raw["high_frequency_tags"],
        risk_counts=raw["risk_counts"],
        positive_samples=raw["positive_samples"],
        suggested_actions=raw["suggested_actions"],
        suggested_system_files=raw["suggested_system_files"],
    )


def to_link(label: str, path: Path) -> str:
    target = str(path)
    if any(char in target for char in [" ", "（", "）"]):
        return f"[{label}](<{target}>)"
    return f"[{label}]({target})"


def chapter_sort_key(chapter_name: str) -> tuple[int, str]:
    match = re.search(r"第(\d+)章", chapter_name)
    if match:
        return (int(match.group(1)), chapter_name)
    return (999, chapter_name)


def class_sort_key(class_name: str) -> tuple[int, str]:
    match = re.search(r"(\d+)", class_name)
    if match:
        return (int(match.group(1)), class_name)
    return (999, class_name)


def build_feedback_index(items: list[FeedbackItem]) -> str:
    by_chapter: dict[str, list[FeedbackItem]] = defaultdict(list)
    for item in items:
        by_chapter[item.chapter_name].append(item)

    lines = [
        "[meta]",
        "type: Memory",
        "status: Draft",
        "version: v5.0",
        "keywords: 班级反馈,教学反馈索引,自动更新",
        "owner: Shen",
        f"updated: {date.today().isoformat()}",
        "[/meta]",
        "",
        "# 班级教学反馈索引 v5.0",
        "",
        "## 1. 用途",
        "",
        "本文件用于快速回答：",
        "",
        "1. 哪些班已经有正式教学反馈",
        "2. 这些反馈对应哪些文件",
        "3. 各班的共性问题是什么",
        "4. 哪些结论值得升级到课程系统",
        "",
        "## 2. 已收录反馈",
        "",
    ]

    for chapter_name in sorted(by_chapter, key=chapter_sort_key):
        lines.append(f"### {chapter_name}")
        lines.append("")
        chapter_items = sorted(by_chapter[chapter_name], key=lambda item: class_sort_key(item.class_name))
        for item in chapter_items:
            lines.append(f"#### {item.class_name}")
            lines.append("")
            lines.append("- 报告：")
            lines.append(f"  - {to_link(item.markdown_path.name, item.markdown_path)}")
            lines.append(f"  - {to_link(item.pdf_path.name, item.pdf_path)}")
            lines.append(f"  - {to_link(item.summary_path.name, item.summary_path)}")
            lines.append("- 核心数据：")
            lines.append(f"  - 班级人数 `{item.summary['class_size']}`")
            lines.append(f"  - 已提交 `{item.summary['submitted_count']}`")
            lines.append(f"  - 未提交 `{item.summary['missing_count']}`")
            lines.append(f"  - 总平均分 `{item.summary['avg_score_all']:.2f}`")
            lines.append(f"  - 已提交平均分 `{item.summary['avg_score_submitted']:.2f}`")
            lines.append("- 高频标签：")
            for tag in item.high_frequency_tags[:5]:
                lines.append(f"  - `{tag['tag']}`")
            if item.risk_counts.get("similarity", 0):
                lines.append("- 高风险项：")
                lines.append(f"  - 高疑似雷同 `{item.risk_counts['similarity']}` 例")
            lines.append("- 当前结论：")
            if item.summary["missing_count"] > max(2, item.summary["class_size"] // 5):
                conclusion = "该班首先需要处理提交率和收口项质量问题。"
            elif any(tag["tag"] in {"R2", "E2"} for tag in item.high_frequency_tags[:3]):
                conclusion = "该班重点不是提交率，而是关系链表达和证据到结论映射。"
            else:
                conclusion = "该班整体完成度较稳，后续重点是提高解释质量和规范性。"
            lines.append(f"  - {conclusion}")
            lines.append("")

    lines.extend(["## 3. 跨班共性结论", ""])
    global_tag_counter = Counter()
    for item in items:
        for tag in item.high_frequency_tags:
            global_tag_counter[tag["tag"]] += int(tag["count"])
    common_tags = [tag for tag, _count in global_tag_counter.most_common(3)]
    if common_tags:
        for index, tag in enumerate(common_tags, start=1):
            lines.append(f"{index}. `{tag}` 在多个班中重复出现，应优先进入模板和讲评修订。")
    else:
        lines.append("1. 当前样本不足，尚未形成跨班共性结论。")

    upgrade_targets = []
    for item in items:
        upgrade_targets.extend(item.suggested_system_files)
    unique_upgrades = []
    for upgrade in upgrade_targets:
        if upgrade not in unique_upgrades:
            unique_upgrades.append(upgrade)
    lines.extend(["", "## 4. 当前建议回写位置", ""])
    if unique_upgrades:
        for index, upgrade in enumerate(unique_upgrades[:6], start=1):
            lines.append(f"{index}. {upgrade}")
    else:
        lines.append("1. 当前暂无明确回写位置。")

    return "\n".join(lines) + "\n"


def build_misconception_library(items: list[FeedbackItem]) -> str:
    observed: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for item in items:
        for tag in item.high_frequency_tags:
            observed[tag["tag"]].append((item.chapter_name, item.class_name, int(tag["count"])))

    lines = [
        "[meta]",
        "type: Memory",
        "status: Draft",
        "version: v5.0",
        "keywords: 误区库,高频问题,自动更新",
        "owner: Shen",
        f"updated: {date.today().isoformat()}",
        "[/meta]",
        "",
        "# 误区库 v5.0",
        "",
        "## 1. 记录原则",
        "",
        "误区库只记录“会反复出现、值得回写系统”的问题，不记录一次性个案。",
        "",
        "每条误区至少写清：",
        "1. 误区是什么",
        "2. 典型症状",
        "3. 最可能来源",
        "4. 下轮教学动作",
        "5. 需要升级的系统文件",
        "",
        "## 2. 自动沉淀结果",
        "",
    ]

    if not observed:
        lines.append("当前尚无可自动沉淀的误区标签。")
        return "\n".join(lines) + "\n"

    sorted_tags = sorted(observed, key=lambda key: sum(count for *_rest, count in observed[key]), reverse=True)
    for index, tag in enumerate(sorted_tags, start=1):
        library = TAG_LIBRARY.get(tag, {})
        title = library.get("title", tag)
        lines.append(f"### M-{index:03d} {title}")
        lines.append("")
        lines.append(f"- 对应标签：`{tag}`")
        lines.append("- 观察来源：")
        for chapter_name, class_name, count in observed[tag]:
            lines.append(f"  - `{chapter_name}` / `{class_name}`：{count} 人次")
        lines.append("- 典型症状：")
        for item in library.get("symptoms", ["待补充。"]):
            lines.append(f"  - {item}")
        lines.append("- 最可能来源：")
        for item in library.get("causes", ["待补充。"]):
            lines.append(f"  - {item}")
        lines.append("- 下轮教学动作：")
        for item in library.get("actions", ["待补充。"]):
            lines.append(f"  - {item}")
        lines.append("- 需升级文件：")
        for item in library.get("upgrade_files", ["待补充。"]):
            lines.append(f"  - {item}")
        lines.append("")

    lines.extend(
        [
            "## 3. 当前结论",
            "",
            "当前更值得优先修的，不是“增加更多工具”，而是：",
            "1. 关系链表达",
            "2. 证据到结论映射",
            "3. AI 输出审核与人工复核记录",
        ]
    )
    return "\n".join(lines) + "\n"


def build_case_library(items: list[FeedbackItem]) -> str:
    by_chapter: dict[str, list[FeedbackItem]] = defaultdict(list)
    for item in items:
        by_chapter[item.chapter_name].append(item)

    lines = [
        "[meta]",
        "type: Memory",
        "status: Draft",
        "version: v5.0",
        "keywords: 案例库,正例,反例,自动更新",
        "owner: Shen",
        f"updated: {date.today().isoformat()}",
        "[/meta]",
        "",
        "# 案例库 v5.0",
        "",
        "## 1. 用途",
        "",
        "案例库服务两件事：",
        "",
        "1. 课堂示范讲评",
        "2. 模板与规则升级时的证据参考",
        "",
        "## 2. 当前记录方式",
        "",
        "本阶段先不复制学生全文，而是记录“案例类型 + 来源班级 + 可借鉴点”，避免记忆层变成原始作业堆积区。",
        "",
        "## 3. 自动沉淀的正例样本",
        "",
    ]

    case_index = 1
    for chapter_name in sorted(by_chapter, key=chapter_sort_key):
        chapter_items = sorted(by_chapter[chapter_name], key=lambda item: class_sort_key(item.class_name))
        lines.append(f"### C-{case_index:03d} {chapter_name} 高质量完成样本")
        lines.append("")
        lines.append("- 来源：")
        found = False
        for item in chapter_items:
            if not item.positive_samples:
                continue
            found = True
            names = "、".join(sample["student_name"] for sample in item.positive_samples)
            lines.append(f"  - `{item.class_name}`：{names}")
        if not found:
            lines.append("  - 当前暂无稳定正例。")
        lines.append("- 共同特征：")
        lines.append("  - 主体任务完成较稳定")
        lines.append("  - 证据或关键字段定位相对清楚")
        lines.append("  - 机制解释相对完整")
        lines.append("- 适合用途：")
        lines.append("  - 作为结构型正例")
        lines.append("  - 作为教师讲评时的完成度参考")
        lines.append("")
        case_index += 1

    if any(item.risk_counts.get("similarity", 0) for item in items):
        lines.append(f"### C-{case_index:03d} 高度雷同待复核类样本")
        lines.append("")
        lines.append("- 来源：")
        for item in items:
            similarity = item.risk_counts.get("similarity", 0)
            if similarity:
                lines.append(f"  - `{item.chapter_name}` / `{item.class_name}`：{similarity} 例")
        lines.append("- 适合用途：")
        lines.append("  - 用于讲诚信边界")
        lines.append("  - 用于提醒“自动检测只做高风险提示，最终仍需教师确认”")
        lines.append("")
        case_index += 1

    if any(item.summary.get("missing_count", 0) for item in items):
        lines.append(f"### C-{case_index:03d} 补交管理类样本")
        lines.append("")
        lines.append("- 来源：")
        for item in items:
            missing = item.summary.get("missing_count", 0)
            if missing:
                lines.append(f"  - `{item.chapter_name}` / `{item.class_name}`：未提交 {missing} 人")
        lines.append("- 适合用途：")
        lines.append("  - 用于改进截止前核对表与最小提交清单")
        lines.append("")

    lines.extend(
        [
            "## 4. 当前边界",
            "",
            "若要把案例库进一步升级成真正的讲评库，后续还应补入：",
            "1. 对应章节",
            "2. 对应标签",
            "3. 对应推荐讲法",
            "4. 对应可回写的模板位置",
        ]
    )
    return "\n".join(lines) + "\n"


def build_snapshot(items: list[FeedbackItem]) -> dict[str, Any]:
    global_tag_counter = Counter()
    for item in items:
        for tag in item.high_frequency_tags:
            global_tag_counter[tag["tag"]] += int(tag["count"])
    return {
        "updated": date.today().isoformat(),
        "feedback_count": len(items),
        "chapters": sorted({item.chapter_name for item in items}, key=chapter_sort_key),
        "classes": [item.class_name for item in sorted(items, key=lambda item: class_sort_key(item.class_name))],
        "top_tags": global_tag_counter.most_common(8),
        "sources": [str(item.summary_path) for item in items],
    }


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据教学反馈摘要 JSON 自动回填 projects5.0 的 10_memory。")
    parser.add_argument("--inputs", nargs="+", type=Path, required=True, help="一个或多个 教学反馈摘要_v5.json")
    parser.add_argument("--memory-dir", type=Path, help="10_memory 根目录；默认使用脚本上级目录")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    memory_dir = args.memory_dir or Path(__file__).resolve().parent.parent
    items = [load_feedback(path) for path in args.inputs]
    items.sort(key=lambda item: (chapter_sort_key(item.chapter_name), class_sort_key(item.class_name)))

    feedback_index_path = memory_dir / "班级教学反馈索引_v5.0.md"
    misconception_path = memory_dir / "误区库_v5.0.md"
    case_library_path = memory_dir / "案例库_v5.0.md"
    snapshot_path = memory_dir / "memory_snapshot_v5.json"

    write_text(feedback_index_path, build_feedback_index(items))
    write_text(misconception_path, build_misconception_library(items))
    write_text(case_library_path, build_case_library(items))
    snapshot_path.write_text(
        json.dumps(build_snapshot(items), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "memory_dir": str(memory_dir),
                "updated_files": [
                    str(feedback_index_path),
                    str(misconception_path),
                    str(case_library_path),
                    str(snapshot_path),
                ],
                "input_count": len(items),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
