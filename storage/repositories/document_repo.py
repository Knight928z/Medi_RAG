from typing import List

from sqlalchemy import select

from storage.models import Document


class DocumentRepository:
    def __init__(self, session):
        self.session = session

    async def bulk_create(self, documents: List[Document]) -> None:
        self.session.add_all(documents)
        await self.session.commit()

    async def list_for_bm25(self, limit: int = 2000) -> List[Document]:
        result = await self.session.execute(select(Document).limit(limit))
        return list(result.scalars().all())
