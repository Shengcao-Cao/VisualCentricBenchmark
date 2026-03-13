"""VLM client abstraction with OpenAI, Gemini, and Claude implementations."""

import asyncio
import base64
import logging
from abc import ABC, abstractmethod
from pathlib import Path

import json
import os

import boto3
import botocore.config
from google import genai
from google.genai import types
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class VLMClient(ABC):
    """Base class for vision-language model clients."""

    def __init__(self, model_name: str, max_retries: int = 5):
        self.model_name = model_name
        self.max_retries = max_retries

    @abstractmethod
    async def _call(
        self, messages: list[dict], max_tokens: int, temperature: float
    ) -> str:
        """Execute the actual API call. Subclasses implement this."""
        ...

    async def chat(
        self, messages: list[dict], max_tokens: int = 8192, temperature: float = 1.0
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

    @staticmethod
    def encode_image(image_path: str | Path) -> dict:
        """Encode a local image as a base64 data URL content part."""
        path = Path(image_path)
        with open(path, "rb") as f:
            raw = f.read()
        mime_type = VLMClient._detect_mime(raw)
        data = base64.b64encode(raw).decode("utf-8")
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{data}"},
        }


class OpenAIClient(VLMClient):
    """OpenAI Responses API client with vision support."""

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
        max_retries: int = 5,
    ):
        super().__init__(model_name, max_retries=max_retries)
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

        kwargs = dict(
            model=self.model_name,
            input=input_messages,
            reasoning={"effort": "low"},
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
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

    def __init__(
        self,
        model_name: str = "us.anthropic.claude-sonnet-4-20250514-v1:0",
        api_key: str | None = None,
        region: str = "us-west-2",
        max_retries: int = 5,
    ):
        super().__init__(model_name, max_retries=max_retries)
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

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": api_messages,
        }
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
        return result["content"][0]["text"]

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

    def __init__(
        self,
        model_name: str = "gemini-3.1-pro-preview",
        api_key: str | None = None,
        max_retries: int = 5,
    ):
        super().__init__(model_name, max_retries=max_retries)
        self.client = genai.Client(api_key=api_key)

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
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        return response.text

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
