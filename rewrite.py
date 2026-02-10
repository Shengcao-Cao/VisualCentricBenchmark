import argparse
import json
import os
import re

from gpt import GPT


zh_prompt_template = """你的任务是改写以下问题，使得新版本中的文本不包含图像中已经包含的信息。换句话说，改写后的问题与图像没有信息重叠。不要改变问题的实际内容，改写后问题的答案应保持不变。请保持问题解决指令（例如，"请以...结束你的回答"）不变，保持图像的占位符（例如，"[图1]"、"[图2]"）不变。

原始问题如下：
{original_problem}

图像的详细描述如下：
{image_descriptions}

你改写后的问题：
"""

en_prompt_template = """Your task is to rewrite the text description of the following problem so that the text in the new version is and contains no information that is already included in the image. In other words, the rewritten problem has no information overlap with the image. Do not change the actual content of the problem and the answer to the rewritten problem should remain the same. Keep the problem-solving instructions (e.g., "Please end your response with...") and placeholders for images (e.g., "[figure1]", "[figure2]") unchanged.

The original problem is as follows:
{original_problem}

Detailed descriptions of the images are provided below:
{image_descriptions}

Your rewritten problem:
"""


def build_prompt(data):
    samples = []
    for sample in data:
        problem = sample["prompt"]
        if sample["language"] == "ZH":
            figure_matches = re.findall(r'\[图(\d+)\]', problem)
        else:
            figure_matches = re.findall(r'\[figure(\d+)\]', problem)
        max_figure_index = max([int(idx) for idx in figure_matches]) if figure_matches else 0
        image_descriptions = []
        for i in range(max_figure_index):
            caption = sample["figure_captions"][i]
            if sample["language"] == "ZH":
                image_descriptions.append(f"- [图{i+1}]: {caption}")
            else:
                image_descriptions.append(f"- [figure{i+1}]: {caption}")
        image_descriptions = "\n".join(image_descriptions)
        if sample["language"] == "ZH":
            prompt_text = zh_prompt_template.format(
                original_problem=problem,
                image_descriptions=image_descriptions
            )
        else:
            prompt_text = en_prompt_template.format(
                original_problem=problem,
                image_descriptions=image_descriptions
            )
        content = [{"type": "text", "text": prompt_text}]
        samples.append(content)
    return samples


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="mm_dataset")
    parser.add_argument("--problem_file", type=str)
    parser.add_argument("--model", type=str, default="gpt-5.2")
    parser.add_argument("--api_key", type=str, default=None)
    parser.add_argument("--output", type=str, default="saves/gpt_5_2_base.json")
    args = parser.parse_args()

    if args.problem_file:
        problems = json.load(open(args.problem_file, "r", encoding="utf-8"))
    else:
        problems = json.load(open(os.path.join(args.data, "problems.json"), "r", encoding="utf-8"))
    prompts = build_prompt(problems)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    if args.model.startswith("gpt-"):
        model = GPT(model=args.model, api_key=args.api_key)
    else:
        raise ValueError(f"Unsupported model: {args.model}")
    
    responses = model.generate_batch(prompts)
    for i in range(len(problems)):
        problems[i]["rewritten_prompt"] = responses[i]

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)
