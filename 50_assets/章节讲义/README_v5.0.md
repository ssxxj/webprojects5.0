[meta]
type: AssetsIndex
status: Draft
version: v5.0
keywords: 章节讲义,教师版,学生预习版,迁移样本
owner: Shen
updated: 2026-04-20
[/meta]

# 章节讲义资产索引 v5.0

## 1. 定位

本目录存放 `projects5.0` 的正式章节讲义资产。

与 `assignment_packs/` 不同，这里的文件不直接承担作业执行与评分功能，而是承担：

1. 教师授课主线展开
2. 学生预习与观察起点提供
3. assignment pack 背后的机制解释
4. 课堂 OMDM 与作业证据字段之间的桥接

## 2. 当前状态

当前目录采用 `逐章迁移` 原则，不整体复制 `projects4.0/50_assets/章节讲义/`。

正式纳入前，必须通过：

`4.0讲义来源 -> 5.0讲义重组 -> assignment pack 对齐 -> 评分与反馈闭环`

## 3. 当前已生成讲义资产

1. `chapter01_http_request_response/`
   - 第一章讲义已迁移样本
   - 已对齐第一章 profile 与 assignment pack
   - 当前待第一次真实班级反馈后再做回归修订
2. `chapter02_web_info_collection/`
   - 第二章讲义迁移回归样本
   - 已对齐第二章 profile、assignment pack、memory 与正式班级反馈
3. `chapter03_sql_injection/`
   - 第三章讲义已迁移样本
   - 已对齐第三章 profile 与 assignment pack
   - 当前待第一次真实班级反馈后再做回归修订
4. `chapter04_xss/`
   - 第四章讲义已迁移样本
   - 已对齐第四章 profile 与 assignment pack
   - 当前待第一次真实班级反馈后再做回归修订
5. `chapter05_file_upload/`
   - 第五章讲义已迁移样本
   - 已对齐第五章 profile 与 assignment pack
   - 当前待第一次真实班级反馈后再做回归修订
6. `chapter06_command_injection/`
   - 第六章讲义已迁移样本
   - 已对齐第六章 profile 与 assignment pack
   - 当前待第一次真实班级反馈后再做回归修订
7. `chapter07_auth_session_access_control/`
   - 第七章讲义已迁移样本
   - 已对齐第七章 profile 与 assignment pack
   - 当前待第一次真实班级反馈后再做回归修订
8. `chapter08_integrated_review_project/`
   - 第八章讲义已迁移样本
   - 已对齐第八章 profile 与 assignment pack
   - 当前待第一次真实班级反馈后再做回归修订

## 4. 每章默认文件

每个章节目录至少包含：

1. `教师版讲义_v5.0.md`
2. `学生预习版讲义_v5.0.md`
3. `讲义迁移清单_v5.0.json`
4. `4.0讲义 -> 5.0讲义 -> 5.0作业包 对照表.md`

## 5. 上游与下游关系

上游：

1. `40_evaluation/runtime/chapter_profiles/`
2. `50_assets/assignment_packs/`
3. `10_memory/`
4. `projects4.0/50_assets/章节讲义/`

下游：

1. `20_skills/SK06_授课实施设计器` 对应的课堂实施方案
2. `40_evaluation` 的作业与评分模板
3. `build_teaching_feedback_v5.py` 产出的班级反馈

## 6. 配套策略

本目录的新增与扩展，统一遵循：

1. [章节讲义迁移策略_v5.0.md](../章节讲义迁移策略_v5.0.md)
2. [assignment_packs/README_v5.0.md](../assignment_packs/README_v5.0.md)
3. [讲义层治理策略_v5.0.md](讲义层治理策略_v5.0.md)

## 7. 治理边界

当前讲义层采用 `方案 B`：

`独立维护，但纳入 preflight 轻量一致性检查，不并入章节主配置单一来源。`

因此，本目录当前会被检查：

1. 章节目录与 `chapter_id` 是否对应
2. 讲义文件名与章节标题是否对应
3. 迁移清单、对照表是否齐全
4. 迁移清单中的 `profile / assignment_pack / generated_assets` 是否可追溯

但不会被检查：

1. 教师版讲义正文是否逐字等于某个模板
2. 学生预习版讲义的叙事表达是否与其他章节完全同构
