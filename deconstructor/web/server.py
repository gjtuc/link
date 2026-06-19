"""
로컬 웹 UI — Google 번역 스타일 입력 + graph_output.html 미리보기
"""

from __future__ import annotations

import cgi
import json
import mimetypes
import os
import sys
import threading
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from deconstructor.web.extract import (
    ExtractedSource,
    detect_mime,
    extract_batch,
    split_text_blocks,
    split_urls,
)

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "web"
GRAPH_HTML = ROOT / "graph_output.html"

_run_lock = threading.Lock()
_last_result: dict | None = None


def _run_pipeline_batch(sources: list[ExtractedSource]) -> dict:
    global _last_result
    from deconstructor.graph_builder import run_pipeline
    from deconstructor.report import format_dry_run_report
    from deconstructor.viz.neo4j_utils import fetch_causal_graph
    from deconstructor.viz.visualizer import render_to_html

    runs: list[dict] = []
    with _run_lock:
        for idx, src in enumerate(sources, start=1):
            print(f"[LinkUI] 분석 {idx}/{len(sources)} — {src.kind}: {src.label}")
            state = run_pipeline(src.text, persist_db=True)
            report = format_dry_run_report(state)
            verified = state.get("verified_edges") or []
            completed = state.get("completed_facts") or []
            runs.append(
                {
                    "index": idx,
                    "kind": src.kind,
                    "label": src.label,
                    "chars": len(src.text),
                    "verified_edges": len(verified),
                    "atomic_facts": len(completed),
                    "preview": src.text[:240] + ("…" if len(src.text) > 240 else ""),
                    "report_excerpt": "\n".join(report.splitlines()[:12]),
                }
            )

        fetched = fetch_causal_graph(max_nodes=300)
        render_to_html(fetched.nodes, fetched.edges, GRAPH_HTML, title="Deconstructor Causal Graph")

        _last_result = {
            "ok": True,
            "items_processed": len(sources),
            "sources": runs,
            "nodes": len(fetched.nodes),
            "edges": len(fetched.edges),
            "verified_edges_total": sum(r["verified_edges"] for r in runs),
            "atomic_facts_total": sum(r["atomic_facts"] for r in runs),
        }
        return _last_result


def _parse_multipart_batch(form: cgi.FieldStorage) -> list[ExtractedSource]:
    text_raw = form.getfirst("text", "") or ""
    urls_raw = form.getfirst("urls", "") or ""

    text_blocks = split_text_blocks(text_raw)
    urls = split_urls(urls_raw) if urls_raw.strip() else []

    files: list[tuple[str, bytes, str, str]] = []

    def _append_file_field(field, kind_hint: str) -> None:
        if field is None:
            return
        if isinstance(field, list):
            for item in field:
                _append_one(item, kind_hint)
            return
        _append_one(field, kind_hint)

    def _append_one(field, kind_hint: str) -> None:
        if not getattr(field, "file", None):
            return
        data = field.file.read()
        fname = getattr(field, "filename", None) or "upload.bin"
        mime = field.type or detect_mime(fname)
        files.append((fname, data, mime, kind_hint))

    if "images" in form:
        _append_file_field(form["images"], "image")
    if "documents" in form:
        _append_file_field(form["documents"], "document")
    if "files" in form:
        _append_file_field(form["files"], "auto")

    return extract_batch(text_blocks=text_blocks, urls=urls, files=files)


def _parse_json_batch(payload: dict) -> list[ExtractedSource]:
    text_blocks = split_text_blocks(payload.get("text", "") or "")
    extra = payload.get("texts") or []
    if isinstance(extra, list):
        text_blocks.extend(str(t).strip() for t in extra if str(t).strip())

    urls = split_urls(payload.get("urls", "") or "")
    extra_urls = payload.get("url_list") or []
    if isinstance(extra_urls, list):
        for u in extra_urls:
            u = str(u).strip()
            if u:
                urls.extend(split_urls(u))

    return extract_batch(text_blocks=text_blocks, urls=urls, files=[])


class LinkUIHandler(BaseHTTPRequestHandler):
    server_version = "LinkUI/1.1"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[LinkUI] {self.address_string()} - {fmt % args}\n")

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, data: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length) if length else b""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            index = WEB_DIR / "index.html"
            if not index.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "index.html missing")
                return
            self._send_bytes(index.read_bytes(), "text/html; charset=utf-8")
            return

        if path == "/graph_output.html":
            if not GRAPH_HTML.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "graph not generated yet")
                return
            self._send_bytes(GRAPH_HTML.read_bytes(), "text/html; charset=utf-8")
            return

        if path == "/api/last":
            self._send_json(_last_result or {"ok": False, "message": "아직 실행 기록 없음"})
            return

        if path.startswith("/static/"):
            rel = path.removeprefix("/static/")
            target = (WEB_DIR / rel).resolve()
            if not str(target).startswith(str(WEB_DIR.resolve())) or not target.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            self._send_bytes(target.read_bytes(), ctype)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        ctype = self.headers.get("Content-Type", "")
        try:
            if ctype.startswith("application/json"):
                payload = json.loads(self._read_body().decode("utf-8"))
                sources = _parse_json_batch(payload)
            elif ctype.startswith("multipart/form-data"):
                environ = {
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": ctype,
                    "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
                }
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=environ)
                sources = _parse_multipart_batch(form)
            else:
                raise ValueError("Content-Type must be multipart/form-data or application/json")

            result = _run_pipeline_batch(sources)
            self._send_json(result)
        except Exception as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": str(exc),
                    "detail": traceback.format_exc(limit=4),
                },
                status=500,
            )


def main(host: str = "127.0.0.1", port: int = 8765) -> None:
    os.chdir(ROOT)
    server = ThreadingHTTPServer((host, port), LinkUIHandler)
    url = f"http://{host}:{port}/"
    print(f"[LinkUI] Deconstructor web UI → {url}")
    print(f"[LinkUI] 지원: 텍스트·URL·이미지·PDF/DOCX — 여러 개 동시 입력")
    print("[LinkUI] 종료: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[LinkUI] stopped")


if __name__ == "__main__":
    main()
