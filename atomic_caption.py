import argparse
import json
import os

from gpt import GPT


def build_caption_prompt(data, image_dir):
    samples = []
    for sample in data:
        for figure_path in sample["figure_local_paths"]:
            content = [{"type": "image", "image_url": os.path.join(image_dir, figure_path)}]
            if sample["language"] == "ZH":
                content += [{"type": "text", "text": "尽可能详细地描述上图。将每个基本的、原子的、元素的事实作为单独的一句话列出。只包含可以直接从图像中观察和验证的事实，不要进行任何假设或更深入的推理。严格遵循每句话单独成行并以'* '开头的格式。"}]
            else:
                content += [{"type": "text", "text": "Describe the image above with as many details as possible. List each basic, atomic, elemental fact as a separate sentence. Only include facts that can be directly observed and verified from the image without any assumptions or deeper reasoning. Strictly follow the format that lists each sentence in a separate line starting with '* '."}]
            samples.append(content)
    return samples


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="mm_dataset")
    parser.add_argument("--model", type=str, default="gpt-5.2")
    parser.add_argument("--api_key", type=str, default=None)
    parser.add_argument("--output", type=str, default="saves/gpt_5_2_caption.json")
    args = parser.parse_args()

    problems = json.load(open(os.path.join(args.data, "problems.json"), "r", encoding="utf-8"))
    image_dir = os.path.join(args.data, "images")
    prompts = build_caption_prompt(problems, image_dir)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    if args.model.startswith("gpt-"):
        model = GPT(model=args.model, api_key=args.api_key)
    else:
        raise ValueError(f"Unsupported model: {args.model}")

    responses = model.generate_batch(prompts)
    caption_index = 0
    for i in range(len(problems)):
        problems[i]["figure_captions"] = []
        for _ in problems[i]["figure_local_paths"]:
            problems[i]["figure_captions"].append(responses[caption_index])
            caption_index += 1
    assert caption_index == len(responses)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)
