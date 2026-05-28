from typing import List

from storage.models import MemoryEntry


class MemoryRepository:
    def __init__(self, session):
        self.session = session

    def create(self, entry: MemoryEntry) -> MemoryEntry:
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def list_by_patient(self, patient_id: str) -> List[MemoryEntry]:
        return (
            self.session.query(MemoryEntry)
            .filter(MemoryEntry.patient_id == patient_id)
            .order_by(MemoryEntry.created_at.desc())
            .all()
        )
