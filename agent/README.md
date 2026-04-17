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
│   ├── tuning_actions.py        # 车型/弹簧/稳定杆 (9 个 action)
│   ├── simulation_actions.py    # CarSim 运行/Simulink/缓存 (5 个)
│   ├── recording_actions.py     # 数据记录 (4 个)
│   ├── haptic_actions.py        # 触感力反馈 (2 个)
│   ├── platform_actions.py      # 平台指令/偏置 (4 个)
│   ├── scene_actions.py         # 地图/起点/工况 (4 个)
│   ├── visual_actions.py        # 视觉补偿 (2 个)
│   ├── plot_actions.py          # 绘图/报警 (5 个)
│   └── misc_actions.py          # 预定义/信号 (3 个)
└── services/             # 业务能力 service 层 (预留, 目前未使用)
    ├── __init__.py
    └── platform_service.py
```

## Action 清单 (共 38 个)

### 车型与调校 (9)
- `select_vehicle` — 切换车型
- `select_front_spring` / `select_rear_spring` — 前/后弹簧 (名称或数值)
- `select_front_right_spring` / `select_rear_right_spring` — 右侧弹簧 (左右独立车型)
- `select_front_antiroll` / `select_rear_antiroll` — 前/后稳定杆
- `refresh_tuning_params` — 重新读取样件列表
- `get_current_setup` — 查询当前调校配置

### 仿真 (5)
- `run_carsim` — 运行 CarSim 仿真
- `open_simulink` — 打开 Simulink
- `build_dspace` — 编译 DSpace
- `clear_offline_data` — 清除离线仿真缓存
- `view_offline_data` — 查看离线仿真对比

### 数据记录 (4)
- `start_recording` / `stop_recording` — 开始/结束记录
- `set_recording_options` — 配置记录开关 (disusx/video/par/auto)
- `get_recording_status` — 查询记录状态

### 触感力反馈 (2)
- `set_haptic_gains` — 设置触感增益 (6 个参数)
- `get_haptic_gains` — 查询触感增益

### 运动平台 (4)
- `platform_control` — 发送 0-6 指令
- `one_click_platform_start` / `one_click_platform_stop` — 一键启停
- `set_platform_offset` — 平台位置偏置 X/Y/Z

### 场景设置 (4)
- `select_map_and_start_point` — 切换地图/起点
- `confirm_scene` — 确认场景, 发起点坐标
- `set_condition` — 切换工况
- `get_current_scene` — 查询当前场景

### 视觉补偿 (2)
- `set_visual_compensation` — 视觉运动跟随补偿 (12 参数)
- `set_visual_delay_compensation` — 视觉延迟补偿 (5 参数)

### 绘图与报警 (5)
- `control_plotting` — 绘图 run/pause/clear
- `set_all_plots` — 全开/全关图表
- `set_plot_visibility` — 显示/隐藏指定通道
- `set_plot_time_range` — 设置 X 轴时间范围
- `set_alarm` — 开关报警 / 切换报警工况

### 其他 (3)
- `set_preset` — 设置评价预定义字段
- `get_preset` — 查询评价预定义
- `toggle_all_signals` — 信号总开关

## 记录状态保护

以下会修改 CarSim 状态的 action 在**数据记录中被自动拒绝**:
`select_vehicle`, `select_*_spring`, `select_*_antiroll`, `run_carsim`

## 已知注意事项

### Context 容量
38 个 action 的 tools schema 约 3000-4000 tokens。
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
