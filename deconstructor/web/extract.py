"""
입력 추출 — 텍스트 / URL / 이미지 / 문서 → 파이프라인 헤드라인
================================================================

STAGE 0-1 (제품 계약) — Ingest
------------------------------
  - **완성품 → 부스러기 재료**: 서술을 Deconstruct에 넘기기 **전** 원문을 잃지 않는다.
  - **압축 ≠ 분해**: document 모드에서 LLM 2–5문장 요약 금지 (NG-1).
  - **因·과 crumb의 원천**: 여기서 나온 ``ExtractedSource.text`` 가 Deconstruct 입력.
  - 상세: ``docs/design/STAGE-0-1-product-definition.md`` (β-1~3, C-1, C-2)

모드 (``LINK_DOCUMENT_INGEST``)
------------------------------
  - ``document`` (기본): PDF/DOCX/긴 txt — 청크 분해, 요약 없음.
  - ``summarize`` (레거시): 뉴스용 2–5문장 요약 — 명시적 opt-in만.

뉴스 URL(HTML)·짧은 텍스트: 기존 요약·직접 입력 경로 유지 (α-2 부록).

STAGE 0-3 (Acceptance)
----------------------
  - AC-ING-01~04: ``document_sources_from_bytes``, ``expand_document_sources``
  - AC-NEG-01/02: tests/test_stage0_acceptance.py
  - See ``docs/design/STAGE-0-3-acceptance-criteria.md``

STAGE 0-5 (Roadmap) — Sprint 1 ✅
----------------------------------
  - SP1-META-*: ``ExtractedSource`` / ``AtomicFact`` / ``source_document_meta``
  - See ``docs/design/SPRINT-1-ingest-meta-spec.md``
"""

from __future__ import annotations

import base64
import io
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from langchain_core.messages import HumanMessage

from deconstructor.provenance.source_meta import (
    make_chunk_id,
    meta_from_extracted_fields,
    page_range_from_suffix,
)
from deconstructor.web.document_chunks import (
    DOC_CHUNK_CHARS,
    chunk_pdf_page_texts,
    chunk_text,
)

MAX_HEADLINE_CHARS = 12_000
_DOC_SUMMARIZE_THRESHOLD = 2_000
# PDF 페이지 상한 (0 = 무제한)
DOC_PDF_MAX_PAGES = int(os.getenv("DOC_PDF_MAX_PAGES", "100"))
# document | summarize — summarize 는 레거시 뉴스용
DOCUMENT_INGEST_MODE = os.getenv("LINK_DOCUMENT_INGEST", "document").lower()
_URL_RE = re.compile(r"^https?://", re.I)
_USER_AGENT = "Deconstructor/1.0 (local research UI)"

_IMAGE_PROMPT = (
    "Extract news headline or factual text suitable for causal event analysis from this image. "
    "Preserve timestamps and entity names. Korean/English mixed OK. Output plain text only, no commentary."
)

_URL_PROMPT = (
    "Extract the main factual news content from the following web page text for causal graph analysis. "
    "2-5 sentences, preserve times and entity names. Korean/English mixed OK. Plain text only.\n\n"
)

_DOC_SUMMARIZE_PROMPT = (
    "Summarize the following document into 2-5 short factual sentences suitable for causal graph analysis. "
    "Include times and entity names when present. Korean/English mixed OK. Plain text only.\n\n"
)

# Link UI 자기 자신 — HTML을 LLM이 "UI 안내문"으로 요약해 원문(원숭이 등)과 섞임
_SELF_UI_NETLOCS = frozenset({"127.0.0.1:8765", "localhost:8765"})


def is_deconstructor_self_url(url: str) -> bool:
    """메인 UI(/) URL — 뉴스 분석용이 아님."""
    try:
        p = urlparse(url.strip())
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    host = (p.netloc or "").lower()
    path = (p.path or "/").rstrip("/") or "/"
    return host in _SELF_UI_NETLOCS and path in ("/", "/index.html")


def assert_not_self_ui_url(url: str) -> None:
    if is_deconstructor_self_url(url):
        raise ValueError(
            "Deconstructor 메인 UI 주소(http://127.0.0.1:8765/)는 분석할 수 없습니다. "
            "뉴스·사실 문장을 텍스트 상자에 직접 입력하세요. (원숭이 문장 등)"
        )


@dataclass
class ExtractedSource:
    kind: str  # text | url | image | document
    label: str
    text: str
    source_file: str = ""
    page_range: str = ""
    chunk_id: str = ""
    chunk_index: int = 1
    chunk_total: int = 1
    document_page_count: int = 0

    def document_meta_dict(self) -> dict[str, str | int]:
        """Pipeline ``source_document_meta`` (Sprint 1, μ L-03)."""
        return meta_from_extracted_fields(
            source_file=self.source_file,
            page_range=self.page_range,
            chunk_id=self.chunk_id,
            chunk_index=self.chunk_index,
            chunk_total=self.chunk_total,
        ).to_state_dict()


def _content_to_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif "text" in block:
                    parts.append(str(block["text"]))
            else:
                parts.append(str(block))
        return "\n".join(p for p in parts if p)
    return str(content)


def _normalize(text) -> str:
    text = _content_to_text(text).strip()
    if len(text) > MAX_HEADLINE_CHARS:
        return text[:MAX_HEADLINE_CHARS]
    return text


def split_text_blocks(raw: str) -> list[str]:
    """빈 줄로 구분된 여러 텍스트 블록."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n+", raw or "") if b.strip()]
    return blocks


def split_urls(raw: str) -> list[str]:
    urls = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if _URL_RE.match(line):
            urls.append(line)
        else:
            raise ValueError(f"URL 형식이 아닙니다 (http/https 필요): {line}")
    return urls


def from_text(raw: str) -> str:
    text = _normalize(raw)
    if not text:
        raise ValueError("텍스트를 입력하세요.")
    return text


def _html_to_text(data: bytes) -> str:
    html = data.decode("utf-8", errors="replace")
    html = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", html)
    html = re.sub(r"(?is)<noscript[^>]*>.*?</noscript>", " ", html)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fetch_url_bytes(url: str, timeout: int = 30) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "application/octet-stream")
            return data, ctype.split(";")[0].strip().lower()
    except urllib.error.URLError as exc:
        raise ValueError(f"URL 접근 실패: {url} — {exc.reason}") from exc


def from_url(url: str) -> str:
    url = url.strip()
    assert_not_self_ui_url(url)
    if not _URL_RE.match(url):
        raise ValueError(f"URL 형식이 아닙니다: {url}")

    data, ctype = _fetch_url_bytes(url)
    lower_url = url.lower()

    if "pdf" in ctype or lower_url.endswith(".pdf"):
        text = _read_pdf(data)
    elif ctype.startswith("image/"):
        return from_image(data, ctype)
    elif "html" in ctype or lower_url.endswith((".html", ".htm")):
        text = _html_to_text(data)
        if len(text) < 80:
            raise ValueError(f"URL에서 본문을 거의 추출하지 못했습니다: {url}")
        return _summarize_with_llm(_URL_PROMPT, text)
    elif ctype.startswith("text/") or lower_url.endswith((".txt", ".md", ".csv")):
        text = _read_plain(data, url)
    else:
        # 알 수 없는 형식 — 텍스트 시도
        try:
            text = _read_plain(data, url)
        except ValueError:
            raise ValueError(f"지원하지 않는 URL 콘텐츠 형식: {ctype or url}") from None

    text = text.strip()
    if not text:
        raise ValueError(f"URL에서 텍스트를 추출하지 못했습니다: {url}")
    if _use_document_deconstruct_ingest():
        return text
    return _maybe_summarize(text)


def url_sources_from_fetch(url: str, data: bytes, ctype: str) -> list[ExtractedSource]:
    """URL 다운로드 결과 → ExtractedSource (PDF/긴 텍스트는 청크)."""
    url = url.strip()
    assert_not_self_ui_url(url)
    lower_url = url.lower()
    ctype = (ctype or "").split(";")[0].strip().lower()

    if "pdf" in ctype or lower_url.endswith(".pdf"):
        pages = _read_pdf_pages(data)
        if not any(p.strip() for p in pages):
            raise ValueError(f"URL에서 PDF 텍스트를 추출하지 못했습니다: {url}")
        if _use_document_deconstruct_ingest():
            page_chunks = chunk_pdf_page_texts(pages)
            return expand_document_sources(url, "", kind="url", page_chunks=page_chunks)
        return [ExtractedSource("url", url, _read_pdf(data))]

    if ctype.startswith("image/"):
        return [ExtractedSource("url", url, from_image(data, ctype, label=url))]

    if "html" in ctype or lower_url.endswith((".html", ".htm")):
        text = _html_to_text(data)
        if len(text) < 80:
            raise ValueError(f"URL에서 본문을 거의 추출하지 못했습니다: {url}")
        return [ExtractedSource("url", url, _summarize_with_llm(_URL_PROMPT, text))]

    if ctype.startswith("text/") or lower_url.endswith((".txt", ".md", ".csv")):
        text = _read_plain(data, url).strip()
    else:
        text = _read_plain(data, url).strip()

    if not text:
        raise ValueError(f"URL에서 텍스트를 추출하지 못했습니다: {url}")
    if _use_document_deconstruct_ingest() and len(text) > _DOC_SUMMARIZE_THRESHOLD:
        return expand_document_sources(url, text, kind="url")
    if len(text) > _DOC_SUMMARIZE_THRESHOLD:
        return [ExtractedSource("url", url, _summarize_with_llm(_DOC_SUMMARIZE_PROMPT, text))]
    return [ExtractedSource("url", url, _normalize(text))]


def from_image(data: bytes, mime: str, *, label: str = "image") -> str:
    if not data:
        raise ValueError(f"이미지가 비어 있습니다: {label}")
    mime = mime or "image/png"
    b64 = base64.standard_b64encode(data).decode("ascii")
    model = get_chat_model(tier="flash")
    msg = HumanMessage(
        content=[
            {"type": "text", "text": _IMAGE_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]
    )
    resp = model.invoke([msg])
    text = _normalize(getattr(resp, "content", str(resp)))
    if not text:
        raise ValueError(f"이미지에서 텍스트를 추출하지 못했습니다: {label}")
    return text


def _maybe_summarize(text: str) -> str:
    if len(text) <= _DOC_SUMMARIZE_THRESHOLD:
        return _normalize(text)
    return _summarize_with_llm(_DOC_SUMMARIZE_PROMPT, text)


def _read_pdf_pages(data: bytes) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("PDF 지원을 위해 pip install pypdf 가 필요합니다.") from exc
    reader = PdfReader(io.BytesIO(data))
    pages = reader.pages
    if DOC_PDF_MAX_PAGES > 0:
        pages = pages[:DOC_PDF_MAX_PAGES]
    return [(page.extract_text() or "") for page in pages]


def _read_pdf(data: bytes) -> str:
    return "\n\n".join(p for p in _read_pdf_pages(data) if p.strip()).strip()


def _read_docx(data: bytes) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise ValueError("Word 지원을 위해 pip install python-docx 가 필요합니다.") from exc
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()


def _read_plain(data: bytes, filename: str) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp949", "euc-kr"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"텍스트 인코딩을 읽을 수 없습니다: {filename}")


def _summarize_with_llm(prompt: str, text: str) -> str:
    model = get_chat_model(tier="pro")
    resp = model.invoke([HumanMessage(content=prompt + text[:MAX_HEADLINE_CHARS])])
    out = _normalize(getattr(resp, "content", str(resp)))
    return out or _normalize(text[:_DOC_SUMMARIZE_THRESHOLD])


def _use_document_deconstruct_ingest() -> bool:
    return DOCUMENT_INGEST_MODE in ("document", "deconstruct", "chunk")


def expand_document_sources(
    label: str,
    text: str,
    *,
    kind: str = "document",
    source_file: str | None = None,
    page_chunks: list[tuple[str, str]] | None = None,
    document_page_count: int = 0,
) -> list[ExtractedSource]:
    """원문 1건 → Deconstruct용 ExtractedSource N건 (요약 없음)."""
    file_ref = (source_file or label).strip()

    def _one(body: str, display_label: str, *, suffix: str, idx: int, total: int) -> ExtractedSource:
        return ExtractedSource(
            kind=kind,
            label=display_label,
            text=body,
            source_file=file_ref,
            page_range=page_range_from_suffix(suffix),
            chunk_id=make_chunk_id(file_ref, idx, total),
            chunk_index=idx,
            chunk_total=total,
            document_page_count=document_page_count,
        )

    if page_chunks:
        total = len(page_chunks)
        if total == 1:
            suffix, body = page_chunks[0]
            return [_one(body, f"{label} ({suffix})", suffix=suffix, idx=1, total=1)]
        return [
            _one(
                body,
                f"{label} ({suffix}) · {i}/{total}",
                suffix=suffix,
                idx=i,
                total=total,
            )
            for i, (suffix, body) in enumerate(page_chunks, start=1)
        ]

    pieces = chunk_text(text, max_chars=min(DOC_CHUNK_CHARS, MAX_HEADLINE_CHARS))
    if len(pieces) == 1:
        return [_one(pieces[0], label, suffix="", idx=1, total=1)]
    total = len(pieces)
    return [
        _one(piece, f"{label} · 청크 {i}/{total}", suffix="", idx=i, total=total)
        for i, piece in enumerate(pieces, start=1)
    ]


def _finalize_document_text(label: str, text: str, *, kind: str = "document") -> list[ExtractedSource]:
    """문서 ingest 모드에 따라 청크 분해 또는 레거시 요약."""
    text = text.strip()
    if not text:
        raise ValueError(f"문서에서 텍스트를 추출하지 못했습니다: {label}")
    if _use_document_deconstruct_ingest():
        return expand_document_sources(label, text, kind=kind, source_file=label)
    return [ExtractedSource(kind, label, _maybe_summarize(text))]


def read_document_raw(data: bytes, filename: str, mime: str = "") -> str:
    """PDF/DOCX/텍스트 바이너리 → 원문 문자열 (요약 없음)."""
    if not data:
        raise ValueError("문서 파일이 비어 있습니다.")
    name = (filename or "").lower()
    ext = Path(name).suffix

    if ext in {".txt", ".md", ".csv", ".log"} or mime.startswith("text/"):
        return _read_plain(data, filename).strip()
    if ext == ".pdf" or mime == "application/pdf":
        return _read_pdf(data)
    if ext in {".docx"} or "wordprocessingml" in mime:
        return _read_docx(data)
    raise ValueError(f"지원하지 않는 형식입니다: {ext or mime or filename}")


def document_sources_from_bytes(
    data: bytes,
    filename: str,
    mime: str = "",
    *,
    kind: str = "document",
) -> list[ExtractedSource]:
    """파일 1건 → ExtractedSource 목록 (PDF는 페이지 단위 청크)."""
    mime = mime or detect_mime(filename)
    name = (filename or "").lower()
    ext = Path(name).suffix

    if ext == ".pdf" or mime == "application/pdf":
        pages = _read_pdf_pages(data)
        if not any(p.strip() for p in pages):
            raise ValueError(f"문서에서 텍스트를 추출하지 못했습니다: {filename}")
        page_count = len(pages)
        page_chunks = chunk_pdf_page_texts(pages)
        return expand_document_sources(
            filename,
            "",
            kind=kind,
            page_chunks=page_chunks,
            source_file=filename,
            document_page_count=page_count,
        )

    text = read_document_raw(data, filename, mime)
    return _finalize_document_text(filename, text, kind=kind)


def from_document(data: bytes, filename: str, mime: str = "") -> str:
    """레거시: 첫 청크(또는 전체) 텍스트만 반환."""
    sources = document_sources_from_bytes(data, filename, mime)
    return sources[0].text


def detect_mime(filename: str, fallback: str = "application/octet-stream") -> str:
    ext = Path(filename.lower()).suffix
    table = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
    }
    return table.get(ext, fallback)


def is_image_file(filename: str, mime: str = "") -> bool:
    if mime.startswith("image/"):
        return True
    return Path((filename or "").lower()).suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def extract_batch(
    *,
    text_blocks: list[str] | None = None,
    urls: list[str] | None = None,
    files: list[tuple[str, bytes, str, str]] | None = None,
) -> list[ExtractedSource]:
    """
    여러 입력을 한꺼번에 추출.

    files: [(filename, data, mime, kind_hint)]  kind_hint = image|document|auto
    """
    out: list[ExtractedSource] = []

    for i, block in enumerate(text_blocks or [], start=1):
        if block.strip().startswith(("http://", "https://")):
            url = block.strip()
            data, ctype = _fetch_url_bytes(url)
            out.extend(url_sources_from_fetch(url, data, ctype))
        else:
            text = from_text(block)
            if _use_document_deconstruct_ingest() and len(text) > _DOC_SUMMARIZE_THRESHOLD:
                out.extend(expand_document_sources(f"텍스트 #{i}", text, kind="text"))
            else:
                out.append(ExtractedSource("text", f"텍스트 #{i}", text))

    for url in urls or []:
        data, ctype = _fetch_url_bytes(url)
        out.extend(url_sources_from_fetch(url, data, ctype))

    for fname, data, mime, hint in files or []:
        mime = mime or detect_mime(fname)
        if hint == "image" or (hint == "auto" and is_image_file(fname, mime)):
            text = from_image(data, mime, label=fname)
            out.append(ExtractedSource("image", fname, text))
        elif hint == "document" or hint == "auto":
            try:
                out.extend(document_sources_from_bytes(data, fname, mime))
            except ValueError:
                if hint == "auto":
                    text = _read_plain(data, fname).strip()
                    if not text:
                        raise ValueError(f"파일에서 텍스트를 추출하지 못했습니다: {fname}") from None
                    out.extend(_finalize_document_text(fname, text))
                else:
                    raise
        else:
            raise ValueError(f"알 수 없는 파일 종류: {fname}")

    if not out:
        raise ValueError("분석할 입력이 없습니다. 텍스트·링크·파일 중 하나 이상 추가하세요.")

    return out
