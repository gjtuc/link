"""
Link UI — 입력 추출 (단계별 추적)
"""

from __future__ import annotations

from deconstructor.web.extract import (
    ExtractedSource,
    _fetch_url_bytes,
    document_sources_from_bytes,
    expand_document_sources,
    from_image,
    from_text,
    is_image_file,
    detect_mime,
    url_sources_from_fetch,
    _use_document_deconstruct_ingest,
    _DOC_SUMMARIZE_THRESHOLD,
)
from deconstructor.web.link_steps import LinkStepTracker


def _extract_url_tracked(tracker: LinkStepTracker, n: int, url: str) -> list[ExtractedSource]:
    base = f"S2-URL-{n}"
    url = url.strip()

    tracker.start(f"{base}-FETCH", "URL HTTP 다운로드", url[:80])
    data, ctype = _fetch_url_bytes(url)
    tracker.ok(f"{base}-FETCH", ctype)

    tracker.start(f"{base}-PARSE", "콘텐츠 파싱·청크", ctype)
    sources = url_sources_from_fetch(url, data, ctype)
    tracker.ok(f"{base}-PARSE", f"{len(sources)}건 · {sum(len(s.text) for s in sources)}자")
    return sources


def _extract_document_tracked(
    tracker: LinkStepTracker, n: int, fname: str, data: bytes, mime: str, hint: str
) -> list[ExtractedSource]:
    base = f"S2-DOC-{n}"
    mime = mime or detect_mime(fname)

    tracker.start(f"{base}-READ", "파일 읽기·청크 분해", f"{fname} ({len(data)} bytes)")
    try:
        sources = document_sources_from_bytes(data, fname, mime)
    except ValueError:
        if hint != "auto":
            raise
        from deconstructor.web.extract import _read_plain, _finalize_document_text

        text = _read_plain(data, fname).strip()
        sources = _finalize_document_text(fname, text)
    total_chars = sum(len(s.text) for s in sources)
    tracker.ok(f"{base}-READ", f"{len(sources)}청크 · {total_chars}자")
    return sources


def extract_batch_tracked(
    tracker: LinkStepTracker,
    *,
    text_blocks: list[str] | None = None,
    urls: list[str] | None = None,
    files: list[tuple[str, bytes, str, str]] | None = None,
) -> list[ExtractedSource]:
    """여러 입력 추출 — 항목·하위 단계마다 tracker 기록."""
    out: list[ExtractedSource] = []
    url_n = 0
    doc_n = 0

    for i, block in enumerate(text_blocks or [], start=1):
        step = f"S2-TEXT-{i}"
        tracker.start(step, f"텍스트 블록 #{i}")
        if block.strip().startswith(("http://", "https://")):
            url_n += 1
            tracker.ok(step, "URL 블록 → URL 추출")
            out.extend(_extract_url_tracked(tracker, url_n, block.strip()))
        else:
            text = from_text(block)
            if _use_document_deconstruct_ingest() and len(text) > _DOC_SUMMARIZE_THRESHOLD:
                pieces = expand_document_sources(f"텍스트 #{i}", text, kind="text")
                tracker.ok(step, f"{len(pieces)}청크 · {len(text)}자")
                out.extend(pieces)
            else:
                tracker.ok(step, f"{len(text)}자")
                out.append(ExtractedSource("text", f"텍스트 #{i}", text))

    for url in urls or []:
        url_n += 1
        out.extend(_extract_url_tracked(tracker, url_n, url))

    for fname, data, mime, hint in files or []:
        mime = mime or detect_mime(fname)
        if hint == "image" or (hint == "auto" and is_image_file(fname, mime)):
            img_n = sum(1 for s in out if s.kind == "image") + 1
            step = f"S2-IMG-{img_n}"
            tracker.start(step, "이미지 Vision 추출", fname)
            text = from_image(data, mime, label=fname)
            tracker.ok(step, f"{len(text)}자")
            out.append(ExtractedSource("image", fname, text))
        elif hint in ("document", "auto"):
            doc_n += 1
            out.extend(_extract_document_tracked(tracker, doc_n, fname, data, mime, hint))
        else:
            raise ValueError(f"알 수 없는 파일 종류: {fname}")

    if not out:
        raise ValueError("분석할 입력이 없습니다. 텍스트·링크·파일 중 하나 이상 추가하세요.")

    tracker.start("S2-EXTRACT-DONE", "추출 완료", f"{len(out)}청크")
    tracker.ok("S2-EXTRACT-DONE")
    return out
