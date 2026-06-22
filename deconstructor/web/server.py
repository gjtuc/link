"""
로컬 웹 UI — Google 번역 스타일 입력 + graph_output.html 미리보기
================================================================

STAGE 0-2 (사용자 시나리오) — UI ↔ 시나리오 매핑
-------------------------------------------------
  | UI 진입 | 시나리오 ID | 설명 |
  |---------|-------------|------|
  | 파일 탭 PDF/DOCX | S0-A, S0-C | 완성품 → 청크 ingest (ζ-1) |
  | 텍스트 탭 붙여넣기 | S0-B | 보고서 초안, 길면 청크 |
  | URL / 텍스트 내 URL | S0-D | HTML summarize (ingest 부록) |
  | 그래프 우클릭 가설 | S0-E | Human-in-the-loop |
  | /debug.html | S0-F | 파이프라인·FC mode 재현 (δ) |

  상세 Given/When/Then: ``docs/design/STAGE-0-2-user-scenarios.md``
  Acceptance (AC-*): ``docs/design/STAGE-0-3-acceptance-criteria.md``
  Gap (G-*): ``docs/design/STAGE-0-4-current-vs-target.md`` — AC-FC-02 stub UI (G-FC-UI)
  Roadmap: ``docs/design/STAGE-0-5-implementation-roadmap.md`` — Sprint 0 SP0-FC-* ✅
  Sprint 0: ``config.fact_checker_status_mode()`` → index.html 「미검증 가설」 (AC-FC-02)
  계약: ``docs/design/STAGE-0-1-product-definition.md``
  진행: ``docs/design/PROCESS.md``

엔드포인트
----------
  GET  /           — ``web/index.html`` (PDF·URL·텍스트 입력, 그래프 iframe)
  POST /api/analyze — 비동기 분석 시작 (202) → GET progress/result 폴링
  GET  /api/analyze/progress — 진행률 %
  GET  /api/analyze/result — 완료 후 결과 JSON
  POST /api/human-hypothesis — 사용자 가설 1건 추가 (MVP: Neo4j·그래프 갱신)
  GET  /graph_output.html — pyvis 산출물 (범례·hover JS 주입됨)
  GET  /debug.html       — 마지막 배치 파이프라인·Neo4j·색상 디버그
  GET  /api/debug/pipeline — 동일 JSON
  GET  /api/capabilities — Q2 능력·한계 카드 JSON (μ-Q2-03)

런타임 연동
-----------
  - ``neo4j_launcher`` — 분석 전 bolt 가용 시 자동 기동, 세션 heartbeat
  - ``fact_checker_dry_run`` — ``config.tavily_enabled()`` False면 stub 검증
  - Neo4j 불가 시 ``state_graph.graph_from_pipeline_state`` 로 세션 그래프만 표시
"""

from __future__ import annotations

# 회사 SSL 프록시(PRISM) — requests 패치는 가장 먼저 (Tavily·Gemini HTTPS)
from deconstructor.ssl_trust import bootstrap_ssl_trust

bootstrap_ssl_trust()

import cgi
import json
import mimetypes
import os
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from deconstructor.web.extract import (
    ExtractedSource,
    detect_mime,
    split_text_blocks,
    split_urls,
)

from deconstructor.web.pipeline_batch import run_pipeline_batch

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "web"
GRAPH_HTML = ROOT / "graph_output.html"

# link_launch.py 가 구 서버 재사용 여부 판단에 사용
LINK_UI_VERSION = "1.2"
LINK_UI_FEATURES = (
    "analyze_async",
    "analyze_progress",
    "analyze_result",
    "human_hypothesis",
    "debug_pipeline",
    "skeleton",
    "recompose",
)

_run_lock = threading.Lock()
_last_result: dict | None = None
_last_pipeline_debug: dict | None = None


def _run_pipeline_batch(sources: list[ExtractedSource], tracker: LinkStepTracker | None = None) -> dict:
    global _last_result, _last_pipeline_debug
    with _run_lock:
        result = run_pipeline_batch(sources, tracker=tracker)
        if result.get("ok"):
            _last_result = result
            _last_pipeline_debug = result.get("pipeline_debug")
        return result


def _parse_multipart_fields(form: cgi.FieldStorage) -> tuple[list[str], list[str], list[tuple[str, bytes, str, str]]]:
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

    return text_blocks, urls, files


def _parse_json_fields(payload: dict) -> tuple[list[str], list[str], list[tuple[str, bytes, str, str]]]:
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

    return text_blocks, urls, []


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

    def _send_bytes(self, data: bytes, content_type: str, *, extra_headers: dict | None = None) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if extra_headers:
            for key, val in extra_headers.items():
                self.send_header(key, val)
        self.end_headers()
        self.wfile.write(data)

    def _serve_graph_html(self) -> None:
        from deconstructor.viz.legend import prepare_graph_html

        if not GRAPH_HTML.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "graph not generated yet")
            return
        raw = GRAPH_HTML.read_text(encoding="utf-8")
        body = prepare_graph_html(raw).encode("utf-8")
        self._send_bytes(
            body,
            "text/html; charset=utf-8",
            extra_headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
        )

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
            self._serve_graph_html()
            return

        if path == "/api/last":
            self._send_json(_last_result or {"ok": False, "message": "아직 실행 기록 없음"})
            return

        if path == "/api/skeleton":
            if _last_result and _last_result.get("skeleton"):
                self._send_json({"ok": True, "skeleton": _last_result["skeleton"]})
                return
            self._send_json({"ok": False, "message": "아직 skeleton 없음 — 분석 후 조회"}, status=404)
            return

        if path == "/api/recompose":
            if _last_result and _last_result.get("recompose"):
                self._send_json({"ok": True, "recompose": _last_result["recompose"]})
                return
            self._send_json({"ok": False, "message": "아직 recompose 없음 — 분석 후 조회"}, status=404)
            return

        if path == "/api/graph-filter":
            from deconstructor.web.graph_context import get_graph_filter_snapshot

            self._send_json(get_graph_filter_snapshot())
            return

        if path == "/api/analyze/progress":
            from deconstructor.web.analyze_job import is_analyze_running
            from deconstructor.web.analyze_progress import snapshot

            snap = snapshot()
            snap["ok"] = True
            snap["analyze_thread"] = is_analyze_running()
            self._send_json(snap)
            return

        if path == "/api/analyze/result":
            from deconstructor.web.analyze_job import (
                get_analyze_error,
                get_analyze_result,
                is_analyze_running,
            )
            from deconstructor.web.analyze_progress import snapshot

            if is_analyze_running():
                self._send_json(
                    {"ok": False, "running": True, "message": "분석 진행 중"},
                    status=202,
                )
                return
            err = get_analyze_error()
            if err:
                self._send_json(err, status=500)
                return
            result = get_analyze_result()
            if result:
                self._send_json(result)
                return
            prog = snapshot()
            if prog.get("percent", 0) >= 100:
                self._send_json({"ok": False, "message": "결과 없음 — 다시 분석하세요"}, status=404)
                return
            self._send_json({"ok": False, "running": False, "message": "아직 분석 기록 없음"}, status=404)
            return

        if path == "/api/debug/pipeline":
            from deconstructor.web.graph_context import get_graph_filter_snapshot

            payload = {
                "ok": _last_pipeline_debug is not None,
                "graph_filter": get_graph_filter_snapshot(),
                "last_analyze": _last_result,
                "pipeline_debug": _last_pipeline_debug,
            }
            if not _last_pipeline_debug:
                payload["message"] = "아직 분석 기록 없음 — 메인 UI에서 전체 분석 시작"
            self._send_json(payload)
            return

        if path == "/debug.html":
            debug_page = WEB_DIR / "debug.html"
            if not debug_page.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "debug.html missing")
                return
            self._send_bytes(debug_page.read_bytes(), "text/html; charset=utf-8")
            return

        if path == "/api/launch-log":
            launch_log = ROOT / "logs" / "link_launch.log"
            if launch_log.is_file():
                try:
                    payload = json.loads(launch_log.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    payload = {"ok": False, "error": "link_launch.log 파싱 실패"}
            else:
                payload = {"ok": False, "error": "link_launch.log 없음 — Cursor에 link 입력"}
            self._send_json(payload)
            return

        if path == "/api/status":
            from deconstructor import config
            from deconstructor.neo4j_launcher import (
                _dbms_display_name,
                active_ui_tab_count,
                is_managed_neo4j,
                link_neo4j_ui_session_active,
                probe_neo4j_installation,
            )
            from deconstructor.viz.neo4j_utils import neo4j_is_available

            probe = probe_neo4j_installation(ROOT)
            self._send_json(
                {
                    "link_ui": {
                        "version": LINK_UI_VERSION,
                        "features": list(LINK_UI_FEATURES),
                    },
                    "neo4j": neo4j_is_available(),
                    "neo4j_managed": is_managed_neo4j(),
                    "neo4j_link_session": link_neo4j_ui_session_active(),
                    "ui_tabs": active_ui_tab_count(),
                    "fact_checker": config.fact_checker_status_mode(),
                    "corpus_fc_enabled": config.corpus_fc_enabled(),
                    "tavily_disabled": config.TAVILY_DISABLED,
                    "install": {
                        "docker": probe.docker_cli,
                        "compose": probe.compose_file,
                        "desktop": probe.desktop_exe is not None,
                        "desktop_exe": str(probe.desktop_exe) if probe.desktop_exe else None,
                        "desktop_dbms_count": len(probe.desktop_dbms),
                        "desktop_dbms_names": [
                            _dbms_display_name(b) for b in probe.desktop_dbms
                        ],
                        "can_auto_start": probe.any_installed,
                    },
                }
            )
            return

        if path == "/api/capabilities":
            from deconstructor.capabilities import build_capabilities

            self._send_json(build_capabilities())
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

        if parsed.path == "/api/heartbeat":
            from deconstructor.neo4j_launcher import (
                is_managed_neo4j,
                maybe_stop_managed_if_ui_idle,
                record_ui_heartbeat,
                remove_ui_tab,
            )

            try:
                payload = json.loads(self._read_body().decode("utf-8") or "{}")
            except json.JSONDecodeError:
                payload = {}
            tab_id = str(payload.get("tab_id", "")).strip()
            action = str(payload.get("action", "ping")).strip().lower()
            if action == "bye":
                remove_ui_tab(tab_id)
                stopped = maybe_stop_managed_if_ui_idle(reason="last_tab_bye")
            else:
                record_ui_heartbeat(tab_id)
                stopped = False
            self._send_json(
                {
                    "ok": True,
                    "neo4j_managed": is_managed_neo4j(),
                    "neo4j_stopped": stopped,
                }
            )
            return

        if parsed.path == "/api/human-hypothesis":
            self._handle_human_hypothesis()
            return

        if parsed.path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        from deconstructor.web.analyze_job import is_analyze_running, start_analyze_job
        from deconstructor.web.analyze_progress import begin_job, set_label, snapshot
        from deconstructor.web.link_steps import LinkStepTracker

        if is_analyze_running():
            self._send_json(
                {"ok": False, "error": "이미 분석이 진행 중입니다.", "failed_step": "S0-BUSY"},
                status=409,
            )
            return

        ctype = self.headers.get("Content-Type", "")

        try:
            if ctype.startswith("application/json"):
                payload = json.loads(self._read_body().decode("utf-8"))
                text_blocks, urls, files = _parse_json_fields(payload)
            elif ctype.startswith("multipart/form-data"):
                environ = {
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": ctype,
                    "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
                }
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=environ)
                text_blocks, urls, files = _parse_multipart_fields(form)
            else:
                raise ValueError("Content-Type must be multipart/form-data or application/json")
        except Exception as exc:
            self._send_json(
                {"ok": False, "error": str(exc), "failed_step": "S0-PARSE-CTYPE"},
                status=400,
            )
            return

        n_files = len(files)
        n_urls = len(urls)
        n_text = len(text_blocks)
        source_count = max(1, n_text + n_urls + n_files)
        job_id = begin_job(source_count=source_count)
        set_label("요청 접수 · 분석 준비…", percent=3)

        def _worker() -> dict:
            from deconstructor.web.analyze_progress import clear_job, finish_job, set_label, set_source_count, sync_tracker
            from deconstructor.web.extract_tracked import extract_batch_tracked
            from deconstructor.web.link_steps import LinkStepTracker

            def _on_step(tr: LinkStepTracker) -> None:
                sync_tracker(tr)

            tracker = LinkStepTracker(on_change=_on_step)
            sync_tracker(tracker)
            set_source_count(source_count)
            set_label("파이프라인 기동…", percent=5)

            try:
                tracker.start("S0-PARSE-CTYPE", "Content-Type 확인", ctype.split(";")[0])
                tracker.ok(
                    "S0-PARSE-FIELDS",
                    f"text={n_text} url={n_urls} file={n_files}",
                )
                tracker.ok("S0-PARSE-CTYPE")

                sources = extract_batch_tracked(
                    tracker,
                    text_blocks=text_blocks,
                    urls=urls,
                    files=files,
                )

                result = _run_pipeline_batch(sources, tracker=tracker)
                pre_steps = tracker.to_list()
                if result.get("steps"):
                    result["steps"] = pre_steps + result["steps"]
                else:
                    result["steps"] = pre_steps
                if not result.get("ok"):
                    clear_job()
                    return result
                finish_job()
                return result
            except Exception as exc:
                clear_job()
                return tracker.fail(exc)

        if not start_analyze_job(_worker):
            from deconstructor.web.analyze_progress import clear_job

            clear_job()
            self._send_json(
                {"ok": False, "error": "분석 시작 실패", "failed_step": "S0-BUSY"},
                status=409,
            )
            return

        self._send_json(
            {
                "ok": True,
                "async": True,
                "job_id": job_id,
                "message": "분석 시작됨 — 진행률 폴링",
            },
            status=202,
        )

    def _handle_human_hypothesis(self) -> None:
        """POST /api/human-hypothesis — 파란 노드에서 이은 사용자 가설 (MVP)."""
        from pydantic import ValidationError

        from deconstructor.web.human_hypothesis import (
            HumanHypothesisCreate,
            submit_human_hypothesis,
        )
        from deconstructor.web.human_hypothesis.store import HumanHypothesisStoreError

        try:
            raw = json.loads(self._read_body().decode("utf-8") or "{}")
            payload = HumanHypothesisCreate.model_validate(raw)
        except (json.JSONDecodeError, ValidationError) as exc:
            self._send_json(
                {"ok": False, "error": str(exc), "failed_step": "H0-PARSE"},
                status=400,
            )
            return

        result = submit_human_hypothesis(payload)
        if not result.get("ok", True):
            status = 400 if result.get("failed_step", "").startswith("H1") else 500
            self._send_json(result, status=status)
            return
        self._send_json(result)


def main(host: str = "127.0.0.1", port: int = 8765) -> None:
    from deconstructor.neo4j_launcher import _cleanup_on_process_exit, start_ui_watchdog
    from deconstructor.print_util import bootstrap_stdio_utf8, safe_print

    bootstrap_stdio_utf8()
    bootstrap_ssl_trust()
    os.chdir(ROOT)
    start_ui_watchdog()
    server = ThreadingHTTPServer((host, port), LinkUIHandler)
    url = f"http://{host}:{port}/"
    safe_print(f"[LinkUI] Deconstructor web UI → {url}")
    safe_print("[LinkUI] 지원: 텍스트·URL·이미지·PDF/DOCX - 여러 개 동시 입력")
    safe_print("[LinkUI] 브라우저 탭·창이 닫히거나 45초 이상 숨겨지면 Link가 켠 Neo4j·Desktop 자동 정리")
    safe_print("[LinkUI] 종료: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        safe_print("\n[LinkUI] stopped")
    finally:
        _cleanup_on_process_exit()


if __name__ == "__main__":
    main()
