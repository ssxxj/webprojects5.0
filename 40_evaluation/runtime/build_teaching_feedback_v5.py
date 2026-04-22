#!/usr/bin/env python3
"""
projects5.0 班级级教学反馈报告生成器

输入：
1. v5 评分批量输出的 debug JSON
2. 可选 chapter profile

输出：
1. 教学反馈 Markdown 报告
2. 教学反馈 PDF 报告
2. 结构化 JSON 摘要
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle


DEFAULT_TAG_DESCRIPTIONS = {
    "T1": "任务字段缺失",
    "T2": "任务部分完成",
    "E1": "证据不清晰",
    "E2": "证据与结论不对应",
    "M1": "机制解释不足",
    "R1": "关系图/关系表缺失",
    "R2": "关系链不足",
    "B1": "授权边界表达不足",
    "P1": "防护建议泛化",
    "C1": "高度雷同待复核",
}


@dataclass
class ProfileLite:
    chapter_name: str
    relation_item_name: str
    relation_item_score: float
    default_tags: list[str]
    task_names: list[str]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile(path: Path) -> ProfileLite:
    raw = load_json(path)
    task_names = [item["name"] for item in raw.get("tasks", [])]
    return ProfileLite(
        chapter_name=raw.get("chapter_name", ""),
        relation_item_name=raw.get("relation_item_name", "关系图/关系表"),
        relation_item_score=float(raw.get("relation_item_score", 3.0)),
        default_tags=raw.get("default_tags", list(DEFAULT_TAG_DESCRIPTIONS)),
        task_names=task_names,
    )


def infer_profile(debug_payload: dict[str, Any], explicit_profile: Path | None) -> ProfileLite:
    if explicit_profile and explicit_profile.exists():
        return load_profile(explicit_profile)
    summary = debug_payload.get("summary", {})
    profile_hint = summary.get("profile")
    if profile_hint:
        profile_path = Path(profile_hint)
        if profile_path.exists():
            return load_profile(profile_path)
    chapter_name = "未知章节"
    if debug_payload.get("results"):
        chapter_name = debug_payload["results"][0].get("debug", {}).get("chapter_name", chapter_name)
    return ProfileLite(
        chapter_name=chapter_name or "未知章节",
        relation_item_name="关系图/关系表",
        relation_item_score=3.0,
        default_tags=list(DEFAULT_TAG_DESCRIPTIONS),
        task_names=[],
    )


def average(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def compact_class_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"作业成绩.*$", "", name)
    name = re.sub(r"_debug.*$", "", name)
    name = re.sub(r"_v5.*$", "", name)
    name = re.sub(r"第二章.*$", "", name).strip() if "第二章" in name and "作业成绩" not in name else name
    return name.strip(" _-") or "未命名班级"


def infer_class_name(debug_path: Path, payload: dict[str, Any], override: str | None) -> str:
    if override:
        return override
    excel_updated = payload.get("excel_updated")
    if excel_updated:
        return compact_class_name(Path(excel_updated).stem)
    return compact_class_name(debug_path.stem)


def relation_points(status: str, max_score: float) -> float:
    if status == "complete":
        return max_score
    if status == "partial":
        return round(max_score * 0.5, 2)
    return 0.0


def derive_tags(debug: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    task_scores = debug.get("task_scores", {})
    task_max = debug.get("task_max_scores", {})
    low_task_count = 0
    zero_like_count = 0
    for key, value in task_scores.items():
        max_score = task_max.get(key, 0.0)
        if max_score <= 0:
            continue
        if value <= 0.15 * max_score:
            zero_like_count += 1
        elif value < 0.6 * max_score:
            low_task_count += 1
    if zero_like_count >= 1:
        tags.append("T1")
    elif low_task_count >= 1:
        tags.append("T2")

    if debug.get("evidence_quality", 0.0) < 10 or debug.get("screenshot_markers", 0) < 2:
        tags.append("E1")

    professional_errors = debug.get("professional_errors", [])
    absolute_hits = debug.get("absolute_hits", [])
    if absolute_hits or professional_errors:
        if any(
            keyword in json.dumps(professional_errors, ensure_ascii=False)
            for keyword in ["结论", "绝对化", "证据", "根因", "证明"]
        ):
            tags.append("E2")

    if debug.get("mechanism_score", 0.0) < 12:
        tags.append("M1")

    relation_status = debug.get("relation_status", "missing")
    if relation_status == "missing":
        tags.append("R1")
    elif relation_status == "partial":
        tags.append("R2")

    hard_gate_reasons = debug.get("hard_gate_reasons", [])
    content_issues = debug.get("content_issues", [])
    boundary_text = " ".join(hard_gate_reasons + content_issues + debug.get("unchecked_traces", []))
    if "授权边界" in boundary_text or "边界" in boundary_text:
        tags.append("B1")

    protection_text = json.dumps(professional_errors, ensure_ascii=False)
    if debug.get("protection_score", 0.0) < 5 or any(
        keyword in protection_text for keyword in ["防护", "控制", "最小权限", "输出编码", "参数化", "加固"]
    ):
        tags.append("P1")

    similarity = debug.get("similarity_review", {})
    if any("雷同" in item for item in hard_gate_reasons + content_issues) or similarity.get("is_suspected_similar") or similarity.get("is_highly_similar"):
        tags.append("C1")

    unique_tags: list[str] = []
    for tag in tags:
        if tag not in unique_tags:
            unique_tags.append(tag)
    return unique_tags


def pick_positive_samples(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    candidates: list[dict[str, Any]] = []
    for item in results:
        if not item.get("submitted", True):
            continue
        debug = item.get("debug", {})
        if debug.get("hard_gate_reasons"):
            continue
        score = item.get("score", 0)
        composite = (
            score,
            debug.get("professional_score", 0.0),
            debug.get("mechanism_score", 0.0),
            debug.get("evidence_quality", 0.0),
        )
        candidates.append(
            {
                "student_id": item.get("student_id", ""),
                "student_name": item.get("student_name", ""),
                "why": item.get("good_points", ""),
                "composite": composite,
            }
        )
    candidates.sort(key=lambda item: item["composite"], reverse=True)
    return [
        {
            "student_id": item["student_id"],
            "student_name": item["student_name"],
            "why": item["why"],
        }
        for item in candidates[:3]
    ]


def build_action_suggestions(tag_counter: Counter[str], missing_count: int, submitted_count: int) -> list[str]:
    actions: list[str] = []
    top_tags = [tag for tag, _count in tag_counter.most_common(5)]
    if missing_count > 0:
        actions.append("先处理未提交样本：在下一轮布置时压缩提交清单，明确最小提交集与截止前核对表。")
    if "R1" in top_tags or "R2" in top_tags:
        actions.append("下轮课增加一次“关系图/关系表示范讲评”，重点演示如何把现象、机制、控制点和下一步连成链。")
    if "E1" in top_tags or "E2" in top_tags:
        actions.append("补讲“证据 -> 结论”的对应规则，示范如何标关键字段、如何避免用抽象结论代替技术证据。")
    if "M1" in top_tags:
        actions.append("课堂收束时增加 5 分钟机制解释模板训练，要求学生用固定链条复述“为什么成立、根因在哪、控制哪一层”。")
    if "B1" in top_tags:
        actions.append("在学生版说明单首页强化授权边界、脱敏和禁止动作提示，并在课上明确展示正反例。")
    if "P1" in top_tags:
        actions.append("加强“防护建议分层”训练，把根因控制、暴露面控制和后果范围控制分开讲。")
    if "C1" in top_tags:
        actions.append("对高疑似雷同样本做人工复核，并在下次布置中要求保留中间过程或草图证据。")
    if not actions:
        actions.append("维持当前作业结构，重点保留章节主线、关系图和 AI 输出审核三项要求。")
    return actions[:3]


def build_upgrade_suggestions(tag_counter: Counter[str], missing_ai_ratio: float) -> list[str]:
    suggestions: list[str] = []
    top_tags = [tag for tag, _count in tag_counter.most_common(5)]
    if "R1" in top_tags or "R2" in top_tags:
        suggestions.append("`40_evaluation/学生版作业说明单模板_v5.0.md`：强化关系图/关系表正例与反例。")
        suggestions.append("`40_evaluation/教师验收表模板_v5.0.md`：把关系图三档评分说明前置。")
    if "E1" in top_tags or "E2" in top_tags:
        suggestions.append("`40_evaluation/第11步作业设计模板_v5.0.md`：增加“关键字段示例”和“证据到结论映射”字段。")
    if "M1" in top_tags:
        suggestions.append("`20_skills/SK07_课后练习与章节项目生成器_v5.0.md`：默认生成机制解释提示语。")
    if "B1" in top_tags:
        suggestions.append("`50_assets/assignment_packs/*/学生版作业说明单_v5.0.md`：把授权边界块放到第一页并高亮。")
    if missing_ai_ratio >= 0.3:
        suggestions.append("`40_evaluation/学生版作业说明单模板_v5.0.md` 与 `教师验收表模板_v5.0.md`：强化 AI输出审核与人工复核记录的检查提示。")
    if "C1" in top_tags:
        suggestions.append("`40_evaluation/runtime/course_assignment_eval_v5.py`：继续优化雷同检测阈值与人工复核提示字段。")
    if not suggestions:
        suggestions.append("当前系统文件无需大改，优先保持现有 assignment pack 与评分链稳定。")
    # 去重
    unique: list[str] = []
    for item in suggestions:
        if item not in unique:
            unique.append(item)
    return unique[:4]


def build_markdown_report(
    *,
    class_name: str,
    profile: ProfileLite,
    summary: dict[str, Any],
    submitted_results: list[dict[str, Any]],
    avg_dimensions: dict[str, str],
    tag_counter: Counter[str],
    risk_counts: dict[str, int],
    positives: list[dict[str, str]],
    actions: list[str],
    upgrades: list[str],
) -> str:
    top_tags = tag_counter.most_common(5)
    lines = [
        "[meta]",
        "type: TeachingFeedback",
        "status: Draft",
        "version: v5.0",
        "keywords: 班级反馈,教学反馈,projects5.0",
        "owner: Shen",
        f"updated: {date.today().isoformat()}",
        "[/meta]",
        "",
        f"# {class_name} {profile.chapter_name} 教学反馈报告 v5.0",
        "",
        "## 一、总体情况",
        "",
        f"1. 班级人数：{summary['class_size']}",
        f"2. 已提交人数：{summary['submitted_count']}",
        f"3. 未提交人数：{summary['missing_count']}",
        f"4. 平均分：总平均 {summary['avg_score_all']:.2f}；已提交平均 {summary['avg_score_submitted']:.2f}",
        "",
        "## 二、各维度平均分",
        "",
        "> 注：以下维度均按“已提交样本”统计。",
        "",
        f"1. 任务完成度：{avg_dimensions['task_completion']}",
        f"2. 证据质量：{avg_dimensions['evidence_quality']}",
        f"3. 机制解释：{avg_dimensions['mechanism_score']}",
        f"4. 关系链与下一步：{avg_dimensions['relation_score']}",
        f"5. 风险与防护：{avg_dimensions['risk_protection']}",
        f"6. 表达与结构：{avg_dimensions['expression_score']}",
        f"7. 专业校验与责任意识：{avg_dimensions['professional_score']}",
        "",
        "## 三、高频错误标签",
        "",
    ]
    if top_tags:
        for index, (tag, count) in enumerate(top_tags, start=1):
            desc = DEFAULT_TAG_DESCRIPTIONS.get(tag, "未定义标签")
            lines.append(f"{index}. `{tag}`：{desc}，共 {count} 人次")
    else:
        lines.append("1. 暂无高频错误标签。")
    lines.extend(
        [
            "",
            "## 四、高风险问题",
            "",
            f"1. 未脱敏：{risk_counts['desensitize']} 例",
            f"2. 超出授权边界：{risk_counts['boundary']} 例",
            f"3. 高度雷同待复核：{risk_counts['similarity']} 例",
            f"4. 其他：{risk_counts['other']} 例",
            "",
            "## 五、可作为正例的样本",
            "",
        ]
    )
    if positives:
        for index, item in enumerate(positives, start=1):
            lines.append(f"{index}. `{item['student_id']} {item['student_name']}`：{item['why']}")
    else:
        lines.append("1. 当前无稳定正例样本。")
    lines.extend(["", "## 六、建议下轮教学动作", ""])
    for index, item in enumerate(actions, start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 七、建议升级的系统文件", ""])
    for index, item in enumerate(upgrades, start=1):
        lines.append(f"{index}. {item}")
    lines.extend(
        [
            "",
            "## 八、附记",
            "",
            f"- 本报告基于 `{profile.chapter_name}` 的 v5 debug 批量输出自动生成。",
            f"- 当前关系图/关系表名称：`{profile.relation_item_name}`。",
            f"- 当前提交样本数：{len(submitted_results)}。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_pdf_report(
    *,
    output_path: Path,
    class_name: str,
    profile: ProfileLite,
    summary: dict[str, Any],
    avg_dimensions: dict[str, str],
    tag_counter: Counter[str],
    risk_counts: dict[str, int],
    positives: list[dict[str, str]],
    actions: list[str],
    upgrades: list[str],
) -> None:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CN",
            fontName="STSong-Light",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1f2937"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="CNTitle",
            fontName="STSong-Light",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#111827"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="CNSubTitle",
            fontName="STSong-Light",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="CNMeta",
            fontName="STSong-Light",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4b5563"),
        )
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    story: list[Any] = [
        Paragraph(f"{class_name} {profile.chapter_name} 教学反馈报告 v5.0", styles["CNTitle"]),
        Spacer(1, 3 * mm),
        Paragraph(
            "本报告基于班级批量评分 debug 输出自动汇总，重点服务教师复盘、后续讲解调整和 Step11 模板修订。",
            styles["CNMeta"],
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            f"生成日期：{date.today().isoformat()}；关系图/关系表名称：{profile.relation_item_name}",
            styles["CNMeta"],
        ),
        Spacer(1, 5 * mm),
    ]

    story.append(Paragraph("一、总体情况", styles["CNSubTitle"]))
    story.append(Spacer(1, 2 * mm))
    summary_rows = [
        [Paragraph("指标", styles["CN"]), Paragraph("结果", styles["CN"])],
        [Paragraph("班级人数", styles["CN"]), Paragraph(str(summary["class_size"]), styles["CN"])],
        [Paragraph("已提交人数", styles["CN"]), Paragraph(str(summary["submitted_count"]), styles["CN"])],
        [Paragraph("未提交人数", styles["CN"]), Paragraph(str(summary["missing_count"]), styles["CN"])],
        [Paragraph("总平均分", styles["CN"]), Paragraph(f"{summary['avg_score_all']:.2f}", styles["CN"])],
        [Paragraph("已提交平均分", styles["CN"]), Paragraph(f"{summary['avg_score_submitted']:.2f}", styles["CN"])],
    ]
    summary_table = LongTable(summary_rows, colWidths=[42 * mm, 120 * mm], repeatRows=1)
    summary_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("二、各维度平均分", styles["CNSubTitle"]))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("以下维度均按已提交样本统计。", styles["CNMeta"]))
    story.append(Spacer(1, 2 * mm))
    dimension_rows = [[Paragraph("维度", styles["CN"]), Paragraph("平均分", styles["CN"])]]
    dimension_labels = {
        "task_completion": "任务完成度",
        "evidence_quality": "证据质量",
        "mechanism_score": "机制解释",
        "relation_score": "关系链与下一步",
        "risk_protection": "风险与防护",
        "expression_score": "表达与结构",
        "professional_score": "专业校验与责任意识",
    }
    for key in [
        "task_completion",
        "evidence_quality",
        "mechanism_score",
        "relation_score",
        "risk_protection",
        "expression_score",
        "professional_score",
    ]:
        dimension_rows.append(
            [Paragraph(dimension_labels[key], styles["CN"]), Paragraph(avg_dimensions[key], styles["CN"])]
        )
    dimension_table = LongTable(dimension_rows, colWidths=[52 * mm, 110 * mm], repeatRows=1)
    dimension_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dcfce7")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(dimension_table)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("三、高频错误标签", styles["CNSubTitle"]))
    story.append(Spacer(1, 2 * mm))
    tag_rows = [[Paragraph("标签", styles["CN"]), Paragraph("说明", styles["CN"]), Paragraph("人次", styles["CN"])]]
    top_tags = tag_counter.most_common(5)
    if top_tags:
        for tag, count in top_tags:
            tag_rows.append(
                [
                    Paragraph(tag, styles["CN"]),
                    Paragraph(DEFAULT_TAG_DESCRIPTIONS.get(tag, "未定义标签"), styles["CN"]),
                    Paragraph(str(count), styles["CN"]),
                ]
            )
    else:
        tag_rows.append(
            [
                Paragraph("-", styles["CN"]),
                Paragraph("暂无高频错误标签。", styles["CN"]),
                Paragraph("0", styles["CN"]),
            ]
        )
    tag_table = LongTable(tag_rows, colWidths=[20 * mm, 112 * mm, 20 * mm], repeatRows=1)
    tag_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef3c7")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(tag_table)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("四、高风险问题", styles["CNSubTitle"]))
    story.append(Spacer(1, 2 * mm))
    risk_rows = [
        [Paragraph("问题类型", styles["CN"]), Paragraph("数量", styles["CN"])],
        [Paragraph("未脱敏", styles["CN"]), Paragraph(str(risk_counts["desensitize"]), styles["CN"])],
        [Paragraph("超出授权边界", styles["CN"]), Paragraph(str(risk_counts["boundary"]), styles["CN"])],
        [Paragraph("高度雷同待复核", styles["CN"]), Paragraph(str(risk_counts["similarity"]), styles["CN"])],
        [Paragraph("其他", styles["CN"]), Paragraph(str(risk_counts["other"]), styles["CN"])],
    ]
    risk_table = LongTable(risk_rows, colWidths=[58 * mm, 104 * mm], repeatRows=1)
    risk_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fee2e2")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(risk_table)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("五、可作为正例的样本", styles["CNSubTitle"]))
    story.append(Spacer(1, 2 * mm))
    if positives:
        for index, item in enumerate(positives, start=1):
            story.append(
                Paragraph(f"{index}. {item['student_id']} {item['student_name']}：{item['why']}", styles["CN"])
            )
            story.append(Spacer(1, 1.5 * mm))
    else:
        story.append(Paragraph("1. 当前无稳定正例样本。", styles["CN"]))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("六、建议下轮教学动作", styles["CNSubTitle"]))
    story.append(Spacer(1, 2 * mm))
    for index, item in enumerate(actions, start=1):
        story.append(Paragraph(f"{index}. {item}", styles["CN"]))
        story.append(Spacer(1, 1.5 * mm))
    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("七、建议升级的系统文件", styles["CNSubTitle"]))
    story.append(Spacer(1, 2 * mm))
    for index, item in enumerate(upgrades, start=1):
        story.append(Paragraph(f"{index}. {item}", styles["CN"]))
        story.append(Spacer(1, 1.5 * mm))

    doc.build(story)


def summarize(debug_payload: dict[str, Any], profile: ProfileLite, class_name: str) -> dict[str, Any]:
    results = debug_payload.get("results", [])
    submitted_results = [item for item in results if item.get("submitted", True)]
    missing_count = len([item for item in results if not item.get("submitted", True)])
    class_size = len(results)
    submitted_count = len(submitted_results)
    avg_score_all = average([float(item.get("score", 0)) for item in results])
    avg_score_submitted = average([float(item.get("score", 0)) for item in submitted_results])

    relation_scores = [
        relation_points(item.get("debug", {}).get("relation_status", "missing"), profile.relation_item_score)
        for item in submitted_results
    ]
    risk_scores = [float(item.get("debug", {}).get("risk_score", 0.0)) for item in submitted_results]
    protection_scores = [float(item.get("debug", {}).get("protection_score", 0.0)) for item in submitted_results]

    avg_dimensions = {
        "task_completion": f"{average([float(item.get('debug', {}).get('task_completion', 0.0)) for item in submitted_results]):.2f}/20",
        "evidence_quality": f"{average([float(item.get('debug', {}).get('evidence_quality', 0.0)) for item in submitted_results]):.2f}/18",
        "mechanism_score": f"{average([float(item.get('debug', {}).get('mechanism_score', 0.0)) for item in submitted_results]):.2f}/20",
        "relation_score": f"{average(relation_scores):.2f}/{profile.relation_item_score:.1f}",
        "risk_protection": f"{average([r + p for r, p in zip(risk_scores, protection_scores)]):.2f}/22（风险 {average(risk_scores):.2f}/12；防护 {average(protection_scores):.2f}/10）",
        "expression_score": f"{average([float(item.get('debug', {}).get('expression_score', 0.0)) for item in submitted_results]):.2f}/10",
        "professional_score": f"{average([float(item.get('debug', {}).get('professional_score', 0.0)) for item in submitted_results]):.2f}/10",
    }

    tag_counter: Counter[str] = Counter()
    risk_counts = {"desensitize": 0, "boundary": 0, "similarity": 0, "other": 0}
    ai_missing = 0
    for item in results:
        debug = item.get("debug", {})
        for tag in derive_tags(debug):
            tag_counter[tag] += 1
        if not debug.get("ai_review_present", False):
            ai_missing += 1
        reasons = debug.get("hard_gate_reasons", [])
        matched = False
        if any("脱敏" in reason for reason in reasons):
            risk_counts["desensitize"] += 1
            matched = True
        if any("授权边界" in reason or "边界" in reason for reason in reasons):
            risk_counts["boundary"] += 1
            matched = True
        if any("雷同" in reason for reason in reasons):
            risk_counts["similarity"] += 1
            matched = True
        if reasons and not matched:
            risk_counts["other"] += 1

    positives = pick_positive_samples(results)
    actions = build_action_suggestions(tag_counter, missing_count, submitted_count)
    upgrades = build_upgrade_suggestions(tag_counter, ai_missing / max(1, class_size))

    report_summary = {
        "class_name": class_name,
        "chapter_name": profile.chapter_name,
        "class_size": class_size,
        "submitted_count": submitted_count,
        "missing_count": missing_count,
        "avg_score_all": avg_score_all,
        "avg_score_submitted": avg_score_submitted,
    }
    markdown = build_markdown_report(
        class_name=class_name,
        profile=profile,
        summary=report_summary,
        submitted_results=submitted_results,
        avg_dimensions=avg_dimensions,
        tag_counter=tag_counter,
        risk_counts=risk_counts,
        positives=positives,
        actions=actions,
        upgrades=upgrades,
    )

    structured = {
        "class_name": class_name,
        "chapter_name": profile.chapter_name,
        "batch_date": date.today().isoformat(),
        "summary": report_summary,
        "avg_dimensions": avg_dimensions,
        "high_frequency_tags": [
            {"tag": tag, "description": DEFAULT_TAG_DESCRIPTIONS.get(tag, ""), "count": count}
            for tag, count in tag_counter.most_common(8)
        ],
        "risk_counts": risk_counts,
        "positive_samples": positives,
        "suggested_actions": actions,
        "suggested_system_files": upgrades,
    }
    return {"markdown": markdown, "json": structured}


def default_output(debug_path: Path, suffix: str) -> Path:
    stem = re.sub(r"_debug.*$", "", debug_path.stem)
    return debug_path.with_name(f"{stem}_{suffix}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据 v5 debug JSON 生成班级级教学反馈报告。")
    parser.add_argument("--debug", required=True, type=Path, help="评分批量输出的 debug JSON")
    parser.add_argument("--profile", type=Path, help="可选章节 profile 路径")
    parser.add_argument("--class-name", help="可选班级名覆盖")
    parser.add_argument("--out-md", type=Path, help="Markdown 报告输出路径")
    parser.add_argument("--out-pdf", type=Path, help="PDF 报告输出路径")
    parser.add_argument("--out-json", type=Path, help="JSON 摘要输出路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    debug_payload = load_json(args.debug)
    profile = infer_profile(debug_payload, args.profile)
    class_name = infer_class_name(args.debug, debug_payload, args.class_name)
    outputs = summarize(debug_payload, profile, class_name)

    out_md = args.out_md or default_output(args.debug, "教学反馈报告_v5.md")
    out_pdf = args.out_pdf or default_output(args.debug, "教学反馈报告_v5.pdf")
    out_json = args.out_json or default_output(args.debug, "教学反馈摘要_v5.json")
    out_md.write_text(outputs["markdown"], encoding="utf-8")
    build_pdf_report(
        output_path=out_pdf,
        class_name=class_name,
        profile=profile,
        summary=outputs["json"]["summary"],
        avg_dimensions=outputs["json"]["avg_dimensions"],
        tag_counter=Counter({item["tag"]: item["count"] for item in outputs["json"]["high_frequency_tags"]}),
        risk_counts=outputs["json"]["risk_counts"],
        positives=outputs["json"]["positive_samples"],
        actions=outputs["json"]["suggested_actions"],
        upgrades=outputs["json"]["suggested_system_files"],
    )
    out_json.write_text(json.dumps(outputs["json"], ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "class_name": class_name,
                "chapter_name": profile.chapter_name,
                "out_md": str(out_md),
                "out_pdf": str(out_pdf),
                "out_json": str(out_json),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
