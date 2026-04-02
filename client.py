"""VLM client abstraction with OpenAI, Gemini, and Claude implementations."""

import asyncio
import base64
import io
import logging
from abc import ABC, abstractmethod
from pathlib import Path

import json
import os

from PIL import Image

import boto3
import botocore.config
from google import genai
from google.genai import types
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class VLMClient(ABC):
    """Base class for vision-language model clients."""

    @abstractmethod
    async def _call(
        self, messages: list[dict], max_tokens: int, temperature: float
    ) -> str:
        """Execute the actual API call. Subclasses implement this."""
        ...

    async def chat(
        self, messages: list[dict], max_tokens: int = 20000, temperature: float = 1.0
    ) -> str:
        """Send a chat request with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                return await self._call(messages, max_tokens, temperature)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait = min(2**attempt, 60)
                logger.warning(
                    "Attempt %d/%d failed (%s: %s), retrying in %ds...",
                    attempt + 1,
                    self.max_retries,
                    type(e).__name__,
                    str(e)[:200],
                    wait,
                )
                await asyncio.sleep(wait)

    @staticmethod
    def _detect_mime(data: bytes) -> str:
        """Detect image MIME type from file magic bytes."""
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if data[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "image/webp"
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return "image/gif"
        return "image/png"

    # Default limits — subclasses or env vars can override
    MAX_IMAGE_DIMENSION = 8000
    MAX_IMAGE_BYTES = 0  # 0 = no file-size limit by default

    # Valid thinking effort levels across providers
    VALID_THINKING_EFFORTS = ("none", "low", "medium", "high")

    def __init__(self, model_name: str, max_retries: int = 5, thinking_effort: str = "low"):
        self.model_name = model_name
        self.max_retries = max_retries
        if thinking_effort not in self.VALID_THINKING_EFFORTS:
            raise ValueError(
                f"Invalid thinking_effort '{thinking_effort}', "
                f"must be one of {self.VALID_THINKING_EFFORTS}"
            )
        self.thinking_effort = thinking_effort
        # Allow env-var overrides: VLM_MAX_IMAGE_DIM, VLM_MAX_IMAGE_BYTES
        self.max_image_dim = int(os.environ.get("VLM_MAX_IMAGE_DIM", self.MAX_IMAGE_DIMENSION))
        self.max_image_bytes = int(os.environ.get("VLM_MAX_IMAGE_BYTES", self.MAX_IMAGE_BYTES))

    @staticmethod
    def _resize_if_needed(raw: bytes, max_dim: int, max_bytes: int = 0) -> bytes:
        """Downscale image if dimensions exceed max_dim or size exceeds max_bytes."""
        img = Image.open(io.BytesIO(raw))
        orig_w, orig_h = img.size
        fmt = img.format or ("PNG" if VLMClient._detect_mime(raw) == "image/png" else "JPEG")

        # Step 1: dimension-based resize
        w, h = orig_w, orig_h
        if w > max_dim or h > max_dim:
            scale = max_dim / max(w, h)
            w, h = int(w * scale), int(h * scale)
            img = img.resize((w, h), Image.LANCZOS)

        # Step 2: file-size-based resize — progressively shrink until under limit
        def _encode(image: Image.Image, fmt: str) -> bytes:
            if fmt in ("JPEG", "WEBP") and image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            buf = io.BytesIO()
            save_kwargs = {"format": fmt}
            if fmt in ("JPEG", "WEBP"):
                save_kwargs["quality"] = 85
            image.save(buf, **save_kwargs)
            return buf.getvalue()

        result = _encode(img, fmt)
        if max_bytes > 0:
            while len(result) > max_bytes and max(w, h) > 256:
                scale = 0.75
                w, h = int(w * scale), int(h * scale)
                img = img.resize((w, h), Image.LANCZOS)
                result = _encode(img, fmt)

        if (w, h) != (orig_w, orig_h):
            logger.info(
                "Resized image from %dx%d to %dx%d (%d bytes)",
                orig_w, orig_h, w, h, len(result),
            )
        return result

    def encode_image(self, image_path: str | Path) -> dict:
        """Encode a local image as a base64 data URL content part."""
        path = Path(image_path)
        with open(path, "rb") as f:
            raw = f.read()
        raw = VLMClient._resize_if_needed(raw, self.max_image_dim, self.max_image_bytes)
        mime_type = VLMClient._detect_mime(raw)
        data = base64.b64encode(raw).decode("utf-8")
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{data}"},
        }


class OpenAIClient(VLMClient):
    """OpenAI Responses API client with vision support."""

    # OpenAI supports: none, minimal, low, medium, high, xhigh
    _EFFORT_MAP = {"none": "none", "low": "low", "medium": "medium", "high": "high"}

    def __init__(
        self,
        model_name: str = "gpt-5.4",
        api_key: str | None = None,
        base_url: str | None = None,
        max_retries: int = 5,
        thinking_effort: str = "low",
    ):
        super().__init__(model_name, max_retries=max_retries, thinking_effort=thinking_effort)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def _call(
        self, messages: list[dict], max_tokens: int, temperature: float
    ) -> str:
        instructions = None
        input_messages = []
        for msg in messages:
            if msg["role"] == "system":
                instructions = msg["content"] if isinstance(msg["content"], str) else msg["content"]
            else:
                input_messages.append(self._convert_message(msg))

        reasoning = (
            {"effort": self._EFFORT_MAP[self.thinking_effort]}
            if self.thinking_effort != "none"
            else None
        )
        kwargs = dict(
            model=self.model_name,
            input=input_messages,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        if reasoning:
            kwargs["reasoning"] = reasoning
        if instructions:
            kwargs["instructions"] = instructions

        response = await self.client.responses.create(**kwargs)
        return response.output_text

    @staticmethod
    def _convert_message(msg: dict) -> dict:
        """Convert Chat Completions message format to Responses API format."""
        content = msg.get("content", "")
        if isinstance(content, str):
            return {"role": msg["role"], "content": content}
        # Convert multimodal content parts
        parts = []
        for part in content:
            if part["type"] == "text":
                parts.append({"type": "input_text", "text": part["text"]})
            elif part["type"] == "image_url":
                parts.append({"type": "input_image", "image_url": part["image_url"]["url"]})
        return {"role": msg["role"], "content": parts}


class ClaudeClient(VLMClient):
    """Claude API client via AWS Bedrock (boto3 invoke_model) with vision support.

    Authenticates using AWS_BEARER_TOKEN_BEDROCK env var.
    """

    # Bedrock enforces 5 MB base64 limit; 3.9 MB raw ≈ 5.2 MB encoded
    MAX_IMAGE_BYTES = 3_900_000

    # Bedrock adaptive thinking + output_config effort: low, medium, high
    _EFFORT_MAP = {"none": None, "low": "low", "medium": "medium", "high": "high"}

    def __init__(
        self,
        model_name: str = "us.anthropic.claude-opus-4-6-v1",
        api_key: str | None = None,
        region: str = "us-west-2",
        max_retries: int = 5,
        thinking_effort: str = "low",
    ):
        super().__init__(model_name, max_retries=max_retries, thinking_effort=thinking_effort)
        token = api_key or os.environ["AWS_BEARER_TOKEN_BEDROCK"]
        session = boto3.Session()
        self.client = session.client(
            "bedrock-runtime",
            region_name=region,
            config=botocore.config.Config(read_timeout=3600),
            aws_access_key_id="bedrock",
            aws_secret_access_key="bedrock",
            aws_session_token=token,
        )

    async def _call(
        self, messages: list[dict], max_tokens: int, temperature: float
    ) -> str:
        system = None
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"] if isinstance(msg["content"], str) else msg["content"]
            else:
                api_messages.append(self._convert_message(msg))

        effort = self._EFFORT_MAP[self.thinking_effort]
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": api_messages,
        }
        if effort:
            body["thinking"] = {"type": "adaptive"}
            body["output_config"] = {"effort": effort}
        else:
            body["thinking"] = {"type": "disabled"}
        if system:
            body["system"] = system

        response = await asyncio.to_thread(
            self.client.invoke_model,
            modelId=self.model_name,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        result = json.loads(response["body"].read())
        # With thinking enabled, response may contain thinking blocks; extract the text block
        for block in result["content"]:
            if block.get("type") == "text":
                return block["text"]
        # No text block found — model likely exhausted max_tokens during thinking
        stop = result.get("stop_reason", "unknown")
        block_types = [b.get("type") for b in result.get("content", [])]
        raise RuntimeError(
            f"Claude response contained no text block (stop_reason={stop}, "
            f"blocks={block_types}). Try increasing max_tokens or lowering thinking_effort."
        )

    @staticmethod
    def _convert_message(msg: dict) -> dict:
        """Convert OpenAI-style message to Bedrock Claude format."""
        content = msg.get("content", "")
        if isinstance(content, str):
            return {"role": msg["role"], "content": content}
        parts = []
        for part in content:
            if part["type"] == "text":
                parts.append({"type": "text", "text": part["text"]})
            elif part["type"] == "image_url":
                url = part["image_url"]["url"]
                if url.startswith("data:"):
                    header, b64_data = url.split(",", 1)
                    media_type = header.split(":")[1].split(";")[0]
                    parts.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_data,
                        },
                    })
        return {"role": msg["role"], "content": parts}


class GeminiClient(VLMClient):
    """Google Gemini API client with vision support."""

    # Gemini 3.x thinking levels: minimal, low, medium, high
    _EFFORT_MAP = {"none": "minimal", "low": "low", "medium": "medium", "high": "high"}

    def __init__(
        self,
        model_name: str = "gemini-3.1-pro-preview",
        api_key: str | None = None,
        max_retries: int = 5,
        thinking_effort: str = "low",
    ):
        super().__init__(model_name, max_retries=max_retries, thinking_effort=thinking_effort)
        self.client = genai.Client(api_key=api_key)

    # Disable safety filters to avoid MALFORMED_RESPONSE / silent None returns.
    # Only the 4 standard text categories are accepted by the API;
    # image-specific and jailbreak categories cause INVALID_ARGUMENT errors.
    _SAFETY_SETTINGS = [
        types.SafetySetting(category=c, threshold=types.HarmBlockThreshold.OFF)
        for c in [
            types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        ]
    ]

    async def _call(
        self, messages: list[dict], max_tokens: int, temperature: float
    ) -> str:
        contents = self._convert_messages(messages)
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                thinking_config=types.ThinkingConfig(
                    thinking_level=self._EFFORT_MAP[self.thinking_effort]
                ),
                safety_settings=self._SAFETY_SETTINGS,
            ),
        )
        try:
            text = response.text
        except Exception:
            text = None
        if text is None:
            # Gather diagnostic info safely
            try:
                cand = response.candidates[0] if response.candidates else None
                finish = getattr(cand, 'finish_reason', 'unknown') if cand else 'no_candidates'
                parts = cand.content.parts if (cand and cand.content) else []
                part_info = [getattr(p, 'thought', False) for p in parts]
            except Exception:
                finish, part_info = 'unknown', []
            raise RuntimeError(
                f"Gemini returned no text (finish_reason={finish}, "
                f"parts_are_thought={part_info}). "
                f"Try increasing max_tokens or lowering thinking_effort."
            )
        return text

    @staticmethod
    def _convert_messages(messages: list[dict]) -> list[types.Content]:
        """Convert OpenAI-style messages to Gemini Content objects."""
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            parts = []
            content = msg.get("content", "")
            if isinstance(content, str):
                parts.append(types.Part.from_text(text=content))
            elif isinstance(content, list):
                for item in content:
                    if item["type"] == "text":
                        parts.append(types.Part.from_text(text=item["text"]))
                    elif item["type"] == "image_url":
                        url = item["image_url"]["url"]
                        if url.startswith("data:"):
                            header, b64_data = url.split(",", 1)
                            mime = header.split(":")[1].split(";")[0]
                            parts.append(
                                types.Part.from_bytes(
                                    data=base64.b64decode(b64_data),
                                    mime_type=mime,
                                )
                            )
                        else:
                            parts.append(types.Part.from_uri(file_uri=url))
            contents.append(types.Content(role=role, parts=parts))
        return contents
