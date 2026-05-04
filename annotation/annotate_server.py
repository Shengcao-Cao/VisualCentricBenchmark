"""Minimal stdlib HTTP server for the annotation UI.

Serves static files (the annotator page, shard JSONs, images from all_figures/)
and accepts POST /save requests that patch annotation blocks into a named
shard file.

Run:
    python annotate_server.py --port 8000

Open:
    http://localhost:8000/annotator.html?shard=data/needs_review_shard_01.json
"""

import argparse
import json
import os
import re
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


_SHARD_RE = re.compile(r"^needs_review_shard_[A-Za-z0-9_-]+\.json$")
_WRITE_LOCK = threading.Lock()
_ROOT: Path  # set in main()


def _json_response(handler: "AnnotateHandler", status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _safe_shard_path(shard_name: str) -> Path:
    """Validate shard filename and return a path that stays inside _ROOT."""
    if not _SHARD_RE.match(shard_name or ""):
        raise ValueError(f"invalid shard name: {shard_name!r}")
    path = (_ROOT / shard_name).resolve()
    if _ROOT.resolve() not in path.parents and path != _ROOT.resolve() / shard_name:
        raise ValueError(f"shard path escapes root: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"shard not found: {shard_name}")
    return path


def _atomic_write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _apply_annotations(
    problem: dict, t1_annotations: dict, t2_annotation
) -> None:
    """Patch annotation fields into a problem in place."""
    t1_by_id = {
        q.get("question_id"): q for q in (problem.get("tier1_questions") or [])
    }
    for qid, ann in (t1_annotations or {}).items():
        target = t1_by_id.get(qid)
        if target is not None and isinstance(ann, dict):
            target["annotation"] = ann

    t2_list = problem.get("tier2_questions") or []
    if t2_list and isinstance(t2_annotation, dict):
        t2_list[0]["annotation"] = t2_annotation


class AnnotateHandler(SimpleHTTPRequestHandler):
    # Silence the default stderr logger for static hits; keep it for POST.
    def log_message(self, fmt, *args):  # noqa: D401, N802
        if self.command == "POST":
            super().log_message(fmt, *args)

    def do_POST(self):  # noqa: N802
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

        shard = payload.get("shard")
        problem_id = payload.get("problem_id")
        t1_annotations = payload.get("t1_annotations") or {}
        t2_annotation = payload.get("t2_annotation")

        if not shard or not problem_id:
            _json_response(
                self,
                HTTPStatus.BAD_REQUEST,
                {"error": "shard and problem_id are required"},
            )
            return

        try:
            shard_path = _safe_shard_path(shard)
        except (ValueError, FileNotFoundError) as e:
            _json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(e)})
            return

        with _WRITE_LOCK:
            data = json.loads(shard_path.read_text(encoding="utf-8"))
            problem = next((p for p in data if p.get("id") == problem_id), None)
            if problem is None:
                _json_response(
                    self,
                    HTTPStatus.NOT_FOUND,
                    {"error": f"problem_id {problem_id!r} not in {shard}"},
                )
                return
            _apply_annotations(problem, t1_annotations, t2_annotation)
            _atomic_write_json(shard_path, data)

        _json_response(self, HTTPStatus.OK, {"ok": True, "problem": problem})

    def list_directory(self, path):
        self.send_error(HTTPStatus.FORBIDDEN, "Directory listing disabled")
        return None


def main() -> None:
    global _ROOT
    parser = argparse.ArgumentParser(description="Annotation HTTP server")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Directory to serve files from (default: coreset root)",
    )
    args = parser.parse_args()

    _ROOT = Path(args.root).resolve()
    if not _ROOT.is_dir():
        raise SystemExit(f"--root is not a directory: {_ROOT}")

    os.chdir(_ROOT)  # SimpleHTTPRequestHandler resolves from cwd
    server = ThreadingHTTPServer(("0.0.0.0", args.port), AnnotateHandler)
    print(f"Serving {_ROOT} on http://localhost:{args.port}")
    print(
        f"  open http://localhost:{args.port}/annotation/annotator.html"
        f"?shard=data/needs_review_shard_01.json"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")


if __name__ == "__main__":
    main()
