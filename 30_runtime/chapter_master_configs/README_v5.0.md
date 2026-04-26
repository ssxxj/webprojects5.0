# 章节主配置目录 v5.0

本目录是 `projects5.0` 的章节级单一来源（single source of truth）。

目标不是再维护多套平行输入，而是把同一章里会反复出现在以下资产中的公共字段收束到一份主配置里：

1. `40_evaluation/runtime/chapter_profiles/<chapter_id>.json`
2. `50_assets/assignment_packs/<chapter_id>/...`
3. `50_assets/课堂实施方案/<chapter_id>/lesson_script_input_v5.yaml`
4. `50_assets/课堂实施方案/<chapter_id>/...课堂实施方案_v5.0.md`

## 目录内容

1. `章节主配置模板_v5.0.yaml`
   统一模板，定义章节主线、评分约束、课堂实施变量。
2. `<chapter_id>.yaml`
   具体章节主配置文件。

## 推荐使用方式

1. 先编辑本目录中的章节主配置。
2. 再运行：

```bash
python3 30_runtime/build_chapter_assets_v5.py \
  --input 30_runtime/chapter_master_configs/<chapter_id>.yaml
```

3. 由编排脚本统一写出：
   - `chapter_profile.json`
   - `assignment pack`
   - `lesson_script_input_v5.yaml`
   - `课堂实施方案_v5.0.md`

若需一次性重建全课程章节资产，可直接运行：

```bash
python3 30_runtime/build_all_chapter_assets_v5.py
```

默认会补出全课程批量摘要：

- `30_runtime/chapter_master_configs/all_chapters_build_manifest_v5.json`

若要检查当前产物是否已经与主配置漂移，可运行：

```bash
python3 30_runtime/check_all_chapter_asset_drift_v5.py
```

默认会输出：

- `30_runtime/chapter_master_configs/all_chapters_drift_report_v5.json`

若要把“批量重建 + 漂移检查”作为一个统一维护命令执行，默认使用：

```bash
python3 30_runtime/maintain_projects5_v5.py
```

CI 推荐：

```bash
python3 30_runtime/maintain_projects5_v5.py --mode check
```

若只需要发布前高层摘要，可使用：

```bash
python3 30_runtime/preflight_projects5_v5.py
```

它不会展开完整漂移细节，只保留：

- 是否可发布
- 主配置校验统计
- drift 统计
- 讲义层轻量一致性统计
- 失败章节列表

## 原则

1. 优先改主配置，不优先直接改生成结果。
2. 若生成结果需要长期保留的结构调整，应回写到主配置模板或生成器，而不是只改产物。
3. 讲义层当前仍是独立迁移资产，未纳入本轮单一来源；但已纳入 preflight 的轻量一致性检查。本轮只统一：
   - `profile`
   - `assignment pack`
   - `lesson script input`
   - `课堂实施方案`
