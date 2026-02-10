import argparse
import json


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=str, default="saves/gpt_5_2_base.json")
    args = parser.parse_args()

    base_result = json.load(open(args.base, "r", encoding="utf-8"))
    caption_result = json.load(open(args.base.replace("base", "caption"), "r", encoding="utf-8"))
    text_only_result = json.load(open(args.base.replace("base", "text_only"), "r", encoding="utf-8"))
    rewrite_base_result = json.load(open(args.base.replace("base", "rewrite"), "r", encoding="utf-8"))
    rewrite_caption_result = json.load(open(args.base.replace("base", "rewrite_caption"), "r", encoding="utf-8"))
    rewrite_text_only_result = json.load(open(args.base.replace("base", "rewrite_text_only"), "r", encoding="utf-8"))

    base_correct = set([item["id"] for item in base_result if item.get("is_correct", False)])
    caption_correct = set([item["id"] for item in caption_result if item.get("is_correct", False)])
    text_only_correct = set([item["id"] for item in text_only_result if item.get("is_correct", False)])
    rewrite_base_correct = set([item["id"] for item in rewrite_base_result if item.get("is_correct", False)])
    rewrite_caption_correct = set([item["id"] for item in rewrite_caption_result if item.get("is_correct", False)])
    rewrite_text_only_correct = set([item["id"] for item in rewrite_text_only_result if item.get("is_correct", False)])

    target_samples = text_only_correct - rewrite_text_only_correct
    print("Samples that were correct in text_only but incorrect after rewrite:", target_samples)
