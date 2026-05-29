import argparse
import json
import os
import re
from gpt import GPT

# ── Edit this prompt to test your own instructions ──────────────────────────
PROMPT_EN = (
    "Do not solve the problem. Output three sections:"
    "Section 1: Exact Values (from problem text) List every coordinate, equation, and geometric relationship explicitly stated in the problem. These are ground truth."
    "Section 2: Topology (from figure) Describe relationships as chains and intersections, not isolated facts. For each element state:"
    "What it passes through or lies on, in order (e.g. Line L passes through A, then X, then B from left to right)"
    "What it intersects and where in the sequence (e.g. Line L and Line M intersect at X, which is between A and B on Line L)"
    "Relative ordering along a curve or axis (e.g. Along the x-axis from left to right: A, Q, B, D)"
    "Section 3: Visual Estimates (figure only) For anything not covered above, give a coordinate or positional estimate. Keep this list as short as possible."
)

PROMPT_ZH = (
    "不要解题。输出三个部分："
    "第一部分：精确值（来自题目文字）列出题目中明确陈述的每个坐标、方程和几何关系。这些是基本事实。"
    "第二部分：拓扑结构（来自图形）将关系描述为链式结构和交叉关系，而不是孤立的事实。对于每个元素，说明："
    "它按顺序经过或位于哪些元素上（例如：直线L从左到右依次经过A、X、B）"
    "它与哪些元素相交以及在序列中的位置（例如：直线L与直线M相交于X，X在直线L上位于A和B之间）"
    "沿曲线或坐标轴的相对顺序（例如：沿x轴从左到右：A、Q、B、D）"
    "第三部分：视觉估计（仅来自图形）对于上述未涵盖的内容，给出坐标或位置估计。尽量保持此列表简短。"
)
# ────────────────────────────────────────────────────────────────────────────


def is_chinese(sample):
    lang = sample.get("extra", {}).get("metadata", {}).get("language", "")
    return lang.lower() in ("chinese", "zh")


def build_caption_prompt(data, image_dir):
    """
    Returns a flat list of prompts (one per image) and a parallel index list
    that maps each prompt back to (sample_index, image_index).
    """
    prompts = []
    index_map = []  # (sample_idx, img_idx)

    for s_idx, sample in enumerate(data):
        instruction = PROMPT_ZH if is_chinese(sample) else PROMPT_EN
        question = sample.get("question", "")
        prompt_text = f"{question}\n\n{instruction}"
        for i_idx, figure_path in enumerate(sample.get("images", [])):
            full_path = os.path.join(image_dir, figure_path)
            content = [
                {"type": "image", "image_url": full_path},
                {"type": "text",  "text": prompt_text},
            ]
            prompts.append(content)
            index_map.append((s_idx, i_idx))

    return prompts, index_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",      type=str, default="../coreset/filtered_data.json",
                        help="Path to the input JSON file")
    parser.add_argument("--image_dir", type=str,
                        default="../coreset",
                        help="Directory that contains the images")
    parser.add_argument("--model",     type=str, default="gpt-4o")
    parser.add_argument("--api_key",   type=str, default=None)
    parser.add_argument("--output",    type=str, default=None,
                        help="Where to save the enriched JSON (default: saves/atomic_captions_<timestamp>.json)")
    args = parser.parse_args()

    if args.output is None:
        saves_dir = "saves"
        existing = os.listdir(saves_dir) if os.path.exists(saves_dir) else []
        nums = [int(m.group(1)) for f in existing if (m := re.search(r"atomic_captions(\d+)\.json", f))]
        next_num = max(nums) + 1 if nums else 0
        args.output = f"{saves_dir}/atomic_captions{next_num}.json"

    problems = json.load(open(args.data, "r", encoding="utf-8"))
    prompts, index_map = build_caption_prompt(problems, args.image_dir)

    print(f"Loaded {len(problems)} problems → {len(prompts)} image prompts")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    if args.model.startswith("gpt-"):
        model = GPT(model=args.model, api_key=args.api_key)
    else:
        raise ValueError(f"Unsupported model: {args.model}")

    responses = model.generate_batch(prompts)

    # Write captions back into the data under a top-level "atomic_captions" list
    for problem in problems:
        problem["atomic_captions"] = [None] * len(problem.get("images", []))

    for response, (s_idx, i_idx) in zip(responses, index_map):
        problems[s_idx]["atomic_captions"][i_idx] = response

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)

    print(f"Saved results to {args.output}")
