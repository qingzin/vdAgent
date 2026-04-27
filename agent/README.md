# Agent 模块 - 驾驶模拟器 AI 控制助手

通过本地 LLM 为驾驶模拟器提供自然语言控制能力。

## 对 main.py 的侵入

**仅一行, 永远不变**:

```python
from agent.bootstrap import attach_agent
attach_agent(self)    # 放在 SimulatorUI.__init__ 末尾
```

新增/修改 action 均不需要动 main.py, 也不需要动 bootstrap.py。

## 目录结构

```
agent/
├── __init__.py
├── bootstrap.py          # attach_agent 入口
├── context.py            # AgentContext 自动定位 main 模块
├── registry.py           # ActionRegistry
├── llm_client.py         # llama-server 通信
├── executor.py           # 调度 + 对话历史滑动窗口 + 并发保护
├── planner.py            # 规则式底盘规划/建议
├── chat_widget.py        # 聊天面板 UI
├── bridge.py             # 汇总所有 action 模块
├── memory/               # JSONL 过程日志和经验种子
├── actions/              # 按领域拆分的 action 定义
│   ├── _helpers.py
│   ├── tuning_actions.py        # 车型/弹簧/稳定杆
│   ├── simulation_actions.py    # CarSim 运行/仿真工作区/离线分析
│   ├── recording_actions.py     # 数据记录/记录准备
│   ├── haptic_actions.py        # 触感力反馈
│   ├── platform_actions.py      # 平台准备/一键启停
│   ├── scene_actions.py         # 工况/地图/起点/确认
│   ├── visual_actions.py        # 视觉补偿
│   ├── planning_actions.py      # 底盘任务规划
│   ├── knowledge_actions.py     # 底盘调校建议
│   ├── plot_actions.py          # 绘图/报警（已不对 LLM 暴露）
│   └── misc_actions.py          # 评价元数据
└── services/             # 业务能力 service 层 (预留, 目前未使用)
    ├── __init__.py
    └── platform_service.py
```

## Action 清单 (当前对 LLM 暴露 21 个)

### 规划与知识建议 (2)
- `plan_chassis_task` — 针对复杂底盘目标生成步骤、参数方向、风险和验证指标
- `suggest_chassis_tuning` — 根据主观抱怨输出保守调校建议, 不直接修改硬件参数

### 车型与调校 (4)
- `select_vehicle` — 切换车型
- `set_spring` — 统一设置前/后/左/右弹簧
- `set_antiroll_bar` — 统一设置前/后稳定杆
- `get_current_setup` — 查询当前调校配置

### 仿真 (3)
- `run_carsim` — 运行 CarSim 仿真
- `manage_simulation_workspace` — 打开 Simulink / 编译 DSpace
- `analyze_offline_result` — 查看离线仿真对比

### 数据记录 (4)
- `start_recording` / `stop_recording` — 开始/结束记录
- `prepare_recording_session` — 配置记录开关 (disusx/video/par/auto)
- `get_recording_status` — 查询记录状态

### 触感力反馈 (1)
- `tune_haptic_feedback` — 查询或设置触感增益

### 运动平台 (3)
- `one_click_platform_start` / `one_click_platform_stop` — 一键启停
- `prepare_platform` — 平台位置偏置 X/Y/Z

### 场景设置 (2)
- `prepare_test_scene` — 切换工况/地图/起点并确认生效
- `get_current_scene` — 查询当前场景

### 视觉补偿 (1)
- `set_visual_profile` — 统一设置视觉运动跟随补偿和视觉延迟补偿

### 其他 (1)
- `prepare_evaluation_metadata` — 设置或查询评价预定义字段

## 已收敛的工具

以下旧 action 仍可能保留在内部实现中，但已不再作为 LLM 直接工具暴露：

- 弹簧细分工具：`select_front_spring`、`select_rear_spring`、`select_front_right_spring`、`select_rear_right_spring`
- 稳定杆细分工具：`select_front_antiroll`、`select_rear_antiroll`
- 场景细分工具：`select_map_and_start_point`、`confirm_scene`、`set_condition`
- 触感细分工具：`set_haptic_gains`、`get_haptic_gains`
- 视觉细分工具：`set_visual_compensation`、`set_visual_delay_compensation`
- 预定义细分工具：`set_preset`、`get_preset`

## 已下线的工具

以下 action 不再对 LLM 暴露：

- `refresh_tuning_params`
- `clear_offline_data`
- `platform_control`
- `control_plotting`
- `set_all_plots`
- `set_plot_visibility`
- `set_plot_time_range`
- `set_alarm`
- `toggle_all_signals`

## 记录状态保护

以下会修改 CarSim 状态的 action 在**数据记录中被自动拒绝**:
`select_vehicle`, `set_spring`, `set_antiroll_bar`, `run_carsim`

## 过程日志与经验种子

executor 会把关键过程写入默认目录 `agent_data/`:

- `run_logs.jsonl` — 用户输入、LLM 工具调用、确认/取消、执行结果和错误路径
- `experience_seeds.jsonl` — 对关键动作的经验样本种子

当前会为这些确认执行后的关键动作写入经验种子:
`set_spring`, `set_antiroll_bar`, `prepare_test_scene`, `run_carsim`,
`start_recording`, `stop_recording`。

这些文件是轻量 JSONL, 便于后续做检索、复盘或蒸馏知识库。日志写入失败不会阻塞主程序。

## 规划优先策略

系统提示词已约束: 遇到复杂底盘目标或主观反馈时, LLM 应优先调用
`plan_chassis_task` 或 `suggest_chassis_tuning`, 先形成方案和验证指标,
不要直接修改弹簧、稳定杆或触感参数。

典型场景:

- “单移线侧倾大” → 先规划/建议稳定杆和验证指标
- “方向盘中心区重” → 先建议触感参数方向, 不直接改悬架
- “起伏舒适性差/垂向冲击大” → 先建议弹簧/稳定杆方向和舒适性指标
- “准备工况并记录” → 先规划场景、记录开关、开始/结束记录顺序
- “修改悬架并仿真验证” → 先建立基线、单变量修改、run_carsim、结果对比

## 已知注意事项

### Context 容量
当前 19 个 action 的 tools schema 明显比旧版更短, 更适合本地模型做稳定路由。
如果你用 llama-server 的 `-c 4096`, 建议升到 `-c 8192` 以留出对话和历史空间。

### 对话历史
executor 默认保留最近 20 条消息。修改:

```python
from agent.executor import AgentExecutor
AgentExecutor.MAX_HISTORY = 10   # 或在 bootstrap 里传参
```

### 新增 action

(1) 在已有模块加: 在对应的 `actions/xxx.py` 里加函数 + `registry.register`

(2) 新领域: 新建 `actions/new_domain.py`, 暴露 `register(registry, ctx)`,
    然后在 `bridge.py` 的 `ACTION_MODULES` 列表里加一行

两种情况都不需要改 main.py 和 bootstrap.py。

## 测试

优先运行:

```bash
python -m pytest tests
```

如果当前环境未安装 pytest, 至少做语法检查:

```bash
python -m py_compile agent/registry.py agent/executor.py agent/planner.py agent/memory/models.py agent/memory/store.py agent/actions/planning_actions.py agent/actions/knowledge_actions.py
```

## 启动 llama-server

```bash
llama-server --jinja -fa \
  -m /path/to/qwen2.5-coder-14b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 --port 8080 -ngl 99 -c 8192
```
