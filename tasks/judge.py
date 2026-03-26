"""Task 2: Judge whether model answers are correct."""

import copy
from pathlib import Path

from client import VLMClient
from utils import build_multimodal_content, run_batch

JUDGE_SYSTEM_PROMPT = """\
You are a strict but fair judge evaluating whether a model's answer is correct.

You will be given:
- A question (possibly with images)
- The ground-truth answer
- The model's full solution (which may contain step-by-step reasoning followed by a final answer in \\boxed{...})
- The question type

Judging rules:
- Focus on the model's FINAL ANSWER (typically in \\boxed{...}). The intermediate reasoning is context but the final boxed answer is what matters.
- For single_selection / multiple_selection: The model must select exactly the correct option letter(s). Minor formatting differences are OK (e.g., "A" vs "a" vs "(A)").
- For free_form: Be more lenient. The model's answer is correct if it is semantically equivalent to the ground truth. Accept equivalent mathematical expressions, different notations, rounding differences, or rephrased but correct answers.

Respond with EXACTLY this JSON format (no markdown fencing):
{"correct": true/false, "reasoning": "brief explanation"}"""


def _format_gt_answer(answer) -> str:
    if isinstance(answer, list):
        return "; ".join(str(a) for a in answer)
    return str(answer)


async def run_judge(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Judge each answer and store result under item["model"][model_key]["judge"]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        model_data = item.get("model", {}).get(model_key, {})
        model_answer = model_data.get("answer")

        if model_answer is None:
            item.setdefault("model", {}).setdefault(model_key, {})["judge"] = {
                "correct": False,
                "reasoning": "No model answer found.",
            }
            return item

        gt_answer = _format_gt_answer(item["answer"])
        q_type = item["question_type"]
        options = item.get("options")

        # Build the judging prompt with images for context
        user_text = f"""Question: {item["question"]}
{f"Options: {options}" if options else ""}
Question type: {q_type}

Ground-truth answer: {gt_answer}
Model's answer: {model_answer}"""

        content = build_multimodal_content(
            user_text, item["images"], base_dir, client
        )

        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]

        response = await client.chat(messages)

        # Parse JSON response
        import json

        try:
            judge_result = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    judge_result = json.loads(match.group())
                except json.JSONDecodeError:
                    judge_result = {"correct": False, "reasoning": f"Parse error: {response}"}
            else:
                judge_result = {"correct": False, "reasoning": f"Parse error: {response}"}

        item.setdefault("model", {}).setdefault(model_key, {})["judge"] = judge_result
        return item

    return await run_batch(
        data, process, concurrency=concurrency, desc="Judging",
        skip_fn=skip_fn, output_path=output_path, save_interval=save_interval,
    )
