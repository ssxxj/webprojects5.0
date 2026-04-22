[meta]
type: PilotChecklist
status: Draft
version: v5.0
chapter: chapter04_xss
owner: Shen
updated: 2026-04-21
[/meta]

# 第四章 XSS漏洞与防护 5.0首轮真实教学试点执行清单 v5.0

## 1. Concept

这份清单的目标，不是“把第四章上完”，而是用第四章验证 `projects5.0` 的第一轮真实教学闭环是否成立：

`讲义 -> 课堂实施 -> 作业提交 -> 批量评分 -> 教学反馈 -> memory 回写 -> 模板修订`

第四章之所以适合作为首轮试点，是因为它已经同时具备：

1. 正式讲义资产
2. 正式 assignment pack
3. 正式课堂实施方案
4. 正式 chapter profile
5. 正式评分、反馈、memory 更新链

因此，第四章试点的成功标准，不是学生平均分高，而是系统能否暴露真实问题、并把问题稳定回写到 `projects5.0`。

## 2. Mechanism

本次试点按四段执行：

1. `课前准备`
   确认第四章资产、运行环境、评分入口、观察记录入口全部可用。
2. `课堂执行`
   严格按第四章课堂实施方案运行，并留下 Step 9 最小观察记录。
3. `课后批改`
   用 v5 评分链跑真实作业，生成评估、反馈和 debug。
4. `回归修订`
   只追三类问题：
   - 课堂节奏问题
   - 作业要求问题
   - 评分与反馈问题

本轮试点不追求“立即最优”，而追求：

1. 问题定位准确
2. 反馈可追溯
3. 修订有明确落点

## 3. 成功标准

若满足以下条件，可认为第四章首轮试点有效：

1. 课前 preflight 为 `READY`
2. 课堂中有完整 Step 9 最小观察记录
3. 学生作业可按 v5 正常批量评分
4. 能生成班级教学反馈报告
5. 能把本轮反馈回写到 `10_memory`
6. 至少能明确指出 3 类需修订对象中的 1 类以上：
   - 讲义
   - assignment pack
   - 课堂实施方案
   - 评分规则

## 4. 上游资产入口

### 4.1 讲义

- [第四章 XSS漏洞与防护_教师版讲义_v5.0.md](/Users/shen/教学/web应用安全与防护/web应用安全与防护projects5.0/50_assets/章节讲义/chapter04_xss/第四章%20XSS漏洞与防护_教师版讲义_v5.0.md)
- [第四章 XSS漏洞与防护_学生预习版讲义_v5.0.md](/Users/shen/教学/web应用安全与防护/web应用安全与防护projects5.0/50_assets/章节讲义/chapter04_xss/第四章%20XSS漏洞与防护_学生预习版讲义_v5.0.md)

### 4.2 课堂执行

- [第四章 XSS漏洞与防护_课堂实施方案_v5.0.md](/Users/shen/教学/web应用安全与防护/web应用安全与防护projects5.0/50_assets/课堂实施方案/chapter04_xss/第四章%20XSS漏洞与防护_课堂实施方案_v5.0.md)
- [lesson_script_input_v5.yaml](/Users/shen/教学/web应用安全与防护/web应用安全与防护projects5.0/50_assets/课堂实施方案/chapter04_xss/lesson_script_input_v5.yaml)

### 4.3 作业与评分

- [第四章 XSS漏洞与防护_教师端作业包_v5.0.md](/Users/shen/教学/web应用安全与防护/web应用安全与防护projects5.0/50_assets/assignment_packs/chapter04_xss/第四章%20XSS漏洞与防护_教师端作业包_v5.0.md)
- [chapter04_xss.json](/Users/shen/教学/web应用安全与防护/web应用安全与防护projects5.0/40_evaluation/runtime/chapter_profiles/chapter04_xss.json)

## 5. Application

## 5.1 课前一周到课前一天

### 必做

1. 确认第四章授课环境只包含授权对象：
   - DVWA
   - 本机浏览器
   - localhost / 127.0.0.1
   - 教师授权实验环境
2. 确认第四章讲义、assignment pack、课堂实施方案三者口径一致。
3. 确认本次班级的作业目录与成绩表路径已经预留。
4. 确认学生提交格式、命名规则、脱敏要求、AI 审核要求已提前告知。

### 命令检查

在 `projects5.0` 根目录执行：

```bash
make preflight
```

预期结果：

```text
[preflight] READY | config 8/8 | clean 8/8 | lecture 8/8 | drift=0 error=0 | report: ...
```

若不是 `READY`，本轮试点不应开始。

## 5.2 课前当天

### 教师准备检查

1. 按第四章课堂实施方案准备 90 分钟节奏。
2. 准备至少 1 组：
   - Reflected 样例
   - Stored 样例
   - DOM 样例
3. 准备强制选择题、证据追问题、条件变化题。
4. 预先决定本节课要重点观察的三个误区：
   - 是否把输入内容本身误写成根因
   - 是否混淆输入层、输出层、执行层控制点
   - 是否把现象直接写成完整机制结论

### 建议携带的观察记录模板

至少准备下面 5 项观察位：

1. 学生最常把哪个表面现象误写成根因
2. 哪个控制层次最容易被混在一起
3. 强制选择题里最常见的错误选项
4. 哪一段课堂最明显超时
5. 哪个任务字段最容易在作业里缺失

## 5.3 课堂执行

### 必做动作

1. 开场明确：
   - 本章不是脚本样例记忆课
   - 仅限授权环境
   - 本章主线是：
     `输入 -> 输出位置 -> 浏览器解析 -> 是否执行 -> 风险范围 -> 控制点`
2. 按课堂实施方案推进五段节奏：
   - 开场与边界
   - Concept
   - Mechanism
   - Application
   - 形成性评估与收口
3. 课堂中至少做一次“证据 -> 结论”示范收束。
4. 收口时明确作业要求：
   - 五类任务
   - 风险链关系图/表
   - 学生自评
   - AI输出审核与人工复核记录

### 课堂观察最小门槛

至少记录以下 3 条真实观察，否则本次试点视为观察不足：

1. 一条学生对 XSS 根因的误判
2. 一条学生对三类路径差异的误判
3. 一条学生对防护层次的误判

## 5.4 作业发布与收集

### 发布后检查

1. 学生收到的是第四章正式 assignment pack，而不是旧版说明。
2. 班级目录已建立。
3. Excel roster 已就位。

### 建议目录变量

将以下路径在批改前替换成真实值：

```text
<作业目录>
<成绩表.xlsx>
<班级评估.pdf>
<debug.json>
<教学反馈.md/.pdf/.json>
```

## 5.5 批量评分

在 `projects5.0` 根目录执行：

```bash
python3 40_evaluation/runtime/course_assignment_eval_v5.py \
  --profile 40_evaluation/runtime/chapter_profiles/chapter04_xss.json \
  --dir "<作业目录>" \
  --excel "<成绩表.xlsx>" \
  --pdf-output "<班级评估.pdf>" \
  --debug-output "<debug.json>"
```

### 批改后最少检查

1. 是否成功生成 Excel 回写结果
2. 是否成功生成班级评估 PDF
3. 是否成功生成 debug JSON
4. 是否出现红线问题：
   - 未脱敏
   - 超出授权边界
   - 高度雷同
   - 证据不可追溯

## 5.6 班级教学反馈生成

```bash
python3 40_evaluation/runtime/build_teaching_feedback_v5.py \
  --debug "<debug.json>" \
  --profile 40_evaluation/runtime/chapter_profiles/chapter04_xss.json \
  --class-name "<班级名称>" \
  --out-md "<教学反馈.md>" \
  --out-pdf "<教学反馈.pdf>" \
  --out-json "<教学反馈摘要.json>"
```

### 反馈阶段必须回答的 3 个问题

1. 本章学生最常错在 `根因理解`、`证据表达`、`路径差异` 还是 `防护层次`
2. 本章 assignment pack 是否把作业要求说清了
3. 本章课堂实施方案的哪个环节最需要缩短或加强

## 5.7 memory 回写

```bash
python3 10_memory/runtime/memory_update_v5.py \
  --inputs "<教学反馈摘要.json>"
```

### 回写后检查

1. `误区库`
2. `案例库`
3. `班级教学反馈索引`
4. `memory_snapshot_v5.json`

都应出现本轮第四章的增量。

## 5.8 回归修订会

建议在批改后 48 小时内完成。

### 只看四类对象

1. 讲义
2. 课堂实施方案
3. assignment pack
4. 评分规则 / 反馈规则

### 修订决策模板

对每个问题，只做如下判断：

1. 这是 `教学表达问题` 还是 `结构设计问题`
2. 应该改：
   - 讲义
   - 课堂实施方案
   - assignment pack
   - profile / 评分规则
3. 这是第四章特有问题，还是应上升到课程级 memory

## 6. 试点结束判定

若以下 6 项都满足，本轮试点可记为 `完成`：

1. preflight 为 `READY`
2. 课堂观察记录完成
3. 作业批量评分完成
4. 教学反馈报告完成
5. memory 回写完成
6. 已形成至少一条明确修订动作并知道应改哪个文件

若缺任一项，本轮试点仍可视为“部分完成”，但不得宣称第四章已经完成真实教学回归。

## 7. 试点后优先修订顺序

1. 先修会导致误教或误判的结构问题
2. 再修高频误区前置不足的问题
3. 最后再修措辞与模板美化问题

换句话说：

`先修主线，再修约束，再修文案。`
