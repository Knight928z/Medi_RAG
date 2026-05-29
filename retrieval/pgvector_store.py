from typing import Any, Dict, List

from sqlalchemy import select

from storage.models import Document


class PgVectorStore:
    def __init__(self, session):
        self.session = session

    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        payloads = [
            Document(
                source=item.get("source"),
                source_type=item.get("source_type"),
                content=item["content"],
                document_metadata=item.get("metadata"),
                embedding=item.get("embedding"),
                chunk_id=item.get("chunk_id"),
                chunk_index=item.get("chunk_index"),
                page_number=item.get("page_number"),
                content_hash=item.get("content_hash"),
                created_at=item.get("created_at"),
            )
            for item in documents
        ]
        self.session.add_all(payloads)
        await self.session.commit()

    async def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            select(Document)
            .order_by(Document.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        documents = result.scalars().all()
        return [
            {
                "id": str(item.id),
                "chunk_id": item.chunk_id,
                "source": item.source,
                "source_type": item.source_type,
                "chunk_index": item.chunk_index,
                "page_number": item.page_number,
                "content": item.content,
                "metadata": item.document_metadata,
                "created_at": item.created_at.isoformat(),
                "retrieval": "vector",
            }
            for item in documents
        ]
