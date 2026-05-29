from typing import Any, Dict, List


def _rrf_rank(results: List[Dict[str, Any]], weight: float, k: int = 60) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for rank, item in enumerate(results, start=1):
        key = item.get("chunk_id") or item.get("id")
        if not key:
            continue
        scores[key] = scores.get(key, 0.0) + weight * (1.0 / (k + rank))
    return scores


def hybrid_search(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    top_k: int = 5,
    vector_weight: float = 1.0,
    bm25_weight: float = 0.7,
) -> List[Dict[str, Any]]:
    """使用 RRF 融合向量与关键词结果，并保留原始证据字段。"""
    score_map = _rrf_rank(vector_results, vector_weight)
    bm25_score_map = _rrf_rank(bm25_results, bm25_weight)
    for key, score in bm25_score_map.items():
        score_map[key] = score_map.get(key, 0.0) + score

    combined = {item.get("chunk_id") or item.get("id"): item for item in vector_results + bm25_results}
    ranked = sorted(
        ((key, score_map.get(key, 0.0)) for key in combined.keys()),
        key=lambda item: item[1],
        reverse=True,
    )
    results: List[Dict[str, Any]] = []
    for key, score in ranked[:top_k]:
        payload = {**combined[key]}
        payload["hybrid_score"] = float(score)
        results.append(payload)
    return results
