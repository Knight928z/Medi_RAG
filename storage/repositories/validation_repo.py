from typing import List, Optional
from uuid import UUID

from sqlalchemy import select

from storage.models import ValidationHistory


class ValidationHistoryRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, entry: ValidationHistory) -> ValidationHistory:
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def create_many(self, entries: List[ValidationHistory]) -> List[ValidationHistory]:
        if not entries:
            return []
        self.session.add_all(entries)
        await self.session.commit()
        return entries

    async def list_by_request_id(self, request_id: str) -> List[ValidationHistory]:
        result = await self.session.execute(
            select(ValidationHistory)
            .where(ValidationHistory.request_id == request_id)
            .order_by(ValidationHistory.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_for_dashboard(
        self,
        user_id: Optional[UUID] = None,
        patient_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ValidationHistory]:
        filters = []
        if user_id is not None:
            filters.append(ValidationHistory.user_id == user_id)
        if patient_id:
            filters.append(ValidationHistory.patient_id == patient_id)
        query = select(ValidationHistory)
        if filters:
            query = query.where(*filters)
        result = await self.session.execute(
            query.order_by(ValidationHistory.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
