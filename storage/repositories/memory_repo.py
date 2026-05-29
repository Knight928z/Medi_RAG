from typing import List

from sqlalchemy import select

from storage.models import MemoryEntry


class MemoryRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, entry: MemoryEntry) -> MemoryEntry:
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def list_by_patient(self, patient_id: str) -> List[MemoryEntry]:
        result = await self.session.execute(
            select(MemoryEntry)
            .where(MemoryEntry.patient_id == patient_id)
            .order_by(MemoryEntry.created_at.desc())
        )
        return list(result.scalars().all())
