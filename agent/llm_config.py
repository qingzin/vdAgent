"""
LLM 配置 — 支持本地模式和远程 API 模式切换，配置持久化到 agent_data/llm_config.json。
"""

import json
import os
from pathlib import Path


DEFAULT_CONFIG = {
    "mode": "local",
    "local_url": "http://127.0.0.1:8080",
    "remote_url": "https://aiservice.byd.com/yicellm-api/v1/chat/completions",
    "remote_api_key": "sk-kBP4BlJTUlhcaMVkfS2z7TIWlX7nVBnLtWRzDeHDG04mgOnM",
    "remote_model": "MiniMax-M2.5",
}

CONFIG_PATH = Path("agent_data/llm_config.json")


class LLMConfig:
    """LLM 配置管理器，从 JSON 文件加载/保存。"""

    def __init__(self, path: Path = CONFIG_PATH):
        self._path = path
        self._data = dict(DEFAULT_CONFIG)
        self.load()

    @property
    def mode(self) -> str:
        return self._data.get("mode", "local")

    @mode.setter
    def mode(self, value: str):
        self._data["mode"] = value

    @property
    def local_url(self) -> str:
        return self._data.get("local_url", "http://127.0.0.1:8080")

    @local_url.setter
    def local_url(self, value: str):
        self._data["local_url"] = value

    @property
    def remote_url(self) -> str:
        return self._data.get("remote_url", "")

    @remote_url.setter
    def remote_url(self, value: str):
        self._data["remote_url"] = value

    @property
    def remote_api_key(self) -> str:
        return self._data.get("remote_api_key", "")

    @remote_api_key.setter
    def remote_api_key(self, value: str):
        self._data["remote_api_key"] = value

    @property
    def remote_model(self) -> str:
        return self._data.get("remote_model", "")

    @remote_model.setter
    def remote_model(self, value: str):
        self._data["remote_model"] = value

    @property
    def is_local(self) -> bool:
        return self.mode == "local"

    def load(self):
        try:
            if self._path.exists():
                saved = json.loads(self._path.read_text(encoding="utf-8"))
                self._data.update(saved)
        except Exception:
            pass

    def save(self):
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def as_dict(self) -> dict:
        return dict(self._data)
