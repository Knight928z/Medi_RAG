from typing import Any, Dict, List

from storage.models import Document


class PgVectorStore:
    def __init__(self, session):
        self.session = session

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        payloads = [
            Document(
                source=item.get("source"),
                content=item["content"],
                metadata=item.get("metadata"),
                embedding=item.get("embedding"),
            )
            for item in documents
        ]
        self.session.add_all(payloads)
        self.session.commit()

    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        results = (
            self.session.query(Document)
            .order_by(Document.embedding.cosine_distance(query_embedding))
            .limit(top_k)
            .all()
        )
        return [
            {
                "id": str(item.id),
                "source": item.source,
                "content": item.content,
                "metadata": item.metadata,
            }
            for item in results
        ]
