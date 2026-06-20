"""
문서 ingest — 요약 없이 청크 분해 (완성품 → 부스러기 1단계)

STAGE 0-1: β-1 (압축≠분해), β-2 (청크=Deconstruct 1회 입력 상한)
Sprint 1 (G-ING-META): chunk_id via expand_document_sources (AC-ING-05)
See ``docs/design/STAGE-0-1-product-definition.md``
"""

from __future__ import annotations

import re

DOC_CHUNK_CHARS = 8_000
DOC_CHUNK_OVERLAP = 400
DOC_CHUNK_MIN = 200


def chunk_text(
    text: str,
    *,
    max_chars: int = DOC_CHUNK_CHARS,
    overlap: int = DOC_CHUNK_OVERLAP,
) -> list[str]:
    """
    긴 원문을 Deconstruct용 청크로 분할.

    - ``max_chars`` 이하면 단일 청크
    - 가능하면 빈 줄(문단) 경계에서 자름
    - 청크 경계에 ``overlap`` 문자 재사용 (문맥 단절 완화)
    """
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    def flush() -> None:
        nonlocal current, current_len
        if not current:
            return
        blob = "\n\n".join(current).strip()
        if blob:
            chunks.append(blob)
        current = []
        current_len = 0

    for para in paragraphs:
        para_len = len(para) + (2 if current else 0)
        if len(para) > max_chars:
            flush()
            chunks.extend(_split_hard(para, max_chars=max_chars, overlap=overlap))
            continue
        if current_len + para_len > max_chars and current:
            flush()
        current.append(para)
        current_len += para_len

    flush()

    if len(chunks) <= 1:
        return chunks or [text[:max_chars]]

    if overlap > 0:
        merged: list[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-overlap:].strip()
            if tail and not chunks[i].startswith(tail):
                merged.append(f"{tail}\n\n{chunks[i]}")
            else:
                merged.append(chunks[i])
        chunks = merged

    return chunks


def _split_hard(text: str, *, max_chars: int, overlap: int) -> list[str]:
    out: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        out.append(text[start:end].strip())
        if end >= n:
            break
        start = max(end - overlap, start + DOC_CHUNK_MIN)
    return [c for c in out if c]


def chunk_pdf_page_texts(
    pages: list[str],
    *,
    max_chars: int = DOC_CHUNK_CHARS,
) -> list[tuple[str, str]]:
    """페이지별 텍스트 → (라벨 접미사, 청크 본문). 예: ``p.1-3``."""
    if not pages:
        return []

    nonempty: list[tuple[int, str]] = [
        (i + 1, p.strip()) for i, p in enumerate(pages) if p and p.strip()
    ]
    if not nonempty:
        return []

    chunks: list[tuple[str, str]] = []
    batch_pages: list[int] = []
    batch_parts: list[str] = []
    batch_len = 0

    def flush_batch() -> None:
        nonlocal batch_pages, batch_parts, batch_len
        if not batch_parts:
            return
        label = (
            f"p.{batch_pages[0]}"
            if len(batch_pages) == 1
            else f"p.{batch_pages[0]}-{batch_pages[-1]}"
        )
        chunks.append((label, "\n\n".join(batch_parts)))
        batch_pages = []
        batch_parts = []
        batch_len = 0

    for page_no, page_text in nonempty:
        add_len = len(page_text) + (2 if batch_parts else 0)
        if batch_parts and batch_len + add_len > max_chars:
            flush_batch()
        if len(page_text) > max_chars:
            flush_batch()
            for piece in chunk_text(page_text, max_chars=max_chars, overlap=0):
                chunks.append((f"p.{page_no}", piece))
            continue
        batch_pages.append(page_no)
        batch_parts.append(page_text)
        batch_len += add_len

    flush_batch()
    return chunks
