"""
LLM Client - 支持本地 llama-server 和远程 API 两种模式
兼容 OpenAI API 格式，支持 function calling，带 fallback JSON 解析
"""

import json
import requests
import re
from typing import Optional

from agent.llm_config import LLMConfig


class LLMResponse:
    """LLM 响应的统一封装"""

    def __init__(self):
        self.text: Optional[str] = None
        self.has_tool_call: bool = False
        self.tool_name: Optional[str] = None
        self.tool_params: Optional[dict] = None
        self.tool_calls: list[dict] = []
        self.raw: Optional[dict] = None


class ModelTurn(LLMResponse):
    """Structured model turn returned by LLMClient."""

    @property
    def assistant_text(self) -> Optional[str]:
        return self.text

    @assistant_text.setter
    def assistant_text(self, value: Optional[str]):
        self.text = value


class LLMClient:
    """支持本地和远程两种模式的 LLM 客户端。"""

    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig()

    def check_connection(self) -> bool:
        """检查 LLM 服务是否可用"""
        if self.config.is_local:
            try:
                resp = requests.get(f"{self.config.local_url}/health", timeout=3)
                return resp.status_code == 200
            except Exception:
                return False
        else:
            # 远程 API 无法简单检查，假设可用
            return True

    def chat(self, messages: list, tools: list = None,
             system: str = None, temperature: float = 0.3) -> ModelTurn:
        """
        发送聊天请求。根据 config.mode 选择本地或远程 API。
        """
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        if self.config.is_local:
            api_url = f"{self.config.local_url}/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
            model = "qwen2.5-coder"
            payload = {
                "model": model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": 512,
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
        else:
            api_url = self.config.remote_url
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.remote_api_key}",
            }
            model = self.config.remote_model
            payload = {
                "model": model,
                "messages": full_messages,
                "temperature": temperature,
                "max_tokens": 512,
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"

        try:
            resp = requests.post(api_url, json=payload, timeout=60, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_response(data)
        except requests.exceptions.ConnectionError:
            result = ModelTurn()
            result.text = "无法连接到 LLM 服务，请确认服务已启动。"
            return result
        except requests.exceptions.Timeout:
            result = ModelTurn()
            result.text = "LLM 响应超时，请重试。"
            return result
        except Exception as e:
            result = ModelTurn()
            result.text = f"LLM 通信错误：{e}"
            return result

    def _parse_response(self, data: dict) -> ModelTurn:
        """解析 API 响应，处理正常返回和 fallback"""
        result = ModelTurn()
        result.raw = data

        try:
            choice = data["choices"][0]
            message = choice["message"]

            # 情况 1：标准 tool_calls 格式
            if "tool_calls" in message and message["tool_calls"]:
                for tc in message["tool_calls"]:
                    if not isinstance(tc, dict):
                        continue
                    func = tc.get("function", tc)
                    name = func.get("name", "")
                    args = func.get("arguments", "{}")
                    if isinstance(args, str):
                        parsed_args = json.loads(args)
                    else:
                        parsed_args = args
                    result.tool_calls.append({
                        "name": name,
                        "arguments": parsed_args,
                    })
                if result.tool_calls:
                    first = result.tool_calls[0]
                    result.has_tool_call = True
                    result.tool_name = first["name"]
                    result.tool_params = first["arguments"]
                    return result

            # 情况 2：模型把 tool call 输出为纯文本（Qwen2.5-Coder 的已知问题）
            content = message.get("content", "")
            if content:
                parsed = self._try_parse_tool_call_from_text(content)
                if parsed:
                    result.tool_calls.append(parsed)
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
