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
├── chat_widget.py        # 聊天面板 UI
├── bridge.py             # 汇总所有 action 模块
├── actions/              # 按领域拆分的 action 定义
│   ├── _helpers.py
│   ├── tuning_actions.py        # 车型/弹簧/稳定杆
│   ├── simulation_actions.py    # CarSim 运行/仿真工作区/离线分析
│   ├── recording_actions.py     # 数据记录/记录准备
│   ├── haptic_actions.py        # 触感力反馈
│   ├── platform_actions.py      # 平台准备/一键启停
│   ├── scene_actions.py         # 工况/地图/起点/确认
│   ├── visual_actions.py        # 视觉补偿
│   ├── plot_actions.py          # 绘图/报警（已不对 LLM 暴露）
│   └── misc_actions.py          # 评价元数据
└── services/             # 业务能力 service 层 (预留, 目前未使用)
    ├── __init__.py
    └── platform_service.py
```

## Action 清单 (当前对 LLM 暴露 19 个)

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

## 启动 llama-server

```bash
llama-server --jinja -fa \
  -m /path/to/qwen2.5-coder-14b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 --port 8080 -ngl 99 -c 8192
```
