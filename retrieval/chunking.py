from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Dict, Iterable, List, Optional


def _hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    source: str,
    source_type: str,
    page_number: Optional[int] = None,
) -> List[Dict[str, object]]:
    chunks: List[Dict[str, object]] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        content = text[start:end].strip()
        if content:
            chunk_id = str(uuid.uuid4())
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "content": content,
                    "chunk_index": len(chunks),
                    "source": source,
                    "source_type": source_type,
                    "page_number": page_number,
                    "offset_start": start,
                    "offset_end": end,
                    "content_hash": _hash_content(content),
                    "created_at": datetime.utcnow(),
                }
            )
        if end == length:
            break
        start = max(0, end - chunk_overlap)
    return chunks


def chunk_documents(
    texts: Iterable[Dict[str, object]],
    chunk_size: int,
    chunk_overlap: int,
) -> List[Dict[str, object]]:
    all_chunks: List[Dict[str, object]] = []
    for item in texts:
        chunks = chunk_text(
            text=str(item["content"]),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            source=str(item["source"]),
            source_type=str(item["source_type"]),
            page_number=item.get("page_number"),
        )
        for chunk in chunks:
            metadata = {**item.get("metadata", {})}
            metadata.update({"total_chunks": len(chunks)})
            chunk["metadata"] = metadata
            all_chunks.append(chunk)
    return all_chunks
