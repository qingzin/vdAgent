# Agent 模块 - 驾驶模拟器 AI 控制助手

## 概述

通过本地部署的 LLM（Qwen2.5-Coder-14B）为驾驶模拟器控制面板增加自然语言控制能力。
用户在聊天面板中输入中文指令，Agent 解析意图后调用对应操作，所有操作需用户确认后执行。

## 架构

```
agent/
├── __init__.py        # 包标记
├── registry.py        # Action 注册表（核心数据结构）
├── llm_client.py      # LLM 通信（llama-server OpenAI API）
├── executor.py        # Agent 调度（意图解析→确认→执行）
├── chat_widget.py     # 聊天面板 UI（QDockWidget）
├── bridge.py          # 胶水层（Action → SimulatorUI 方法映射）
└── bootstrap.py       # 入口点（main.py 调用此文件）
```

## 安装步骤

### 1. 放置 agent 目录

将 `agent/` 文件夹放到 `main.py` 同级目录：

```
your_project/
├── main.py              # 现有代码
├── agent/               # 新增
│   ├── __init__.py
│   ├── registry.py
│   ├── llm_client.py
│   ├── executor.py
│   ├── chat_widget.py
│   ├── bridge.py
│   └── bootstrap.py
├── CustomWidget.py      # 现有
├── cueing_change.py     # 现有
└── ...
```

### 2. 安装 Python 依赖

```bash
pip install requests
```

（PyQt5、numpy 等已在现有项目中安装）

### 3. 修改 main.py（仅 2 行）

在 `SimulatorUI.__init__` 方法的**最末尾**，添加以下代码：

```python
# ===== AI 助手 =====
from agent.bootstrap import attach_agent
attach_agent(self)
```

具体位置：在 `self.visual_compensator_thread.start()` 之后、
`self.update_indicator(False)` 之前（或之后都可以）。

### 4. 启动 llama-server

```bash
llama-server \
    --jinja \
    -fa \
    -m /path/to/qwen2.5-coder-14b-instruct-q4_k_m.gguf \
    --host 127.0.0.1 \
    --port 8080 \
    -ngl 99 \
    -c 4096
```

关键参数：
- `--jinja`：启用 Jinja 模板，function calling 必需
- `-fa`：Flash Attention，提升性能
- `-ngl 99`：GPU 层数，根据显存调整
- `-c 4096`：上下文长度，Agent 场景 4K 足够

### 5. 启动应用

正常启动 main.py 即可。右侧会出现 AI 助手聊天面板。

## 第一批支持的操作（8 个）

| 操作 | 示例指令 |
|------|---------|
| 选择车型 | "把车型换成 SUV_baseline" |
| 选择前弹簧 | "前弹簧换成 Spring_Front_25" |
| 选择后弹簧 | "后弹簧刚度设为 30" |
| 选择前稳定杆 | "前稳定杆换成 ARB_Front_v2" |
| 选择后稳定杆 | "后稳定杆换成 ARB_Rear_soft" |
| 设置触感增益 | "把摩擦增益改成 1.5，阻尼改成 0.8" |
| 平台控制 | "发送平台指令 4" 或 "接合平台" |
| 运行 CarSim | "运行仿真" |

## 安全机制

- **所有操作需确认**：Agent 解析完意图后，会在黄色确认框中展示即将执行的操作和参数，
  用户点击"确认执行"才会真正执行。
- **主线程执行**：所有 GUI 操作通过 Qt 信号槽机制在主线程执行，
  LLM 调用在子线程进行，不阻塞 UI。
- **连接检测**：每 10 秒检查 llama-server 连接状态，
  状态指示灯显示在聊天面板标题栏。

## 扩展新操作

在 `bridge.py` 的 `register_actions` 函数中添加新的注册即可。模板：

```python
def my_new_action(param1: str, param2: float = 1.0) -> str:
    # 操作逻辑...
    # 更新 UI（如果需要）...
    return "执行结果描述"

registry.register(
    name="my_new_action",
    description="中文描述，告诉 LLM 这个操作做什么",
    params_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "参数1的中文说明"},
            "param2": {"type": "number", "description": "参数2说明"},
        },
        "required": ["param1"]
    },
    callback=my_new_action,
)
```

## 故障排查

### LLM 连接失败（红色指示灯）
- 确认 llama-server 已启动
- 确认端口号匹配（默认 8080）
- 检查防火墙设置

### Tool Call 解析失败
- 确认 llama-server 启动时加了 `--jinja` 参数
- Qwen2.5-Coder 偶尔会输出纯文本 JSON 而非结构化 tool_calls，
  代码中已有 fallback 解析器处理此情况

### 操作执行后 UI 不更新
- 检查胶水函数中是否同步更新了对应的 Widget
- 确认操作是否在主线程执行（通过 Qt 信号槽）

## LLM 服务地址配置

默认连接 `http://127.0.0.1:8080`。如需修改，在 main.py 中：

```python
attach_agent(self, llm_url="http://192.168.1.100:8080")
```
