"""Shared utilities: message building, JSON I/O, async batch processing."""

import asyncio
import json
import re
from pathlib import Path
from typing import Any, Callable, Coroutine

from tqdm.asyncio import tqdm_asyncio

from client import VLMClient


def load_dataset(path: str | Path) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def save_dataset(data: list[dict], path: str | Path) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_multimodal_content(
    text: str, image_paths: list[str], base_dir: str | Path, client: VLMClient
) -> list[dict]:
    """Build a list of content parts by replacing <image_N> placeholders with images.

    Splits the text at each <image_N> placeholder and interleaves text parts
    with the corresponding encoded image. Any remaining images not referenced
    in the text are appended at the end.
    """
    base_dir = Path(base_dir)
    parts: list[dict] = []
    referenced: set[int] = set()

    # Split text around <image_N> placeholders
    segments = re.split(r"(<image_\d+>)", text)

    for segment in segments:
        match = re.fullmatch(r"<image_(\d+)>", segment)
        if match:
            idx = int(match.group(1)) - 1  # 0-based
            if 0 <= idx < len(image_paths):
                parts.append(client.encode_image(base_dir / image_paths[idx]))
                referenced.add(idx)
        else:
            stripped = segment.strip()
            if stripped:
                parts.append({"type": "text", "text": stripped})

    # Append any images not referenced in the text
    for idx, img_path in enumerate(image_paths):
        if idx not in referenced:
            parts.append(client.encode_image(base_dir / img_path))

    return parts


async def run_batch(
    items: list[dict],
    process_fn: Callable[[dict], Coroutine[Any, Any, dict]],
    concurrency: int = 10,
    desc: str = "Processing",
) -> list[dict]:
    """Run an async function over a list of items with concurrency control."""
    semaphore = asyncio.Semaphore(concurrency)

    async def wrapper(item: dict) -> dict:
        async with semaphore:
            return await process_fn(item)

    tasks = [wrapper(item) for item in items]
    results = await tqdm_asyncio.gather(*tasks, desc=desc)
    return list(results)
