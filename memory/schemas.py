from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    layer: str
    kind: str
    source: str
    content: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    score: Optional[float] = None


class MemorySummary(BaseModel):
    summary: str
    pinned_facts: List[str] = Field(default_factory=list)
    recent_changes: List[str] = Field(default_factory=list)
    item_count: int = 0
    dropped_count: int = 0


class MemoryBundle(BaseModel):
    memory_context: List[Dict[str, Any]] = Field(default_factory=list)
    memory_summary: MemorySummary
    memory_notes: str
