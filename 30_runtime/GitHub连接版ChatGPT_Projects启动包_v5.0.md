[meta]
type: Runtime
status: Draft
version: v5.0
keywords: GitHub,ChatGPT Projects,启动包,连接模式
owner: Shen
updated: 2026-04-22
[/meta]

# GitHub连接版 ChatGPT Projects 启动包 v5.0

## 1. Concept

本文件用于定义 `projects5.0` 在 `GitHub 仓库 + ChatGPT Projects` 场景下的最小稳定用法。

核心原则不是“把所有文件重新上传给 ChatGPT”，而是：

`GitHub 仓库负责承载完整工程，ChatGPT Project 负责读取入口、理解层级、围绕当前任务组织推理。`

因此，GitHub 连接模式下，ChatGPT Project 的角色应是：

1. 读取仓库正式内容
2. 遵守 `projects5.0` 的层级关系
3. 在章节设计、课堂实施、评分复核、教学反馈时，优先使用仓库中的真实文件

它不应被当作：

1. 本地脚本执行器
2. 仓库结构自动理解器
3. 可以替代教师做纪律裁决的系统

## 2. Mechanism

## 2.1 GitHub 连接模式下的层级关系

ChatGPT Project 必须按以下顺序理解仓库：

### 第一层：课程母规则层

用于定义课程目标、评分原则、责任边界。

1. `README.md`
2. `00_kernel/系统总控与ai-skill-os映射_v5.0.md`
3. `00_kernel/课程项目化作业评估母规则_v5.0.md`
4. `30_runtime/12步运行手册_v5.0.md`

### 第二层：章节主配置层

这是章节级 single source。

1. `30_runtime/chapter_master_configs/*.yaml`

### 第三层：正式产物层

由章节主配置派生：

1. `40_evaluation/runtime/chapter_profiles/*.json`
2. `50_assets/assignment_packs/<chapter_dir>/`
3. `50_assets/课堂实施方案/<chapter_dir>/lesson_script_input_v5.yaml`
4. `50_assets/课堂实施方案/<chapter_dir>/*课堂实施方案_v5.0.md`

### 第四层：讲义层

讲义层当前采用 `B 方案`：

`独立维护，但纳入 preflight 轻量一致性检查，不并入 single source。`

对应目录：

1. `50_assets/章节讲义/<chapter_dir>/`
2. `50_assets/章节讲义/讲义层治理策略_v5.0.md`

### 第五层：反馈与记忆层

用于把真实教学反馈回流到系统。

1. `10_memory/*`
2. `40_evaluation/runtime/build_teaching_feedback_v5.py`
3. `10_memory/runtime/memory_update_v5.py`

## 2.2 GitHub 连接模式下必须保留的入口文件

即使已经连接 GitHub，也建议在 ChatGPT Project 中保留少量“稳定入口文件”，避免模型把仓库理解成平行文档堆。

推荐保留这 6 个入口文件：

1. `README.md`
2. `30_runtime/12步运行手册_v5.0.md`
3. `30_runtime/ChatGPT_Projects项目指令词_v5.0.md`
4. `30_runtime/最小上传清单_v5.0.md`
5. `30_runtime/chapter_master_configs/README_v5.0.md`
6. `50_assets/章节讲义/讲义层治理策略_v5.0.md`

## 2.3 GitHub 连接模式下不应怎么做

1. 不要再手动上传整套 8 章所有产物，避免和仓库版本混淆。
2. 不要把 `assignment pack` 当成 single source。
3. 不要把 `README` 当成正式上游。
4. 不要假设 ChatGPT 已经执行了本地 `make` / `python` / `CI` 命令。
5. 不要让 ChatGPT 直接替代教师做红线、雷同、纪律性裁决。

## 3. Application

## 3.1 GitHub 连接模式下的最小上传清单

若仓库已经连接 GitHub，Project 内只保留以下入口文件即可：

1. `README.md`
2. `30_runtime/ChatGPT_Projects项目指令词_v5.0.md`
3. `30_runtime/12步运行手册_v5.0.md`
4. `30_runtime/最小上传清单_v5.0.md`
5. `30_runtime/chapter_master_configs/README_v5.0.md`
6. `50_assets/章节讲义/讲义层治理策略_v5.0.md`

若当前聚焦单一章节，再额外指定该章节的：

1. `chapter_master_configs/<chapter_id>.yaml`
2. `chapter_profiles/<chapter_id>.json`
3. `assignment_packs/<chapter_dir>/教师端作业包`
4. `章节讲义/<chapter_dir>/教师版讲义`
5. `课堂实施方案/<chapter_dir>/课堂实施方案`

## 3.2 建议放入 ChatGPT Project Settings 的 Instructions

以下内容可直接使用：

```text
你正在协助维护《Web应用安全与防护》projects5.0 教学操作系统。

你可以通过 GitHub 读取完整仓库内容，但必须把仓库理解成一个有上下游关系的系统，而不是一组并列文件。

先按以下顺序理解仓库：
1. 课程母规则层：
   - README.md
   - 00_kernel/*
   - 30_runtime/12步运行手册_v5.0.md
   - 30_runtime/ChatGPT_Projects项目指令词_v5.0.md
2. 章节 single source：
   - 30_runtime/chapter_master_configs/*.yaml
3. 正式产物层：
   - chapter profile
   - assignment pack
   - lesson_script_input_v5.yaml
   - 课堂实施方案
4. 讲义层：
   - 50_assets/章节讲义/*
   - 讲义层采用 B 方案：独立维护，但纳入 preflight 轻量一致性检查，不并入 single source
5. feedback / memory 层：
   - 10_memory/*
   - build_teaching_feedback_v5.py
   - memory_update_v5.py

回答时必须先判断：
- 当前步骤判断
- 当前主要依据文件
- 当前问题属于规则层、章节层、产物层还是反馈层

你必须遵守：
1. 不把 README 当成 single source。
2. 不把 assignment pack 当成母规则。
3. 优先把 chapter_master_configs/*.yaml 视为章节正式上游。
4. 讲义层当前采用 B 方案，只做轻量一致性治理，不做正文级 drift。
5. 红线问题、雷同问题和纪律性问题必须保留教师最终裁决。
6. 如果需要执行本地工程动作，只能建议我运行已有脚本，不要假设你已经运行了命令。

最后必须输出：
- 当前系统理解摘要
- 下一步最小动作
```

## 3.3 建议作为项目第一条消息发送的启动提示词

### 通用启动版

```text
请把当前 GitHub 仓库中的 projects5.0 按系统视角组织起来，先输出：

1. 这个系统的层级结构
2. 当前最重要的 single source 文件
3. 正式产物和治理/说明文件的区别
4. 讲义层当前采用什么治理方案
5. 如果后续做章节设计、课堂实施、评分复核、教学反馈，各自应优先看哪一层文件

最后输出：
- 当前系统理解摘要
- 不确定点
- 下一步最小动作
```

### 第四章试点启动版

```text
请把第四章作为 projects5.0 的首轮真实教学试点来理解。

先输出：
1. 第四章的章节主线
2. 第四章当前的正式 single source 文件
3. 第四章当前的正式产物
4. 课前、课中、课后分别应以哪个文件为主
5. 如果我要先做课前准备，最少应读哪 3 个文件

然后给出：
- 第四章试点的风险点
- 第四章试点的成功标准
- 下一步最小动作
```

## 3.4 GitHub 连接模式下的调用关系说明

建议在项目里额外保留一段简短说明：

```text
文件调用关系：

1. 课程母规则层
定义课程目标、评分原则、责任边界。

2. 章节主配置层
30_runtime/chapter_master_configs/*.yaml
是章节正式 single source。

3. 资产生成层
由主配置派生：
- chapter profile
- assignment pack
- lesson_script_input_v5.yaml
- 课堂实施方案

4. 讲义层
独立维护，但进入 preflight 轻量治理，不做正文级 drift check。

5. feedback / memory 层
评分输出 -> 教学反馈 -> memory 回写 -> 反向修订模板与章节资产。
```

## 4. 推荐工作法

### 最稳的做法

1. GitHub 连接全仓库
2. Project 内只保留少量入口文件
3. 用长期 Instructions 固定系统理解方式
4. 每次对话只补“当前章节 / 当前任务”

### 不推荐的做法

1. GitHub 连接全仓库后，又继续手动上传整套章节产物
2. 在一个 Project 里同时混入大量旧版草稿
3. 不说明文件关系就直接让模型“自己理解仓库”

## 5. 结论

在 `projects5.0` 场景下，GitHub 连接模式是可用且推荐的。  
但它只有在“入口文件 + 指令词 + 文件关系说明”三者同时存在时，才能稳定工作。
