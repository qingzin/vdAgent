"""
LLM Client - 与 llama-server 的 OpenAI 兼容 API 通信
支持 function calling，带 fallback JSON 解析
"""

import json
import requests
import re
from typing import Optional


class LLMResponse:
    """LLM 响应的统一封装"""

    def __init__(self):
        self.text: Optional[str] = None
        self.has_tool_call: bool = False
        self.tool_name: Optional[str] = None
        self.tool_params: Optional[dict] = None
        self.raw: Optional[dict] = None


class LLMClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        """
        Args:
            base_url: llama-server 的地址，默认 http://127.0.0.1:8080
        """
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/v1/chat/completions"

    def check_connection(self) -> bool:
        """检查 llama-server 是否可用"""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def chat(self, messages: list, tools: list = None,
             system: str = None, temperature: float = 0.3) -> LLMResponse:
        """
        发送聊天请求

        Args:
            messages: 对话历史
            tools: function calling 的 tools 列表
            system: 系统提示词
            temperature: 采样温度

        Returns:
            LLMResponse 对象
        """
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        payload = {
            "model": "qwen2.5-coder",
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": 1024,
        }

        if tools:
            payload["tools"] = tools
            # Qwen2.5-Coder 在 required 模式下 tool call 更可靠
            payload["tool_choice"] = "auto"

        try:
            resp = requests.post(
                self.api_url,
                json=payload,
                timeout=60,
                headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()
            return self._parse_response(data)
        except requests.exceptions.ConnectionError:
            result = LLMResponse()
            result.text = "无法连接到 LLM 服务，请确认 llama-server 已启动。"
            return result
        except requests.exceptions.Timeout:
            result = LLMResponse()
            result.text = "LLM 响应超时，请重试。"
            return result
        except Exception as e:
            result = LLMResponse()
            result.text = f"LLM 通信错误：{e}"
            return result

    def _parse_response(self, data: dict) -> LLMResponse:
        """解析 API 响应，处理正常返回和 fallback"""
        result = LLMResponse()
        result.raw = data

        try:
            choice = data["choices"][0]
            message = choice["message"]

            # 情况 1：标准 tool_calls 格式
            if "tool_calls" in message and message["tool_calls"]:
                tc = message["tool_calls"][0]
                if isinstance(tc, dict):
                    func = tc.get("function", tc)
                    result.has_tool_call = True
                    result.tool_name = func.get("name", "")
                    args = func.get("arguments", "{}")
                    if isinstance(args, str):
                        result.tool_params = json.loads(args)
                    else:
                        result.tool_params = args
                    return result

            # 情况 2：模型把 tool call 输出为纯文本（Qwen2.5-Coder 的已知问题）
            content = message.get("content", "")
            if content:
                parsed = self._try_parse_tool_call_from_text(content)
                if parsed:
                    result.has_tool_call = True
                    result.tool_name = parsed["name"]
                    result.tool_params = parsed["arguments"]
                    return result

            # 情况 3：纯文本回复
            result.text = content or "（无响应内容）"
            return result

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            result.text = f"解析 LLM 响应失败：{e}"
            return result

    def _try_parse_tool_call_from_text(self, text: str) -> Optional[dict]:
        """
        Fallback：从纯文本中提取 tool call JSON
        处理 Qwen2.5-Coder 有时不用 <tool_call> 标签的情况
        """
        # 尝试匹配 <tool_call> 标签
        tag_pattern = r'<tool_call>\s*(\{.*?\})\s*</tool_call>'
        match = re.search(tag_pattern, text, re.DOTALL)
        if match:
            try:
                obj = json.loads(match.group(1))
                if "name" in obj and "arguments" in obj:
                    return obj
            except json.JSONDecodeError:
                pass

        # 尝试匹配裸 JSON（包含 name 和 arguments 字段）
        json_pattern = r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{.*?\})\s*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                name = match.group(1)
                args = json.loads(match.group(2))
                return {"name": name, "arguments": args}
            except json.JSONDecodeError:
                pass

        return None
