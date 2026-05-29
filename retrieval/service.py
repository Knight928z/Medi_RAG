from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from core.config import get_settings
from llm.router import LLMRouter
from retrieval.bm25 import bm25_search
from retrieval.embeddings import EmbeddingProvider
from retrieval.hybrid import hybrid_search
from retrieval.pgvector_store import PgVectorStore
from storage.repositories.document_repo import DocumentRepository


class RetrievalService:
    """无状态检索服务：每次调用都从数据库拉取必要数据。"""

    def __init__(self, session):
        self.session = session
        self.settings = get_settings()
        self.embedder = EmbeddingProvider(self.settings.default_embedding_model)
        self.llm_router = LLMRouter()

    async def _rewrite_query(self, query: str) -> str:
        if not self.settings.retrieval_query_rewrite:
            return query
        prompt = (
            "你是医疗检索助手，请将用户问题改写为更适合检索的中文关键词短语，"
            "只输出改写后的文本：\n" + query
        )
        response = await asyncio.to_thread(self.llm_router.generate, prompt)
        return response.get("response", query).strip() or query

    async def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        effective_top_k = top_k or self.settings.retrieval_top_k
        rewritten = await self._rewrite_query(query)

        query_embedding = await self.embedder.embed_async([rewritten])
        vector_store = PgVectorStore(self.session)
        vector_results = await vector_store.similarity_search(
            query_embedding[0],
            top_k=effective_top_k,
        )

        repo = DocumentRepository(self.session)
        docs = await repo.list_for_bm25(limit=self.settings.retrieval_bm25_limit)
        bm25_results = bm25_search(
            [
                {
                    "id": str(doc.id),
                    "chunk_id": doc.chunk_id,
                    "source": doc.source,
                    "source_type": doc.source_type,
                    "chunk_index": doc.chunk_index,
                    "page_number": doc.page_number,
                    "content": doc.content,
                    "metadata": doc.document_metadata,
                    "created_at": doc.created_at.isoformat(),
                }
                for doc in docs
            ],
            rewritten,
            top_k=effective_top_k,
        )

        combined = hybrid_search(vector_results, bm25_results, top_k=effective_top_k)
        for item in combined:
            item["citation"] = {
                "source": item.get("source"),
                "source_type": item.get("source_type"),
                "chunk_id": item.get("chunk_id"),
                "chunk_index": item.get("chunk_index"),
                "page_number": item.get("page_number"),
            }
        return combined
