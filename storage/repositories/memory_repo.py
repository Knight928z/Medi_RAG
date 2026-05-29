from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select

from storage.models import Conversation, MemoryEntry, Report, WorkflowRun


class MemoryRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, entry: MemoryEntry) -> MemoryEntry:
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def create_many(self, entries: List[MemoryEntry]) -> List[MemoryEntry]:
        if not entries:
            return []
        self.session.add_all(entries)
        await self.session.commit()
        return entries

    @staticmethod
    def _identity_filter(user_id: Optional[UUID], patient_id: Optional[str]):
        filters = []
        if user_id is not None:
            filters.append(MemoryEntry.user_id == user_id)
        if patient_id:
            filters.append(MemoryEntry.patient_id == patient_id)
        if not filters:
            return None
        return or_(*filters)

    @staticmethod
    def _active_filter(include_expired: bool = False):
        if include_expired:
            return None
        now = datetime.utcnow()
        return or_(MemoryEntry.expires_at.is_(None), MemoryEntry.expires_at > now)

    async def list_by_patient(
        self,
        patient_id: str,
        limit: int = 50,
        include_expired: bool = False,
    ) -> List[MemoryEntry]:
        filters = [MemoryEntry.patient_id == patient_id]
        active_filter = self._active_filter(include_expired)
        if active_filter is not None:
            filters.append(active_filter)
        result = await self.session.execute(
            select(MemoryEntry)
            .where(and_(*filters))
            .order_by(MemoryEntry.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_context(
        self,
        user_id: Optional[UUID] = None,
        patient_id: Optional[str] = None,
        limit: int = 50,
        include_expired: bool = False,
    ) -> List[MemoryEntry]:
        identity_filter = self._identity_filter(user_id, patient_id)
        if identity_filter is None:
            return []
        filters = [identity_filter]
        active_filter = self._active_filter(include_expired)
        if active_filter is not None:
            filters.append(active_filter)
        result = await self.session.execute(
            select(MemoryEntry)
            .where(and_(*filters))
            .order_by(MemoryEntry.importance.desc(), MemoryEntry.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def semantic_search(
        self,
        query_embedding: List[float],
        user_id: Optional[UUID] = None,
        patient_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[MemoryEntry]:
        identity_filter = self._identity_filter(user_id, patient_id)
        if identity_filter is None:
            return []
        active_filter = self._active_filter()
        filters = [
            identity_filter,
            MemoryEntry.embedding.is_not(None),
            MemoryEntry.layer == "semantic",
        ]
        if active_filter is not None:
            filters.append(active_filter)
        result = await self.session.execute(
            select(MemoryEntry)
            .where(and_(*filters))
            .order_by(MemoryEntry.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        return list(result.scalars().all())

    async def list_historical_reports(
        self,
        user_id: Optional[UUID] = None,
        patient_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Report]:
        filters = []
        if user_id is not None:
            filters.append(Report.user_id == user_id)
        if patient_id:
            filters.append(Report.patient_id == patient_id)
        if not filters:
            return []
        result = await self.session.execute(
            select(Report)
            .where(or_(*filters))
            .order_by(Report.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_historical_conversations(
        self,
        user_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> List[Conversation]:
        if user_id is None:
            return []
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_historical_workflows(
        self,
        user_id: Optional[UUID] = None,
        patient_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[WorkflowRun]:
        filters = []
        if user_id is not None:
            filters.append(WorkflowRun.user_id == user_id)
        if patient_id:
            filters.append(WorkflowRun.state_snapshot["patient_id"].astext == patient_id)
        if not filters:
            return []
        result = await self.session.execute(
            select(WorkflowRun)
            .where(or_(*filters))
            .order_by(WorkflowRun.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def expire_entries(self, now: Optional[datetime] = None) -> int:
        cutoff = now or datetime.utcnow()
        result = await self.session.execute(
            select(MemoryEntry).where(
                MemoryEntry.expires_at.is_not(None),
                MemoryEntry.expires_at <= cutoff,
            )
        )
        entries = list(result.scalars().all())
        for entry in entries:
            await self.session.delete(entry)
        await self.session.commit()
        return len(entries)
