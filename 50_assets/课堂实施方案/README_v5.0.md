[meta]
type: AssetsIndex
status: Draft
version: v5.0
keywords: 课堂实施方案,SK06,Step8,目录索引
owner: Shen
updated: 2026-04-20
[/meta]

# 课堂实施方案资产索引 v5.0

## 1. 定位

本目录用于存放 `projects5.0` 的 Step 8 正式课堂实施方案资产。

这里的文件不是章节讲义，也不是 assignment pack，而是连接二者的课堂执行层：

`章节讲义 -> 课堂动作 -> 形成性评估 -> 作业收口 -> Step 9 观察记录`

## 2. 当前结构

当前目录已接入：

1. `50_assets/课堂实施方案模板_v5.0.md`
   - SK06 的标准输出模板
   - 用于把章节讲义稳定转成 90 分钟可执行课堂方案
2. `逐章授课脚本生成器输入规范_v5.0.md`
   - 用于定义未来授课脚本生成器的稳定输入接口
3. `逐章授课脚本输入模板_v5.0.yaml`
   - 用于把章节变量压成生成器可直接读取的结构化输入
4. `chapter01_http_request_response/`
   - 第一章正式课堂实施样本
   - 已对齐第一章讲义、assignment pack、profile 与课程级 memory
5. `chapter02_web_info_collection/`
   - 第二章正式课堂实施样本
   - 已对齐第二章讲义、assignment pack、profile 与 memory
6. `chapter03_sql_injection/`
   - 第三章正式课堂实施样本
   - 已对齐第三章讲义、assignment pack、profile 与课程级 memory
7. `chapter04_xss/`
   - 第四章正式课堂实施样本
   - 已对齐第四章讲义、assignment pack、profile 与课程级 memory
   - 已补 `第四章 5.0首轮真实教学试点执行清单`
8. `chapter05_file_upload/`
   - 第五章正式课堂实施样本
   - 已对齐第五章讲义、assignment pack、profile 与课程级 memory
9. `chapter06_command_injection/`
   - 第六章正式课堂实施样本
   - 已对齐第六章讲义、assignment pack、profile 与课程级 memory
10. `chapter07_auth_session_access_control/`
   - 第七章正式课堂实施样本
   - 已对齐第七章讲义、assignment pack、profile 与课程级 memory
11. `chapter08_integrated_review_project/`
   - 第八章正式课堂实施样本
   - 已对齐第八章讲义、assignment pack、profile 与课程级 memory

后续若某章课堂实施方案正式沉淀，建议统一落为：

- `课堂实施方案/<chapter_dir>/<章节名>_课堂实施方案_v5.0.md`
- `课堂实施方案/<chapter_dir>/lesson_script_input_v5.yaml`

当前第一章到第八章目录中，已经全部补齐正式 `lesson_script_input_v5.yaml`。

## 3. 上游输入

Step 8 的课堂实施方案默认应同时对齐：

1. `50_assets/章节讲义/<chapter_dir>/`
2. `50_assets/assignment_packs/<chapter_dir>/`
3. `40_evaluation/runtime/chapter_profiles/<chapter_profile>.json`
4. `10_memory/`

## 4. 下游作用

本目录输出的课堂实施方案，主要服务：

1. `SK06_授课实施设计器_v5.0.md`
2. `12步运行手册_v5.0.md` 的 Step 8
3. `SK08` 的 Step 9 / Step 10 观察与复盘
4. `runtime/generate_lesson_script_v5.py` 的正式输出落点

## 4A. 自动化入口

当章节输入已经整理为 YAML/JSON 后，可直接运行：

```bash
python3 50_assets/课堂实施方案/runtime/generate_lesson_script_v5.py \
  --input 50_assets/课堂实施方案/逐章授课脚本输入模板_v5.0.yaml
```

默认会生成：

1. `课堂实施方案_v5.0.md`
2. `课堂实施方案_生成清单_v5.0.json`

若要一次性重建当前已落地的全部章节课堂实施方案，可运行：

```bash
python3 50_assets/课堂实施方案/runtime/generate_all_lesson_scripts_v5.py
```

默认会额外生成：

3. `批量生成清单_v5.0.json`

## 5. 推荐使用顺序

1. 先看 `章节讲义`
2. 再看 `assignment pack`
3. 若准备脚本化生成，先用 `逐章授课脚本输入模板_v5.0.yaml` 整理稳定输入
4. 再用 `SK06` 结合 `课堂实施方案模板_v5.0.md` 生成课堂实施方案
5. 课堂结束后将最小观察记录交给 `SK08`
