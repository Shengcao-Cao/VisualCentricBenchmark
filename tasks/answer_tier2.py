"""Task: Answer tier2 pruned questions with original images.

Input format (filtered substantive tier2 items):
    Each item has top-level ``question_type``, ``options``, ``images``, ``answer``,
    and ``tier2_questions[0]["pruned_question"]`` as the question text.

Stores the model response under tier2_questions[0]["predictions"][model_key].
"""

import copy
from pathlib import Path

from client import VLMClient
from utils import build_multimodal_content, run_batch

SYSTEM_PROMPT_SELECTION = """\
You are an expert problem solver. Answer the following question by selecting the correct option(s).
Show your full reasoning and solution process step by step.
{selection_instruction}"""

SYSTEM_PROMPT_FREE_FORM = """\
You are an expert problem solver. Answer the following question.
Show your full reasoning and solution process step by step.
At the very end, clearly state your final answer on its own line in the format:
\\boxed{your final answer}"""

SINGLE_SELECTION_INSTRUCTION = (
    "At the very end, state your chosen option letter on its own line in the format:\n"
    "\\boxed{your chosen letter}\n"
    "For example: \\boxed{A}"
)
MULTIPLE_SELECTION_INSTRUCTION = (
    "At the very end, state your chosen option letters on its own line in the format:\n"
    "\\boxed{your chosen letters}\n"
    "For example: \\boxed{A, C}"
)


def _format_options(options: list[str]) -> str:
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "\n".join(f"{labels[i]}. {opt}" for i, opt in enumerate(options))


async def run_answer_tier2(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Answer each tier2 pruned question and store result under predictions[model_key]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        q = item["tier2_questions"][0]

        q_type = item["question_type"]
        question_text = q["pruned_question"]
        options = item.get("options")

        # Build system prompt
        if q_type in ("single_selection", "multiple_selection"):
            instruction = (
                SINGLE_SELECTION_INSTRUCTION
                if q_type == "single_selection"
                else MULTIPLE_SELECTION_INSTRUCTION
            )
            system = SYSTEM_PROMPT_SELECTION.format(selection_instruction=instruction)
            if options:
                question_text += "\n\nOptions:\n" + _format_options(options)
        else:
            system = SYSTEM_PROMPT_FREE_FORM

        # Build multimodal user message using the original images
        content = build_multimodal_content(
            question_text, item["images"], base_dir, client
        )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ]

        response = await client.chat(messages)

        # Store result
        q.setdefault("predictions", {})[model_key] = response
        return item

    return await run_batch(
        data, process, concurrency=concurrency, desc="Answering (tier2)",
        skip_fn=skip_fn, output_path=output_path, save_interval=save_interval,
    )
