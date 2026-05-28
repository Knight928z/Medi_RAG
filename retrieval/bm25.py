from typing import List

from rank_bm25 import BM25Okapi


def build_bm25(corpus: List[List[str]]) -> BM25Okapi:
    return BM25Okapi(corpus)
