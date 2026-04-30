# Agent 模块 - 驾驶模拟器 AI 控制助手

通过本地 LLM 为驾驶模拟器提供自然语言控制能力。

## 对 main.py 的侵入

**仅一行, 永远不变**:

```python
from agent.bootstrap import attach_agent
attach_agent(self)    # 放在 SimulatorUI.__init__ 末尾
```

新增/修改 action 均不需要动 main.py, 也不需要动 bootstrap.py。

## 启动方式

```bash
# 1. 先启动 llama-server (需 Qwen2.5-Coder 14B 或兼容模型)
llama-server --jinja -fa \
  -m /path/to/qwen2.5-coder-14b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 --port 8080 -ngl 99 -c 8192

# 2. 再启动驾驶模拟器主程序
python main.py
```

启动后 GUI 右侧出现 "Toggle AI Assistant" 按钮，点击打开 AI 对话面板即可使用。

## 目录结构

```
agent/
├── __init__.py
├── bootstrap.py          # attach_agent 入口 (唯一侵入点)
├── context.py            # AgentContext 自动定位 main 模块
├── registry.py           # ActionRegistry
├── llm_client.py         # llama-server 通信 (OpenAI 兼容 API)
├── executor.py           # 调度 + 对话历史滑动窗口 + LLM 上下文注入
├── planner.py            # 规则式底盘规划/建议 (LLM fallback)
├── chat_widget.py        # 聊天面板 UI
├── bridge.py             # 汇总所有 action 模块
├── knowledge/            # 领域知识库
│   ├── __init__.py
│   ├── store.py          # KnowledgeStore (Markdown + YAML frontmatter)
│   └── data/             # 中文知识种子文件 (*.md)
├── memory/               # JSONL 过程日志和经验种子
├── actions/              # 按领域拆分的 action 定义
│   ├── _helpers.py
│   ├── tuning_actions.py        # 车型/弹簧/稳定杆
│   ├── simulation_actions.py    # CarSim 运行/仿真工作区/离线分析/清除缓存
│   ├── recording_actions.py     # 数据记录/记录准备
│   ├── haptic_actions.py        # 触感力反馈
│   ├── platform_actions.py      # 平台准备/一键启停
│   ├── scene_actions.py         # 工况/地图/起点/路段/确认
│   ├── visual_actions.py        # 视觉补偿
│   ├── planning_actions.py      # 底盘任务规划
│   ├── knowledge_actions.py     # 底盘调校建议/知识检索/知识保存
│   ├── analysis_actions.py      # 历史数据加载
│   ├── monitoring_actions.py    # 报警监控开关
│   ├── plot_actions.py          # 绘图/报警（已不对 LLM 暴露）
│   └── misc_actions.py          # 评价元数据
└── services/             # 业务能力 service 层 (预留, 目前未使用)
    ├── __init__.py
    └── platform_service.py
```

## Action 清单 (当前对 LLM 暴露 25 个)

### 规划与知识建议 (4)
- `plan_chassis_task` — 针对复杂底盘目标生成步骤、参数方向、风险和验证指标
- `suggest_chassis_tuning` — 根据主观抱怨输出保守调校建议, 不直接修改硬件参数
- `search_knowledge` — 检索底盘调校领域知识库
- `save_knowledge` — 保存新的领域知识条目 (LLM 自动积累)

### 车型与调校 (4)
- `select_vehicle` — 切换车型
- `set_spring` — 统一设置前/后/左/右弹簧
- `set_antiroll_bar` — 统一设置前/后稳定杆
- `get_current_setup` — 查询当前调校配置

### 仿真 (4)
- `run_carsim` — 运行 CarSim 仿真
- `manage_simulation_workspace` — 打开 Simulink / 编译 DSpace
- `analyze_offline_result` — 查看离线仿真对比
- `clear_simulation_cache` — 清除离线仿真缓存, 方案计数归零

### 数据记录 (4)
- `start_recording` / `stop_recording` — 开始/结束记录
- `prepare_recording_session` — 配置记录开关 (disusx/video/par/auto)
- `get_recording_status` — 查询记录状态

### 数据分析 (1)
- `load_historical_record` — 加载指定路径的历史 CSV 数据并绘图回放

### 触感力反馈 (1)
- `tune_haptic_feedback` — 查询或设置触感增益

### 运动平台 (3)
- `one_click_platform_start` / `one_click_platform_stop` — 一键启停
- `prepare_platform` — 平台位置偏置 X/Y/Z

### 场景设置 (3)
- `prepare_test_scene` — 切换工况/地图/起点并确认生效
- `get_current_scene` — 查询当前场景
- `set_road_segment` — 设置/查询路段 (自动记录触发区域)

### 视觉补偿 (1)
- `set_visual_profile` — 统一设置视觉运动跟随补偿和视觉延迟补偿

### 监控报警 (1)
- `toggle_alarm` — 启停实时驾驶报警监控

### 其他 (1)
- `prepare_evaluation_metadata` — 设置或查询评价预定义字段

## LLM 驱动推理

每次 LLM 调用前, executor 会自动注入当前系统上下文:

- **车型与悬架配置** — 当前车型、前后弹簧/稳定杆名称
- **场景信息** — 当前地图、起点、工况
- **触感参数** — 摩擦/阻尼/回正/限位/手感轻重增益值
- **记录状态** — IMU/CarSim/MOOG 是否在记录中
- **方案计数** — 当前第几组仿真方案
- **报警状态** — 报警监控是否开启
- **近期操作经验** — 最近 5 条关键操作及结果

LLM 获得这些上下文后，能够：
1. 基于当前配置给出有针对性的分析建议
2. 调用 `search_knowledge` 检索领域原理支持回答
3. 调用 `save_knowledge` 自动积累交互中发现的调校规律
4. 结合历史案例和当前工况自主规划多步操作

## 领域知识库

`agent/knowledge/data/` 下的 Markdown 文件是人类可读、可修正的中文知识条目。
每条知识 = YAML 元数据 (标题/分类/标签/日期) + Markdown 正文。

当前已植入 6 篇知识种子：
- 稳定杆调校基本原则 (chassis_tuning)
- 弹簧刚度选型经验 (chassis_tuning)
- 转向触感调校指南 (haptic)
- 侧倾问题诊断与调校 (chassis_tuning)
- 驾驶模拟器数据记录规范 (recording)
- 工况与场景选择指南 (scene)

知识积累双轨并行：
- **人工编写** — 直接用编辑器在 `agent/knowledge/data/` 下创建 .md 文件
- **Agent 自动积累** — LLM 调用 `save_knowledge` 将交互中的经验沉淀为知识

## 已知注意事项

### Context 容量
当前 25 个 action 的 tools schema 明显比旧版更短, 更适合本地模型做稳定路由。
如果你用 llama-server 的 `-c 4096`, 建议升到 `-c 8192` 以留出对话、上下文注入和历史空间。

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
python -m py_compile agent/registry.py agent/executor.py agent/planner.py agent/memory/models.py agent/memory/store.py agent/actions/planning_actions.py agent/actions/knowledge_actions.py agent/knowledge/store.py
```

### 功能测试

**离线测试** (无需 PyQt5/CarSim 环境):

```bash
# 1. 验证核心模块可导入
python -c "from agent.knowledge.store import KnowledgeStore; print('Knowledge OK')"
python -c "from agent.executor import AgentExecutor; print('Executor OK')"

# 2. 验证知识库检索 (6篇种子, 搜索"侧倾"命中4条)
python -c "
from agent.knowledge.store import KnowledgeStore
s = KnowledgeStore()
print(f'知识条目: {len(s.list_all())}')
r = s.search(keyword='侧倾')
print(f'搜索侧倾命中: {len(r)} 条')
for e in r:
    print(f'  - {e[\"meta\"][\"title\"]}')
"

# 3. 语法检查全部模块
python -m py_compile agent/knowledge/store.py agent/executor.py agent/planner.py \
  agent/actions/*.py agent/bridge.py agent/bootstrap.py
```

**在线测试** (需要 PyQt5 + CarSim + llama-server 环境):

启动 main.py 后，在 AI 对话面板中:
- 输入 `"查询当前悬架配置"` 验证基础操作链路
- 输入 `"什么是稳定杆调校的基本原则"` 验证知识库检索
- 输入 `"单移线侧倾大怎么办"` 验证 LLM 推理+规划
- 输入 `"帮我开启报警监控"` 验证新增操作
