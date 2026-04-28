# Nanobot Runtime PoC 交接文档

## 1. 本分支目标

当前分支 `codex/nanobot-migration-eval` 的目标不是把 vdAgent 整体替换成 nanobot，而是先建立一条可迁移的运行时适配层。

核心策略是：

- 保留当前 `main.py`、PyQt GUI、`AgentContext`、`agent/actions/*` 和已有安全确认逻辑。
- 在外层新增 `agent/runtime/`，把现有底盘业务能力包装成更接近 nanobot/MCP 的工具接口。
- 第一阶段只验证“用户目标 -> 规划工具 -> 工具调用 -> 结果记录”的链路，不实现完整自主多步执行器。
- 不引入 nanobot 依赖，避免上游 Alpha API 变化影响当前项目。

## 2. 已完成内容

### 新增 runtime 适配层

新增目录：`agent/runtime/`

主要文件：

- `models.py`：定义 runtime 层的数据结构，包括 `RuntimeTool`、`RuntimeToolResult`、`RuntimeTurnResult`。
- `memory.py`：定义 `NanobotMemoryBridge`，把当前 JSONL 记忆映射成 session、history、knowledge 三层。
- `adapter.py`：定义 `NanobotRuntimeAdapter`，负责导出工具、执行工具、处理确认、安全记录和简单目标路由。
- `README.md`：说明 runtime PoC 的范围和非目标。

### Runtime 工具导出

`NanobotRuntimeAdapter.export_nanobot_tools()` 会把当前 `ActionRegistry` 中暴露给 LLM 的工具转换为 runtime-neutral 结构：

```python
{
    "name": "...",
    "description": "...",
    "input_schema": {...},
    "metadata": {
        "category": "...",
        "risk_level": "...",
        "side_effects": True or False,
    },
}
```

这不是 nanobot 官方协议的最终绑定，只是一个中间接口。后续如果正式接入 nanobot 或 MCP server，可以从这个接口继续适配。

### 安全策略保留

runtime adapter 没有绕过原有安全规则：

- `risk_level="low"` 且 `side_effects=False` 的工具可以直接执行。
- `risk_level` 为 `medium/high` 或 `side_effects=True` 的工具默认返回 `requires_confirmation`。
- 高风险工具只有在 `confirmed=True` 时才真正调用 `registry.execute(...)`。
- 如果动作没有匹配最近计划，会在确认摘要里提示需要明确确认。

### Memory 映射

`NanobotMemoryBridge` 基于现有 `AgentMemoryStore`：

- `session`：runtime 用户/助手消息。
- `history`：runtime 工具调用、结果、确认请求、计划上下文等过程日志。
- `knowledge`：已有 `experience_seeds.jsonl` 中的工程经验种子。

这一步只是记忆分层映射，还没有做向量检索、长期知识蒸馏或 Dream 机制。

### PoC 目标路由

`NanobotRuntimeAdapter.handle_user_goal(...)` 当前实现的是最小 PoC：

- 收到复杂底盘目标后，先记录用户 session。
- 召回相关经验种子。
- 默认路由到 `plan_chassis_task`。
- 如果输入更像“建议/抱怨/suggest”，路由到 `suggest_chassis_tuning`。
- 不会直接调用 `set_spring`、`set_antiroll_bar` 等写操作。

## 3. 当前没有做的事

以下内容本分支刻意没有实现：

- 没有把 nanobot 包安装进项目。
- 没有修改 `main.py` 或 GUI 挂载流程。
- 没有把现有 `AgentExecutor` 替换掉。
- 没有实现完整 autonomous multi-step executor。
- 没有实现 step retry、失败恢复、跨会话 plan lifecycle。
- 没有引入数据库、向量库或第三方依赖。

原因是当前项目仍处于从 GUI Agent 原型向业务 Agent runtime 迁移的阶段。直接整体替换风险太高，容易破坏现有底盘控制、记录、确认和 GUI 链路。

## 4. 如何验证

当前分支验证命令：

```powershell
python -m pytest tests
$env:PYTHONDONTWRITEBYTECODE='1'; python tests\smoke_agent.py
```

最近一次验证结果：

```text
22 passed
smoke_agent: ok
```

新增测试文件：

- `tests/test_nanobot_runtime_adapter.py`

覆盖内容：

- runtime 能读取当前 registry tool schema。
- runtime 能导出 nanobot/MCP 友好的工具描述。
- 只读工具可以直接执行并写入 history。
- 高风险工具默认只返回确认请求，不执行真实 callback。
- 高风险工具在 `confirmed=True` 后才执行并写入经验种子。
- 复杂底盘目标会先路由到规划工具，不会直接执行写操作。

## 5. 后续建议迭代顺序

建议按以下顺序继续优化，不要直接跳到完整自主演化：

1. 强化 runtime policy：把“确认规则、计划匹配、记录中禁止动作”等策略从 adapter 中抽成独立 policy 模块。
2. 强化 plan-to-tool 映射：让 plan step 不只匹配 `action_name`，还要支持参数草案、前置条件和验证指标。
3. 强化 memory recall：把经验召回从简单 keyword 过滤升级为按目标、工况、动作类型、结果好坏综合检索。
4. 增加 dry-run 任务执行：先生成多步执行计划和 next action，不直接连续执行写操作。
5. 再评估正式接入 nanobot：锁定 nanobot 版本，做一个真实 skill/MCP binding，而不是直接替换现有 executor。

## 6. 当前架构关系

```text
User / Future Nanobot Runtime
        |
        v
agent/runtime/NanobotRuntimeAdapter
        |
        +--> ActionRegistry.get_tools_schema()
        +--> ActionRegistry.execute()
        +--> NanobotMemoryBridge
        |
        v
agent/actions/* + agent/memory/*
        |
        v
Existing PyQt GUI / CarSim / Simulator workflow
```

本分支的关键价值是增加了一个“运行时边界”。后续可以在这个边界外接 nanobot，也可以继续保留当前 GUI agent，不需要一次性推倒重构。
