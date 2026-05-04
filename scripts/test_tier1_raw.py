"""Test tier1 raw responses for a given model. Usage:

    python test_tier1_raw.py --model-name qwen/qwen3.5-397b-a17b --open-router --n 5
    python test_tier1_raw.py --model-name gemma-4-31b-it --n 5
"""

import argparse
import asyncio
import json
import os
import re
from pathlib import Path

# Load API keys from api_key.sh
api_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.sh")
with open(api_key_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("export ") and "=" in line:
            kv = line[len("export "):]
            k, v = kv.split("=", 1)
            os.environ[k] = v.strip('"').strip("'")

from client import OpenRouterClient, GeminiClient, OpenAIClient, ClaudeClient

BASE = os.path.dirname(os.path.abspath(__file__))

_SYSTEM = (
    "You are evaluating a visual perception question about a diagram. "
    "Answer based solely on what you can directly see in the image. "
    "Do not solve the problem, apply theorems, or perform calculations."
)

_USER_TEMPLATE = """\
Question: {question}

Options:
A. {A}
B. {B}
C. {C}
D. {D}

Respond with only a single letter: A, B, C, or D."""


def _extract_letter(text):
    if not text:
        return None
    text = text.strip()
    if text in ("A", "B", "C", "D"):
        return text
    m = re.match(r"^([ABCD])\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b([ABCD])\b", text)
    if m:
        return m.group(1)
    return None


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--open-router", action="store_true")
    parser.add_argument("--n", type=int, default=5, help="Number of sub-questions to test")
    args = parser.parse_args()

    if args.open_router:
        client = OpenRouterClient(
            model_name=args.model_name,
            api_key=os.environ["OPENROUTER_API_KEY"],
            thinking_effort="none",
            max_tokens=1024,
        )
    elif "gemini" in args.model_name.lower() or "gemma" in args.model_name.lower():
        client = GeminiClient(
            model_name=args.model_name,
            api_key=os.environ["GOOGLE_API_KEY"],
            thinking_effort="none",
            max_tokens=1024,
        )
    elif "gpt" in args.model_name.lower():
        client = OpenAIClient(
            model_name=args.model_name,
            api_key=os.environ["OPENAI_API_KEY"],
            thinking_effort="none",
            max_tokens=1024,
        )
    else:
        raise ValueError(f"Unsupported model: {args.model_name}")

    data = json.loads(Path(f"{BASE}/no_review_needed.json").read_text())
    base_dir = Path(BASE)

    tested = 0
    for item in data:
        if tested >= args.n:
            break
        images = item.get("images") or []
        encoded_images = [client.encode_image(base_dir / p) for p in images]

        for q in item.get("tier1_questions") or []:
            if tested >= args.n:
                break

            opts = q.get("options", {})
            user_text = _USER_TEMPLATE.format(
                question=q["question"],
                A=opts.get("A", ""),
                B=opts.get("B", ""),
                C=opts.get("C", ""),
                D=opts.get("D", ""),
            )

            img_idx = q.get("image_index", 0)
            img = encoded_images[img_idx] if img_idx < len(encoded_images) else encoded_images[0]
            content = [img, {"type": "text", "text": user_text}]

            messages = [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": content},
            ]

            try:
                response = await client.chat(messages, max_tokens=1024)
            except Exception as e:
                response = f"ERROR: {e}"

            majority = (q.get("reference_answers") or {}).get("majority_vote")
            letter = _extract_letter(response)

            print(f"Q: {q['question_id']}")
            print(f"  Question: {q['question'][:100]}")
            print(f"  Majority vote: {majority}")
            print(f"  Extracted letter: {letter}")
            print(f"  Raw response ({len(response)} chars): {response[:300]!r}")
            print(f"  Match: {'YES' if letter == majority else 'NO'}")
            print()
            tested += 1


asyncio.run(main())
