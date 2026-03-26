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
    skip_fn: Callable[[dict], bool] | None = None,
    output_path: str | Path | None = None,
    save_interval: int = 0,
) -> list[dict]:
    """Run an async function over a list of items with concurrency control.

    Args:
        skip_fn: If provided, items where skip_fn(item) is True are kept as-is.
        output_path: Path to save intermediate results (required if save_interval > 0).
        save_interval: Save results every N completed samples. 0 = disabled.
    """
    results: list[dict] = [None] * len(items)  # type: ignore[list-item]
    to_process: list[tuple[int, dict]] = []

    for i, item in enumerate(items):
        if skip_fn and skip_fn(item):
            results[i] = item
        else:
            to_process.append((i, item))

    if skip_fn:
        skipped = len(items) - len(to_process)
        if skipped:
            print(f"  Skipping {skipped}/{len(items)} already-completed samples")

    if not to_process:
        return results

    semaphore = asyncio.Semaphore(concurrency)
    completed = 0
    lock = asyncio.Lock()

    async def wrapper(idx: int, item: dict) -> None:
        nonlocal completed
        async with semaphore:
            result = await process_fn(item)
        results[idx] = result
        async with lock:
            completed += 1
            if save_interval > 0 and output_path and completed % save_interval == 0:
                save_dataset(results[:], output_path)
                print(f"  Checkpoint saved ({completed}/{len(to_process)} done)")

    tasks = [wrapper(idx, item) for idx, item in to_process]
    await tqdm_asyncio.gather(*tasks, desc=desc)

    # Final save if checkpointing was enabled
    if save_interval > 0 and output_path:
        save_dataset(results, output_path)
        print(f"  Final checkpoint saved ({len(to_process)}/{len(to_process)} done)")

    return results
