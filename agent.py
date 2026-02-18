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
import os
import re
import sys
import time
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

_TRACE_V = 1
_MAX_EVENT_BYTES = 65536
_TRUNCATION_SUFFIX = "...[truncated]"

_FIELD_LIMITS = {
    "tool": 64,
    "tool_use_id": 128,
    "input": 256,
    "input_full": 16384,
    "result_summary": 512,
    "result_text": 32768,
    "error.name": 128,
    "error.message": 1024,
    "error.stack": 8192,
    "redaction.rule": 64,
    "artifacts.kind": 64,
    "artifacts.reason": 64,
}

_REDACTION_RULE_LIMIT = 16
_ARTIFACT_OMITTED_LIMIT = 16

_SENSITIVE_EXACT_KEYS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "id_token",
    "token",
    "secret",
    "client_secret",
    "password",
    "passphrase",
    "private_key",
    "ssh_key",
}

_TEXT_REDACTION_PATTERNS: list[tuple[str, re.Pattern[str], Any]] = [
    (
        "auth_header",
        re.compile(r"(?i)authorization\s*[:=]\s*(bearer|basic)\s+[^\s\"]+"),
        lambda m: f"authorization: {m.group(1).lower()} [REDACTED]",
    ),
    (
        "header_secret",
        re.compile(r"(?i)(x-api-key|api-key|x-auth-token|x-access-token)\s*[:=]\s*[^\s\"]+"),
        lambda m: f"{m.group(1)}: [REDACTED]",
    ),
    (
        "openai_key",
        re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
        "sk-[REDACTED]",
    ),
    (
        "anthropic_key",
        re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
        "sk-ant-[REDACTED]",
    ),
    (
        "github_token",
        re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
        "ghp_[REDACTED]",
    ),
    (
        "github_token",
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
        "github_pat_[REDACTED]",
    ),
    (
        "slack_token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
        "xox*- [REDACTED]",
    ),
    (
        "private_key_block",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
        ),
        "[REDACTED_PRIVATE_KEY_BLOCK]",
    ),
    (
        "dotenv_line",
        re.compile(r"(?m)^([A-Z0-9_]{2,})=(.+)$"),
        lambda m: f"{m.group(1)}=[REDACTED]",
    ),
]

_ENV_LINE_KEYS = {"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL"}


def _utf8_size(value: str) -> int:
    return len(value.encode("utf-8"))


def _now_ms() -> int:
    return int(time.time() * 1000)


def _truncate_to_bytes(value: str, max_bytes: int) -> tuple[str, bool]:
    if _utf8_size(value) <= max_bytes:
        return value, False
    suffix = _TRUNCATION_SUFFIX
    suffix_bytes = _utf8_size(suffix)
    if max_bytes <= suffix_bytes:
        return suffix.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore"), True
    budget = max_bytes - suffix_bytes
    out_chars: list[str] = []
    used = 0
    for ch in value:
        size = _utf8_size(ch)
        if used + size > budget:
            break
        out_chars.append(ch)
        used += size
    return "".join(out_chars) + suffix, True


def _is_sensitive_key(key: str) -> bool:
    k = key.lower()
    if k in _SENSITIVE_EXACT_KEYS:
        return True
    return (
        k.endswith("_key")
        or k.endswith("_token")
        or k.endswith("_secret")
        or k.endswith("_password")
    )


def _redact_structured(value: Any, rules: set[str]) -> tuple[Any, bool]:
    changed = False
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if _is_sensitive_key(str(key)):
                out[key] = "[REDACTED]"
                changed = True
                rules.add("key_based")
                continue
            next_item, child_changed = _redact_structured(item, rules)
            changed = changed or child_changed
            out[key] = next_item
        return out, changed
    if isinstance(value, list):
        out_list = []
        for item in value:
            next_item, child_changed = _redact_structured(item, rules)
            changed = changed or child_changed
            out_list.append(next_item)
        return out_list, changed
    return value, False


def _build_env_secret_values() -> list[str]:
    values: list[str] = []
    for key, val in os.environ.items():
        if not val:
            continue
        upper_key = key.upper()
        looks_secret_name = (
            upper_key in _ENV_LINE_KEYS
            or "KEY" in upper_key
            or "TOKEN" in upper_key
            or "SECRET" in upper_key
            or "PASSWORD" in upper_key
            or "PASSPHRASE" in upper_key
            or "AUTH" in upper_key
        )
        if looks_secret_name or len(val) >= 20:
            values.append(val)
    values.sort(key=len, reverse=True)
    return values


_ENV_SECRET_VALUES = _build_env_secret_values()


def _redact_text(value: str, rules: set[str]) -> tuple[str, bool]:
    text = value
    changed_any = False

    while True:
        changed = False
        for rule_name, pattern, replacement in _TEXT_REDACTION_PATTERNS:
            text, count = pattern.subn(replacement, text)
            if count:
                changed = True
                changed_any = True
                rules.add(rule_name)

        new_lines = []
        env_line_redacted = False
        for line in text.splitlines(keepends=True):
            normalized = line.upper()
            if any(f"{k}=" in normalized for k in _ENV_LINE_KEYS):
                line = re.sub(r"=[^\s]+", "=[REDACTED]", line)
                env_line_redacted = True
            new_lines.append(line)
        if env_line_redacted:
            changed = True
            changed_any = True
            rules.add("env_line")
            text = "".join(new_lines)

        env_value_changed = False
        for env_val in _ENV_SECRET_VALUES:
            if env_val and env_val in text:
                text = text.replace(env_val, "[REDACTED_ENV]")
                env_value_changed = True
        if env_value_changed:
            changed = True
            changed_any = True
            rules.add("env_value")

        if not changed:
            break

    return text, changed_any


def _redact_jsonish(value: Any, *, mark_non_json_rule: str | None = None) -> tuple[str, bool, list[str]]:
    rules: set[str] = set()
    structured, structured_changed = _redact_structured(value, rules)
    try:
        text = json.dumps(structured, separators=(",", ":"), sort_keys=True)
    except TypeError:
        text = str(value)
        if mark_non_json_rule:
            rules.add(mark_non_json_rule)
    text, text_changed = _redact_text(text, rules)
    return text, (structured_changed or text_changed), sorted(rules)


def _clamp_string_list(values: list[str], max_items: int, max_item_bytes: int) -> list[str]:
    clamped = []
    for v in values[:max_items]:
        txt, _ = _truncate_to_bytes(str(v), max_item_bytes)
        clamped.append(txt)
    return clamped


def _estimate_base64_decoded_size(data: str) -> int:
    stripped = data.rstrip("=")
    return (len(stripped) * 3) // 4


def _project_result_text(result_content: Any) -> tuple[str | None, dict[str, Any] | None]:
    if isinstance(result_content, str):
        return result_content, {"has_binary": False, "omitted": []}

    if not isinstance(result_content, list):
        return str(result_content), {"has_binary": False, "omitted": []}

    texts: list[str] = []
    omitted: list[dict[str, Any]] = []
    has_binary = False

    for block in result_content:
        if not isinstance(block, dict):
            has_binary = True
            omitted.append({"kind": "unknown", "size_bytes": None, "reason": "binary_not_streamed"})
            continue

        block_type = str(block.get("type", "unknown"))
        if block_type == "text":
            text = block.get("text")
            if isinstance(text, str) and text:
                texts.append(text)
            continue

        has_binary = True
        kind = block_type
        size_bytes = None
        source = block.get("source") if isinstance(block.get("source"), dict) else None
        if source is not None:
            media_type = source.get("media_type")
            if isinstance(media_type, str) and media_type:
                kind = media_type
            if source.get("type") == "base64" and isinstance(source.get("data"), str):
                size_bytes = _estimate_base64_decoded_size(source["data"])

        omitted.append({"kind": kind, "size_bytes": size_bytes, "reason": "binary_not_streamed"})

    artifacts = {
        "has_binary": has_binary,
        "omitted": omitted[:_ARTIFACT_OMITTED_LIMIT],
    }
    if not texts:
        return None, artifacts
    return "\n".join(texts), artifacts


def _finalize_trace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    event_truncated = False

    payload["tool"], tool_changed = _truncate_to_bytes(str(payload.get("tool", "")), _FIELD_LIMITS["tool"])
    payload["tool_use_id"], id_changed = _truncate_to_bytes(
        str(payload.get("tool_use_id", "")), _FIELD_LIMITS["tool_use_id"]
    )
    event_truncated = event_truncated or tool_changed or id_changed

    redaction = payload.get("redaction") or {"mode": "stream", "applied": False, "rules": []}
    rules = redaction.get("rules") if isinstance(redaction, dict) else []
    if not isinstance(rules, list):
        rules = []
    redaction["rules"] = _clamp_string_list(rules, _REDACTION_RULE_LIMIT, _FIELD_LIMITS["redaction.rule"])
    redaction["mode"] = "stream"
    redaction["applied"] = bool(redaction.get("applied"))
    payload["redaction"] = redaction

    error_obj = payload.get("error")
    if isinstance(error_obj, dict):
        if error_obj.get("stack") is not None:
            error_obj["stack"], stack_changed = _truncate_to_bytes(
                str(error_obj["stack"]), _FIELD_LIMITS["error.stack"]
            )
            if stack_changed:
                error_obj["stack_truncated"] = True
            event_truncated = event_truncated or stack_changed
        if error_obj.get("name") is not None:
            error_obj["name"], name_changed = _truncate_to_bytes(
                str(error_obj["name"]), _FIELD_LIMITS["error.name"]
            )
            event_truncated = event_truncated or name_changed
        if error_obj.get("message") is not None:
            error_obj["message"], message_changed = _truncate_to_bytes(
                str(error_obj["message"]), _FIELD_LIMITS["error.message"]
            )
            event_truncated = event_truncated or message_changed
        payload["error"] = error_obj

    if payload.get("result_text") is not None:
        payload["result_text"], result_text_changed = _truncate_to_bytes(
            str(payload["result_text"]), _FIELD_LIMITS["result_text"]
        )
        if result_text_changed:
            payload["result_truncated"] = True
        event_truncated = event_truncated or result_text_changed

    if payload.get("input_full") is not None:
        payload["input_full"], input_full_changed = _truncate_to_bytes(
            str(payload["input_full"]), _FIELD_LIMITS["input_full"]
        )
        if input_full_changed:
            payload["input_truncated"] = True
        event_truncated = event_truncated or input_full_changed

    if payload.get("result_summary") is not None:
        payload["result_summary"], result_summary_changed = _truncate_to_bytes(
            str(payload["result_summary"]), _FIELD_LIMITS["result_summary"]
        )
        event_truncated = event_truncated or result_summary_changed

    if payload.get("input") is not None:
        payload["input"], input_changed = _truncate_to_bytes(str(payload["input"]), _FIELD_LIMITS["input"])
        event_truncated = event_truncated or input_changed

    artifacts = payload.get("artifacts")
    if isinstance(artifacts, dict):
        raw_omitted = artifacts.get("omitted")
        if not isinstance(raw_omitted, list):
            raw_omitted = []
        cleaned_omitted: list[dict[str, Any]] = []
        for item in raw_omitted[:_ARTIFACT_OMITTED_LIMIT]:
            if not isinstance(item, dict):
                continue
            kind, kind_changed = _truncate_to_bytes(
                str(item.get("kind", "unknown")), _FIELD_LIMITS["artifacts.kind"]
            )
            reason, reason_changed = _truncate_to_bytes(
                str(item.get("reason", "binary_not_streamed")), _FIELD_LIMITS["artifacts.reason"]
            )
            event_truncated = event_truncated or kind_changed or reason_changed
            size_bytes = item.get("size_bytes")
            cleaned_omitted.append(
                {
                    "kind": kind,
                    "size_bytes": size_bytes if isinstance(size_bytes, int) else None,
                    "reason": reason,
                }
            )
        artifacts["omitted"] = cleaned_omitted
        artifacts["has_binary"] = bool(artifacts.get("has_binary"))
        payload["artifacts"] = artifacts

    payload["size"] = {"event_bytes": 0, "event_truncated": event_truncated}

    def event_size() -> int:
        return _utf8_size(json.dumps(payload))

    for _ in range(8):
        size_now = event_size()
        if payload["size"]["event_bytes"] == size_now:
            break
        payload["size"]["event_bytes"] = size_now

    if payload["size"]["event_bytes"] > _MAX_EVENT_BYTES:
        payload["size"]["event_truncated"] = True
        if payload.get("result_text") is not None:
            payload["result_text"] = None
            payload["result_truncated"] = True
        if payload.get("input_full") is not None and event_size() > _MAX_EVENT_BYTES:
            payload["input_full"] = None
            payload["input_truncated"] = True
        for _ in range(8):
            size_now = event_size()
            if payload["size"]["event_bytes"] == size_now:
                break
            payload["size"]["event_bytes"] = size_now

    return payload


def _build_tool_start_payload(
    tool: str,
    tool_use_id: str,
    tool_input: Any,
    seq: int,
    ts_ms: int,
) -> dict[str, Any]:
    summary_raw = _summarize(tool_input if isinstance(tool_input, dict) else {"input": tool_input})
    summary_rules: set[str] = set()
    summary_redacted, summary_changed = _redact_text(summary_raw, summary_rules)

    input_full, input_full_redacted, full_rules = _redact_jsonish(
        tool_input,
        mark_non_json_rule="non_json_input",
    )
    input_full_size = _utf8_size(input_full)
    input_full_limited, input_full_truncated = _truncate_to_bytes(input_full, _FIELD_LIMITS["input_full"])

    all_rules = sorted(set(summary_rules) | set(full_rules))
    payload = {
        "tool": tool,
        "input": summary_redacted,
        "trace_v": _TRACE_V,
        "tool_use_id": tool_use_id,
        "ts_ms": ts_ms,
        "seq": seq,
        "input_full": input_full_limited,
        "input_full_size_bytes": input_full_size,
        "input_truncated": input_full_truncated,
        "redaction": {
            "mode": "stream",
            "applied": bool(summary_changed or input_full_redacted),
            "rules": all_rules,
        },
    }
    return _finalize_trace_payload(payload)


def _build_tool_result_payload(
    tool: str,
    tool_use_id: str,
    seq: int,
    ts_ms: int,
    started_ms: int | None,
    result_content: Any,
    tool_error: Exception | None,
) -> dict[str, Any]:
    status = "error" if tool_error else "ok"
    duration_ms = ts_ms - started_ms if started_ms is not None else None

    if tool_error is not None:
        raw_result_text = str(tool_error)
        artifacts = {"has_binary": False, "omitted": []}
    else:
        raw_result_text, artifacts = _project_result_text(result_content)

    rules: set[str] = set()
    result_summary = None
    result_text = None
    result_text_size = None
    result_truncated = False

    if raw_result_text is not None:
        result_text, _ = _redact_text(str(raw_result_text), rules)
        result_text_size = _utf8_size(result_text)
        result_text_limited, result_text_truncated = _truncate_to_bytes(
            result_text,
            _FIELD_LIMITS["result_text"],
        )
        result_text = result_text_limited
        result_truncated = result_text_truncated
        summary_seed = result_text
        summary_limited, _ = _truncate_to_bytes(summary_seed, _FIELD_LIMITS["result_summary"])
        result_summary = summary_limited if summary_limited else None

    error_obj = None
    if tool_error is not None:
        err_name, _ = _redact_text(tool_error.__class__.__name__, rules)
        err_message, _ = _redact_text(str(tool_error), rules)
        error_obj = {
            "name": err_name,
            "message": err_message,
            "stack": None,
            "stack_truncated": False,
        }
        result_summary = f"Tool failed: {err_name}"

    if isinstance(result_content, str) and status == "ok":
        lowered = result_content.lower()
        if lowered.startswith("render failed") or lowered.startswith("unknown tool"):
            status = "error"

    payload = {
        "tool": tool,
        "trace_v": _TRACE_V,
        "tool_use_id": tool_use_id,
        "ts_ms": ts_ms,
        "seq": seq,
        "status": status,
        "duration_ms": duration_ms,
        "result_summary": result_summary,
        "result_text": result_text,
        "result_text_size_bytes": result_text_size,
        "result_truncated": result_truncated,
        "error": error_obj,
        "artifacts": artifacts,
        "redaction": {
            "mode": "stream",
            "applied": bool(rules),
            "rules": sorted(rules),
        },
    }
    return _finalize_trace_payload(payload)


def _store_tool_trace_start(
    session: ConversationSession,
    tool: str,
    tool_use_id: str,
    tool_input: Any,
    started_at_ms: int,
    start_payload: dict[str, Any],
) -> None:
    summary_raw = _summarize(tool_input if isinstance(tool_input, dict) else {"input": tool_input})
    summary_rules: set[str] = set()
    input_summary, _ = _redact_text(summary_raw, summary_rules)
    input_full_untruncated, _, input_rules = _redact_jsonish(
        tool_input,
        mark_non_json_rule="non_json_input",
    )

    existing = session.traces.get(tool_use_id, {})
    existing_rules = existing.get("redaction_rules") if isinstance(existing, dict) else []
    merged_rules = sorted(
        set(input_rules)
        | set(summary_rules)
        | (set(existing_rules) if isinstance(existing_rules, list) else set())
    )

    session.traces[tool_use_id] = {
        "tool_use_id": tool_use_id,
        "tool": tool,
        "input_full_untruncated": input_full_untruncated,
        "input_summary": input_summary,
        "result_ok": None,
        "status": None,
        "result_text_untruncated": None,
        "result_summary": None,
        "started_at_ms": started_at_ms,
        "ended_at_ms": None,
        "duration_ms": None,
        "artifacts": None,
        "input_truncated": bool(start_payload.get("input_truncated")),
        "result_truncated": False,
        "event_truncated": bool(start_payload.get("size", {}).get("event_truncated")),
        "input_full_size_bytes": start_payload.get("input_full_size_bytes"),
        "result_text_size_bytes": None,
        "redaction_rules": merged_rules,
    }


def _store_tool_trace_result(
    session: ConversationSession,
    tool: str,
    tool_use_id: str,
    ended_at_ms: int,
    result_content: Any,
    tool_error: Exception | None,
    result_payload: dict[str, Any],
) -> None:
    if tool_error is not None:
        raw_result_text = str(tool_error)
        artifacts = {"has_binary": False, "omitted": []}
    else:
        raw_result_text, artifacts = _project_result_text(result_content)

    rules: set[str] = set()
    result_text_untruncated = None
    result_summary = None

    if raw_result_text is not None:
        result_text_untruncated, _ = _redact_text(str(raw_result_text), rules)
        result_summary, _ = _truncate_to_bytes(
            result_text_untruncated,
            _FIELD_LIMITS["result_summary"],
        )

    if tool_error is not None:
        err_name, _ = _redact_text(tool_error.__class__.__name__, rules)
        result_summary = f"Tool failed: {err_name}"

    trace = session.traces.get(tool_use_id, {})
    existing_rules = trace.get("redaction_rules") if isinstance(trace, dict) else []
    result_rules = result_payload.get("redaction", {}).get("rules")
    merged_rules = sorted(
        (set(existing_rules) if isinstance(existing_rules, list) else set())
        | set(rules)
        | (set(result_rules) if isinstance(result_rules, list) else set())
    )

    started_at_ms = trace.get("started_at_ms") if isinstance(trace, dict) else None
    duration_ms = (
        ended_at_ms - started_at_ms
        if isinstance(started_at_ms, int)
        else result_payload.get("duration_ms")
    )

    session.traces[tool_use_id] = {
        "tool_use_id": tool_use_id,
        "tool": tool,
        "input_full_untruncated": trace.get("input_full_untruncated") if isinstance(trace, dict) else None,
        "input_summary": trace.get("input_summary") if isinstance(trace, dict) else None,
        "result_ok": result_payload.get("status") == "ok",
        "status": result_payload.get("status"),
        "result_text_untruncated": result_text_untruncated,
        "result_summary": result_summary,
        "started_at_ms": started_at_ms,
        "ended_at_ms": ended_at_ms,
        "duration_ms": duration_ms,
        "artifacts": artifacts,
        "input_truncated": bool(trace.get("input_truncated")) if isinstance(trace, dict) else False,
        "result_truncated": bool(result_payload.get("result_truncated")),
        "event_truncated": bool(trace.get("event_truncated")) if isinstance(trace, dict) else False
        or bool(result_payload.get("size", {}).get("event_truncated")),
        "input_full_size_bytes": trace.get("input_full_size_bytes") if isinstance(trace, dict) else None,
        "result_text_size_bytes": result_payload.get("result_text_size_bytes"),
        "redaction_rules": merged_rules,
    }


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
        trace_seq = 0
        tool_start_ms: dict[str, int] = {}
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

            tool_use_id = block.id or f"tool_use_{_turn}_{len(tool_results) + 1}"
            start_ts = _now_ms()
            trace_seq += 1
            tool_start_ms[tool_use_id] = start_ts
            start_payload = _build_tool_start_payload(
                tool=block.name,
                tool_use_id=tool_use_id,
                tool_input=block.input,
                seq=trace_seq,
                ts_ms=start_ts,
            )
            _store_tool_trace_start(
                session=session,
                tool=block.name,
                tool_use_id=tool_use_id,
                tool_input=block.input,
                started_at_ms=start_ts,
                start_payload=start_payload,
            )
            yield "tool_start", start_payload

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

            result_ts = _now_ms()
            trace_seq += 1
            result_payload = _build_tool_result_payload(
                tool=block.name,
                tool_use_id=tool_use_id,
                seq=trace_seq,
                ts_ms=result_ts,
                started_ms=tool_start_ms.get(tool_use_id),
                result_content=result_content,
                tool_error=None,
            )
            _store_tool_trace_result(
                session=session,
                tool=block.name,
                tool_use_id=tool_use_id,
                ended_at_ms=result_ts,
                result_content=result_content,
                tool_error=None,
                result_payload=result_payload,
            )
            yield "tool_result", result_payload

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
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
        trace_seq = 0
        tool_start_ms: dict[str, int] = {}
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
        for index, tc in enumerate(sorted(accumulated_tool_calls.values(), key=lambda x: x["id"]), start=1):
            tool_input = json.loads(tc["arguments"])
            tool_use_id = tc["id"] or f"tool_call_{_turn}_{index}"
            start_ts = _now_ms()
            trace_seq += 1
            tool_start_ms[tool_use_id] = start_ts
            start_payload = _build_tool_start_payload(
                tool=tc["name"],
                tool_use_id=tool_use_id,
                tool_input=tool_input,
                seq=trace_seq,
                ts_ms=start_ts,
            )
            _store_tool_trace_start(
                session=session,
                tool=tc["name"],
                tool_use_id=tool_use_id,
                tool_input=tool_input,
                started_at_ms=start_ts,
                start_payload=start_payload,
            )
            yield "tool_start", start_payload

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

            result_ts = _now_ms()
            trace_seq += 1
            result_payload = _build_tool_result_payload(
                tool=tc["name"],
                tool_use_id=tool_use_id,
                seq=trace_seq,
                ts_ms=result_ts,
                started_ms=tool_start_ms.get(tool_use_id),
                result_content=result_content,
                tool_error=None,
            )
            _store_tool_trace_result(
                session=session,
                tool=tc["name"],
                tool_use_id=tool_use_id,
                ended_at_ms=result_ts,
                result_content=result_content,
                tool_error=None,
                result_payload=result_payload,
            )
            yield "tool_result", result_payload

            if isinstance(result_content, list):
                result_content = anthropic_content_to_openai(result_content)

            session.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_use_id,
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
