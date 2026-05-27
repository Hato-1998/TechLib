#!/usr/bin/env python3
"""TechLib 위키 편집기 - 로컬 브라우저 기반 마크다운 편집기.

3컬럼 UI:
  | 파일 트리 | 마크다운 편집 | 실시간 미리보기 |

기능:
  - docs/ 하위 모든 .md 파일 열기·저장
  - 실시간 마크다운 미리보기 (mermaid + 코드 하이라이트 포함)
  - 새 페이지 추가 (기존 add_page 로직 재사용)
  - 편집 보조 도구 (TODO 주석, 코드블록, 표, mermaid 템플릿)

사용:
    python tools/editor/server.py
    또는 tools/launch_editor.cmd (Windows)
    또는 바탕화면 'TechLib 편집기' 바로가기
"""
from __future__ import annotations

import http.server
import json
import socketserver
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

# tools/를 sys.path에 추가하여 add_page 모듈 재사용
TOOLS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS_DIR))
import add_page as ap  # noqa: E402

ROOT = ap.ROOT
DOCS = ap.DOCS
STATIC = Path(__file__).resolve().parent / "static"
HOST = "127.0.0.1"
PORT = 7700


# ============================================================
# 보안: docs/ 하위 경로만 허용
# ============================================================

def safe_doc_path(rel_path: str) -> Path | None:
    try:
        rel = Path(rel_path)
        if rel.is_absolute() or ".." in rel.parts:
            return None
        full = (DOCS / rel).resolve()
        docs_resolved = DOCS.resolve()
        # full이 docs_resolved 하위인지 확인
        try:
            full.relative_to(docs_resolved)
        except ValueError:
            return None
        return full
    except Exception:
        return None


# ============================================================
# 파일 트리 구성
# ============================================================

def list_tree() -> list[dict]:
    """mkdocs.yml nav를 따라 (섹션 → 파일들) 리스트 생성."""
    config = ap.load_config()
    sections = ap.get_sections(config)
    result = []

    # 홈
    if (DOCS / "index.md").exists():
        result.append({"section": "홈", "files": [{"name": "홈", "path": "index.md"}]})

    for name, value in sections:
        files = []
        if isinstance(value, str):
            files.append({"name": "(개요)", "path": value})
        elif isinstance(value, list):
            for sub in value:
                if isinstance(sub, dict):
                    for sname, spath in sub.items():
                        files.append({"name": sname, "path": spath})
        result.append({"section": name, "files": files})
    return result


# ============================================================
# HTTP 핸들러
# ============================================================

class EditorHandler(http.server.BaseHTTPRequestHandler):
    # 로그 조용히
    def log_message(self, fmt: str, *args) -> None:
        return

    # ---- 응답 헬퍼 ----
    def _send_json(self, data, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(404, f"not found: {path.name}")
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", "0") or "0")
        if n <= 0:
            return {}
        raw = self.rfile.read(n)
        return json.loads(raw.decode("utf-8"))

    # ---- 라우팅 ----
    def do_GET(self) -> None:
        try:
            url = urlparse(self.path)
            path = unquote(url.path)

            # 정적 파일
            if path == "/" or path == "/index.html":
                return self._send_file(STATIC / "index.html", "text/html; charset=utf-8")
            if path == "/app.js":
                return self._send_file(STATIC / "app.js", "application/javascript; charset=utf-8")
            if path == "/style.css":
                return self._send_file(STATIC / "style.css", "text/css; charset=utf-8")

            # API
            if path == "/api/tree":
                return self._send_json({"sections": list_tree()})

            if path == "/api/file":
                qs = parse_qs(url.query)
                rel = qs.get("path", [""])[0]
                full = safe_doc_path(rel)
                if full is None or not full.exists():
                    return self._send_json({"error": f"not found: {rel}"}, 404)
                return self._send_json({
                    "path": rel,
                    "content": full.read_text(encoding="utf-8"),
                })

            if path == "/api/sections":
                config = ap.load_config()
                sections = ap.get_sections(config)
                return self._send_json({
                    "sections": [
                        {"name": n, "multipage": isinstance(v, list)}
                        for n, v in sections
                    ]
                })

            self.send_error(404)
        except Exception as e:
            self._send_json({"error": str(e), "trace": traceback.format_exc()}, 500)

    def do_POST(self) -> None:
        try:
            url = urlparse(self.path)
            path = url.path

            if path == "/api/file":
                body = self._read_json()
                rel = body.get("path", "")
                content = body.get("content", "")
                full = safe_doc_path(rel)
                if full is None:
                    return self._send_json({"error": "invalid path"}, 400)
                full.parent.mkdir(parents=True, exist_ok=True)
                full.write_text(content, encoding="utf-8")
                return self._send_json({"ok": True, "bytes": len(content.encode("utf-8"))})

            if path == "/api/page":
                body = self._read_json()
                section = body.get("section", "").strip()
                title = body.get("title", "").strip()
                slug = body.get("slug", "").strip()
                summary = body.get("summary", "").strip()
                if not (section and title and slug):
                    return self._send_json({"error": "필수 항목 누락"}, 400)

                # add_page의 stdout을 임시로 캡처
                import io, contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = ap.add_page_to_section(
                        section, title, slug, summary,
                        auto_confirm=True, open_editor=False,
                    )
                if rc != 0:
                    return self._send_json({"error": "생성 실패", "log": buf.getvalue()}, 500)

                # 새 파일의 상대 경로 계산
                config = ap.load_config()
                for item in config["nav"]:
                    if isinstance(item, dict) and section in item:
                        folder = ap.section_folder(item[section])
                        new_rel = (folder / f"{slug}.md").relative_to(DOCS).as_posix()
                        return self._send_json({"ok": True, "path": new_rel})
                return self._send_json({"error": "post-create 조회 실패"}, 500)

            self.send_error(404)
        except Exception as e:
            self._send_json({"error": str(e), "trace": traceback.format_exc()}, 500)


# ============================================================
# 서버 실행
# ============================================================

class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def open_browser() -> None:
    time.sleep(0.4)
    webbrowser.open(f"http://{HOST}:{PORT}/")


def main() -> int:
    print()
    print("  +-----------------------------------+")
    print("  |  TechLib Wiki Editor              |")
    print(f"  |  http://{HOST}:{PORT}/        |")
    print("  |  Ctrl+C to stop                   |")
    print("  +-----------------------------------+")
    print()

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        with ThreadingServer((HOST, PORT), EditorHandler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        print(f"  [error] 서버 시작 실패: {e}")
        print(f"  포트 {PORT}이 이미 사용 중일 수 있습니다.")
        return 1
    except KeyboardInterrupt:
        print("\n  종료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
