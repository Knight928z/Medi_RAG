from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from core.config import get_settings
from core.telemetry import trace_event
from memory.compression import MemoryCompressor, MemorySummarizer, truncate_text
from memory.schemas import MemoryBundle, MemoryItem
from memory.short_term import ShortTermWorkflowMemory
from retrieval.embeddings import EmbeddingProvider
from storage.models import MemoryEntry
from storage.repositories.memory_repo import MemoryRepository


def parse_uuid(value: Optional[str]) -> Optional[UUID]:
    if not value:
        return None
    try:
        return UUID(str(value))
    except ValueError:
        return None


def normalize_user_id(value: Optional[str]) -> Optional[UUID]:
    return parse_uuid(value)


class MemoryService:
    """Coordinates short-term, long-term, and semantic memory retrieval."""

    def __init__(self, session, redis_client=None):
        self.session = session
        self.redis_client = redis_client
        self.settings = get_settings()
        self.repo = MemoryRepository(session)
        self.compressor = MemoryCompressor(max_items=self.settings.memory_summary_max_items)
        self.summarizer = MemorySummarizer(max_items=self.settings.memory_summary_max_items)
        self._embedder: Optional[EmbeddingProvider] = None

    @property
    def embedder(self) -> EmbeddingProvider:
        if self._embedder is None:
            self._embedder = EmbeddingProvider(self.settings.default_embedding_model)
        return self._embedder

    def _short_term(self) -> Optional[ShortTermWorkflowMemory]:
        if self.redis_client is None:
            return None
        return ShortTermWorkflowMemory(
            self.redis_client,
            ttl_seconds=self.settings.memory_short_ttl_seconds,
        )

    @staticmethod
    def _iso(value) -> Optional[str]:
        return value.isoformat() if value is not None else None

    @staticmethod
    def _workflow_summary(state: Dict[str, Any]) -> str:
        parsed = state.get("parsed_report") or {}
        report_type = parsed.get("report_type") or "unknown_report"
        reasoning = state.get("reasoning") or {}
        reasoning_summary = reasoning.get("summary")
        if reasoning_summary:
            return truncate_text(str(reasoning_summary), 220)
        biomarkers = parsed.get("biomarkers") or []
        names = [
            item.get("name")
            for item in biomarkers
            if isinstance(item, dict) and item.get("name")
        ]
        if names:
            return truncate_text(f"{report_type}: " + ", ".join(names[:8]), 220)
        return f"{report_type}: workflow completed"

    @staticmethod
    def _report_item(report) -> MemoryItem:
        parsed = report.parsed_payload or {}
        notes = parsed.get("notes")
        summary = notes[0] if isinstance(notes, list) and notes else None
        return MemoryItem(
            layer="long_term",
            kind="historical_report",
            source=f"report:{report.id}",
            content={
                "report_type": parsed.get("report_type"),
                "biomarkers": parsed.get("biomarkers", [])[:12],
                "notes": parsed.get("notes", []),
            },
            summary=summary,
            created_at=MemoryService._iso(report.created_at),
        )

    @staticmethod
    def _entry_item(entry: MemoryEntry) -> MemoryItem:
        return MemoryItem(
            layer=entry.layer or "long_term",
            kind=entry.kind or "memory_entry",
            source=f"memory:{entry.id}",
            content=entry.content or {},
            summary=entry.summary,
            created_at=MemoryService._iso(entry.created_at),
            expires_at=MemoryService._iso(entry.expires_at),
        )

    @staticmethod
    def _workflow_item(run) -> MemoryItem:
        snapshot = run.state_snapshot or {}
        return MemoryItem(
            layer="historical_workflow",
            kind="workflow_lookup",
            source=f"workflow:{run.request_id}",
            content={
                "request_id": run.request_id,
                "status": run.status,
                "intent": snapshot.get("intent"),
                "patient_id": snapshot.get("patient_id"),
                "reasoning_summary": (snapshot.get("reasoning") or {}).get("summary"),
                "validation": snapshot.get("validation"),
            },
            summary=MemoryService._workflow_summary(snapshot),
            created_at=MemoryService._iso(run.created_at),
        )

    @staticmethod
    def _conversation_item(conversation) -> MemoryItem:
        return MemoryItem(
            layer="long_term",
            kind="historical_conversation",
            source=f"conversation:{conversation.id}",
            content={
                "title": conversation.title,
                "metadata": conversation.conversation_metadata or {},
            },
            summary=conversation.title,
            created_at=MemoryService._iso(conversation.created_at),
        )

    def get_short_term(self, request_id: Optional[str]) -> Optional[Dict[str, Any]]:
        store = self._short_term()
        if store is None:
            return None
        try:
            return store.get(request_id)
        except Exception as exc:  # noqa: BLE001
            trace_event("memory:short_term:get_failed", {"error": str(exc)})
            return None

    def store_short_term(self, request_id: str, state: Dict[str, Any]) -> None:
        store = self._short_term()
        if store is None:
            return
        try:
            compact_state = self.compressor.compress_content(state)
            store.set(request_id, compact_state)
        except Exception as exc:  # noqa: BLE001
            trace_event("memory:short_term:set_failed", {"error": str(exc)})

    async def semantic_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[MemoryItem]:
        if not user_id and not patient_id:
            return []
        if not query.strip():
            return []
        try:
            embedding = await self.embedder.embed_async([query])
            entries = await self.repo.semantic_search(
                embedding[0],
                user_id=normalize_user_id(user_id),
                patient_id=patient_id,
                top_k=top_k or self.settings.memory_semantic_top_k,
            )
            return [self._entry_item(entry) for entry in entries]
        except Exception as exc:  # noqa: BLE001
            trace_event("memory:semantic_search_failed", {"error": str(exc)})
            return []

    async def historical_workflow_lookup(
        self,
        user_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        workflows = await self.repo.list_historical_workflows(
            user_id=normalize_user_id(user_id),
            patient_id=patient_id,
            limit=limit,
        )
        return [self._workflow_item(run) for run in workflows]

    async def retrieve(
        self,
        request_id: str,
        report_text: str,
        user_id: Optional[str] = None,
        patient_id: Optional[str] = None,
    ) -> MemoryBundle:
        user_uuid = normalize_user_id(user_id)
        items: List[MemoryItem] = []

        short_state = self.get_short_term(request_id)
        if short_state:
            items.append(
                MemoryItem(
                    layer="short_term",
                    kind="current_session_state",
                    source=f"redis:{request_id}",
                    content=short_state,
                    summary="当前会话状态快照",
                )
            )

        entries = await self.repo.list_context(
            user_id=user_uuid,
            patient_id=patient_id,
            limit=self.settings.memory_long_term_limit,
        )
        items.extend(self._entry_item(entry) for entry in entries)

        reports = await self.repo.list_historical_reports(
            user_id=user_uuid,
            patient_id=patient_id,
            limit=self.settings.memory_summary_max_items,
        )
        items.extend(self._report_item(report) for report in reports)

        conversations = await self.repo.list_historical_conversations(
            user_id=user_uuid,
            limit=self.settings.memory_summary_max_items,
        )
        items.extend(self._conversation_item(item) for item in conversations)

        items.extend(
            await self.historical_workflow_lookup(
                user_id=user_id,
                patient_id=patient_id,
                limit=self.settings.memory_summary_max_items,
            )
        )
        items.extend(
            await self.semantic_search(
                report_text,
                user_id=user_id,
                patient_id=patient_id,
                top_k=self.settings.memory_semantic_top_k,
            )
        )

        compact_items, dropped_count = self.compressor.compress_items(items)
        summary = self.summarizer.summarize(items, dropped_count=dropped_count)
        return MemoryBundle(
            memory_context=compact_items,
            memory_summary=summary,
            memory_notes=(
                f"memory_layers={len({item.layer for item in items})}; "
                f"items={len(compact_items)}; dropped={dropped_count}"
            ),
        )

    async def persist_workflow_memory(
        self,
        state: Dict[str, Any],
        ttl_days: Optional[int] = None,
    ) -> List[MemoryEntry]:
        request_id = state.get("request_id")
        user_uuid = normalize_user_id(state.get("user_id"))
        patient_id = state.get("patient_id")
        conversation_uuid = parse_uuid(state.get("conversation_id"))
        if not user_uuid and not patient_id:
            return []

        expires_at = None
        effective_ttl_days = ttl_days
        if effective_ttl_days is None:
            effective_ttl_days = self.settings.memory_long_ttl_days
        if effective_ttl_days is not None:
            expires_at = datetime.utcnow() + timedelta(days=effective_ttl_days)

        summary = self._workflow_summary(state)
        base_content = {
            "request_id": request_id,
            "patient_id": patient_id,
            "intent": state.get("intent"),
            "parsed_report": state.get("parsed_report"),
            "reasoning": state.get("reasoning"),
            "validation": state.get("validation"),
            "memory_summary": state.get("memory_summary"),
        }
        compact_content = self.compressor.compress_content(base_content)

        entries = [
            MemoryEntry(
                user_id=user_uuid,
                patient_id=patient_id,
                conversation_id=conversation_uuid,
                request_id=request_id,
                layer="long_term",
                kind="workflow_summary",
                scope="patient" if patient_id else "user",
                content=compact_content,
                summary=summary,
                expires_at=expires_at,
                importance=2,
            )
        ]

        try:
            embedding = await self.embedder.embed_async([summary])
            entries.append(
                MemoryEntry(
                    user_id=user_uuid,
                    patient_id=patient_id,
                    conversation_id=conversation_uuid,
                    request_id=request_id,
                    layer="semantic",
                    kind="reasoning_trace",
                    scope="patient" if patient_id else "user",
                    content={
                        "request_id": request_id,
                        "summary": summary,
                        "reasoning": self.compressor.compress_content(state.get("reasoning") or {}),
                    },
                    summary=summary,
                    embedding=embedding[0],
                    expires_at=expires_at,
                    importance=3,
                )
            )
        except Exception as exc:  # noqa: BLE001
            trace_event("memory:persist_embedding_failed", {"error": str(exc)})

        created = await self.repo.create_many(entries)
        if request_id:
            self.store_short_term(request_id, state)
        return created
