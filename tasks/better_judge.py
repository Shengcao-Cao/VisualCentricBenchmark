"""Improved judge: dedicated judge model, answer extraction, robust parsing with retry."""

import copy
import json
import re
from pathlib import Path

from json_repair import repair_json

from client import VLMClient
from utils import build_multimodal_content, run_batch

JUDGE_SYSTEM_PROMPT = """\
You are a strict but fair judge evaluating whether a model's answer is correct.

You will be given:
- A question (possibly with images)
- The ground-truth answer
- The model's final answer (extracted from a longer solution)
- The question type

Judging rules:
- Compare the model's final answer against the ground-truth answer.
- Do NOT re-derive or re-solve the problem. Just compare the two answers.
- For single_selection / multiple_selection: The model must select exactly the correct option letter(s). Minor formatting differences are OK (e.g., "A" vs "a" vs "(A)").
- For free_form: Be more lenient. The model's answer is correct if it is semantically equivalent to the ground truth. Accept equivalent mathematical expressions, different notations, rounding differences, or rephrased but correct answers.

Respond with EXACTLY this JSON format (no markdown fencing, no extra text):
{"correct": true/false, "reasoning": "brief explanation"}"""

MAX_PARSE_RETRIES = 3
TAIL_CHARS = 1500


def _extract_final_answer(answer: str) -> str:
    """Extract the final answer from a potentially long chain-of-thought response."""
    answer = str(answer)

    # Find the last \boxed{...} handling nested braces
    boxed = None
    for m in re.finditer(r"\\boxed\{", answer):
        start = m.end()
        depth = 1
        i = start
        while i < len(answer) and depth > 0:
            if answer[i] == "{":
                depth += 1
            elif answer[i] == "}":
                depth -= 1
            i += 1
        if depth == 0:
            boxed = answer[start : i - 1]

    tail = answer[-TAIL_CHARS:] if len(answer) > TAIL_CHARS else answer

    if boxed is not None:
        return f"\\boxed{{{boxed}}}\n\n(Context from end of solution):\n{tail}"

    return tail


def _parse_judge_response(response: str) -> dict | None:
    """Try to parse judge response as JSON. Returns None if unparseable."""
    try:
        result = json.loads(response)
        if isinstance(result, dict) and "correct" in result:
            return result
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        result = repair_json(response, return_objects=True)
        if isinstance(result, dict) and "correct" in result:
            return result
    except Exception:
        pass

    return None


def _format_gt_answer(answer) -> str:
    if isinstance(answer, list):
        return "; ".join(str(a) for a in answer)
    return str(answer)


async def run_better_judge(
    data: list[dict],
    judge_client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Judge each answer using a dedicated judge model with robust parsing."""
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
        final_answer = _extract_final_answer(model_answer)

        user_text = f"""Question: {item["question"]}
{f"Options: {options}" if options else ""}
Question type: {q_type}

Ground-truth answer: {gt_answer}
Model's final answer: {final_answer}"""

        content = build_multimodal_content(
            user_text, item["images"], base_dir, judge_client
        )

        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]

        last_response = ""
        for attempt in range(MAX_PARSE_RETRIES):
            response = await judge_client.chat(messages)
            last_response = response
            judge_result = _parse_judge_response(response)
            if judge_result is not None:
                item.setdefault("model", {}).setdefault(model_key, {})["judge"] = (
                    judge_result
                )
                return item

        item.setdefault("model", {}).setdefault(model_key, {})["judge"] = {
            "correct": False,
            "reasoning": f"Parse error after {MAX_PARSE_RETRIES} retries: {last_response}",
        }
        return item

    return await run_batch(
        data,
        process,
        concurrency=concurrency,
        desc="Judging (better)",
        skip_fn=skip_fn,
        output_path=output_path,
        save_interval=save_interval,
    )
