from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from pypdf import PdfReader


def load_text(path: Path) -> List[Dict[str, object]]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    return [{"content": content, "source": str(path), "source_type": "txt"}]


def load_markdown(path: Path) -> List[Dict[str, object]]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    return [{"content": content, "source": str(path), "source_type": "md"}]


def load_pdf(path: Path) -> List[Dict[str, object]]:
    reader = PdfReader(str(path))
    pages: List[Dict[str, object]] = []
    for index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if not text.strip():
            continue
        pages.append(
            {
                "content": text,
                "source": str(path),
                "source_type": "pdf",
                "page_number": index + 1,
            }
        )
    return pages


def load_documents(paths: Iterable[Path]) -> List[Dict[str, object]]:
    documents: List[Dict[str, object]] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".txt":
            documents.extend(load_text(path))
        elif suffix == ".md":
            documents.extend(load_markdown(path))
        elif suffix == ".pdf":
            documents.extend(load_pdf(path))
    return documents
