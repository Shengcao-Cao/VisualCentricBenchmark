"""VLM client abstraction with OpenAI implementation."""

import asyncio
import base64
import logging
import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path

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
        self, messages: list[dict], max_tokens: int = 4096, temperature: float = 1.0
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
    def encode_image(image_path: str | Path) -> dict:
        """Encode a local image as a base64 data URL content part."""
        path = Path(image_path)
        mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{data}"},
        }


class OpenAIClient(VLMClient):
    """OpenAI Chat Completions API client with vision support."""

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
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_completion_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
