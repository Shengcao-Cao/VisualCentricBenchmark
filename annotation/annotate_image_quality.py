"""Simple server for annotating image equivalence: original vs reproduced."""

import json
import argparse
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

DATA_PATH = None
DATA = None
BASE_DIR = None


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(DATA).encode())
        elif parsed.path == "/api/save":
            params = urllib.parse.parse_qs(parsed.query)
            idx = int(params["idx"][0])
            verdict = params["verdict"][0]
            DATA[idx].setdefault("image_quality_annotation", {})
            DATA[idx]["image_quality_annotation"]["equivalent"] = verdict == "yes"
            with open(DATA_PATH, "w") as f:
                json.dump(DATA, f, indent=2, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        elif parsed.path == "/annotate":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())
        else:
            super().do_GET()

    def translate_path(self, path):
        return str(BASE_DIR / path.lstrip("/"))


HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Image Equivalence Annotation</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header h2 { font-size: 18px; }
.progress { font-size: 14px; color: #666; }
.container { display: flex; gap: 20px; margin-bottom: 16px; }
.panel { flex: 1; background: white; border-radius: 8px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.panel h3 { font-size: 14px; color: #666; margin-bottom: 8px; }
.panel img { width: 100%; max-height: 500px; object-fit: contain; border: 1px solid #eee; border-radius: 4px; }
.question-box { background: white; border-radius: 8px; padding: 12px; margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 13px; line-height: 1.5; max-height: 120px; overflow-y: auto; }
.question-box b { color: #333; }
.buttons { display: flex; gap: 12px; justify-content: center; align-items: center; }
.btn { padding: 10px 32px; font-size: 16px; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; }
.btn-yes { background: #2e7d32; color: white; }
.btn-no { background: #c62828; color: white; }
.btn-skip { background: #757575; color: white; }
.btn:hover { opacity: 0.9; }
.nav { display: flex; gap: 8px; }
.nav button { padding: 6px 16px; font-size: 13px; border: 1px solid #ccc; border-radius: 4px;
  background: white; cursor: pointer; }
.status { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
.status-yes { background: #c8e6c9; color: #2e7d32; }
.status-no { background: #ffcdd2; color: #c62828; }
.status-pending { background: #e0e0e0; color: #666; }
.id-label { font-size: 13px; color: #999; margin-bottom: 4px; }
</style>
</head>
<body>
<div class="header">
  <h2>Image Equivalence Annotation</h2>
  <div class="progress" id="progress"></div>
  <div class="nav">
    <button onclick="jump(-1)">← Prev</button>
    <button onclick="jump(1)">Next →</button>
    <button onclick="jumpUnannotated()">Next Unannotated</button>
  </div>
</div>
<div class="id-label" id="idLabel"></div>
<div class="question-box" id="questionBox"></div>
<div class="container">
  <div class="panel">
    <h3>Original Image</h3>
    <img id="origImg">
  </div>
  <div class="panel">
    <h3>Reproduced Image</h3>
    <img id="reproImg">
  </div>
</div>
<div class="buttons">
  <button class="btn btn-yes" onclick="annotate('yes')">✓ Equivalent (Y)</button>
  <button class="btn btn-no" onclick="annotate('no')">✗ Not Equivalent (N)</button>
  <button class="btn btn-skip" onclick="jump(1)">Skip (→)</button>
  <span class="status" id="currentStatus"></span>
</div>
<script>
let data = [];
let idx = 0;

async function load() {
  const resp = await fetch('/api/data');
  data = await resp.json();
  render();
}

function render() {
  const item = data[idx];
  const origImg = 'data/' + item.images[0];
  const reproImg = 'data/' + item.tier3_questions[0].images[0];
  document.getElementById('origImg').src = '/' + origImg;
  document.getElementById('reproImg').src = '/' + reproImg;
  document.getElementById('idLabel').textContent = item.id + ' (' + (idx+1) + '/' + data.length + ')';
  document.getElementById('questionBox').innerHTML = '<b>Question:</b> ' +
    item.question.replace(/</g, '&lt;').replace(/>/g, '&gt;').substring(0, 500);

  const ann = item.image_quality_annotation;
  const statusEl = document.getElementById('currentStatus');
  if (ann && ann.equivalent === true) {
    statusEl.textContent = 'EQUIVALENT';
    statusEl.className = 'status status-yes';
  } else if (ann && ann.equivalent === false) {
    statusEl.textContent = 'NOT EQUIVALENT';
    statusEl.className = 'status status-no';
  } else {
    statusEl.textContent = 'PENDING';
    statusEl.className = 'status status-pending';
  }

  const done = data.filter(d => d.image_quality_annotation).length;
  document.getElementById('progress').textContent = done + '/' + data.length + ' annotated';
}

function jump(delta) {
  idx = Math.max(0, Math.min(data.length - 1, idx + delta));
  render();
}

function jumpUnannotated() {
  for (let i = 1; i <= data.length; i++) {
    const j = (idx + i) % data.length;
    if (!data[j].image_quality_annotation) { idx = j; render(); return; }
  }
  alert('All annotated!');
}

async function annotate(verdict) {
  await fetch('/api/save?idx=' + idx + '&verdict=' + verdict);
  data[idx].image_quality_annotation = { equivalent: verdict === 'yes' };
  if (idx < data.length - 1) idx++;
  render();
}

document.addEventListener('keydown', e => {
  if (e.key === 'ArrowLeft') jump(-1);
  if (e.key === 'ArrowRight') jump(1);
  if (e.key === 'y' || e.key === 'Y') annotate('yes');
  if (e.key === 'n' || e.key === 'N') annotate('no');
});

load();
</script>
</body>
</html>
"""


def main():
    global DATA_PATH, DATA, BASE_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8003)
    parser.add_argument("--data", default="data/image_quality_equiv_subset.json")
    args = parser.parse_args()

    DATA_PATH = Path(args.data)
    BASE_DIR = DATA_PATH.parent.parent
    with open(DATA_PATH) as f:
        DATA = json.load(f)
    print(f"Loaded {len(DATA)} items from {DATA_PATH}")
    print(f"Serving from {BASE_DIR}")
    print(f"Open http://localhost:{args.port}/annotate")
    HTTPServer(("", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
