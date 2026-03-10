"""Task 4: Judge the difficulty level of each question."""

import copy
import json
import re
from pathlib import Path

from client import VLMClient
from utils import build_multimodal_content, run_batch

DIFFICULTY_SYSTEM_PROMPT = """\
You are an expert educator evaluating the difficulty of a question.

You will be given:
- A question (possibly with images)
- The ground-truth answer
- The model's full solution attempt (if available)
- Whether the model answered correctly (if available)
- Question metadata (domain, subdomain, question type)

Rate the difficulty on a 1-5 scale:

1 - Trivial: Direct observation or simple recall. No reasoning needed. (e.g., read a value off a chart, identify a basic shape)
2 - Easy: One straightforward reasoning step or basic formula application. (e.g., compute area of a rectangle, solve a one-step equation)
3 - Medium: Multi-step reasoning combining 2-3 concepts. Requires careful thought. (e.g., Pythagorean theorem + trigonometry, multi-step algebra)
4 - Hard: Complex reasoning chains, creative insight, or advanced domain knowledge. Many students would struggle. (e.g., olympiad-style geometry, multi-variable optimization)
5 - Very Hard: Deep expertise, novel problem-solving strategies, or synthesis across multiple advanced topics. Even strong models frequently fail. (e.g., competition math, advanced proofs)

Consider:
- The inherent complexity of the question and number of reasoning steps required
- The depth of domain knowledge needed
- The complexity of the ground-truth solution path
- The model's solution attempt as a calibration signal (long chain of reasoning or incorrect answer suggests higher difficulty), but do NOT rely solely on model correctness

Respond with EXACTLY this JSON format (no markdown fencing):
{"difficulty": <1-5>, "reasoning": "brief explanation"}"""


def _format_gt_answer(answer) -> str:
    if isinstance(answer, list):
        return "; ".join(str(a) for a in answer)
    return str(answer)


async def run_difficulty(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
) -> list[dict]:
    """Rate difficulty and store under item["model"][model_key]["difficulty"]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        gt_answer = _format_gt_answer(item["answer"])
        model_data = item.get("model", {}).get(model_key, {})
        model_answer = model_data.get("answer")
        judge_result = model_data.get("judge")

        # Build context about model performance
        model_info = ""
        if model_answer is not None:
            model_info += f"\nModel's solution:\n{model_answer}"
        if judge_result is not None:
            correct = judge_result.get("correct", "unknown")
            model_info += f"\nModel answered correctly: {correct}"

        user_text = f"""Question: {item["question"]}
Question type: {item["question_type"]}
Domain: {item.get("domain", "unknown")}
Subdomain: {item.get("subdomain", "unknown")}

Ground-truth answer: {gt_answer}{model_info}"""

        content = build_multimodal_content(
            user_text, item["images"], base_dir, client
        )

        messages = [
            {"role": "system", "content": DIFFICULTY_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]

        response = await client.chat(messages)

        # Parse JSON response
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group())
                except json.JSONDecodeError:
                    result = {"difficulty": -1, "reasoning": f"Parse error: {response}"}
            else:
                result = {"difficulty": -1, "reasoning": f"Parse error: {response}"}

        item.setdefault("model", {}).setdefault(model_key, {})["difficulty"] = result
        return item

    return await run_batch(
        data, process, concurrency=concurrency, desc="Rating difficulty"
    )
