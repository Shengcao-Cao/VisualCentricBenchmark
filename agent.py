"""Diagram generation agent.

Usage:
    uv run agent.py "a right triangle with legs labeled a, b and hypotenuse c"
    uv run agent.py "sine and cosine on [-2π, 2π]" --output trig.png
    uv run agent.py "binary search tree with values 5,3,7,1,4" --output bst.png
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, AsyncGenerator

import config as cfg
from llm_client import (
    anthropic_content_to_openai,
    anthropic_tools_to_openai,
    get_async_client,
    get_client,
)
from session import ConversationSession, SessionStore
from tools import TOOL_DEFINITIONS, dispatch_tool

_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text(encoding="utf-8")

# Single store used by the server; CLI creates ephemeral sessions
_store = SessionStore()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _summarize(inputs: dict) -> str:
    """Short human-readable summary of tool inputs for logging."""
    parts = []
    for k, v in inputs.items():
        s = str(v)
        parts.append(f"{k}={s[:60]!r}" if len(s) > 60 else f"{k}={v!r}")
    return ", ".join(parts)


def _content_blocks_to_dicts(content) -> list[dict]:
    """Convert Anthropic SDK ContentBlock objects to plain dicts for message history."""
    result = []
    for block in content:
        if block.type == "text":
            result.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            result.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                }
            )
    return result


# ── Streaming dialogue turn (async, for the server) ───────────────────────────

async def run_turn_stream(
    session: ConversationSession,
    user_message: str,
) -> AsyncGenerator[tuple[str, dict], None]:
    """Run one user turn and yield SSE events as they occur.

    Yields ``(event_type, payload)`` tuples:
      text_delta     — partial assistant text as it streams
      tool_start     — tool invocation about to run
      tool_result    — tool finished (generic notification)
      render_ready   — a new render was produced; payload has render_id
      validate_result — validate_visual ran; payload has score/issues
      turn_complete  — agent said end_turn; payload has reply + render_id
      error          — unrecoverable problem
    """
    session.messages.append({"role": "user", "content": user_message})

    if cfg.API_PROVIDER == "openai":
        async for event in _stream_openai(session):
            yield event
        return

    # ── Anthropic streaming path ──────────────────────────────────────────────
    async for event in _stream_anthropic(session):
        yield event


async def _stream_anthropic(
    session: ConversationSession,
) -> AsyncGenerator[tuple[str, dict], None]:
    import anthropic

    client = get_async_client()
    loop = asyncio.get_event_loop()

    for _turn in range(cfg.MAX_AGENT_TURNS):
        async with client.messages.stream(
            model=cfg.DEFAULT_MODEL,
            max_tokens=8096,
            system=_SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=session.messages,
        ) as stream:
            # Yield text tokens as they arrive
            async for text in stream.text_stream:
                yield "text_delta", {"delta": text}

            final = await stream.get_final_message()

        # Store assistant turn in history (plain dicts, not SDK objects)
        session.messages.append(
            {"role": "assistant", "content": _content_blocks_to_dicts(final.content)}
        )

        if final.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in final.content if hasattr(b, "text")),
                "",
            )
            yield "turn_complete", {
                "reply": final_text,
                "render_id": session.current_render_id,
            }
            return

        if final.stop_reason != "tool_use":
            yield "error", {"message": f"Unexpected stop_reason: {final.stop_reason}"}
            return

        # Dispatch tool calls (sync backends run in thread pool)
        tool_results = []
        for block in final.content:
            if block.type != "tool_use":
                continue

            yield "tool_start", {"tool": block.name, "input": _summarize(block.input)}

            prev_render_id = session.current_render_id
            result_content = await loop.run_in_executor(
                None, dispatch_tool, block.name, block.input, session
            )

            # Emit render_ready when a new render was produced
            if session.current_render_id != prev_render_id and session.current_render_id:
                yield "render_ready", {
                    "render_id": session.current_render_id,
                    "backend": block.name.replace("render_", ""),
                }

            # Emit structured validate payload
            if block.name == "validate_visual" and isinstance(result_content, str):
                try:
                    vr = json.loads(result_content)
                    yield "validate_result", {
                        "render_id": session.current_render_id,
                        **vr,
                    }
                except Exception:
                    pass

            yield "tool_result", {"tool": block.name}

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                }
            )

        session.messages.append({"role": "user", "content": tool_results})

    yield "error", {"message": f"Reached {cfg.MAX_AGENT_TURNS} turns without completing."}


async def _stream_openai(
    session: ConversationSession,
) -> AsyncGenerator[tuple[str, dict], None]:
    """OpenAI streaming path — streams text deltas via the async client."""
    client = get_async_client()
    oai_tools = anthropic_tools_to_openai(TOOL_DEFINITIONS)
    loop = asyncio.get_event_loop()

    for _turn in range(cfg.MAX_AGENT_TURNS):
        # Build OpenAI message list: system first, then history
        oai_messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + session.messages

        # Collect full response while streaming text deltas
        accumulated_text = ""
        accumulated_tool_calls: dict[int, dict] = {}

        async with client.chat.completions.stream(
            model=cfg.DEFAULT_MODEL,
            max_completion_tokens=8096,
            messages=oai_messages,
            tools=oai_tools,
        ) as stream:
            async for event in stream:
                # OpenAI SDK may yield either raw chunk objects or wrapper events
                # (e.g. ChunkEvent with a .chunk attribute), depending on version.
                chunk = getattr(event, "chunk", event)
                if not getattr(chunk, "choices", None):
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    accumulated_text += delta.content
                    yield "text_delta", {"delta": delta.content}
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "id": tc_delta.id or "",
                                "name": (tc_delta.function and tc_delta.function.name) or "",
                                "arguments": "",
                            }
                        if tc_delta.function and tc_delta.function.arguments:
                            accumulated_tool_calls[idx]["arguments"] += (
                                tc_delta.function.arguments
                            )

            finish_reason = (await stream.get_final_completion()).choices[0].finish_reason

        # Build assistant message for history
        assistant_msg: dict = {"role": "assistant", "content": accumulated_text or None}
        if accumulated_tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                }
                for tc in sorted(accumulated_tool_calls.values(), key=lambda x: x["id"])
            ]
        session.messages.append(assistant_msg)

        if finish_reason == "stop":
            yield "turn_complete", {
                "reply": accumulated_text,
                "render_id": session.current_render_id,
            }
            return

        if finish_reason != "tool_calls":
            yield "error", {"message": f"Unexpected finish_reason: {finish_reason}"}
            return

        # Dispatch tools
        for tc in sorted(accumulated_tool_calls.values(), key=lambda x: x["id"]):
            tool_input = json.loads(tc["arguments"])
            yield "tool_start", {"tool": tc["name"], "input": _summarize(tool_input)}

            prev_render_id = session.current_render_id
            result_content = await loop.run_in_executor(
                None, dispatch_tool, tc["name"], tool_input, session
            )

            if session.current_render_id != prev_render_id and session.current_render_id:
                yield "render_ready", {
                    "render_id": session.current_render_id,
                    "backend": tc["name"].replace("render_", ""),
                }

            if tc["name"] == "validate_visual" and isinstance(result_content, str):
                try:
                    vr = json.loads(result_content)
                    yield "validate_result", {
                        "render_id": session.current_render_id,
                        **vr,
                    }
                except Exception:
                    pass

            yield "tool_result", {"tool": tc["name"]}

            if isinstance(result_content, list):
                result_content = anthropic_content_to_openai(result_content)

            session.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_content
                    if isinstance(result_content, str)
                    else json.dumps(result_content),
                }
            )

    yield "error", {"message": f"Reached {cfg.MAX_AGENT_TURNS} turns without completing."}


# ── Sync agent loop (CLI) ─────────────────────────────────────────────────────

def run_agent(description: str, output_filename: str = "diagram.png") -> dict[str, Any]:
    """Run the diagram agent for the given description (CLI / one-shot use).

    Returns a dict with keys:
        status  : "complete" | "max_turns" | "error"
        message : final agent message (if any)
        output  : Path to saved diagram (if saved)
    """
    session = ConversationSession(id="cli")
    if cfg.API_PROVIDER == "openai":
        return _run_openai(description, output_filename, session)
    return _run_anthropic(description, output_filename, session)


def _run_anthropic(
    description: str, output_filename: str, session: ConversationSession
) -> dict[str, Any]:
    client = get_client()

    session.messages.append(
        {
            "role": "user",
            "content": (
                f"{description}\n\n"
                f"Save the final diagram as: {output_filename}"
            ),
        }
    )

    print(f"[agent] Starting — {description!r}", file=sys.stderr)

    for turn in range(cfg.MAX_AGENT_TURNS):
        response = client.messages.create(
            model=cfg.DEFAULT_MODEL,
            max_tokens=8096,
            system=_SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=session.messages,
        )

        session.messages.append(
            {"role": "assistant", "content": _content_blocks_to_dicts(response.content)}
        )

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
            result_content = dispatch_tool(block.name, block.input, session)

            if isinstance(result_content, str):
                preview = result_content[:300].replace("\n", " ")
                print(f"       → {preview}", file=sys.stderr)
            else:
                print("       → [image + text]", file=sys.stderr)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                }
            )

        session.messages.append({"role": "user", "content": tool_results})

    return {
        "status": "max_turns",
        "message": f"Reached {cfg.MAX_AGENT_TURNS} turns without completing.",
        "output": None,
    }


def _run_openai(
    description: str, output_filename: str, session: ConversationSession
) -> dict[str, Any]:
    client = get_client()
    tools = anthropic_tools_to_openai(TOOL_DEFINITIONS)

    session.messages = [
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
            messages=session.messages,
            tools=tools,
        )

        choice = response.choices[0]

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
        session.messages.append(assistant_msg)

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
            result_content = dispatch_tool(tc.function.name, tool_input, session)

            if isinstance(result_content, list):
                result_content = anthropic_content_to_openai(result_content)

            if isinstance(result_content, str):
                preview = result_content[:300].replace("\n", " ")
                print(f"       → {preview}", file=sys.stderr)
            else:
                print("       → [image + text]", file=sys.stderr)

            session.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_content
                    if isinstance(result_content, str)
                    else json.dumps(result_content),
                }
            )

    return {
        "status": "max_turns",
        "message": f"Reached {cfg.MAX_AGENT_TURNS} turns without completing.",
        "output": None,
    }


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
