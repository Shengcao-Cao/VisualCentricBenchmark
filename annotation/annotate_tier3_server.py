"""Minimal stdlib HTTP server for the tier3 annotation UI.

Serves static files (the annotator page, data JSONs, images from all_figures/
and tier3_figures_jpg/) and accepts POST /save requests that patch annotation
blocks into the data file.

Run:
    python annotate_tier3_server.py --port 8001

Open:
    http://localhost:8001/annotator_tier3.html?file=data/filtered_data_with_solution_hard_tier3_jpg_pruned_fixed.json
"""

import argparse
import json
import os
import re
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


_FILE_RE = re.compile(r"^[A-Za-z0-9_.-]+\.json$")
_WRITE_LOCK = threading.Lock()
_ROOT: Path  # set in main()


def _json_response(handler: "AnnotateHandler", status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _safe_file_path(file_name: str) -> Path:
    """Validate filename and return a path that stays inside _ROOT."""
    if not _FILE_RE.match(file_name or ""):
        raise ValueError(f"invalid file name: {file_name!r}")
    path = (_ROOT / file_name).resolve()
    if _ROOT.resolve() not in path.parents and path != _ROOT.resolve() / file_name:
        raise ValueError(f"file path escapes root: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"file not found: {file_name}")
    return path


def _atomic_write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _apply_annotation(problem: dict, annotation: dict) -> None:
    """Patch annotation into tier3_pruned_questions[0]."""
    tp_list = problem.get("tier3_pruned_questions") or []
    if tp_list and isinstance(annotation, dict):
        tp_list[0]["annotation"] = annotation


class AnnotateHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        if self.command == "POST":
            super().log_message(fmt, *args)

    def do_POST(self):
        if self.path != "/save":
            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b""
            payload = json.loads(raw.decode("utf-8"))
        except Exception as e:
            _json_response(
                self, HTTPStatus.BAD_REQUEST, {"error": f"invalid JSON body: {e}"}
            )
            return

        file_name = payload.get("file")
        problem_id = payload.get("problem_id")
        annotation = payload.get("annotation")

        if not file_name or not problem_id:
            _json_response(
                self,
                HTTPStatus.BAD_REQUEST,
                {"error": "file and problem_id are required"},
            )
            return

        try:
            file_path = _safe_file_path(file_name)
        except (ValueError, FileNotFoundError) as e:
            _json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(e)})
            return

        with _WRITE_LOCK:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            problem = next((p for p in data if p.get("id") == problem_id), None)
            if problem is None:
                _json_response(
                    self,
                    HTTPStatus.NOT_FOUND,
                    {"error": f"problem_id {problem_id!r} not in {file_name}"},
                )
                return
            _apply_annotation(problem, annotation)
            _atomic_write_json(file_path, data)

        _json_response(self, HTTPStatus.OK, {"ok": True, "problem": problem})

    def list_directory(self, path):
        self.send_error(HTTPStatus.FORBIDDEN, "Directory listing disabled")
        return None


def main() -> None:
    global _ROOT
    parser = argparse.ArgumentParser(description="Tier3 annotation HTTP server")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Directory to serve files from (default: coreset root)",
    )
    args = parser.parse_args()

    _ROOT = Path(args.root).resolve()
    if not _ROOT.is_dir():
        raise SystemExit(f"--root is not a directory: {_ROOT}")

    os.chdir(_ROOT)
    server = ThreadingHTTPServer(("0.0.0.0", args.port), AnnotateHandler)
    print(f"Serving {_ROOT} on http://localhost:{args.port}")
    print(
        f"  open http://localhost:{args.port}/annotation/annotator_tier3.html"
        f"?file=data/filtered_data_with_solution_hard_tier3_jpg_pruned_fixed.json"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")


if __name__ == "__main__":
    main()
