"""
Action Registry - 注册所有 Agent 可调用的操作
每个 action 包含：名称、中文描述、参数 schema、回调函数
可导出为 OpenAI function calling 格式
"""


class ActionRegistry:
    def __init__(self):
        self._actions = {}

    def register(self, name: str, description: str,
                 params_schema: dict, callback: callable):
        """
        注册一个 agent 可调用的操作

        Args:
            name: 操作名称（英文，用于 function calling）
            description: 操作描述（中文，帮助 LLM 理解用途）
            params_schema: 参数 JSON Schema
            callback: 回调函数，接受 **kwargs 参数
        """
        self._actions[name] = {
            "description": description,
            "parameters": params_schema,
            "callback": callback,
        }

    def get_tools_schema(self) -> list:
        """导出为 OpenAI function calling 的 tools 格式"""
        tools = []
        for name, info in self._actions.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": info["description"],
                    "parameters": info["parameters"],
                }
            })
        return tools

    def get_action_names(self) -> list:
        return list(self._actions.keys())

    def has_action(self, name: str) -> bool:
        return name in self._actions

    def execute(self, name: str, params: dict) -> str:
        """
        执行指定的 action

        Args:
            name: 操作名称
            params: 参数字典

        Returns:
            执行结果的描述字符串
        """
        if name not in self._actions:
            return f"错误：未找到操作 '{name}'"
        try:
            action = self._actions[name]
            result = action["callback"](**params)
            return str(result) if result is not None else "操作已完成"
        except Exception as e:
            return f"执行失败：{e}"

    def get_description(self, name: str) -> str:
        """获取操作的中文描述"""
        if name in self._actions:
            return self._actions[name]["description"]
        return ""

    def format_action_summary(self, name: str, params: dict) -> str:
        """格式化操作摘要，用于确认对话框"""
        desc = self.get_description(name)
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        return f"【{desc}】\n参数：{param_str}"
