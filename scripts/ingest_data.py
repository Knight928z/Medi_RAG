import argparse
import asyncio
from pathlib import Path

from core.config import get_settings
from retrieval.chunking import chunk_documents
from retrieval.embeddings import EmbeddingProvider
from retrieval.loaders import load_documents
from retrieval.pgvector_store import PgVectorStore
from storage.database import get_async_session


async def ingest(data_dir: Path) -> int:
    settings = get_settings()
    documents = load_documents(data_dir.glob("**/*"))
    if not documents:
        return 0

    chunks = chunk_documents(
        documents,
        chunk_size=settings.retrieval_chunk_size,
        chunk_overlap=settings.retrieval_chunk_overlap,
    )
    embedder = EmbeddingProvider(settings.default_embedding_model)
    embeddings = await embedder.embed_async([chunk["content"] for chunk in chunks])
    for chunk, vector in zip(chunks, embeddings):
        chunk["embedding"] = vector
        chunk["source"] = str(Path(chunk["source"]).relative_to(data_dir))

    async with get_async_session(settings.database_url) as session:
        store = PgVectorStore(session)
        await store.add_documents(chunks)
    return len(chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge base files into pgvector")
    parser.add_argument("--data-dir", default="./data", help="知识库目录")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise SystemExit(f"数据目录不存在: {data_dir}")

    count = asyncio.run(ingest(data_dir))
    if count == 0:
        print("未发现可入库的文档")
        return
    print(f"已入库 {count} 条文档片段")


if __name__ == "__main__":
    main()
