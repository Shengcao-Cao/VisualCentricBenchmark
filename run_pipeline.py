"""CLI entry point for the VLM evaluation pipeline.

Usage:
    python run_pipeline.py answer  -i sampled_1000.json -o out1.json --model-name gpt-5.4
    python run_pipeline.py judge   -i out1.json         -o out2.json --model-name gpt-5.4
    python run_pipeline.py caption -i out2.json         -o out3.json --model-name gpt-5.4
    python run_pipeline.py all     -i sampled_1000.json -o final.json --model-name gpt-5.4

    # Tier 1 visual perception
    python run_pipeline.py generate_tier1     -i data.json -o out.json --model-name gpt-5.4
    python run_pipeline.py reference_answer_tier1  -i out.json  -o out.json --model-name gpt-5.4
"""

import argparse
import asyncio
from pathlib import Path

from client import ClaudeClient, GeminiClient, KimiClient, NovaClient, OpenAIClient, OpenRouterClient, QwenClient
from tasks.answer import run_answer
from tasks.answer_tier1 import run_answer_tier1
from tasks.answer_tier2 import run_answer_tier2
from tasks.answer_tier3 import run_answer_tier3
from tasks.caption import run_caption
from tasks.difficulty import run_difficulty
from tasks.better_judge import run_better_judge
from tasks.better_judge_tier2 import run_better_judge_tier2
from tasks.better_judge_tier3 import run_better_judge_tier3
from tasks.judge import run_judge
from tasks.perception import run_perception
from tasks.prune import run_prune
from tasks.generate_tier1 import run_generate_tier1
from tasks.reference_answer_tier1 import run_reference_answer_tier1
from tasks.structured import run_structured
from tasks.trivial_tier2 import run_trivial_tier2
from utils import load_dataset, save_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VLM evaluation pipeline")
    parser.add_argument(
        "task",
        choices=["answer", "answer_tier1", "answer_tier2", "answer_tier3", "judge", "better_judge", "better_judge_tier2", "better_judge_tier3", "caption", "difficulty", "perception", "prune", "trivial_tier2", "all", "structured",
                 "generate_tier1", "reference_answer_tier1"],
        help="Task to run",
    )
    parser.add_argument("-i", "--input", required=True, help="Input JSON path")
    parser.add_argument("-o", "--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--model-name",
        required=True,
        help="Model name (used as API model param and output key, e.g. gpt-5.4)",
    )
    parser.add_argument("--api-key", default=None, help="API key (or set OPENAI_API_KEY)")
    parser.add_argument("--base-url", default=None, help="API base URL")
    parser.add_argument("--region", default="us-east-2", help="AWS region for Bedrock (default: us-east-2)")
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Base directory for image paths (default: input file's parent dir)",
    )
    parser.add_argument("--concurrency", type=int, default=10, help="Max parallel requests")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip samples that already contain the target fields for the task",
    )
    parser.add_argument(
        "--save-interval",
        type=int,
        default=0,
        help="Save intermediate results every N completed samples (0 = disabled)",
    )
    parser.add_argument(
        "--thinking-effort",
        choices=["none", "low", "medium", "high"],
        default="low",
        help="Thinking/reasoning effort level (default: low)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=64000,
        help="Max output tokens per request (default: 64000)",
    )
    parser.add_argument(
        "--open-router",
        action="store_true",
        help="Use OpenRouter API (requires OPENROUTER_API_KEY)",
    )
    parser.add_argument(
        "--judge-model",
        default="gemini-3.1-flash-lite-preview",
        help="Model to use as judge for better_judge task (default: gemini-3.1-flash-lite-preview)",
    )
    parser.add_argument(
        "--judge-api-key",
        default=None,
        help="API key for the judge model (defaults to --api-key if not set)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    output_file = Path(args.output)

    # Resume support: if --skip-existing and the output file already exists,
    # load from it so that previously completed results are preserved.
    # Checkpoints may contain None entries for unprocessed items, so merge
    # with the original input to fill those gaps.
    data = load_dataset(args.input)
    if args.skip_existing and output_file.exists():
        saved = load_dataset(args.output)
        # Build ID-based lookup from saved results so resume works even when
        # the input file has new/reordered items compared to the output file.
        saved_by_id = {}
        for item in saved:
            if item is not None and isinstance(item, dict) and "id" in item:
                saved_by_id[item["id"]] = item
        if saved_by_id:
            merged = 0
            for i, item in enumerate(data):
                if item is not None and isinstance(item, dict) and item.get("id") in saved_by_id:
                    data[i] = saved_by_id[item["id"]]
                    merged += 1
            print(f"Resuming from existing output: {args.output} (merged {merged}/{len(saved_by_id)} saved, {len(data)} total items)")

    base_dir = Path(args.base_dir) if args.base_dir else Path(args.input).parent

    if args.open_router:
        client = OpenRouterClient(
            model_name=args.model_name,
            api_key=args.api_key,
            thinking_effort=args.thinking_effort,
            max_tokens=args.max_tokens,
        )
    elif "gemini" in args.model_name.lower() or "gemma" in args.model_name.lower():
        client = GeminiClient(
            model_name=args.model_name,
            api_key=args.api_key,
            thinking_effort=args.thinking_effort,
            max_tokens=args.max_tokens,
        )
    elif "claude" in args.model_name.lower():
        client = ClaudeClient(
            model_name=args.model_name,
            api_key=args.api_key,
            region=args.region,
            thinking_effort=args.thinking_effort,
            max_tokens=args.max_tokens,
        )
    elif "qwen" in args.model_name.lower():
        client = QwenClient(
            model_name=args.model_name,
            api_key=args.api_key,
            region=args.region,
            thinking_effort=args.thinking_effort,
            max_tokens=args.max_tokens,
        )
    elif "kimi" in args.model_name.lower():
        client = KimiClient(
            model_name=args.model_name,
            api_key=args.api_key,
            region=args.region,
            thinking_effort=args.thinking_effort,
            max_tokens=args.max_tokens,
        )
    elif "nova" in args.model_name.lower():
        client = NovaClient(
            model_name=args.model_name,
            api_key=args.api_key,
            region=args.region,
            thinking_effort=args.thinking_effort,
            max_tokens=args.max_tokens,
        )
    elif "gpt" in args.model_name.lower():
        client = OpenAIClient(
            model_name=args.model_name,
            api_key=args.api_key,
            base_url=args.base_url,
            thinking_effort=args.thinking_effort,
            max_tokens=args.max_tokens,
        )
    else:
        raise ValueError(f"Unsupported model name: {args.model_name}")
    model_key = args.model_name
    output_path = args.output
    save_interval = args.save_interval

    def make_skip_fn(fields: list[str]):
        """Return a skip function that checks if all given fields already exist."""
        if not args.skip_existing:
            return None

        def skip_fn(item: dict) -> bool:
            if item is None:
                return False
            model_data = item.get("model", {}).get(model_key, {})
            return all(model_data.get(f) is not None for f in fields)

        return skip_fn

    common = dict(output_path=output_path, save_interval=save_interval)

    def generate_tier1_skip(item: dict) -> bool:
        """Skip if tier1_questions already exists and is non-empty."""
        if not args.skip_existing or item is None:
            return False
        return bool(item.get("tier1_questions"))

    def reference_answers_skip(item: dict) -> bool:
        """Skip only if every question already has a vote from this model."""
        if not args.skip_existing or item is None:
            return False
        qs = item.get("tier1_questions") or []
        if not qs:
            return True
        return all(
            model_key in (q.get("reference_answers", {}).get("model_votes") or {})
            for q in qs
        )

    def answer_tier3_skip(item: dict) -> bool:
        """Skip if this model already has a prediction for the tier3 question."""
        if not args.skip_existing or item is None:
            return False
        qs = item.get("tier3_questions") or []
        if not qs:
            return True
        return model_key in (qs[0].get("predictions") or {})

    def answer_tier2_skip(item: dict) -> bool:
        """Skip if this model already has a prediction for the tier2 question."""
        if not args.skip_existing or item is None:
            return False
        qs = item.get("tier2_questions") or []
        if not qs:
            return True
        return model_key in (qs[0].get("predictions") or {})

    def answer_tier1_skip(item: dict) -> bool:
        """Skip if every tier1 sub-question already has a prediction from this model."""
        if not args.skip_existing or item is None:
            return False
        qs = item.get("tier1_questions") or []
        if not qs:
            return True
        return all(
            model_key in (q.get("predictions") or {})
            for q in qs
        )

    if args.task == "answer":
        data = await run_answer(data, client, model_key, base_dir, args.concurrency,
                                skip_fn=make_skip_fn(["answer"]), **common)
    elif args.task == "answer_tier1":
        data = await run_answer_tier1(data, client, model_key, base_dir, args.concurrency,
                                      skip_fn=answer_tier1_skip, **common)
    elif args.task == "answer_tier2":
        data = await run_answer_tier2(data, client, model_key, base_dir, args.concurrency,
                                      skip_fn=answer_tier2_skip, **common)
    elif args.task == "answer_tier3":
        data = await run_answer_tier3(data, client, model_key, base_dir, args.concurrency,
                                      skip_fn=answer_tier3_skip, **common)
    elif args.task == "judge":
        data = await run_judge(data, client, model_key, base_dir, args.concurrency,
                               skip_fn=make_skip_fn(["judge"]), **common)
    elif args.task == "better_judge":
        judge_model = args.judge_model
        judge_api_key = args.judge_api_key or args.api_key
        if "gemini" in judge_model.lower() or "gemma" in judge_model.lower():
            judge_client = GeminiClient(
                model_name=judge_model, api_key=judge_api_key,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        elif "gpt" in judge_model.lower():
            judge_client = OpenAIClient(
                model_name=judge_model, api_key=judge_api_key,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        elif "claude" in judge_model.lower():
            judge_client = ClaudeClient(
                model_name=judge_model, api_key=judge_api_key, region=args.region,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported judge model: {judge_model}")
        data = await run_better_judge(data, judge_client, model_key, base_dir, args.concurrency,
                                      skip_fn=make_skip_fn(["judge"]), **common)
    elif args.task == "better_judge_tier2":
        judge_model = args.judge_model
        judge_api_key = args.judge_api_key or args.api_key
        if "gemini" in judge_model.lower() or "gemma" in judge_model.lower():
            judge_client = GeminiClient(
                model_name=judge_model, api_key=judge_api_key,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        elif "gpt" in judge_model.lower():
            judge_client = OpenAIClient(
                model_name=judge_model, api_key=judge_api_key,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        elif "claude" in judge_model.lower():
            judge_client = ClaudeClient(
                model_name=judge_model, api_key=judge_api_key, region=args.region,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported judge model: {judge_model}")

        def better_judge_tier2_skip(item: dict) -> bool:
            if not args.skip_existing or item is None:
                return False
            qs = item.get("tier2_questions") or []
            if not qs:
                return True
            return model_key in (qs[0].get("scoring") or {})

        data = await run_better_judge_tier2(data, judge_client, model_key, base_dir, args.concurrency,
                                             skip_fn=better_judge_tier2_skip, **common)
    elif args.task == "better_judge_tier3":
        judge_model = args.judge_model
        judge_api_key = args.judge_api_key or args.api_key
        if "gemini" in judge_model.lower() or "gemma" in judge_model.lower():
            judge_client = GeminiClient(
                model_name=judge_model, api_key=judge_api_key,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        elif "gpt" in judge_model.lower():
            judge_client = OpenAIClient(
                model_name=judge_model, api_key=judge_api_key,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        elif "claude" in judge_model.lower():
            judge_client = ClaudeClient(
                model_name=judge_model, api_key=judge_api_key, region=args.region,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported judge model: {judge_model}")

        def better_judge_tier3_skip(item: dict) -> bool:
            if not args.skip_existing or item is None:
                return False
            qs = item.get("tier3_questions") or []
            if not qs:
                return True
            return model_key in (qs[0].get("scoring") or {})

        data = await run_better_judge_tier3(data, judge_client, model_key, base_dir, args.concurrency,
                                             skip_fn=better_judge_tier3_skip, **common)
    elif args.task == "caption":
        data = await run_caption(data, client, model_key, base_dir, args.concurrency,
                                 skip_fn=make_skip_fn(["captions"]), **common)
    elif args.task == "difficulty":
        data = await run_difficulty(data, client, model_key, base_dir, args.concurrency,
                                    skip_fn=make_skip_fn(["difficulty"]), **common)
    elif args.task == "perception":
        data = await run_perception(data, client, model_key, base_dir, args.concurrency,
                                    skip_fn=make_skip_fn(["perception"]), **common)
    elif args.task == "prune":
        data = await run_prune(data, client, model_key, base_dir, args.concurrency,
                               skip_fn=make_skip_fn(["pruned_question"]), **common)
    elif args.task == "trivial_tier2":
        judge_model = args.judge_model
        judge_api_key = args.judge_api_key or args.api_key
        if "gemini" in judge_model.lower() or "gemma" in judge_model.lower():
            judge_client = GeminiClient(
                model_name=judge_model, api_key=judge_api_key,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        elif "gpt" in judge_model.lower():
            judge_client = OpenAIClient(
                model_name=judge_model, api_key=judge_api_key,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        elif "claude" in judge_model.lower():
            judge_client = ClaudeClient(
                model_name=judge_model, api_key=judge_api_key, region=args.region,
                thinking_effort=args.thinking_effort, max_tokens=args.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported judge model: {judge_model}")

        def trivial_tier2_skip(item: dict) -> bool:
            if not args.skip_existing or item is None:
                return False
            qs = item.get("tier2_questions") or []
            if not qs:
                return True
            return qs[0].get("trivial") is not None

        data = await run_trivial_tier2(data, judge_client, base_dir, args.concurrency,
                                        skip_fn=trivial_tier2_skip, **common)
    elif args.task == "structured":
        data = await run_structured(data, client, model_key, base_dir, args.concurrency)
    elif args.task == "generate_tier1":
        data = await run_generate_tier1(
            data, client, model_key, base_dir, args.concurrency,
            skip_fn=generate_tier1_skip, **common,
        )
    elif args.task == "reference_answer_tier1":
        data = await run_reference_answer_tier1(
            data, client, model_key, base_dir, args.concurrency,
            skip_fn=reference_answers_skip, **common,
        )
    elif args.task == "all":
        data = await run_answer(data, client, model_key, base_dir, args.concurrency,
                                skip_fn=make_skip_fn(["answer"]), **common)
        data = await run_judge(data, client, model_key, base_dir, args.concurrency,
                               skip_fn=make_skip_fn(["judge"]), **common)
        data = await run_difficulty(data, client, model_key, base_dir, args.concurrency,
                                    skip_fn=make_skip_fn(["difficulty"]), **common)
        data = await run_caption(data, client, model_key, base_dir, args.concurrency,
                                 skip_fn=make_skip_fn(["captions"]), **common)

    save_dataset(data, output_path)
    print(f"Saved {len(data)} items to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
