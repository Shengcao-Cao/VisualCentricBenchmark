"""Tool implementations called by the agent loop.

Each function maps to one tool in registry.py. Results are returned in the
format expected by the Anthropic messages API:
  - plain string  → simple text tool_result
  - list of dicts → multi-part tool_result (text + image blocks)
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from backends import RenderResult, render_graphviz, render_matplotlib, render_tikz
from config import BASE_DIR, DEFAULT_MODEL, OUTPUT_DIR
from llm_client import simple_completion
from validators.visual import validate_visual

_CLASSIFY_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "classify.md"

# ── Module-level state ────────────────────────────────────────────────────────
# Stores the most recent successful RenderResult so validate_visual and
# save_diagram can reference it without the agent passing raw bytes.
_last_render: RenderResult | None = None


# ── Dispatcher ────────────────────────────────────────────────────────────────

def dispatch_tool(name: str, inputs: dict) -> str | list[dict]:
    if name == "classify_diagram":
        return _classify_diagram(inputs["description"])
    if name == "render_tikz":
        return _render("tikz", inputs["source"])
    if name == "render_matplotlib":
        return _render("matplotlib", inputs["source"])
    if name == "render_graphviz":
        return _render("graphviz", inputs["source"], engine=inputs.get("engine", "dot"))
    if name == "validate_visual":
        return _validate(inputs["description"])
    if name == "save_diagram":
        return _save(inputs["filename"])
    return f"Unknown tool: {name}"


# ── Individual implementations ────────────────────────────────────────────────

def _classify_diagram(description: str) -> str:
    system = _CLASSIFY_PROMPT_PATH.read_text(encoding="utf-8")
    return simple_completion(
        messages=[{"role": "user", "content": description}],
        system=system,
        model=DEFAULT_MODEL,
        max_tokens=256,
    )


def _render(backend: str, source: str, **kwargs) -> str | list[dict]:
    global _last_render

    if backend == "tikz":
        result = render_tikz(source)
    elif backend == "matplotlib":
        result = render_matplotlib(source)
    elif backend == "graphviz":
        result = render_graphviz(source, engine=kwargs.get("engine", "dot"))
    else:
        return f"Unknown backend: {backend}"

    if not result.success:
        return (
            f"Render failed ({backend}).\n"
            f"Error: {result.error}\n"
            f"Stderr:\n{result.stderr or '(none)'}"
        )

    _last_render = result
    b64 = base64.standard_b64encode(result.image_bytes).decode()
    return [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": b64,
            },
        },
        {
            "type": "text",
            "text": f"Rendered successfully using {backend}. Examine the image above carefully.",
        },
    ]


def _validate(description: str) -> str:
    global _last_render
    if _last_render is None or not _last_render.success:
        return "No rendered image available. Render a diagram first."

    vr = validate_visual(_last_render.image_bytes, description)
    return json.dumps(
        {
            "score": vr.score,
            "passed": vr.passed,
            "issues": vr.issues,
            "suggestions": vr.suggestions,
        },
        indent=2,
    )


def _save(filename: str) -> str:
    global _last_render
    if _last_render is None or not _last_render.success:
        return "No rendered image available to save."

    # Sanitize filename
    safe = re.sub(r"[^\w\-_. ]", "_", filename)
    if not safe.lower().endswith((".png", ".svg", ".pdf")):
        safe += ".png"

    out_path = OUTPUT_DIR / safe
    out_path.write_bytes(_last_render.image_bytes)
    return f"Saved to {out_path}"
