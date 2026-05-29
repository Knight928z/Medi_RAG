from typing import Any, Dict, Iterable, List

import jieba
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> List[str]:
    return [token.strip() for token in jieba.cut(text) if token.strip()]


def build_bm25(corpus: Iterable[str]) -> BM25Okapi:
    tokenized = [tokenize(doc) for doc in corpus]
    return BM25Okapi(tokenized)


def bm25_search(
    documents: List[Dict[str, Any]],
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    if not documents:
        return []
    bm25 = build_bm25([doc["content"] for doc in documents])
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(zip(documents, scores), key=lambda item: item[1], reverse=True)
    results: List[Dict[str, Any]] = []
    for doc, score in ranked[:top_k]:
        results.append({**doc, "score": float(score), "retrieval": "bm25"})
    return results
