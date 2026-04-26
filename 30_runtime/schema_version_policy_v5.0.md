[meta]
type: Runtime
status: Draft
version: v5.0
keywords: schema_version,兼容策略,迁移
owner: Shen
updated: 2026-04-26
[/meta]

# schema_version 策略 v5.0

## 1. Concept

`schema_version` 不是装饰字段，而是约束“脚本能否安全读取当前结构”的版本信号。

本系统当前正式机器可读输入只接受：

```text
schema_version: v5.0
```

若脚本遇到未知版本，应停止并给出清晰错误，不应猜测字段含义。

## 2. Mechanism

版本升级按影响范围分三类：

1. `v5.0 内部兼容修改`
   - 只增加可选说明字段
   - 不改变既有字段含义
   - 不改变生成产物结构
   - 不需要迁移器
2. `v5.1 小版本`
   - 增加新的可选机器字段
   - 旧 `v5.0` 文件仍能被读取
   - 脚本可用默认值补齐
3. `v6.0 大版本`
   - 删除或重命名必填字段
   - 改变评分、作业包或课堂实施方案的核心结构
   - 需要显式迁移脚本或并行读取策略

## 3. Application

当前落地规则：

1. `30_runtime/chapter_master_configs/*.yaml` 必须显式写 `schema_version: v5.0`。
2. `lesson_script_input_v5.yaml` 必须显式写 `schema_version: v5.0`。
3. 自动生成的 `chapter_profiles/*.json` 会带 `schema_version: v5.0`。
4. 评分脚本和生成脚本遇到非 `v5.0` 的显式版本时直接报错。
5. 若未来出现 `v5.1` 或 `v6.0`，先写迁移说明，再改读取逻辑，不允许静默混读。
