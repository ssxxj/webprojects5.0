[meta]
type: Index
status: Draft
version: v5.0
keywords: projects5.0,教学系统升级,项目化评估
owner: Shen
updated: 2026-04-20
[/meta]

# Web应用安全与防护 projects5.0

## 0. 前 10 分钟使用指南

### Concept

`projects5.0` 不是网页平台，而是一套本地可运行的项目化教学操作系统。当前唯一维护目录约定为：

```bash
/Users/shen/教学/web应用安全与防护projects5.0
```

另一个同名目录只作为历史副本或备份参考，日常不要混用。

### Mechanism

系统的主调用链是：

```text
课程母规则 -> 章节主配置 -> 正式产物 -> 教学实施 / 作业评分 -> 班级反馈 -> memory 回写
```

第一次使用时先安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

### Application

1. 想理解系统：先读 `30_runtime/文件调用关系_v5.0.md` 和 `30_runtime/12步运行手册_v5.0.md`。
2. 想修改某章：优先改 `30_runtime/chapter_master_configs/<chapter_id>.yaml`，不要先手改派生产物。
3. 想重建某章：

```bash
python3 30_runtime/build_chapter_assets_v5.py \
  --input 30_runtime/chapter_master_configs/chapter03_sql_injection.yaml
```

4. 想重建并检查全课程：

```bash
make maintain
make preflight
```

5. 想评分一个班级作业目录：

```bash
python3 40_evaluation/runtime/course_assignment_eval_v5.py \
  --profile 40_evaluation/runtime/chapter_profiles/chapter02_web_info_collection.json \
  --dir <班级PDF目录> \
  --excel <成绩表.xlsx> \
  --pdf-output <评估报告.pdf> \
  --debug-output <debug.json>
```

6. 想从评分 debug 生成班级反馈：

```bash
python3 40_evaluation/runtime/build_teaching_feedback_v5.py \
  --debug <debug.json> \
  --profile 40_evaluation/runtime/chapter_profiles/chapter02_web_info_collection.json \
  --class-name <班级名> \
  --out-md <教学反馈报告.md> \
  --out-pdf <教学反馈报告.pdf> \
  --out-json <教学反馈摘要.json>
```

7. 想把反馈沉淀回长期记忆：

```bash
python3 10_memory/runtime/memory_update_v5.py \
  --inputs <教学反馈摘要.json>
```

## 1. 定位

`projects5.0` 是在 `projects4.0` 基础上的规则升级版。

它不是简单改名，而是把课程从“能生成讲义、能布置作业、能批改作业”的系统，
升级为“目标可映射、作业可诊断、评分可反馈、规则可迁移”的项目化教学操作系统。

## 2. 当前升级重点

本轮 5.0 先升级四个层：

1. `00_kernel`
   课程级母规则、系统总控与步骤映射。
2. `20_skills`
   尤其是 Step 11 的作业生成机制。
3. `30_runtime`
   运行手册与 ChatGPT Project 指令词。
4. `40_evaluation`
   评估母规则、作业设计模板、通用评估脚手架。

## 3. 与 4.0 的关键差异

1. 评分从“硬门槛优先”升级为“安全红线 + 维度扣分”双轨制。
2. 作业从“可提交”升级为“可提交 + 可评分 + 可诊断 + 可复盘”。
3. Step 11 不再只生成任务书和评分表，还必须生成：
   - 目标对齐表
   - 任务分值拆分表
   - 红线与维度扣分表
   - AI 输出审核与人工复核记录
   - 诊断标签
   - 班级级教学反馈模板
4. 课程规则从章节专用 Rubric 升级为课程级母规则 + 章节变量配置。

## 4. 当前状态

当前已生成第一批骨架文件，优先打通：

1. 课程级评估母规则
2. 系统总控与 skill 映射
3. Step 11 生成器
4. 运行手册
5. 项目指令词
6. 评估总表
7. 作业设计模板
8. 学生版作业说明单模板
9. 教师验收表模板
10. 最小上传清单
11. 通用评估脚手架
12. 迁移说明

当前还已补入：

13. 第一章到第八章的章节 profile
14. `course_assignment_eval_v5.py` 的第一章到第八章真实评分入口
15. 单 PDF / 目录批量评分与雷同比对能力
16. 成绩表回写、评估 PDF 生成与 debug JSON 导出
17. `generate_assignment_pack_v5.py` 的 Step 11 整章作业包生成功能
18. `build_teaching_feedback_v5.py` 的班级级教学反馈报告生成功能（Markdown / PDF / JSON）
19. `SK08_课堂观察复盘与流程升级器_v5.0.md` 的真实 skill 落点
20. `10_memory` 已正式接入 `SK07 / SK08`，开始形成“生成前查历史、复盘后回写记忆”的闭环
21. `10_memory/runtime/memory_update_v5.py` 的记忆层自动回填能力
22. `SK06_授课实施设计器_v5.0.md` 与 `课堂实施方案模板_v5.0.md`，开始补齐 Step 8 的课堂执行桥
23. `50_assets/课堂实施方案/chapter02_web_info_collection/` 已作为 Step 8 首个正式课堂实施样本落地
24. `50_assets/课堂实施方案/chapter01_http_request_response/` 已作为第一章正式课堂实施样本落地
25. `50_assets/课堂实施方案/chapter03_sql_injection/` 已作为第三章正式课堂实施样本落地
26. `50_assets/课堂实施方案/chapter04_xss/` 已作为第四章正式课堂实施样本落地
27. `50_assets/课堂实施方案/chapter05_file_upload/` 已作为第五章正式课堂实施样本落地
28. `50_assets/课堂实施方案/chapter06_command_injection/` 已作为第六章正式课堂实施样本落地
29. `50_assets/课堂实施方案/chapter07_auth_session_access_control/` 已作为第七章正式课堂实施样本落地
30. `50_assets/课堂实施方案/chapter08_integrated_review_project/` 已作为第八章正式课堂实施样本落地
31. `50_assets/课堂实施方案/逐章授课脚本生成器输入规范_v5.0.md` 与 `逐章授课脚本输入模板_v5.0.yaml` 已作为 Step 8 后续自动化的稳定输入接口落地
32. `50_assets/课堂实施方案/runtime/generate_lesson_script_v5.py` 已作为 Step 8 正式授课脚本生成器落地
33. 第一章到第八章的 `lesson_script_input_v5.yaml` 已全部落地，并已通过授课脚本生成器校验
34. `30_runtime/chapter_master_configs/` 已作为章节级单一来源目录落地
35. `30_runtime/build_chapter_assets_v5.py` 已可从章节主配置统一重建 `chapter profile + assignment pack + lesson_script_input + 课堂实施方案`
36. `30_runtime/build_all_chapter_assets_v5.py` 已可按章节主配置批量重建全课程资产，并输出全课程构建摘要
37. `30_runtime/check_all_chapter_asset_drift_v5.py` 已可检查现有产物是否已与章节主配置发生漂移
38. `30_runtime/maintain_projects5_v5.py` 已作为日常维护 / CI 统一入口落地
39. `30_runtime/preflight_projects5_v5.py` 已作为发布前轻量摘要入口落地
40. `Makefile`、`justfile` 与 `30_runtime/local_ci_v5.sh` 已作为本地运行入口落地；当前本地目录尚未包含 `.github/workflows/`
41. `50_assets/章节讲义/讲义层治理策略_v5.0.md` 已明确讲义层采用“独立维护 + preflight 轻量一致性检查”的 B 方案
42. `30_runtime/GitHub连接版ChatGPT_Projects启动包_v5.0.md` 已作为 GitHub 仓库连接场景下的 Projects 启动入口落地

章节讲义、章节作业包和更多章节变量配置，将按使用顺序逐章迁移。
当前章节讲义迁移已补入策略文件：

- `50_assets/章节讲义迁移策略_v5.0.md`
当前还已生成首个正式讲义迁移样本：

- `50_assets/章节讲义/chapter02_web_info_collection/`
当前还已迁入第一章讲义资产：

- `50_assets/章节讲义/chapter01_http_request_response/`
当前还已迁入第三章讲义资产：

- `50_assets/章节讲义/chapter03_sql_injection/`
当前还已迁入第四章讲义资产：

- `50_assets/章节讲义/chapter04_xss/`
当前还已迁入第五章讲义资产：

- `50_assets/章节讲义/chapter05_file_upload/`
当前还已迁入第六章讲义资产：

- `50_assets/章节讲义/chapter06_command_injection/`
当前还已迁入第七章讲义资产：

- `50_assets/章节讲义/chapter07_auth_session_access_control/`
当前还已迁入第八章讲义资产：

- `50_assets/章节讲义/chapter08_integrated_review_project/`

## 5. 目录说明

- `00_kernel`
  系统母规则与总控
- `10_memory`
  课程蓝图、章节变量、误区与案例沉淀
- `20_skills`
  12 步流程的主技能
- `30_runtime`
 运行手册、项目指令词、最小上传清单、章节主配置与编排脚本
- `40_evaluation`
  评估母规则、模板、脚本、诊断输出
- `50_assets`
  模板类与章节类资产
- `90_growth`
  教师成长、迁移记录、版本升级复盘
