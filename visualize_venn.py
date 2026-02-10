import argparse
import json
import matplotlib.pyplot as plt
from matplotlib_venn import venn3
from matplotlib_venn.layout.venn3 import DefaultLayoutAlgorithm


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", type=str)
    parser.add_argument("--caption", type=str)
    parser.add_argument("--text_only", type=str)
    parser.add_argument("--output", type=str)
    args = parser.parse_args()

    full_result = json.load(open(args.full, "r", encoding="utf-8"))
    caption_result = json.load(open(args.caption, "r", encoding="utf-8"))
    text_only_result = json.load(open(args.text_only, "r", encoding="utf-8"))

    all_ids = set([item["id"] for item in full_result + caption_result + text_only_result])
    full_correct = set([item["id"] for item in full_result if item.get("is_correct", False)])
    caption_correct = set([item["id"] for item in caption_result if item.get("is_correct", False)])
    text_only_correct = set([item["id"] for item in text_only_result if item.get("is_correct", False)])

    print("Unsolved IDs:", all_ids - (full_correct | caption_correct | text_only_correct))
    print("Only solvable with full input:", full_correct - (caption_correct | text_only_correct))
    print("Only solvable with image or caption input:", (full_correct & caption_correct) - text_only_correct)

    plt.figure(figsize=(10, 8))
    venn3([full_correct, caption_correct, text_only_correct], 
          set_labels=("Full", "Caption", "Text Only"),
          layout_algorithm=DefaultLayoutAlgorithm(fixed_subset_sizes=(1,1,1,1,1,1,1)))
    plt.title("Venn Diagram of Correct Results")

    plt.savefig(args.output, dpi=300, bbox_inches="tight")
    print(f"Venn diagram saved to {args.output}")
