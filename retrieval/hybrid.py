from typing import Any, Dict, List


def hybrid_search(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """占位: 简单合并结果，后续加入加权排序。"""
    combined = vector_results + bm25_results
    return combined[:top_k]
