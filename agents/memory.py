from typing import Any, Dict

from agents.base import BaseAgent
from core.config import get_settings
from memory.compression import MemoryCompressor, MemorySummarizer
from memory.schemas import MemoryItem


class MemoryAgent(BaseAgent):
    name = "memory"

    def __init__(self) -> None:
        settings = get_settings()
        self.compressor = MemoryCompressor(max_items=settings.memory_summary_max_items)
        self.summarizer = MemorySummarizer(max_items=settings.memory_summary_max_items)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        items = []
        for item in state.get("memory_context", []):
            try:
                items.append(MemoryItem.model_validate(item))
            except Exception:  # noqa: BLE001 - malformed memory is ignored, not expanded
                continue
        compact_items, dropped_count = self.compressor.compress_items(items)
        summary = self.summarizer.summarize(items, dropped_count=dropped_count)
        return {
            "memory_context": compact_items,
            "memory_summary": summary.model_dump(),
            "memory_notes": f"已压缩记忆上下文，保留 {len(compact_items)} 条，丢弃 {dropped_count} 条。",
        }
