import argparse
import json
import os
import re

from gpt import GPT


def build_prompt(data, image_dir, text_only=False, caption_only=False, rewrite=False):
    samples = []
    for sample in data:
        content = []
        prompt = sample["prompt"]
        if rewrite:
            prompt = sample["rewritten_prompt"]
        if sample["language"] == "ZH":
            segments = re.split(r'(\[图\d+\])', prompt)
        else:
            segments = re.split(r'(\[figure\d+\])', prompt)
        for seg in segments:
            if not seg.strip():
                continue
            if not seg.startswith('['):
                content.append({"type": "text", "text": seg})
            else:
                if sample["language"] == "ZH":
                    figure_index = int(seg.split("[图")[1].split("]")[0]) - 1
                else:
                    figure_index = int(seg.split("[figure")[1].split("]")[0]) - 1
                if caption_only:
                    caption = "[图像描述：{}]" if sample["language"] == "ZH" else "[Image description: {}]"
                    content.append({
                        "type": "text",
                        "text": caption.format(sample["figure_captions"][figure_index])
                    })
                elif figure_index < len(sample["figure_local_paths"]):
                    content.append({
                        "type": "image",
                        "image_url": os.path.join(image_dir, sample["figure_local_paths"][figure_index])
                    })
        if text_only:
            text_content = ""
            for seg in content:
                if seg["type"] == "text":
                    text_content += seg["text"]
                else:
                    if sample["language"] == "ZH":
                        text_content += "[图像已省略]"
                    else:
                        text_content += "[figure omitted]"
                if sample["language"] == "ZH":
                    text_content += "\n请在没有图像的情况下回答问题。\n"
                else:
                    text_content += "\nPlease answer the question without the image.\n"
            content = [{"type": "text", "text": text_content}]
        elif caption_only:
            text_content = "".join([seg["text"] for seg in content if seg["type"] == "text"])
            if sample["language"] == "ZH":
                text_content += "\n请仅根据图像描述回答问题，而不使用实际图像。\n"
            else:
                text_content += "\nPlease answer the question based only on the image description without the actual image.\n"
            content = [{"type": "text", "text": text_content}]
        samples.append(content)
    return samples


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="mm_dataset")
    parser.add_argument("--problem_file", type=str)
    parser.add_argument("--model", type=str, default="gpt-5.2")
    parser.add_argument("--api_key", type=str, default=None)
    parser.add_argument("--output", type=str, default="saves/gpt_5_2_base.json")
    parser.add_argument("--text_only", action="store_true")
    parser.add_argument("--caption_only", action="store_true")
    parser.add_argument("--rewrite", action="store_true")
    args = parser.parse_args()

    if args.problem_file:
        problems = json.load(open(args.problem_file, "r", encoding="utf-8"))
    else:
        problems = json.load(open(os.path.join(args.data, "problems.json"), "r", encoding="utf-8"))
    image_dir = os.path.join(args.data, "images")
    prompts = build_prompt(problems, image_dir, args.text_only, args.caption_only, args.rewrite)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    if args.model.startswith("gpt-"):
        model = GPT(model=args.model, api_key=args.api_key)
    else:
        raise ValueError(f"Unsupported model: {args.model}")

    responses = model.generate_batch(prompts)
    for i in range(len(problems)):
        problems[i]["model_response"] = responses[i]
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)
