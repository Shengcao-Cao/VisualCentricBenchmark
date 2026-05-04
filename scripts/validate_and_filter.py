#!/usr/bin/env python3
"""Validate all_data.json and filter out questions with images only in options."""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).parent
DATA_JSON = ROOT / "all_data.json"
FIGURES_DIR = ROOT / "all_figures"


def find_placeholders(text: str) -> set[str]:
    """Return set of unique image placeholder indices in text."""
    return set(re.findall(r"<image_(\d+)>", text))


def validate_and_filter(data: list[dict]) -> tuple[list[dict], dict]:
    """Run all checks and return (filtered_data, report)."""
    existing_files = set(os.listdir(FIGURES_DIR))

    no_placeholder = []
    placeholder_exceeds = []
    missing_files = []
    images_only_in_options = []
    clean = []

    for item in data:
        qid = item["id"]
        question = item["question"]
        options = item.get("options") or []
        images = item.get("images") or []

        q_placeholders = find_placeholders(question)
        opt_text = " ".join(str(o) for o in options)
        opt_placeholders = find_placeholders(opt_text)
        all_placeholders = q_placeholders | opt_placeholders

        # Check 1: at least one image placeholder somewhere
        if len(all_placeholders) == 0:
            no_placeholder.append(qid)

        # Check 2: unique placeholders <= actual images
        if len(all_placeholders) > len(images):
            placeholder_exceeds.append(
                (qid, len(all_placeholders), len(images))
            )

        # Check 3: all image files exist
        for img_path in images:
            basename = os.path.basename(img_path)
            if basename not in existing_files:
                missing_files.append((qid, img_path))

        # Check 4: images must appear in question text, not only in options
        if len(q_placeholders) == 0 and len(opt_placeholders) > 0:
            images_only_in_options.append(qid)
            continue

        clean.append(item)

    report = {
        "total": len(data),
        "no_placeholder": no_placeholder,
        "placeholder_exceeds": placeholder_exceeds,
        "missing_files": missing_files,
        "images_only_in_options": images_only_in_options,
        "kept": len(clean),
        "removed": len(data) - len(clean),
    }
    return clean, report


def print_report(report: dict) -> None:
    print(f"Total questions: {report['total']}")
    print()

    print(f"[Check 1] No image placeholder at all: {len(report['no_placeholder'])}")
    for qid in report["no_placeholder"][:10]:
        print(f"  {qid}")

    print(
        f"[Check 2] Placeholder count > image count: "
        f"{len(report['placeholder_exceeds'])}"
    )
    for qid, pc, ic in report["placeholder_exceeds"][:10]:
        print(f"  {qid}: {pc} placeholders, {ic} images")

    print(f"[Check 3] Missing image files: {len(report['missing_files'])}")
    for qid, img in report["missing_files"][:10]:
        print(f"  {qid}: {img}")

    print(
        f"[Check 4] Images only in options (filtered out): "
        f"{len(report['images_only_in_options'])}"
    )
    for qid in report["images_only_in_options"][:10]:
        print(f"  {qid}")
    if len(report["images_only_in_options"]) > 10:
        print(f"  ... and {len(report['images_only_in_options']) - 10} more")

    print()
    print(f"Kept: {report['kept']}  |  Removed: {report['removed']}")


def main():
    with open(DATA_JSON) as f:
        data = json.load(f)

    clean, report = validate_and_filter(data)
    print_report(report)

    if report["removed"] > 0:
        with open(DATA_JSON, "w") as f:
            json.dump(clean, f, indent=2, ensure_ascii=False)
        print(f"\nWrote {len(clean)} questions back to {DATA_JSON}")
    else:
        print("\nNo changes needed.")


if __name__ == "__main__":
    main()
