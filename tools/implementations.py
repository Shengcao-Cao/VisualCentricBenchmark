"""Tool implementations called by the agent loop.

Each function maps to one tool in registry.py. Results are returned in the
format expected by the Anthropic messages API:
  - plain string  → simple text tool_result
  - list of dicts → multi-part tool_result (text + image blocks)

``session`` carries per-conversation render state instead of a module-level
global, so multiple concurrent dialogue sessions don't interfere.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from backends import RenderResult, render_graphviz, render_matplotlib, render_tikz
from config import BASE_DIR, DEFAULT_MODEL, OUTPUT_DIR
from llm_client import simple_completion
from validators.visual import validate_visual

if TYPE_CHECKING:
    from session import ConversationSession

_CLASSIFY_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "classify.md"


# ── Dispatcher ────────────────────────────────────────────────────────────────

def dispatch_tool(
    name: str,
    inputs: dict,
    session: "ConversationSession",
) -> str | list[dict]:
    if name == "classify_diagram":
        return _classify_diagram(inputs["description"])
    if name == "render_tikz":
        return _render("tikz", inputs["source"], session)
    if name == "render_matplotlib":
        return _render("matplotlib", inputs["source"], session)
    if name == "render_graphviz":
        return _render(
            "graphviz", inputs["source"], session,
            engine=inputs.get("engine", "dot"),
        )
    if name == "validate_visual":
        return _validate(inputs["description"], session)
    if name == "save_diagram":
        return _save(inputs["filename"], session)
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


def _render(
    backend: str,
    source: str,
    session: "ConversationSession",
    **kwargs,
) -> str | list[dict]:
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

    session.store_render(result.image_bytes)
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


def _validate(description: str, session: "ConversationSession") -> str:
    if session.current_render_id is None:
        return "No rendered image available. Render a diagram first."

    image_bytes = session.renders[session.current_render_id]
    vr = validate_visual(image_bytes, description)
    return json.dumps(
        {
            "score": vr.score,
            "passed": vr.passed,
            "issues": vr.issues,
            "suggestions": vr.suggestions,
        },
        indent=2,
    )


def _save(filename: str, session: "ConversationSession") -> str:
    if session.current_render_id is None:
        return "No rendered image available to save."

    # Sanitize filename
    safe = re.sub(r"[^\w\-_. ]", "_", filename)
    if not safe.lower().endswith((".png", ".svg", ".pdf")):
        safe += ".png"

    image_bytes = session.renders[session.current_render_id]
    out_path = OUTPUT_DIR / safe
    out_path.write_bytes(image_bytes)
    return f"Saved to {out_path}"
