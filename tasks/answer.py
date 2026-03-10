"""Task 1: Answer questions with images."""

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


async def run_answer(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
) -> list[dict]:
    """Answer each question and store result under item["model"][model_key]["answer"]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        q_type = item["question_type"]
        question_text = item["question"]
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

        # Build multimodal user message
        content = build_multimodal_content(
            question_text, item["images"], base_dir, client
        )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ]

        response = await client.chat(messages)

        # Store result
        item.setdefault("model", {}).setdefault(model_key, {})["answer"] = response
        return item

    return await run_batch(data, process, concurrency=concurrency, desc="Answering")
