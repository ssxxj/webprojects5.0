#!/usr/bin/env python3
"""
projects5.0 Step11 作业包生成器

输入：章节 profile JSON
输出：
1. 教师端作业包
2. 学生版作业说明单
3. 教师验收表
4. 班级级教学反馈模板
5. 任务分值与红线摘要
6. 生成清单 manifest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "30_runtime"))

from project_paths_v5 import project_relative, relativize_mapping  # type: ignore  # noqa: E402


@dataclass
class TaskRule:
    name: str
    score: float
    required: bool
    semantic_requirements: list[str]


@dataclass
class RedlineRule:
    name: str
    description: str
    action: str


@dataclass
class ChapterProfile:
    course_name: str
    chapter_name: str
    chapter_mainline: str
    capability_goals: list[str]
    tasks: list[TaskRule]
    relation_item_name: str
    relation_item_score: float
    self_eval_score: float
    redlines: list[RedlineRule]
    professional_checks: list[str]
    default_tags: list[str]


AI_REVIEW_TEMPLATE = """1. 本作业是否使用 AI：未使用 / 局部使用 / 深度使用
2. 若使用 AI，AI 主要帮助了哪些环节：
3. 我保留了 AI 输出中的哪 2 处内容，为什么保留：
4. 我删改了 AI 输出中的哪 2 处内容，为什么删改：
   若未使用 AI，改填：本作业未使用 AI；我主动删掉或放弃的 2 处思路是什么，为什么放弃。
5. 本作业中我自行核实过的 3 个专业判断：
6. 我认为最容易误判的一处边界问题："""

SELF_EVAL_TEMPLATE = """1. 任务完成情况
2. 机制与关系链理解情况
3. 证据质量情况
4. 边界与风险判断情况
5. AI输出审核与人工复核记录情况
6. 本次最需要改进的一项"""

DEFAULT_ALLOW = "DVWA、本机浏览器、localhost、127.0.0.1，或教师明确授权的实验环境。"
DEFAULT_FORBID = "对未授权真实目标进行扫描、抓包、上传、注入、XSS、命令执行、认证绕过或其他测试。"
DEFAULT_DESENSITIZE = "截图中的 Cookie、SessionID、Token、账号、路径、主机信息等敏感字段必须脱敏。"
TOTAL_SCORE_MODEL = [
    ("任务完成度", 20.0, "由本章任务分值表直接组成，回答“有没有完成、完成到什么程度”。"),
    ("证据质量", 18.0, "判断证据是否真实、清楚、可定位，并且是否真正支撑结论。"),
    ("机制解释", 20.0, "判断是否讲清因果链、是否真正说到根因。"),
    ("关系链与下一步", 12.0, "判断关系图是否成立、边界判断是否稳、下一步是否合理。"),
    ("风险与防护", 10.0, "判断风险后果、防护分层与防护边界说明是否到位。"),
    ("表达与结构", 10.0, "判断结构是否清楚、表述是否准确、材料是否便于验收。"),
    ("专业校验与责任意识", 10.0, "判断授权边界、绝对化表述、层次区分和 AI 审核质量。"),
]
SECONDARY_SCORE_MODEL = [
    (
        "证据质量",
        18.0,
        [
            ("真实性与可追溯性", 6.0, "是否来自授权环境、是否真实、是否可追溯。"),
            ("关键字段可定位性", 6.0, "截图、记录、对比中是否能看清关键字段。"),
            ("证据与结论对应性", 6.0, "结论是否被证据真正支持，是否存在超范围推断。"),
        ],
    ),
    (
        "机制解释",
        20.0,
        [
            ("因果链完整性", 8.0, "是否讲清“输入/现象 -> 处理/机制 -> 结果”。"),
            ("根因定位准确性", 8.0, "是否把真正根因讲对，而不是停在表面现象。"),
            ("差异比较能力", 4.0, "是否能解释版本差异、条件变化或证据差异。"),
        ],
    ),
    (
        "关系链与下一步",
        12.0,
        [
            ("关系图/关系表结构质量", 4.0, "是否体现关系、流程、因果、控制点。"),
            ("当前结果边界判断", 4.0, "是否写清能说明什么、不能替代什么。"),
            ("下一步合理性", 4.0, "是否能从当前结果推出合理下一步。"),
        ],
    ),
    (
        "风险与防护",
        10.0,
        [
            ("风险后果判断", 4.0, "是否能说明风险、影响面和后果。"),
            ("防护措施分层", 4.0, "是否区分根因控制、暴露面控制、后果缩减。"),
            ("防护边界说明", 2.0, "是否知道单一措施不能替代什么。"),
        ],
    ),
    (
        "表达与结构",
        10.0,
        [
            ("结构清晰度", 4.0, "任务顺序、收口项、材料组织是否清楚。"),
            ("术语与表述准确性", 3.0, "是否存在混用、模糊或绝对化表述。"),
            ("可读性与验收友好度", 3.0, "教师能否快速定位、快速验收。"),
        ],
    ),
    (
        "专业校验与责任意识",
        10.0,
        [
            ("边界与授权表达", 3.0, "是否明确授权环境、脱敏要求和边界。"),
            ("绝对化表述控制", 2.0, "是否避免“已经证明漏洞”等越界结论。"),
            ("层次区分能力", 3.0, "是否区分线索、证据、主动探测、验证结果。"),
            ("AI输出审核与人工复核质量", 2.0, "是否能看出真实保留、删改、核实痕迹。"),
        ],
    ),
]


def normalize_filename(name: str) -> str:
    safe = re.sub(r"[\\\\/:*?\"<>|]", "_", name).strip()
    return safe or "assignment_pack"


def load_profile(path: Path) -> ChapterProfile:
    raw = json.loads(path.read_text(encoding="utf-8"))
    schema_version = raw.get("schema_version")
    if schema_version and schema_version != "v5.0":
        raise ValueError(f"不支持的 schema_version：{schema_version}；当前脚本只接受 v5.0。")
    return ChapterProfile(
        course_name=raw["course_name"],
        chapter_name=raw["chapter_name"],
        chapter_mainline=raw["chapter_mainline"],
        capability_goals=raw.get("capability_goals", []),
        tasks=[TaskRule(**task) for task in raw.get("tasks", [])],
        relation_item_name=raw.get("relation_item_name", "关系图/关系表"),
        relation_item_score=float(raw.get("relation_item_score", 0)),
        self_eval_score=float(raw.get("self_eval_score", 0)),
        redlines=[RedlineRule(**item) for item in raw.get("redlines", [])],
        professional_checks=raw.get("professional_checks", []),
        default_tags=raw.get("default_tags", []),
    )


def infer_duration(task_count: int) -> str:
    if task_count <= 4:
        return "3-4 小时"
    if task_count == 5:
        return "4-5 小时"
    return "5-6 小时"


def chapter_short_name(chapter_name: str) -> str:
    short = re.sub(r"^第[一二三四五六七八九十]+章\s*", "", chapter_name).strip()
    return short or chapter_name


def default_submission_name(profile: ChapterProfile) -> str:
    short = chapter_short_name(profile.chapter_name)
    short = re.sub(r"\s+", "", short)
    return f"<学号><姓名>{short}.pdf"


def infer_boundary(profile: ChapterProfile) -> str:
    danger_words = [
        "扫描",
        "抓包",
        "注入",
        "上传",
        "XSS",
        "命令执行",
        "认证",
        "会话",
    ]
    matched = [word for word in danger_words if word in profile.chapter_name or word in profile.chapter_mainline]
    danger_note = f"本章涉及 { '、'.join(matched) } 等实验动作，" if matched else "本章涉及实验观察与验证，"
    return (
        f"{danger_note}仅限 {DEFAULT_ALLOW}"
        "所有案例、截图和论证必须基于课堂授权素材；任何公网真实目标一律不得作为验证对象。"
    )


def keyword_units(text: str) -> list[str]:
    lowered = text.lower()
    english = re.findall(r"[a-z]{2,}", lowered)
    chinese = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    units = english + chinese
    filtered: list[str] = []
    for item in units:
        item = item.strip()
        if item and item not in filtered:
            filtered.append(item)
    return filtered


def map_task_to_goals(task: TaskRule, goals: list[str], task_index: int) -> list[str]:
    if not goals:
        return []
    anchor_goal = goals[min(task_index - 1, len(goals) - 1)]
    task_terms = keyword_units(task.name + " " + " ".join(task.semantic_requirements))
    scored: list[tuple[int, str]] = []
    for goal in goals:
        compact_goal = goal.lower()
        score = 0
        for term in task_terms:
            if len(term) >= 2 and term.lower() in compact_goal:
                score += 1
        scored.append((score, goal))
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [anchor_goal]
    for score, goal in scored:
        if score <= 0:
            continue
        if goal != anchor_goal:
            selected.append(goal)
            break
    return selected


def render_goal_alignment(profile: ChapterProfile) -> str:
    lines = ["| 项目 | 对应能力目标 |", "| --- | --- |"]
    for index, task in enumerate(profile.tasks, start=1):
        goals = "；".join(map_task_to_goals(task, profile.capability_goals, index))
        lines.append(f"| 任务{index}：{task.name} | {goals} |")
    lines.append(f"| 收口项：{profile.relation_item_name} | 组织关系链、表达下一步、形成整体结构化理解 |")
    lines.append("| 收口项：学生自评表 / AI输出审核与人工复核记录 | 反思、自我监控、审核 AI 输出、建立责任意识 |")
    return "\n".join(lines)


def render_score_breakdown(profile: ChapterProfile) -> str:
    lines = ["| 项目 | 分值 | 扣分规则 |", "| --- | ---: | --- |"]
    for index, task in enumerate(profile.tasks, start=1):
        lines.append(f"| 任务{index}：{task.name} | {task.score:.1f} | 缺失则扣该任务全部分值；部分完成在该任务分值内比例扣分。 |")
    lines.append(f"| {profile.relation_item_name} | {profile.relation_item_score:.1f} | 未提交记 0；仅做工具解释、未体现关系链记 1/2 档；关系完整记满分。 |")
    lines.append(f"| 学生自评表 | {profile.self_eval_score:.1f} | 缺失仅扣本项；不作为一刀切退回条件。 |")
    return "\n".join(lines)


def render_total_score_model() -> str:
    lines = ["| 维度 | 分值 | 核心判断 |", "| --- | ---: | --- |"]
    for name, score, desc in TOTAL_SCORE_MODEL:
        lines.append(f"| {name} | {score:.0f} | {desc} |")
    return "\n".join(lines)


def render_secondary_score_tables() -> str:
    blocks: list[str] = []
    for dimension, total, items in SECONDARY_SCORE_MODEL:
        lines = [f"### {dimension}（{total:.0f}）", "", "| 二级评分点 | 分值 | 主要看什么 |", "| --- | ---: | --- |"]
        for name, score, desc in items:
            lines.append(f"| {name} | {score:.0f} | {desc} |")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_secondary_score_list() -> str:
    blocks: list[str] = []
    for dimension, total, items in SECONDARY_SCORE_MODEL:
        lines = [f"{dimension}（{total:.0f}）"]
        for name, score, desc in items:
            lines.append(f"- {name}（{score:.0f}）：{desc}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_score_explanation() -> str:
    return "\n".join(
        [
            "1. 本章最终成绩按课程统一 100 分制七维评分计算。",
            "2. 下方任务分值表合计的 20 分，只对应“任务完成度”子分。",
            "3. 其余 80 分继续看：证据质量、机制解释、关系链与下一步、风险与防护、表达与结构、专业校验与责任意识。",
            "4. 红线中的“60 分以下”作用于 100 分制总评，不是作用于任务分值表。",
        ]
    )


def render_redlines(profile: ChapterProfile) -> str:
    lines = []
    for index, rule in enumerate(profile.redlines, start=1):
        lines.append(f"{index}. `{rule.name}`：{rule.description}，处理方式：`{rule.action}`。")
    return "\n".join(lines)


def render_dimension_deductions(profile: ChapterProfile) -> str:
    generic = [
        "缺少一个任务：扣该任务分值。",
        "任务已提交但关键字段不全：在该任务分值内比例扣分。",
        f"{profile.relation_item_name} 已提交但主要停留在工具解释、未体现关系链：按“部分完成”扣分。",
        "学生自评表、关键字段、局部格式问题：原则上只做小幅扣分，不直接封顶。",
        "AI输出审核与人工复核记录缺失：在专业校验与责任意识、表达结构中扣分，不直接按红线处理。",
    ]
    return "\n".join(f"{index}. {item}" for index, item in enumerate(generic, start=1))


def render_key_field_examples(profile: ChapterProfile) -> str:
    lines = []
    for index, task in enumerate(profile.tasks, start=1):
        examples = "；".join(task.semantic_requirements[: min(4, len(task.semantic_requirements))])
        lines.append(f"{index}. {task.name}：{examples}")
    return "\n".join(lines)


def render_evidence_mapping(profile: ChapterProfile) -> str:
    return "\n".join(
        [
            "```text",
            "任务：",
            "学生最常见证据：",
            "允许支持的结论：",
            "不允许直接下的结论：",
            "教师应检查的误判点：",
            "```",
        ]
    )


def render_relation_guidance(profile: ChapterProfile) -> str:
    return "\n".join(
        [
            f"1. 错误写法：只列工具、术语、概念，或只列结果，不写关系。",
            f"2. 合格写法：至少写出“上一层结果如何导向下一步”。",
            f"3. 较好写法：写出“现象/输入 -> 处理/机制 -> 结果 -> 控制点 -> 下一步”。",
            f"4. 与 {profile.relation_item_name} 相关的结论必须体现“能说明什么 / 不能替代什么 / 下一步为什么是这个”。",
        ]
    )


def render_memory_prompt() -> str:
    return "\n".join(
        [
            "1. `10_memory/诊断标签索引_v5.0.md`",
            "2. `10_memory/误区库_v5.0.md`",
            "3. `10_memory/案例库_v5.0.md`",
            "4. `10_memory/班级教学反馈索引_v5.0.md`",
        ]
    )


def render_task_blocks(profile: ChapterProfile) -> str:
    blocks: list[str] = []
    for index, task in enumerate(profile.tasks, start=1):
        min_fields = "；".join(task.semantic_requirements)
        goals = "；".join(map_task_to_goals(task, profile.capability_goals, index))
        blocks.append(
            "\n".join(
                [
                    f"### 任务{index}：{task.name}",
                    f"- 目标：{goals or task.name}",
                    f"- 最小字段：{min_fields}",
                    f"- 分值：{task.score:.1f} 分",
                ]
            )
        )
    blocks.append(
        "\n".join(
            [
                f"### {profile.relation_item_name}",
                "- 要求：必须体现关系、流程、因果、控制点与下一步，不能退化成孤立概念或工具清单。",
                f"- 分值：{profile.relation_item_score:.1f} 分",
                "- 三档说明：",
                "  1. 未提交：0 分",
                "  2. 已提交但关系不足：按部分完成扣分",
                "  3. 关系表达完整：满分",
                "",
                "### 学生自评表",
                f"- 分值：{profile.self_eval_score:.1f} 分",
            ]
        )
    )
    return "\n\n".join(blocks)


def build_teacher_pack(
    profile: ChapterProfile,
    profile_path: Path,
    environment: str,
    boundary: str,
    submission_format: str,
    duration: str,
    naming: str,
) -> str:
    return f"""# {profile.chapter_name} 教师端作业包 v5.0

## 一、基础信息

- 课程：{profile.course_name}
- 章节：{profile.chapter_name}
- 章节主线：{profile.chapter_mainline}
- profile 来源：`{profile_path.name}`
- 建议完成时长：{duration}
- 提交格式：{submission_format}
- 文件命名：`{naming}`
- 适用环境：{environment}

## 二、授权边界

{boundary}

## 三、能力目标

{chr(10).join(f"- {goal}" for goal in profile.capability_goals)}

## 四、目标对齐表

{render_goal_alignment(profile)}

## 五、课程总评如何计算

{render_total_score_model()}

说明：

{render_score_explanation()}

## 六、任务分值拆分表

{render_score_breakdown(profile)}

## 七、其他六个维度的二级评分点

{render_secondary_score_tables()}

## 八、红线规则

{render_redlines(profile)}

## 九、按维度扣分规则

{render_dimension_deductions(profile)}

## 十、专业校验重点

{chr(10).join(f"{i}. {item}" for i, item in enumerate(profile.professional_checks, start=1))}

## 十一、诊断标签

{chr(10).join(f"- {tag}" for tag in profile.default_tags)}

## 十二、生成前建议查看的历史记忆项

{render_memory_prompt()}

## 十三、证据 -> 结论映射模板

{render_evidence_mapping(profile)}

## 十四、关系图/关系表正反例提示

{render_relation_guidance(profile)}

## 十五、AI输出审核与人工复核记录

```text
{AI_REVIEW_TEMPLATE}
```

教师设计提醒：

1. 不要把本模块设计成“是否用了 AI”的调查表。
2. 要把它设计成“是否会审核 AI 输出”的能力检查点。
3. 若上一轮多次出现 `unchecked_traces`，应把本模块前置到学生说明单的提交要求中。

## 十六、学生自评表

```text
{SELF_EVAL_TEMPLATE}
```

## 十七、正式输出文件

1. 学生版作业说明单
2. 教师验收表
3. 班级级教学反馈模板
4. 任务分值与红线摘要
5. 生成清单 manifest
"""


def build_student_sheet(
    profile: ChapterProfile,
    environment: str,
    boundary: str,
    submission_format: str,
    duration: str,
    naming: str,
) -> str:
    short = chapter_short_name(profile.chapter_name)
    must_submit_screens = []
    must_submit_text = []
    for task in profile.tasks:
        must_submit_screens.append(f"{task.name} 对应截图或过程证据")
        must_submit_text.append(f"{task.name} 的文字说明：{'；'.join(task.semantic_requirements[:3])}")
    return f"""# {profile.chapter_name} 学生版作业说明单 v5.0

标题：{short} 作业
适用章节：{profile.chapter_name}
建议时长：{duration}
提交格式：{submission_format}
文件命名：`{naming}`

## 一、这次作业要完成什么

1. 本次作业对应的能力目标：
{chr(10).join(f'   - {goal}' for goal in profile.capability_goals)}
2. 完成后你应能做到什么：
   - 能按本章主线组织证据，而不是只罗列任务。
   - 能把截图、字段、现象和专业判断对应起来。
   - 能说明自己是否使用 AI，以及是否审核、删改、核实过 AI 输出。

## 二、授权边界与红线

1. 允许：{DEFAULT_ALLOW}
2. 禁止：{DEFAULT_FORBID}
3. 脱敏要求：{DEFAULT_DESENSITIZE}
4. 红线说明：
{chr(10).join(f'   - {rule.name}：{rule.description}' for rule in profile.redlines)}
5. 雷同/抄袭说明：
   - 与同学高度雷同、抄袭、代做，按课程诚信红线处理。

## 三、你需要提交什么

1. 必交截图：
{chr(10).join(f'   - {item}' for item in must_submit_screens)}
2. 必交文字说明：
{chr(10).join(f'   - {item}' for item in must_submit_text)}
3. 必交 {profile.relation_item_name}：
   - 不能只写工具或概念列表，必须体现关系、流程、因果和下一步。
   - 合格写法至少要说明“能说明什么 / 不能替代什么 / 下一步为什么是这个”。
4. 必交 AI输出审核与人工复核记录（必填）
5. 必交学生自评表

## 四、你要按四步完成

### Step 1 观察
- 你需要看到什么：与本章主线直接相关的现象、页面变化、参数、响应、路径、结构或流程。
- 你需要记录什么字段：按每个任务最小字段逐项记录，不要只贴图不说明。

### Step 2 判断
- 你需要做出什么专业判断：根据本章主线，判断风险发生在哪一层、为什么成立、哪些结论还不能直接下。
- 你为什么这样判断：必须回到截图、字段、现象和关系链，而不是直接下抽象结论。

### Step 3 证据
- 你要用什么支持判断：截图、参数、响应、状态码、页面变化、结构图、比较表、流程图等。
- 你必须标出哪些关键字段：
{chr(10).join(f'  - {line}' for line in render_key_field_examples(profile).splitlines())}

### Step 4 推理
- 如果条件改变，会发生什么：说明如果某个控制点加入或移除，结果为什么会变化。
- 下一步应该做什么，为什么：写出最合理的后续验证、比较或防护动作。

### 证据 -> 结论映射
- 我看到了什么证据：
- 这个证据最多能支持到什么结论：
- 哪些话我不能直接下结论：

## 五、你的分数怎么计算

{render_score_explanation()}

课程总评七维：

{render_total_score_model()}

其他六个维度的二级评分点（简版）：

{render_secondary_score_list()}

## 六、任务与分值

{render_task_blocks(profile)}

## 七、AI输出审核与人工复核记录（必填）

```text
{AI_REVIEW_TEMPLATE}
```

提醒：

1. 不能只写“已审核”“已检查”，必须写清保留、删改和核实内容。
2. 若未使用 AI，也要写清自己主动放弃了哪些思路，以及为什么放弃。

## 八、提交前核对表

- [ ] 我已完成所有任务
- [ ] 我已给出必要截图和文字说明
- [ ] 我已标注关键字段
- [ ] 我已完成 {profile.relation_item_name}
- [ ] 我已填写 `AI输出审核与人工复核记录（必填）`
- [ ] 我已明确自己是否使用 AI，以及是否审核、删改、核实过 AI 输出
- [ ] 我已完成脱敏
- [ ] 我没有超出授权边界
- [ ] 我没有照搬他人作业或与同学高度雷同

## 九、你会怎样被扣分

1. 缺少一个任务：扣该任务分值。
2. 任务已做但内容不全：在该任务分值内按比例扣分。
3. {profile.relation_item_name} 已交但主要停留在工具解释、没有体现关系：按部分完成扣分。
4. 自评表、关键字段、局部规范性问题：小幅扣分。

## 十、常见误区提醒

1. 关系图/关系表不是工具清单，必须体现关系链。
2. 截图不是越多越好，关键字段必须能看清。
3. 线索不等于证据，端口不等于漏洞，第三方索引不等于实时探测。
4. AI 可以用，但不审核就等于没有完成本项要求。

## 十一、哪些情况会进入红线处理

{render_redlines(profile)}

## 十二、学生自评表

```text
{SELF_EVAL_TEMPLATE}
```
"""


def build_teacher_acceptance(profile: ChapterProfile) -> str:
    task_blocks = []
    for index, task in enumerate(profile.tasks, start=1):
        task_blocks.append(
            f"""任务{index}：{task.name}
- 完成度：
- 扣分原因：
- 得分："""
        )
    return f"""# {profile.chapter_name} 教师验收表 v5.0

班级：
章节：{profile.chapter_name}
学生：
文件名：

## 说明

{render_score_explanation()}

## 一、红线复核
- [ ] 超出授权边界
- [ ] 未脱敏
- [ ] 证据明显不真实或不可追溯
- [ ] 高度雷同，已进入人工复核
- [ ] 抄袭/代做/其他课程禁止行为

教师说明：

## 二、任务验收

{chr(10).join(task_blocks)}

{profile.relation_item_name}：
- 档位：未提交 / 已提交但关系不足 / 关系表达完整
- 是否只列工具或概念：
- 是否写出“能说明什么 / 不能替代什么 / 下一步”：
- 扣分原因：
- 得分：

学生自评表：
- 完成情况：
- 扣分原因：
- 得分：

## 三、质量维度验收

证据质量（18）：
- 真实性与可追溯性（6）：
- 关键字段可定位性（6）：
- 证据与结论对应性（6）：
- 小计：

机制解释（20）：
- 因果链完整性（8）：
- 根因定位准确性（8）：
- 差异比较能力（4）：
- 小计：

关系链与下一步（12）：
- 关系图/关系表结构质量（4）：
- 当前结果边界判断（4）：
- 下一步合理性（4）：
- 小计：

风险与防护（10）：
- 风险后果判断（4）：
- 防护措施分层（4）：
- 防护边界说明（2）：
- 小计：

表达与结构（10）：
- 结构清晰度（4）：
- 术语与表述准确性（3）：
- 可读性与验收友好度（3）：
- 小计：

专业校验与责任意识（10）：
- 边界与授权表达（3）：
- 绝对化表述控制（2）：
- 层次区分能力（3）：
- AI输出审核与人工复核质量（2）：
- 小计：

## 四、AI输出审核与人工复核记录验收

- [ ] 已写清是否使用 AI
- [ ] 已写出保留内容及原因
- [ ] 已写出删改内容及原因
- [ ] 已写出自行核实的专业判断
- [ ] 已写出最易误判的边界问题

教师判断：
1. 是否看得出学生审核过 AI 输出：
2. 是否存在疑似未经审核痕迹：
3. 是否存在需要人工重点复核的专业错误：
4. 是否存在“写了AI记录但看不出真实审核痕迹”：

## 五、诊断标签

{chr(10).join(f'- {tag}：' for tag in profile.default_tags)}

## 六、教师结论

任务完成度子分（20）：
其他维度总分（80）：
总分（100）：
等级：
是否需要补交：
建议下次课补讲：
"""


def build_feedback_template(profile: ChapterProfile) -> str:
    return f"""# {profile.chapter_name} 班级级教学反馈模板 v5.0

班级：
章节：{profile.chapter_name}
章节主线：{profile.chapter_mainline}

## 一、班级总体情况

平均分：
提交率：
红线样本数：
需补交人数：

## 二、各维度平均情况

- 任务完成度：
- 证据质量：
- 机制解释：
- 关系链与下一步：
- 风险与防护：
- 表达与结构：
- 专业校验与责任意识：

## 三、最弱二级评分点

1.
2.
3.

## 四、高频错误标签

{chr(10).join(f'- {tag}：' for tag in profile.default_tags)}

## 五、本章最常见误区

1.
2.
3.

## 六、建议下次课补讲

1.
2.
3.

## 七、建议升级的模板或字段

1.
2.
3.

## 八、可作为正例的样本

1.
2.
3.
"""


def build_score_summary(profile: ChapterProfile) -> str:
    return f"""# {profile.chapter_name} 任务分值与红线摘要 v5.0

## 一、章节主线

{profile.chapter_mainline}

## 二、任务分值

{render_score_breakdown(profile)}

## 三、课程总评如何计算

{render_total_score_model()}

说明：

{render_score_explanation()}

## 四、其他六个维度的二级评分点

{render_secondary_score_tables()}

## 五、关系图/关系表三档说明

1. 未提交：记 0。
2. 已提交但主要停留在工具解释、概念堆叠、没有体现关系链：按部分完成扣分。
3. 已提交且明确体现关系、流程、因果、控制点与下一步：满分。

## 六、证据 -> 结论映射提醒

1. 线索不等于证据。
2. 第三方索引不等于你本人实时做出的主动探测。
3. 开放端口或服务不等于漏洞已经成立。
4. 局部请求与响应不等于更大结论自动成立。

## 七、关键字段示例

{render_key_field_examples(profile)}

## 八、关系图/关系表正反例提示

{render_relation_guidance(profile)}

## 九、红线规则

{render_redlines(profile)}

## 十、专业校验重点

{chr(10).join(f'{i}. {item}' for i, item in enumerate(profile.professional_checks, start=1))}
"""


def build_manifest(profile: ChapterProfile, generated_files: dict[str, str], args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schema_version": "v5.0",
        "course_name": profile.course_name,
        "chapter_name": profile.chapter_name,
        "chapter_mainline": profile.chapter_mainline,
        "generator": "generate_assignment_pack_v5.py",
        "generated_at": str(date.today()),
        "task_count": len(profile.tasks),
        "task_score_total": round(sum(task.score for task in profile.tasks), 2),
        "relation_item_name": profile.relation_item_name,
        "relation_item_score": profile.relation_item_score,
        "self_eval_score": profile.self_eval_score,
        "environment": args.environment,
        "authorization_boundary": args.boundary,
        "submission_format": args.submission_format,
        "suggested_duration": args.duration,
        "submission_naming": args.naming,
        "generated_files": relativize_mapping(generated_files, PROJECT_ROOT),
    }


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据章节 profile 生成 projects5.0 的 Step11 作业包。")
    parser.add_argument("--profile", required=True, type=Path, help="章节 profile JSON 路径")
    parser.add_argument("--outdir", type=Path, help="输出目录；默认生成到 profile 同级的 generated_assignment_packs/<profile_stem>")
    parser.add_argument("--environment", help="适用环境描述")
    parser.add_argument("--boundary", help="授权边界描述")
    parser.add_argument("--submission-format", default="PDF", help="提交格式描述")
    parser.add_argument("--duration", help="建议完成时长")
    parser.add_argument("--naming", help="文件命名规则")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile = load_profile(args.profile)
    profile_stem = args.profile.stem
    outdir = args.outdir or (args.profile.parent / "generated_assignment_packs" / profile_stem)
    outdir.mkdir(parents=True, exist_ok=True)

    environment = args.environment or "DVWA + 本机浏览器 + 教师授权实验环境"
    boundary = args.boundary or infer_boundary(profile)
    duration = args.duration or infer_duration(len(profile.tasks))
    naming = args.naming or default_submission_name(profile)

    base = normalize_filename(profile.chapter_name)
    files = {
        "teacher_pack": outdir / f"{base}_教师端作业包_v5.0.md",
        "student_sheet": outdir / f"{base}_学生版作业说明单_v5.0.md",
        "teacher_acceptance": outdir / f"{base}_教师验收表_v5.0.md",
        "feedback_template": outdir / f"{base}_班级级教学反馈模板_v5.0.md",
        "score_summary": outdir / f"{base}_任务分值与红线摘要_v5.0.md",
        "manifest": outdir / f"{base}_生成清单_v5.0.json",
    }

    write_text(
        files["teacher_pack"],
        build_teacher_pack(
            profile=profile,
            profile_path=args.profile,
            environment=environment,
            boundary=boundary,
            submission_format=args.submission_format,
            duration=duration,
            naming=naming,
        ),
    )
    write_text(
        files["student_sheet"],
        build_student_sheet(
            profile=profile,
            environment=environment,
            boundary=boundary,
            submission_format=args.submission_format,
            duration=duration,
            naming=naming,
        ),
    )
    write_text(files["teacher_acceptance"], build_teacher_acceptance(profile))
    write_text(files["feedback_template"], build_feedback_template(profile))
    write_text(files["score_summary"], build_score_summary(profile))

    manifest = build_manifest(
        profile,
        {key: str(path) for key, path in files.items() if key != "manifest"},
        argparse.Namespace(
            environment=environment,
            boundary=boundary,
            submission_format=args.submission_format,
            duration=duration,
            naming=naming,
        ),
    )
    files["manifest"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "chapter_name": profile.chapter_name,
                "output_dir": project_relative(outdir, PROJECT_ROOT),
                "generated_files": {key: project_relative(path, PROJECT_ROOT) for key, path in files.items()},
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
