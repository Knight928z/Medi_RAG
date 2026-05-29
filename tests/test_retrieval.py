from retrieval.chunking import chunk_text
from retrieval.hybrid import hybrid_search


def test_chunking_metadata():
    chunks = chunk_text(
        "这是一个用于测试的文本。" * 20,
        chunk_size=50,
        chunk_overlap=10,
        source="demo.md",
        source_type="md",
    )
    assert chunks
    first = chunks[0]
    assert first["source"] == "demo.md"
    assert first["chunk_id"]


def test_hybrid_rrf():
    vector_results = [
        {"chunk_id": "c1", "content": "a"},
        {"chunk_id": "c2", "content": "b"},
    ]
    bm25_results = [{"chunk_id": "c2", "content": "b"}]
    results = hybrid_search(vector_results, bm25_results, top_k=2)
    assert len(results) == 2
