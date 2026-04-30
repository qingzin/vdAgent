"""
KnowledgeStore — 领域知识库存储

采用 Markdown + YAML frontmatter 格式,人类可读、可修正、中文优先。
存储在 agent_data/knowledge/ 目录下。

每个知识条目格式:
    ---
    category: chassis_tuning
    tags: [稳定杆, 侧倾]
    title: 稳定杆调校基本原则
    created: 2026-04-29
    updated: 2026-04-29
    ---
    # 标题
    Markdown 正文...
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _now_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _parse_frontmatter(text: str) -> tuple:
    """解析 YAML-like frontmatter。返回 (metadata_dict, body_text)。"""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    meta = {}
    for line in raw.strip().split("\n"):
        line = line.strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key == "tags":
            val = [t.strip().strip('"').strip("'") for t in val.strip("[]").split(",") if t.strip()]
        meta[key] = val
    body = text[m.end():]
    return meta, body


def _dump_frontmatter(meta: dict, body: str) -> str:
    """将 metadata 和 body 序列化为完整的 Markdown 文本。"""
    lines = ["---"]
    for key, val in meta.items():
        if key == "tags" and isinstance(val, list):
            tag_str = ", ".join(val)
            lines.append(f"tags: [{tag_str}]")
        else:
            lines.append(f"{key}: {val}")
    lines.append("---")
    lines.append("")
    lines.append(body.lstrip("\n"))
    return "\n".join(lines) + "\n"


class KnowledgeStore:
    """领域知识库的读写和检索。"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = str(Path(__file__).resolve().parent / "data")
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 写入
    # ------------------------------------------------------------------

    def save(self, filename: str, meta: dict, body: str) -> str:
        """保存一条知识条目。filename 不含路径、不含扩展名。"""
        meta.setdefault("created", _now_date())
        meta["updated"] = _now_date()
        filepath = self._resolve(filename)
        filepath.write_text(_dump_frontmatter(meta, body), encoding="utf-8")
        return str(filepath)

    def save_from_llm(self, title: str, category: str, body: str,
                      tags: list = None, source: str = "agent") -> str:
        """供 LLM action 调用的便捷写入。"""
        safe_name = re.sub(r"[^\w一-鿿\-]", "_", title)[:60]
        meta = {
            "title": title,
            "category": category,
            "tags": tags or [],
            "source": source,
        }
        return self.save(safe_name, meta, body)

    # ------------------------------------------------------------------
    # 读取
    # ------------------------------------------------------------------

    def load(self, filename: str) -> Optional[dict]:
        """读取单条知识,返回 {meta, body, filename}。"""
        filepath = self._resolve(filename)
        if not filepath.exists():
            return None
        text = filepath.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(text)
        return {"meta": meta, "body": body.strip(), "filename": filepath.stem}

    def list_all(self) -> List[dict]:
        """列出所有知识条目摘要(不含 body)。"""
        results = []
        for fp in sorted(self.base_dir.glob("*.md")):
            text = fp.read_text(encoding="utf-8")
            meta, _body = _parse_frontmatter(text)
            meta["filename"] = fp.stem
            results.append(meta)
        return results

    # ------------------------------------------------------------------
    # 检索
    # ------------------------------------------------------------------

    def search(self, keyword: str = None, category: str = None,
               tags: list = None, limit: int = 10) -> List[dict]:
        """按关键词/分类/标签检索,返回匹配条目(含摘要)。"""
        results = []
        needle = (keyword or "").lower()

        for fp in sorted(self.base_dir.glob("*.md")):
            text = fp.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(text)

            if category and meta.get("category") != category:
                continue
            if tags:
                entry_tags = meta.get("tags", [])
                if not any(t in entry_tags for t in tags):
                    continue
            if needle:
                title = str(meta.get("title", "")).lower()
                body_lower = body.lower()
                tag_str = " ".join(str(t) for t in meta.get("tags", [])).lower()
                haystack = f"{title} {tag_str} {body_lower}"
                if needle not in haystack:
                    continue

            # 返回摘要(前200字)
            summary = body.strip()[:200]
            results.append({
                "meta": meta,
                "summary": summary,
                "filename": fp.stem,
            })

        return results[:limit]

    # ------------------------------------------------------------------
    # 检索接口(供 LLM context 注入)
    # ------------------------------------------------------------------

    def search_for_context(self, keyword: str = None, category: str = None,
                           limit: int = 5) -> str:
        """返回适合注入 LLM 上下文的格式化文本。"""
        entries = self.search(keyword=keyword, category=category, limit=limit)
        if not entries:
            return "（未找到相关知识条目）"
        parts = []
        for e in entries:
            meta = e["meta"]
            title = meta.get("title", e["filename"])
            cat = meta.get("category", "")
            tags = meta.get("tags", [])
            tag_str = "、".join(tags) if tags else ""
            parts.append(
                f"【{title}】分类:{cat} 标签:{tag_str}\n{e['summary']}..."
            )
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _resolve(self, filename: str) -> Path:
        safe = filename.replace("\\", "/").rsplit("/", 1)[-1]
        if not safe.endswith(".md"):
            safe += ".md"
        return self.base_dir / safe
