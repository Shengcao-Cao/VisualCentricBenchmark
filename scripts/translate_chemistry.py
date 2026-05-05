"""Translate Chinese chemistry items to English using Gemini 3.1 Flash-Lite."""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client import GeminiClient
from utils import load_dataset, save_dataset, run_batch

TRANSLATE_PROMPT = """\
Translate the following JSON object from Chinese to English. This is a chemistry exam question.

Rules:
- Translate all Chinese text to English.
- Keep ALL LaTeX math expressions exactly as-is (do not translate content inside $...$ or \\(...\\)).
- Keep ALL image tags like <image_1>, <image_2> exactly as-is in their original positions.
- Keep the JSON keys exactly as-is (they are already in English).
- Keep option labels (A:, B:, C:, D:, etc.) exactly as-is.
- If text is already in English, keep it unchanged.
- Return ONLY the translated JSON object, no explanation.

JSON to translate:
```json
{json_input}
```"""


def has_chinese(text) -> bool:
    if isinstance(text, list):
        return any(has_chinese(t) for t in text)
    return bool(re.search(r"[一-鿿]", str(text)))


def extract_translatable(item: dict) -> dict:
    """Extract fields that need translation from an item."""
    fields = {}
    if has_chinese(item.get("question", "")):
        fields["question"] = item["question"]
    if item.get("options"):
        if any(has_chinese(o) for o in item["options"]):
            fields["options"] = item["options"]
    if has_chinese(item.get("answer", "")):
        fields["answer"] = item["answer"]
    return fields


def apply_translation(item: dict, translated: dict) -> dict:
    """Apply translated fields back to the item."""
    result = dict(item)
    for key in ("question", "options", "answer"):
        if key in translated:
            result[key] = translated[key]
    return result


async def translate_item(item: dict, client: GeminiClient) -> dict:
    """Translate one chemistry item (both top-level and tier3_questions)."""
    result = dict(item)

    # Translate top-level fields
    top_fields = extract_translatable(item)
    if top_fields:
        prompt = TRANSLATE_PROMPT.format(json_input=json.dumps(top_fields, ensure_ascii=False, indent=2))
        response = await client.chat(
            [{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.0,
        )
        translated = _parse_json(response)
        if translated:
            result = apply_translation(result, translated)

    # Translate tier3_questions
    if item.get("tier3_questions"):
        new_tier3 = []
        for t3 in item["tier3_questions"]:
            t3_fields = extract_translatable(t3)
            if t3_fields:
                prompt = TRANSLATE_PROMPT.format(
                    json_input=json.dumps(t3_fields, ensure_ascii=False, indent=2)
                )
                response = await client.chat(
                    [{"role": "user", "content": prompt}],
                    max_tokens=4096,
                    temperature=0.0,
                )
                translated = _parse_json(response)
                if translated:
                    new_tier3.append(apply_translation(t3, translated))
                else:
                    new_tier3.append(t3)
            else:
                new_tier3.append(t3)
        result["tier3_questions"] = new_tier3

    return result


def _parse_json(text: str) -> dict | None:
    """Parse JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # remove opening ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import json_repair
            return json_repair.loads(text)
        except Exception:
            print(f"  [WARN] Failed to parse JSON response: {text[:200]}")
            return None


async def main():
    parser = argparse.ArgumentParser(description="Translate Chinese chemistry items to English")
    parser.add_argument("-i", "--input", required=True, help="Input JSON file")
    parser.add_argument("-o", "--output", required=True, help="Output JSON file")
    parser.add_argument("--api-key", default=None, help="Google API key (or set GOOGLE_API_KEY)")
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--save-interval", type=int, default=10)
    parser.add_argument("--skip-existing", action="store_true", help="Skip already-translated items")
    args = parser.parse_args()

    data = load_dataset(args.input)
    print(f"Loaded {len(data)} items from {args.input}")

    # Load existing output for skip-existing
    if args.skip_existing and Path(args.output).exists():
        existing = load_dataset(args.output)
        existing_map = {}
        for item in existing:
            if item is not None:
                existing_map[item["id"]] = item
        for i, item in enumerate(data):
            if item["id"] in existing_map:
                data[i] = existing_map[item["id"]]
        print(f"  Loaded {len(existing_map)} existing translations")

    client = GeminiClient(
        model_name="gemini-3.1-flash-lite-preview",
        api_key=args.api_key,
        thinking_effort="none",
        max_retries=5,
    )

    def needs_translation(item: dict) -> bool:
        if has_chinese(item.get("question", "")):
            return True
        if item.get("options") and any(has_chinese(o) for o in item["options"]):
            return True
        if has_chinese(item.get("answer", "")):
            return True
        for t3 in item.get("tier3_questions", []):
            if has_chinese(t3.get("question", "")):
                return True
            if t3.get("options") and any(has_chinese(o) for o in t3["options"]):
                return True
            if has_chinese(t3.get("answer", "")):
                return True
        return False

    async def process(item: dict) -> dict:
        return await translate_item(item, client)

    results = await run_batch(
        data,
        process,
        concurrency=args.concurrency,
        desc="Translating",
        skip_fn=lambda item: not needs_translation(item),
        output_path=args.output,
        save_interval=args.save_interval,
    )

    save_dataset(results, args.output)
    translated_count = sum(1 for r in results if not needs_translation(r))
    print(f"Done. {translated_count}/{len(results)} items are now in English.")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
