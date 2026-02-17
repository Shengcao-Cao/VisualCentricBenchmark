"""Provider abstraction for Anthropic and OpenAI-compatible APIs."""
from __future__ import annotations

import config as cfg


def get_client():
    """Return an initialized API client for the configured provider."""
    if cfg.API_PROVIDER == "openai":
        import openai
        # Always pass base_url explicitly so the openai SDK doesn't pick up a
        # blank OPENAI_BASE_URL env var that dotenv may have set from the .env file.
        kwargs: dict = {
            "base_url": cfg.OPENAI_BASE_URL or "https://api.openai.com/v1",
        }
        if cfg.OPENAI_API_KEY:
            kwargs["api_key"] = cfg.OPENAI_API_KEY
        return openai.OpenAI(**kwargs)
    import anthropic
    return anthropic.Anthropic()


def anthropic_tools_to_openai(tools: list[dict]) -> list[dict]:
    """Convert Anthropic tool definitions to OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in tools
    ]


def anthropic_content_to_openai(content: str | list[dict]) -> str | list[dict]:
    """Convert Anthropic-style content blocks to OpenAI message content format.

    Handles:
      {"type": "text", "text": ...}
      {"type": "image", "source": {"type": "base64", "media_type": ..., "data": ...}}
    """
    if isinstance(content, str):
        return content
    result = []
    for block in content:
        if block["type"] == "text":
            result.append({"type": "text", "text": block["text"]})
        elif block["type"] == "image":
            src = block["source"]
            url = f"data:{src['media_type']};base64,{src['data']}"
            result.append({"type": "image_url", "image_url": {"url": url}})
    return result


def simple_completion(
    messages: list[dict],
    system: str,
    model: str,
    max_tokens: int,
) -> str:
    """Single-shot completion (supports text + images); returns the text response.

    ``messages`` may contain Anthropic-style content blocks; they are converted
    automatically when talking to an OpenAI-compatible endpoint.
    """
    client = get_client()
    if cfg.API_PROVIDER == "openai":
        full_messages = [{"role": "system", "content": system}]
        for m in messages:
            msg = dict(m)
            if isinstance(msg.get("content"), list):
                msg["content"] = anthropic_content_to_openai(msg["content"])
            full_messages.append(msg)
        response = client.chat.completions.create(
            model=model,
            max_completion_tokens=max_tokens,
            messages=full_messages,
        )
        return response.choices[0].message.content or ""
    else:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text
