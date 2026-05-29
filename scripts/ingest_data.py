import argparse
from pathlib import Path
from typing import List

from core.config import get_settings
from retrieval.embeddings import EmbeddingProvider
from retrieval.pgvector_store import PgVectorStore
from storage.database import get_session


def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    chunks: List[str] = []
    buffer: List[str] = []
    current_len = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        if current_len + len(line) > max_chars and buffer:
            chunks.append(" ".join(buffer))
            buffer = [line]
            current_len = len(line)
        else:
            buffer.append(line)
            current_len += len(line)
    if buffer:
        chunks.append(" ".join(buffer))
    return chunks


def load_documents(data_dir: Path, max_chars: int) -> List[dict]:
    documents: List[dict] = []
    for path in data_dir.glob("**/*"):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(content, max_chars=max_chars)
        for idx, chunk in enumerate(chunks):
            documents.append(
                {
                    "source": str(path.relative_to(data_dir)),
                    "content": chunk,
                    "metadata": {"chunk_index": idx},
                }
            )
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge base files into pgvector")
    parser.add_argument("--data-dir", default="./data", help="知识库目录")
    parser.add_argument("--max-chars", type=int, default=800, help="每段最大字符数")
    args = parser.parse_args()

    settings = get_settings()
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise SystemExit(f"数据目录不存在: {data_dir}")

    documents = load_documents(data_dir, max_chars=args.max_chars)
    if not documents:
        print("未发现可入库的文档")
        return

    embedder = EmbeddingProvider(settings.default_embedding_model)
    embeddings = embedder.embed([doc["content"] for doc in documents])
    for doc, vector in zip(documents, embeddings):
        doc["embedding"] = vector

    with get_session(settings.database_url) as session:
        store = PgVectorStore(session)
        store.add_documents(documents)

    print(f"已入库 {len(documents)} 条文档片段")


if __name__ == "__main__":
    main()
