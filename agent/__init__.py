"""
Agent 模块 - 为驾驶模拟器控制面板提供 LLM Agent 控制能力

模块结构：
  registry.py    - Action 注册表
  llm_client.py  - LLM 通信客户端（llama-server OpenAI 兼容 API）
  executor.py    - Agent 调度核心
  chat_widget.py - 聊天面板 UI
  bridge.py      - 胶水层（连接 Agent 和现有 GUI）
  bootstrap.py   - 入口点（main.py 唯一需要调用的模块）
"""
