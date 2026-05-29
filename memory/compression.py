from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from memory.schemas import MemoryItem, MemorySummary


SENSITIVE_OR_EXPANSIVE_KEYS = {
    "raw_text",
    "report_text",
    "source_text",
    "stream_buffer",
    "trace",
}


def truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


class MemoryCompressor:
    """Keeps memory payloads compact enough to pass between agents."""

    def __init__(self, max_items: int = 8, max_text_chars: int = 480):
        self.max_items = max_items
        self.max_text_chars = max_text_chars

    def compress_content(self, value: Any) -> Any:
        if isinstance(value, str):
            return truncate_text(value, self.max_text_chars)
        if isinstance(value, list):
            return [self.compress_content(item) for item in value[: self.max_items]]
        if isinstance(value, dict):
            compact: Dict[str, Any] = {}
            for key, item in value.items():
                if key in SENSITIVE_OR_EXPANSIVE_KEYS:
                    continue
                compact[key] = self.compress_content(item)
            return compact
        return value

    def compress_items(self, items: Iterable[MemoryItem]) -> Tuple[List[Dict[str, Any]], int]:
        compact_items: List[Dict[str, Any]] = []
        dropped_count = 0
        for index, item in enumerate(items):
            if index >= self.max_items:
                dropped_count += 1
                continue
            payload = item.model_dump()
            payload["content"] = self.compress_content(payload.get("content", {}))
            if payload.get("summary"):
                payload["summary"] = truncate_text(payload["summary"], self.max_text_chars)
            compact_items.append(payload)
        return compact_items, dropped_count


class MemorySummarizer:
    """Deterministic summarizer used before optional LLM-based personalization."""

    def __init__(self, max_items: int = 8):
        self.max_items = max_items

    @staticmethod
    def _headline(item: MemoryItem) -> str:
        if item.summary:
            return item.summary
        content = item.content
        for key in ("title", "summary", "notes", "reasoning_summary", "report_type"):
            value = content.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return f"{item.kind} from {item.source}"

    def summarize(self, items: List[MemoryItem], dropped_count: int = 0) -> MemorySummary:
        selected = items[: self.max_items]
        pinned = [
            truncate_text(self._headline(item), 160)
            for item in selected
            if item.layer in {"long_term", "semantic"}
        ][: self.max_items]
        recent = [
            truncate_text(self._headline(item), 160)
            for item in selected
            if item.layer in {"short_term", "historical_workflow"}
        ][: self.max_items]
        summary_parts = pinned[:3] + recent[:2]
        summary = "；".join(summary_parts) if summary_parts else "未找到可用历史记忆。"
        return MemorySummary(
            summary=summary,
            pinned_facts=pinned,
            recent_changes=recent,
            item_count=len(items),
            dropped_count=dropped_count,
        )
