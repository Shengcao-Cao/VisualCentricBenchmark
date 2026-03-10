"""Task 3: Generate detailed captions for each image in each question."""

import copy
from pathlib import Path

from client import VLMClient
from utils import run_batch

CAPTION_PROMPT = (
    "Describe the image above with as many details as possible. "
    "List each basic, atomic, elemental fact as a separate sentence. "
    "Only include facts that can be directly observed and verified from the image "
    "without any assumptions or deeper reasoning. "
    "Strictly follow the format that lists each sentence in a separate line starting with '* '."
)


async def run_caption(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
) -> list[dict]:
    """Caption each image and store under item["model"][model_key]["captions"]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        captions = []

        for img_path in item["images"]:
            image_part = client.encode_image(base_dir / img_path)
            messages = [
                {
                    "role": "user",
                    "content": [
                        image_part,
                        {"type": "text", "text": CAPTION_PROMPT},
                    ],
                }
            ]
            caption = await client.chat(messages)
            captions.append(caption)

        item.setdefault("model", {}).setdefault(model_key, {})["captions"] = captions
        return item

    return await run_batch(data, process, concurrency=concurrency, desc="Captioning")
