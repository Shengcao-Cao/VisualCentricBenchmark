"""CLI entry point for the VLM evaluation pipeline.

Usage:
    python run_pipeline.py answer  -i sampled_1000.json -o out1.json --model-name gpt-5.4
    python run_pipeline.py judge   -i out1.json         -o out2.json --model-name gpt-5.4
    python run_pipeline.py caption -i out2.json         -o out3.json --model-name gpt-5.4
    python run_pipeline.py all     -i sampled_1000.json -o final.json --model-name gpt-5.4
"""

import os
import argparse
import asyncio
from pathlib import Path

from client import ClaudeClient, GeminiClient, OpenAIClient
from tasks.answer import run_answer
from tasks.caption import run_caption
from tasks.difficulty import run_difficulty
from tasks.judge import run_judge
from tasks.structured import run_structured
from utils import load_dataset, save_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VLM evaluation pipeline")
    parser.add_argument(
        "task",
        choices=["answer", "judge", "caption", "difficulty", "all", "structured"],
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
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    data = load_dataset(args.input)
    base_dir = Path(args.base_dir) if args.base_dir else Path(args.input).parent

    # if args.model_name.startswith("gemini"):
    if "gemini" in args.model_name.lower():
        client = GeminiClient(model_name=args.model_name, api_key=args.api_key)
    elif "claude" in args.model_name.lower():
        client = ClaudeClient(model_name=args.model_name, api_key=args.api_key, region=args.region)
    elif "gpt" in args.model_name.lower():
        client = OpenAIClient(
            model_name=args.model_name,
            api_key=args.api_key,
            base_url=args.base_url,
        )
    else:
        raise ValueError(f"Unsupported model name: {args.model_name}")
    model_key = args.model_name

    if args.task == "answer":
        data = await run_answer(data, client, model_key, base_dir, args.concurrency)
    elif args.task == "judge":
        data = await run_judge(data, client, model_key, base_dir, args.concurrency)
    elif args.task == "caption":
        data = await run_caption(data, client, model_key, base_dir, args.concurrency)
    elif args.task == "difficulty":
        data = await run_difficulty(data, client, model_key, base_dir, args.concurrency)
    elif args.task == "structured":
        data = await run_structured(data, client, model_key, base_dir, args.concurrency)
    elif args.task == "all":
        # answer → judge → difficulty sequentially (each depends on prior)
        data = await run_answer(data, client, model_key, base_dir, args.concurrency)
        data = await run_judge(data, client, model_key, base_dir, args.concurrency)
        data = await run_difficulty(data, client, model_key, base_dir, args.concurrency)
        data = await run_caption(data, client, model_key, base_dir, args.concurrency)

    os.makedirs(Path(args.output).parent, exist_ok=True)
    save_dataset(data, args.output)
    print(f"Saved {len(data)} items to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
