[meta]
type: Assets
status: Draft
version: v5.0
keywords: assets,模板,章节资产
owner: Shen
updated: 2026-04-20
[/meta]

# 50_assets v5.0 说明

5.0 的资产迁移策略不是一次性重做全部章节讲义，而是：

1. 先升级通用模板资产
2. 再按实际使用顺序迁移章节资产

优先迁移对象：
1. 学生提交模板
2. 关系图/关系表模板
3. 章节项目模板
4. 班级反馈模板

章节讲义正文暂不整体复制，避免 5.0 早期变成 4.0 的镜像副本。

## 当前已落地资产

目前 `50_assets` 已正式接入：

1. `assignment_packs/`
   用于存放按 `projects5.0 Step11` 自动生成的章节作业包。
2. `章节讲义迁移策略_v5.0.md`
   用于定义 4.0 章节讲义何时、依据什么、按什么顺序迁到 5.0。
3. `章节讲义/`
   用于存放按 5.0 迁移策略逐章重建的教师版与学生版讲义。
4. `课堂实施方案模板_v5.0.md`
   用于作为 `SK06` 的标准输出模板。
5. `课堂实施方案/`
   用于存放按 Step 8 生成的正式课堂实施方案资产。
6. `课堂实施方案/逐章授课脚本生成器输入规范_v5.0.md`
   用于定义未来授课脚本生成器的稳定输入接口。
7. `课堂实施方案/逐章授课脚本输入模板_v5.0.yaml`
   用于把章节变量压成生成器可直接读取的结构化输入。
8. `课堂实施方案/runtime/generate_lesson_script_v5.py`
   用于把 YAML/JSON 稳定输入正式转成课堂实施方案 Markdown 与生成清单。
9. `课堂实施方案/chapter01-08/lesson_script_input_v5.yaml`
   作为第一轮正式章节输入样本，已全部落地并通过生成器校验。
10. `30_runtime/chapter_master_configs/*.yaml`
   作为章节级单一来源，用于统一重建 profile、assignment pack、lesson input 与课堂实施方案。
11. `presentation_packs/`
   用于存放展示层试点材料；当前只作为课堂前台薄层，不替代 single source、讲义或评分规则。

当前还已生成：

- `课堂实施方案/chapter01_http_request_response/`
- `课堂实施方案/chapter02_web_info_collection/`
- `课堂实施方案/chapter03_sql_injection/`
- `课堂实施方案/chapter04_xss/`
- `课堂实施方案/chapter05_file_upload/`
- `课堂实施方案/chapter06_command_injection/`
- `课堂实施方案/chapter07_auth_session_access_control/`
- `课堂实施方案/chapter08_integrated_review_project/`

当前已生成：

1. `chapter01_http_request_response/`
2. `chapter02_web_info_collection/`
3. `chapter03_sql_injection/`
4. `chapter04_xss/`
5. `chapter05_file_upload/`
6. `chapter06_command_injection/`
7. `chapter07_auth_session_access_control/`
8. `chapter08_integrated_review_project/`

当前还已迁入第一章讲义资产：

- `章节讲义/chapter01_http_request_response/`
当前还已迁入第三章讲义资产：

- `章节讲义/chapter03_sql_injection/`

每个章节作业包默认包含：

1. 教师端作业包
2. 学生版作业说明单
3. 教师验收表
4. 班级级教学反馈模板
5. 任务分值与红线摘要
6. 生成清单 manifest

## 对齐说明

当前 `assignment_packs/` 与 `课堂实施方案/` 已进入“可由主配置重建”的状态。

推荐顺序：

1. 先改 `30_runtime/chapter_master_configs/<chapter_id>.yaml`
2. 再运行 `30_runtime/build_chapter_assets_v5.py`
3. 不优先直接改生成产物

`assignment_packs` 不是 4.0 章节讲义正文的直接复制，而是：

`4.0 章节讲义的作业与评估执行面 -> 5.0 Step11 正式资产`

第 4 到第 8 章的对齐依据、迁移边界与升级项，见：

- `assignment_packs/第4到第8章_4.0讲义到5.0作业包对照表.md`
- `章节讲义迁移策略_v5.0.md`

第二章补充说明：

- `chapter02_web_info_collection/` 目前已作为模板回归检查样本生成，用于验证：
  - 学生版说明单是否已前置高频误区
  - 教师端作业包是否已包含证据 -> 结论映射
  - 关系图/关系表和 AI 审核要求是否已真正落到作业执行层
- `章节讲义/chapter02_web_info_collection/` 目前已作为讲义迁移回归样本生成，用于验证：
  - 4.0 OMDM 修订稿能否在 5.0 中与 profile、assignment pack、memory 同时对齐
  - 高频误区是否已前置到讲义层，而不是只停留在反馈层

## 当前边界

现阶段 `50_assets` 中：

1. `assignment_packs` 已可视为正式运行资产。
2. 章节讲义正文仍按“逐章迁移”原则处理，暂不整体复制 `projects4.0`；迁移顺序与门槛以 `章节讲义迁移策略_v5.0.md` 为准。
3. `章节讲义/chapter01_http_request_response/` 已完成第一轮迁移，当前待真实课堂回归。
4. `章节讲义/chapter02_web_info_collection/` 已作为首个正式迁移回归样本落地。
5. `章节讲义/chapter03_sql_injection/` 已完成第一轮迁移，当前待真实课堂回归。
6. `章节讲义/chapter04_xss/` 已完成第一轮迁移，当前待真实课堂回归。
7. `章节讲义/chapter05_file_upload/` 已完成第一轮迁移，当前待真实课堂回归。
8. `章节讲义/chapter06_command_injection/` 已完成第一轮迁移，当前待真实课堂回归。
9. `章节讲义/chapter07_auth_session_access_control/` 已完成第一轮迁移，当前待真实课堂回归。
10. `章节讲义/chapter08_integrated_review_project/` 已完成第一轮迁移，当前待真实课堂回归。
11. 后续若生成 `5.0` 综合章节讲义，应以现有 assignment pack、chapter profile 和课程母规则为上游来源，而不是直接镜像 4.0 正文。
12. `课堂实施方案/chapter02_web_info_collection/` 已作为 Step 8 首个正式课堂实施样本落地。
13. `课堂实施方案/chapter01_http_request_response/` 已作为第一章正式课堂实施样本落地。
14. `课堂实施方案/chapter03_sql_injection/` 已作为第三章正式课堂实施样本落地。
15. `课堂实施方案/chapter04_xss/` 已作为第四章正式课堂实施样本落地。
16. `课堂实施方案/chapter05_file_upload/` 已作为第五章正式课堂实施样本落地。
17. `课堂实施方案/chapter06_command_injection/` 已作为第六章正式课堂实施样本落地。
18. `课堂实施方案/chapter07_auth_session_access_control/` 已作为第七章正式课堂实施样本落地。
19. `课堂实施方案/chapter08_integrated_review_project/` 已作为第八章正式课堂实施样本落地。
