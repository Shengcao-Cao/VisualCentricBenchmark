"""Ablation tasks: answer and judge original/tier2 questions under modified input settings.

Three ablation modes:
  - text_only:         Remove images, replace <image_N> with [Image N hidden].
  - text_caption:      Remove images, replace <image_N> with its atomic fact caption.
  - text_image_caption: Keep images and append captions as supplementary context.

Each mode works for both the original question (T0) and the pruned question (T2).

Answers stored under:
  T0: model[model_key]["ablation_answer"]
  T2: tier2_questions[0]["ablation_predictions"][model_key]

Judgments stored under:
  T0: model[model_key]["ablation_judge"]
  T2: tier2_questions[0]["ablation_scoring"][model_key]
"""

import copy
import json
import re
from pathlib import Path

from json_repair import repair_json

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
\\boxed{{your final answer}}"""

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

TEXT_ONLY_NOTE = (
    "\n\nNote: The image(s) referenced in this problem are not available. "
    "Please attempt to answer the question based solely on the textual information provided."
)

TEXT_CAPTION_NOTE = (
    "\n\nNote: The image(s) referenced in this problem are not directly available. "
    "Instead, detailed descriptions of each image are provided inline. "
    "Please use these descriptions to answer the question."
)

TEXT_IMAGE_CAPTION_NOTE = (
    "\n\nNote: In addition to the image(s), detailed descriptions of each image "
    "are provided as supplementary context to aid your understanding."
)


def _format_options(options: list[str]) -> str:
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "\n".join(f"{labels[i]}. {opt}" for i, opt in enumerate(options))


def _replace_image_tags_text_only(text: str) -> str:
    return re.sub(r"<image_(\d+)>", r"[Image \1 hidden]", text)


def _replace_image_tags_with_captions(text: str, captions: list[str]) -> str:
    def replacer(m):
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(captions):
            return f"[Description of Image {idx + 1}]\n{captions[idx]}\n[End of Image {idx + 1} Description]"
        return m.group(0)
    return re.sub(r"<image_(\d+)>", replacer, text)


def _insert_captions_after_image_tags(text: str, captions: list[str]) -> str:
    def replacer(m):
        idx = int(m.group(1)) - 1
        tag = m.group(0)
        if 0 <= idx < len(captions):
            return f"{tag}\n[Description of Image {idx + 1}]\n{captions[idx]}\n[End of Image {idx + 1} Description]"
        return tag
    return re.sub(r"<image_(\d+)>", replacer, text)


async def run_answer_ablation(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    mode: str,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Answer original questions under an ablation setting."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        q_type = item["question_type"]
        question_text = item["question"]
        options = item.get("options")
        captions = item.get("atomic_captions") or []

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

        if mode == "text_only":
            question_text = _replace_image_tags_text_only(question_text) + TEXT_ONLY_NOTE
            content = [{"type": "text", "text": question_text}]
        elif mode == "text_caption":
            question_text = _replace_image_tags_with_captions(question_text, captions) + TEXT_CAPTION_NOTE
            content = [{"type": "text", "text": question_text}]
        elif mode == "text_image_caption":
            question_text = _insert_captions_after_image_tags(question_text, captions) + TEXT_IMAGE_CAPTION_NOTE
            content = build_multimodal_content(
                question_text, item["images"], base_dir, client
            )
        else:
            raise ValueError(f"Unknown ablation mode: {mode}")

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ]
        response = await client.chat(messages)
        item.setdefault("model", {}).setdefault(model_key, {})["ablation_answer"] = response
        return item

    return await run_batch(
        data, process, concurrency=concurrency, desc=f"Answering ({mode})",
        skip_fn=skip_fn, output_path=output_path, save_interval=save_interval,
    )


async def run_answer_tier2_ablation(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    mode: str,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Answer tier2 pruned questions under an ablation setting."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        q = item["tier2_questions"][0]
        q_type = item["question_type"]
        question_text = q["pruned_question"]
        options = item.get("options")
        captions = item.get("atomic_captions") or []

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

        if mode == "text_only":
            question_text = _replace_image_tags_text_only(question_text) + TEXT_ONLY_NOTE
            content = [{"type": "text", "text": question_text}]
        elif mode == "text_caption":
            question_text = _replace_image_tags_with_captions(question_text, captions) + TEXT_CAPTION_NOTE
            content = [{"type": "text", "text": question_text}]
        elif mode == "text_image_caption":
            question_text = _insert_captions_after_image_tags(question_text, captions) + TEXT_IMAGE_CAPTION_NOTE
            content = build_multimodal_content(
                question_text, item["images"], base_dir, client
            )
        else:
            raise ValueError(f"Unknown ablation mode: {mode}")

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ]
        response = await client.chat(messages)
        q.setdefault("ablation_predictions", {})[model_key] = response
        return item

    return await run_batch(
        data, process, concurrency=concurrency, desc=f"Answering tier2 ({mode})",
        skip_fn=skip_fn, output_path=output_path, save_interval=save_interval,
    )


async def run_answer_tier2_recovered(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Answer tier2 recovered questions with original images."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        q = item["tier2_questions"][0]
        q_type = item["question_type"]
        question_text = q["recovered_question"]
        options = item.get("options")

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

        content = build_multimodal_content(
            question_text, item["images"], base_dir, client
        )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ]
        response = await client.chat(messages)
        q.setdefault("ablation_predictions", {})[model_key] = response
        return item

    return await run_batch(
        data, process, concurrency=concurrency, desc="Answering tier2 (recovered)",
        skip_fn=skip_fn, output_path=output_path, save_interval=save_interval,
    )


# ── Judging ──────────────────────────────────────────────

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
    answer = str(answer)
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


async def run_ablation_judge(
    data: list[dict],
    judge_client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Judge ablation T0 answers. Reads ablation_answer, writes ablation_judge."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        model_data = item.get("model", {}).get(model_key, {})
        model_answer = model_data.get("ablation_answer")

        if model_answer is None:
            item.setdefault("model", {}).setdefault(model_key, {})["ablation_judge"] = {
                "correct": False, "reasoning": "No ablation answer found.",
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

        content = build_multimodal_content(user_text, item["images"], base_dir, judge_client)
        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]

        last_response = ""
        for _ in range(MAX_PARSE_RETRIES):
            response = await judge_client.chat(messages)
            last_response = response
            judge_result = _parse_judge_response(response)
            if judge_result is not None:
                item.setdefault("model", {}).setdefault(model_key, {})["ablation_judge"] = judge_result
                return item

        item.setdefault("model", {}).setdefault(model_key, {})["ablation_judge"] = {
            "correct": False,
            "reasoning": f"Parse error after {MAX_PARSE_RETRIES} retries: {last_response}",
        }
        return item

    return await run_batch(
        data, process, concurrency=concurrency, desc="Judging ablation (T0)",
        skip_fn=skip_fn, output_path=output_path, save_interval=save_interval,
    )


async def run_ablation_judge_tier2(
    data: list[dict],
    judge_client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    skip_fn=None,
    output_path=None,
    save_interval: int = 0,
) -> list[dict]:
    """Judge ablation T2 answers. Reads ablation_predictions, writes ablation_scoring."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        q = item["tier2_questions"][0]
        model_answer = (q.get("ablation_predictions") or {}).get(model_key)

        if model_answer is None or (isinstance(model_answer, str) and not model_answer.strip()):
            q.setdefault("ablation_scoring", {})[model_key] = {
                "correct": False, "reasoning": "No ablation answer found.",
            }
            return item

        gt_answer = _format_gt_answer(item["answer"])
        q_type = item["question_type"]
        options = item.get("options")
        final_answer = _extract_final_answer(model_answer)

        user_text = f"""Question: {q["pruned_question"]}
{f"Options: {options}" if options else ""}
Question type: {q_type}

Ground-truth answer: {gt_answer}
Model's final answer: {final_answer}"""

        content = build_multimodal_content(user_text, item["images"], base_dir, judge_client)
        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]

        last_response = ""
        for _ in range(MAX_PARSE_RETRIES):
            response = await judge_client.chat(messages)
            last_response = response
            judge_result = _parse_judge_response(response)
            if judge_result is not None:
                q.setdefault("ablation_scoring", {})[model_key] = judge_result
                return item

        q.setdefault("ablation_scoring", {})[model_key] = {
            "correct": False,
            "reasoning": f"Parse error after {MAX_PARSE_RETRIES} retries: {last_response}",
        }
        return item

    return await run_batch(
        data, process, concurrency=concurrency, desc="Judging ablation (T2)",
        skip_fn=skip_fn, output_path=output_path, save_interval=save_interval,
    )
