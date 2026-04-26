[meta]
type: AssetsIndex
status: Draft
version: v5.0
keywords: presentation_packs,展示层,课堂前台
owner: Shen
updated: 2026-04-26
[/meta]

# presentation_packs 展示层试点说明 v5.0

## 1. Concept

`presentation_packs` 是 `projects5.0` 的展示层试点目录。

它不是新的 single source，也不替代讲义、课堂实施方案或 assignment pack。它只负责把后台已经稳定的章节主线、课堂动作、作业要求和反馈语言，压成学生能看见、能行动、能带走的课堂前台材料。

## 2. Mechanism

展示层试点默认读取以下上游：

1. `30_runtime/chapter_master_configs/<chapter_id>.yaml`
2. `50_assets/课堂实施方案/<chapter_id>/...课堂实施方案_v5.0.md`
3. `50_assets/assignment_packs/<chapter_id>/...学生版作业说明单_v5.0.md`
4. `50_assets/章节讲义/<chapter_id>/...教师版讲义_v5.0.md`

展示层不改变：

1. 评分规则
2. 红线判断
3. 章节主配置
4. 讲义正文治理策略

## 3. Application

当前先落地一个试点：

1. `chapter03_sql_injection/第三章 SQL注入漏洞与防护_展示层试点包_v5.0.md`

若试点有效，再考虑为其他章节补充同类材料。
