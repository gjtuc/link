"""
입력 추출 — 텍스트 / URL / 이미지 / 문서 → 파이프라인 헤드라인
"""

from __future__ import annotations

import base64
import io
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from langchain_core.messages import HumanMessage

from deconstructor.llm import get_chat_model

MAX_HEADLINE_CHARS = 12_000
_DOC_SUMMARIZE_THRESHOLD = 2_000
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
    return _maybe_summarize(text)


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


def _read_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("PDF 지원을 위해 pip install pypdf 가 필요합니다.") from exc
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages[:30]:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


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


def _maybe_summarize(text: str) -> str:
    if len(text) <= _DOC_SUMMARIZE_THRESHOLD:
        return _normalize(text)
    return _summarize_with_llm(_DOC_SUMMARIZE_PROMPT, text)


def from_document(data: bytes, filename: str, mime: str = "") -> str:
    if not data:
        raise ValueError("문서 파일이 비어 있습니다.")
    name = (filename or "").lower()
    ext = Path(name).suffix

    if ext in {".txt", ".md", ".csv", ".log"} or mime.startswith("text/"):
        text = _read_plain(data, filename)
    elif ext == ".pdf" or mime == "application/pdf":
        text = _read_pdf(data)
    elif ext in {".docx"} or "wordprocessingml" in mime:
        text = _read_docx(data)
    else:
        raise ValueError(f"지원하지 않는 형식입니다: {ext or mime or filename}")

    text = text.strip()
    if not text:
        raise ValueError(f"문서에서 텍스트를 추출하지 못했습니다: {filename}")
    return _maybe_summarize(text)


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
            out.append(ExtractedSource("url", url, from_url(url)))
        else:
            out.append(ExtractedSource("text", f"텍스트 #{i}", from_text(block)))

    for url in urls or []:
        out.append(ExtractedSource("url", url, from_url(url)))

    for fname, data, mime, hint in files or []:
        mime = mime or detect_mime(fname)
        if hint == "image" or (hint == "auto" and is_image_file(fname, mime)):
            text = from_image(data, mime, label=fname)
            out.append(ExtractedSource("image", fname, text))
        elif hint == "document" or hint == "auto":
            try:
                text = from_document(data, fname, mime)
            except ValueError:
                if hint == "auto":
                    text = _read_plain(data, fname)
                    text = _maybe_summarize(text.strip())
                    if not text:
                        raise ValueError(f"파일에서 텍스트를 추출하지 못했습니다: {fname}") from None
                else:
                    raise
            out.append(ExtractedSource("document", fname, text))
        else:
            raise ValueError(f"알 수 없는 파일 종류: {fname}")

    if not out:
        raise ValueError("분석할 입력이 없습니다. 텍스트·링크·파일 중 하나 이상 추가하세요.")

    return out
