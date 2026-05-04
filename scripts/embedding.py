#!/usr/bin/env python3
"""Compute Gemini multimodal embeddings for all questions in all_data.json.

Each question's text has <image_1>, <image_2>, ... placeholders that map to the
corresponding entries in the item's `images` list (1-indexed). The script builds
a multimodal Content with interleaved text and image parts, then calls the
Gemini embedding API.

Embeddings are saved incrementally to `embeddings.npz` (arrays: `ids`, `embeddings`).
A checkpoint file tracks which IDs are already done so the script can be resumed.

Usage:
    python embedding.py                        # defaults
    python embedding.py --input all_data.json --output embeddings.npz
    python embedding.py --batch-size 20 --workers 5
"""

import argparse
import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types
from PIL import Image
from tqdm import tqdm

API_KEY = os.environ.get("GOOGLE_API_KEY", "")
MODEL = "gemini-embedding-2-preview"
EMBEDDING_DIM = 3072

# Rate limit: Gemini free tier is ~1500 RPM; be conservative
MAX_WORKERS = 5
RETRY_LIMIT = 5
RETRY_BACKOFF = 2.0     # seconds, doubled each retry
MAX_IMAGE_DIM = 4096    # resize images larger than this
MAX_IMAGE_PARTS = 6     # Gemini embedding API limit


def load_image_bytes(img_path: Path) -> tuple[bytes, str]:
    """Load an image, resizing if any dimension exceeds MAX_IMAGE_DIM.

    Always returns PNG bytes to avoid mime-type mismatches (some files have
    wrong extensions).
    """
    img = Image.open(img_path)
    w, h = img.size
    if max(w, h) > MAX_IMAGE_DIM:
        scale = MAX_IMAGE_DIM / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    if img.mode == "RGBA":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), "image/png"


def build_content(question: str, images: list[str], base_dir: Path) -> types.Content:
    """Parse <image_N> placeholders and build a multimodal Content object.

    Splits the question on placeholders, interleaving text parts and image parts.
    Only images referenced in the question text are included.
    """
    # Split on <image_N> keeping the delimiter
    segments = re.split(r"(<image_\d+>)", question)
    parts: list[types.Part] = []
    image_count = 0

    for seg in segments:
        m = re.fullmatch(r"<image_(\d+)>", seg)
        if m:
            idx = int(m.group(1)) - 1  # 0-indexed
            if 0 <= idx < len(images) and image_count < MAX_IMAGE_PARTS:
                img_path = base_dir / images[idx]
                img_bytes, mime = load_image_bytes(img_path)
                parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
                image_count += 1
        else:
            text = seg.strip()
            if text:
                parts.append(types.Part(text=text))

    return types.Content(parts=parts)


def embed_one(
    client: genai.Client, item: dict, base_dir: Path
) -> tuple[str, np.ndarray | None, str | None]:
    """Embed a single item. Returns (id, embedding_or_None, error_or_None)."""
    item_id = item["id"]
    try:
        content = build_content(item["question"], item.get("images", []), base_dir)
        result = client.models.embed_content(model=MODEL, contents=[content])
        vec = np.array(result.embeddings[0].values, dtype=np.float32)
        return item_id, vec, None
    except Exception as e:
        return item_id, None, str(e)


def embed_with_retry(
    client: genai.Client, item: dict, base_dir: Path
) -> tuple[str, np.ndarray | None, str | None]:
    """Embed with exponential backoff retry."""
    delay = RETRY_BACKOFF
    for attempt in range(RETRY_LIMIT):
        item_id, vec, err = embed_one(client, item, base_dir)
        if vec is not None:
            return item_id, vec, None
        # Don't retry on non-transient errors
        if err and ("not found" in err.lower() or "INVALID_ARGUMENT" in err):
            return item_id, None, err
        if attempt < RETRY_LIMIT - 1:
            time.sleep(delay)
            delay *= 2
    return item_id, None, err


def save_checkpoint(output_path: Path, id_list: list[str], emb_list: list[np.ndarray]):
    """Save current embeddings to npz."""
    if not id_list:
        return
    np.savez(
        output_path,
        ids=np.array(id_list),
        embeddings=np.stack(emb_list),
    )


def main():
    parser = argparse.ArgumentParser(description="Compute multimodal embeddings.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("all_data.json"),
        help="Input JSON file (default: all_data.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("embeddings.npz"),
        help="Output npz file (default: embeddings.npz)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Save checkpoint every N items (default: 100)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=MAX_WORKERS,
        help=f"Concurrent API workers (default: {MAX_WORKERS})",
    )
    args = parser.parse_args()

    base_dir = args.input.parent

    with open(args.input) as f:
        items = json.load(f)
    print(f"Loaded {len(items):,} items from {args.input}")

    # Resume from existing checkpoint
    done_ids: set[str] = set()
    id_list: list[str] = []
    emb_list: list[np.ndarray] = []
    if args.output.exists():
        data = np.load(args.output, allow_pickle=True)
        id_list = list(data["ids"])
        emb_list = list(data["embeddings"])
        done_ids = set(id_list)
        print(f"Resuming: {len(done_ids):,} embeddings already computed")

    pending = [it for it in items if it["id"] not in done_ids]
    print(f"Remaining: {len(pending):,} items to embed")

    if not pending:
        print("Nothing to do.")
        return

    client = genai.Client(api_key=API_KEY)
    errors: list[tuple[str, str]] = []

    pbar = tqdm(total=len(pending), desc="Embedding", unit="item")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(embed_with_retry, client, item, base_dir): item["id"]
            for item in pending
        }

        for future in as_completed(futures):
            item_id, vec, err = future.result()

            if vec is not None:
                id_list.append(item_id)
                emb_list.append(vec)
            else:
                errors.append((item_id, err or "unknown"))
                pbar.write(f"  FAILED: {item_id}: {err}")

            pbar.update(1)
            pbar.set_postfix(ok=len(id_list), fail=len(errors))

            if pbar.n % args.batch_size == 0:
                save_checkpoint(args.output, id_list, emb_list)
                pbar.write(
                    f"  checkpoint saved ({len(id_list)}/{len(items)} total)"
                )

    pbar.close()

    # Final save
    save_checkpoint(args.output, id_list, emb_list)
    print(f"\nDone: {len(id_list):,} embeddings saved to {args.output}")
    if errors:
        print(f"Errors: {len(errors)}")
        for eid, emsg in errors[:10]:
            print(f"  {eid}: {emsg}")


if __name__ == "__main__":
    main()
