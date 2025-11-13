from __future__ import annotations

from typing import Iterable, List


def chunk_text(text: str, *, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping chunks of up to chunk_size words."""
    if not text:
        return []

    words: List[str] = text.split()
    if not words:
        return []

    chunks: List[str] = []
    step = max(chunk_size - overlap, 1)
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            continue
        chunks.append(" ".join(chunk_words))
    return chunks

