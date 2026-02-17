"""Diagram generation agent.

Usage:
    uv run agent.py "a right triangle with legs labeled a, b and hypotenuse c"
    uv run agent.py "sine and cosine on [-2π, 2π]" --output trig.png
    uv run agent.py "binary search tree with values 5,3,7,1,4" --output bst.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import anthropic

import config as cfg
from tools import TOOL_DEFINITIONS, dispatch_tool

_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text(encoding="utf-8")


# ── Agent loop ────────────────────────────────────────────────────────────────

def run_agent(description: str, output_filename: str = "diagram.png") -> dict[str, Any]:
    """Run the diagram agent for the given description.

    Returns a dict with keys:
        status  : "complete" | "max_turns" | "error"
        message : final agent message (if any)
        output  : Path to saved diagram (if saved)
    """
    client = anthropic.Anthropic()

    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"{description}\n\n"
                f"Save the final diagram as: {output_filename}"
            ),
        }
    ]

    print(f"[agent] Starting — {description!r}", file=sys.stderr)

    for turn in range(cfg.MAX_AGENT_TURNS):
        response = client.messages.create(
            model=cfg.DEFAULT_MODEL,
            max_tokens=8096,
            system=_SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        # Log any text the agent says
        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"[agent] {block.text[:200]}", file=sys.stderr)

        if response.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")),
                "",
            )
            output_path = cfg.OUTPUT_DIR / output_filename
            return {
                "status": "complete",
                "message": final_text,
                "output": str(output_path) if output_path.exists() else None,
            }

        if response.stop_reason != "tool_use":
            return {
                "status": "error",
                "message": f"Unexpected stop_reason: {response.stop_reason}",
                "output": None,
            }

        # Process all tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            print(f"[tool] {block.name}({_summarize(block.input)})", file=sys.stderr)
            result_content = dispatch_tool(block.name, block.input)

            # Log text results; don't log raw image bytes
            if isinstance(result_content, str):
                preview = result_content[:300].replace("\n", " ")
                print(f"       → {preview}", file=sys.stderr)
            else:
                print(f"       → [image + text]", file=sys.stderr)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    return {
        "status": "max_turns",
        "message": f"Reached {cfg.MAX_AGENT_TURNS} turns without completing.",
        "output": None,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _summarize(inputs: dict) -> str:
    """Short human-readable summary of tool inputs for logging."""
    parts = []
    for k, v in inputs.items():
        s = str(v)
        parts.append(f"{k}={s[:60]!r}" if len(s) > 60 else f"{k}={v!r}")
    return ", ".join(parts)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate textbook math diagrams using TikZ, Matplotlib, or Graphviz.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("description", help="Natural-language description of the diagram.")
    parser.add_argument(
        "--output",
        default="diagram.png",
        metavar="FILENAME",
        help="Output filename saved to output/ (default: diagram.png).",
    )
    parser.add_argument(
        "--model",
        metavar="MODEL_ID",
        help=f"Override the Claude model (default: {cfg.DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        metavar="N",
        help=f"Override max agent turns (default: {cfg.MAX_AGENT_TURNS}).",
    )
    args = parser.parse_args()

    if args.model:
        cfg.DEFAULT_MODEL = args.model
    if args.max_turns:
        cfg.MAX_AGENT_TURNS = args.max_turns

    result = run_agent(args.description, args.output)

    print(json.dumps(result, indent=2))

    if result["status"] != "complete":
        sys.exit(1)


if __name__ == "__main__":
    main()
