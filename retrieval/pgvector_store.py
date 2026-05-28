from typing import Any, Dict, List


class PgVectorStore:
    def __init__(self, session):
        self.session = session

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """占位: 后续接入 pgvector 写入逻辑。"""
        return None

    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """占位: 后续接入 pgvector 相似度检索。"""
        return []
