"""
Link UI — 입력 추출 (단계별 추적)
"""

from __future__ import annotations

from pathlib import Path

from deconstructor.web.extract import (
    ExtractedSource,
    assert_not_self_ui_url,
    _DOC_SUMMARIZE_THRESHOLD,
    _URL_PROMPT,
    _DOC_SUMMARIZE_PROMPT,
    _fetch_url_bytes,
    _html_to_text,
    _maybe_summarize,
    _read_docx,
    _read_pdf,
    _read_plain,
    _summarize_with_llm,
    _URL_RE,
    detect_mime,
    from_image,
    from_text,
    is_image_file,
)
from deconstructor.web.link_steps import LinkStepTracker


def _extract_url_tracked(tracker: LinkStepTracker, n: int, url: str) -> ExtractedSource:
    base = f"S2-URL-{n}"
    url = url.strip()
    assert_not_self_ui_url(url)
    if not _URL_RE.match(url):
        raise ValueError(f"URL 형식이 아닙니다: {url}")

    tracker.start(f"{base}-FETCH", "URL HTTP 다운로드", url[:80])
    data, ctype = _fetch_url_bytes(url)
    tracker.ok(f"{base}-FETCH", ctype)

    lower_url = url.lower()
    tracker.start(f"{base}-PARSE", "콘텐츠 파싱", ctype)
    if "pdf" in ctype or lower_url.endswith(".pdf"):
        text = _read_pdf(data)
    elif ctype.startswith("image/"):
        tracker.ok(f"{base}-PARSE", "image → Vision")
        tracker.start(f"{base}-VISION", "Gemini 이미지 OCR")
        text = from_image(data, ctype, label=url)
        tracker.ok(f"{base}-VISION", f"{len(text)}자")
        return ExtractedSource("url", url, text)
    elif "html" in ctype or lower_url.endswith((".html", ".htm")):
        text = _html_to_text(data)
        if len(text) < 80:
            raise ValueError(f"URL에서 본문을 거의 추출하지 못했습니다: {url}")
        tracker.ok(f"{base}-PARSE", f"html {len(text)}자")
        tracker.start(f"{base}-LLM", "Gemini HTML 요약")
        text = _summarize_with_llm(_URL_PROMPT, text)
        tracker.ok(f"{base}-LLM", f"{len(text)}자")
        return ExtractedSource("url", url, text)
    elif ctype.startswith("text/") or lower_url.endswith((".txt", ".md", ".csv")):
        text = _read_plain(data, url)
    else:
        text = _read_plain(data, url)

    text = text.strip()
    if not text:
        raise ValueError(f"URL에서 텍스트를 추출하지 못했습니다: {url}")
    tracker.ok(f"{base}-PARSE", f"{len(text)}자")

    if len(text) > _DOC_SUMMARIZE_THRESHOLD:
        tracker.start(f"{base}-LLM", "Gemini 문서 요약")
        text = _summarize_with_llm(_DOC_SUMMARIZE_PROMPT, text)
        tracker.ok(f"{base}-LLM", f"{len(text)}자")
    else:
        text = text[:12000]

    return ExtractedSource("url", url, text)


def _extract_document_tracked(
    tracker: LinkStepTracker, n: int, fname: str, data: bytes, mime: str, hint: str
) -> ExtractedSource:
    base = f"S2-DOC-{n}"
    mime = mime or detect_mime(fname)
    name = (fname or "").lower()
    ext = Path(name).suffix

    tracker.start(f"{base}-READ", "파일 바이너리 읽기", f"{fname} ({len(data)} bytes)")
    if ext in {".txt", ".md", ".csv", ".log"} or mime.startswith("text/"):
        text = _read_plain(data, fname)
        kind = "document"
        tracker.ok(f"{base}-READ", f"plain {len(text)}자")
    elif ext == ".pdf" or mime == "application/pdf":
        tracker.ok(f"{base}-READ", "pdf")
        tracker.start(f"{base}-PDF", "pypdf 텍스트 추출")
        text = _read_pdf(data)
        tracker.ok(f"{base}-PDF", f"{len(text)}자")
        kind = "document"
    elif ext in {".docx"} or "wordprocessingml" in mime:
        tracker.ok(f"{base}-READ", "docx")
        tracker.start(f"{base}-DOCX", "python-docx 추출")
        text = _read_docx(data)
        tracker.ok(f"{base}-DOCX", f"{len(text)}자")
        kind = "document"
    elif hint == "auto":
        text = _read_plain(data, fname)
        kind = "document"
        tracker.ok(f"{base}-READ", f"fallback {len(text)}자")
    else:
        raise ValueError(f"지원하지 않는 형식입니다: {ext or mime or fname}")

    text = text.strip()
    if not text:
        raise ValueError(f"문서에서 텍스트를 추출하지 못했습니다: {fname}")

    if len(text) > _DOC_SUMMARIZE_THRESHOLD:
        tracker.start(f"{base}-LLM", "Gemini 요약 (긴 문서)")
        text = _summarize_with_llm(_DOC_SUMMARIZE_PROMPT, text)
        tracker.ok(f"{base}-LLM", f"{len(text)}자")

    return ExtractedSource(kind, fname, text)


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
            out.append(_extract_url_tracked(tracker, url_n, block.strip()))
        else:
            text = from_text(block)
            tracker.ok(step, f"{len(text)}자")
            out.append(ExtractedSource("text", f"텍스트 #{i}", text))

    for url in urls or []:
        url_n += 1
        out.append(_extract_url_tracked(tracker, url_n, url))

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
            out.append(_extract_document_tracked(tracker, doc_n, fname, data, mime, hint))
        else:
            raise ValueError(f"알 수 없는 파일 종류: {fname}")

    if not out:
        raise ValueError("분석할 입력이 없습니다. 텍스트·링크·파일 중 하나 이상 추가하세요.")

    tracker.start("S2-EXTRACT-DONE", "추출 완료", f"{len(out)}건")
    tracker.ok("S2-EXTRACT-DONE")
    return out
