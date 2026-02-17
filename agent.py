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

import config as cfg
from llm_client import anthropic_content_to_openai, anthropic_tools_to_openai, get_client
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
    if cfg.API_PROVIDER == "openai":
        return _run_openai(description, output_filename)
    return _run_anthropic(description, output_filename)


def _run_anthropic(description: str, output_filename: str) -> dict[str, Any]:
    client = get_client()

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

        messages.append({"role": "assistant", "content": response.content})

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

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            print(f"[tool] {block.name}({_summarize(block.input)})", file=sys.stderr)
            result_content = dispatch_tool(block.name, block.input)

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


def _run_openai(description: str, output_filename: str) -> dict[str, Any]:
    client = get_client()
    tools = anthropic_tools_to_openai(TOOL_DEFINITIONS)

    messages: list[dict] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"{description}\n\n"
                f"Save the final diagram as: {output_filename}"
            ),
        },
    ]

    print(f"[agent] Starting — {description!r}", file=sys.stderr)

    for turn in range(cfg.MAX_AGENT_TURNS):
        response = client.chat.completions.create(
            model=cfg.DEFAULT_MODEL,
            max_completion_tokens=8096,
            messages=messages,
            tools=tools,
        )

        choice = response.choices[0]

        # Build assistant message; include tool_calls only when present
        assistant_msg: dict = {"role": "assistant", "content": choice.message.content}
        if choice.message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in choice.message.tool_calls
            ]
        messages.append(assistant_msg)

        if choice.message.content:
            print(f"[agent] {choice.message.content[:200]}", file=sys.stderr)

        if choice.finish_reason == "stop":
            output_path = cfg.OUTPUT_DIR / output_filename
            return {
                "status": "complete",
                "message": choice.message.content or "",
                "output": str(output_path) if output_path.exists() else None,
            }

        if choice.finish_reason != "tool_calls":
            return {
                "status": "error",
                "message": f"Unexpected finish_reason: {choice.finish_reason}",
                "output": None,
            }

        for tc in choice.message.tool_calls:
            tool_input = json.loads(tc.function.arguments)
            print(f"[tool] {tc.function.name}({_summarize(tool_input)})", file=sys.stderr)
            result_content = dispatch_tool(tc.function.name, tool_input)

            # Convert Anthropic image blocks to OpenAI image_url blocks
            if isinstance(result_content, list):
                result_content = anthropic_content_to_openai(result_content)

            if isinstance(result_content, str):
                preview = result_content[:300].replace("\n", " ")
                print(f"       → {preview}", file=sys.stderr)
            else:
                print("       → [image + text]", file=sys.stderr)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_content,
                }
            )

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
        help=f"Override the model (default: {cfg.DEFAULT_MODEL}).",
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
