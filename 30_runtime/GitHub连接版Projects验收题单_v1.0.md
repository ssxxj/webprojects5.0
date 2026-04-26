[meta]
type: Runtime
status: Draft
version: v1.0
keywords: GitHub,Projects,验收题单,系统辨识,任务执行
owner: Shen
updated: 2026-04-23
[/meta]

# GitHub连接版 Projects 验收题单 v1.0

## 1. Concept

本题单用于验证：

`GitHub 连接后的 ChatGPT Project，是否真的理解了 projects5.0 的系统结构，并能基于该结构做出正确动作。`

它不评估模型“会不会说漂亮话”，而评估两件事：

1. `系统辨识能力`
   能否区分 single source、正式产物、治理说明、讲义层和反馈层。
2. `任务执行能力`
   能否把这种结构理解转化为正确的章节级和运行级判断。

## 2. Mechanism

本题单分两组：

### 第一组：结构辨识

验证模型是否已经理解：

1. 哪一层是课程母规则
2. 哪一层是章节主配置
3. 哪一层是正式产物
4. 讲义层当前采用什么治理方案
5. 评分与 memory 的闭环如何发生

### 第二组：动作判断

验证模型是否能据此做出正确动作：

1. 改哪里
2. 先看什么
3. 先运行什么
4. 哪个脚本负责哪一步

## 3. Application

## 3.1 验收题 1：章节映射验证

### 题目

```text
请以 chapter04_xss.yaml 为 single source，画出它与以下四类正式产物之间的映射关系：

1. chapter04_xss.json
2. 第四章 assignment pack
3. lesson_script_input_v5.yaml
4. 第四章课堂实施方案

要求：
1. 说明哪些字段来自主配置
2. 说明哪些文件是正式产物而不是母规则
3. 说明讲义层为什么不在这条 single source 派生链里

最后输出：
- 映射关系摘要
- 哪个文件先改
- 下一步最小动作
```

### 通过标准

1. 能明确指出 `chapter_master_configs/*.yaml` 是 single source
2. 能明确指出四类文件都是正式产物
3. 不把讲义层误判为主配置直接派生正文
4. 能指出讲义层当前采用 `B 方案`

---

## 3.2 验收题 2：运行入口验证

### 题目

```text
如果第四章讲义中的“章节主线”需要做方向性修改，请回答：

1. 最先应该改哪个文件
2. 随后应重建哪些正式产物
3. 最后用什么命令检查一致性
4. 讲义层在这个过程中应如何处理

要求：
不要只说文件名，要说明顺序和原因。

最后输出：
- 正确修改顺序
- 应调用的脚本/命令
- 下一步最小动作
```

### 通过标准

1. 能回答“先改 `chapter_master_configs/<chapter>.yaml`”
2. 能回答应重建：
   - chapter profile
   - assignment pack
   - lesson_script_input_v5.yaml
   - 课堂实施方案
3. 能回答使用：
   - `build_chapter_assets_v5.py`
   - `preflight` 或 `maintain / drift check`
4. 能回答讲义层不自动跟随单一来源重写，但应按 `B 方案` 做回改与轻量一致性检查

---

## 3.3 验收题 3：反馈回流验证

### 题目

```text
第四章首轮真实教学试点批改完成后，请说明：

1. debug、教学反馈、memory 的调用顺序
2. 每一步对应哪个脚本
3. 每一步的主要输入和输出是什么
4. 最终这些结果应回改哪些对象

最后输出：
- 反馈闭环摘要
- 哪一步最容易被做错
- 下一步最小动作
```

### 通过标准

1. 能说清：
   `评分输出 -> 教学反馈 -> memory 回写 -> 修订讲义 / assignment pack / 课堂实施方案 / 评分规则`
2. 能点到至少这两个脚本：
   - `build_teaching_feedback_v5.py`
   - `memory_update_v5.py`
3. 不把 debug 当成最终规则来源
4. 能区分“反馈输出”和“single source”的角色差异

---

## 3.4 评分口径

建议按三档判断当前 Project 是否通过：

### A 档：通过

1. 三题都能稳定回答
2. 不再出现 `README = single source`、`assignment pack = 母规则` 这类错误
3. 能把结构理解转成动作顺序

### B 档：结构通过，执行待验证

1. 第一题回答好
2. 第二、三题仍停留在“概念描述”，不能稳定落到脚本和顺序

### C 档：未通过

1. 仍混淆 single source、正式产物、治理说明
2. 仍不能区分讲义层和产物层
3. 不能说明评分反馈如何回流到 memory

## 4. 结论

只有当 GitHub 连接版 Project 至少达到 `B 档`，它才算通过“系统辨识测试”；  
只有达到 `A 档`，它才算通过“任务执行测试”。

建议先用本题单验证，再决定是否把该 Project 作为长期协作入口。
