"""Build clean release data files from the internal dataset.

Produces four JSON files and copies referenced images:
  - visatom_base.json   (T0: original questions, 2711 items)
  - visatom_tier1.json  (T1: visual perception MCQs, 2710 items)
  - visatom_tier2.json  (T2: pruned questions, 1035 items)
  - visatom_tier3.json  (T3: formalized diagrams + pruned questions, 283 items)
  - images/             (only images referenced by the above files)

Usage:
  python scripts/build_release_data.py
"""

import json
import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "release", "data")


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def save(data, name):
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  {name}: {len(data)} items")


def _base_fields(item):
    """Fields shared across all tiers."""
    return {
        "id": item["id"],
        "question": item["question"],
        "question_type": item["question_type"],
        "options": item["options"],
        "answer": item["answer"],
        "images": item["images"],
        "domain": item["domain"],
        "subdomain": item["subdomain"],
        "dataset": item["dataset"],
        "language": item["language"],
    }


def build_base(t0_data):
    """T0: original problem-solving with original images."""
    out = []
    for item in t0_data:
        entry = _base_fields(item)
        entry["solution"] = item["solution"]
        out.append(entry)
    return out


def build_tier1(t12_data):
    """T1: visual perception MCQs on original images."""
    out = []
    for item in t12_data:
        t1_qs = item.get("tier1_questions", [])
        if not t1_qs:
            continue
        clean_qs = []
        for q in t1_qs:
            clean_qs.append({
                "id": q["question_id"],
                "question": q["question"],
                "question_type": "single_selection",
                "options": q["options"],
                "answer": q["gt_answer"],
                "images": item["images"],
                "image_index": q["image_index"],
                "type": q["type"],
                "type_name": q["type_name"],
            })
        entry = _base_fields(item)
        entry["tier1_questions"] = clean_qs
        out.append(entry)
    return out


def build_tier2(t12_data):
    """T2: pruned questions with original images."""
    out = []
    for item in t12_data:
        t2_qs = item.get("tier2_questions", [])
        if not t2_qs:
            continue
        t2 = t2_qs[0]
        entry = _base_fields(item)
        entry["tier2_questions"] = [{
            "id": t2["question_id"],
            "question": t2["pruned_question"],
            "question_type": item["question_type"],
            "options": item["options"],
            "answer": item["answer"],
            "images": item["images"],
        }]
        out.append(entry)
    return out


def build_tier3(t3_data):
    """T3: formalized diagrams with pruned questions."""
    out = []
    for item in t3_data:
        t3 = item["tier3_questions"][0]
        entry = _base_fields(item)
        entry["tier3_questions"] = [{
            "id": t3["question_id"],
            "question": t3["pruned_question"],
            "question_type": t3["question_type"],
            "options": t3["options"],
            "answer": t3["answer"],
            "images": t3["images"],
        }]
        out.append(entry)
    return out


def collect_images(*datasets):
    """Collect all unique image paths referenced across all datasets."""
    paths = set()
    for data in datasets:
        for item in data:
            for img in item.get("images", []):
                paths.add(img)
            for key in ("tier1_questions", "tier2_questions", "tier3_questions"):
                for q in item.get(key, []):
                    for img in q.get("images", []):
                        paths.add(img)
    return paths


def copy_images(image_paths):
    """Copy referenced images to release/data/, preserving subdirectory structure."""
    copied = 0
    for img_path in sorted(image_paths):
        src = os.path.join(DATA, img_path)
        dst = os.path.join(OUT, img_path)
        if not os.path.exists(src):
            print(f"  WARNING: missing {src}")
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            copied += 1
    print(f"  Copied {copied} images ({len(image_paths)} total referenced)")


def main():
    print("Loading source data...")
    t0_data = load("filtered_data_with_solution_hard.json")
    t12_data = load("filtered_data_with_solution_hard_tier1+2_clean.json")
    t3_data = load("filtered_data_with_solution_hard_tier3_2.json")

    print("Building release files:")
    base = build_base(t0_data)
    tier1 = build_tier1(t12_data)
    tier2 = build_tier2(t12_data)
    tier3 = build_tier3(t3_data)

    save(base, "visatom_base.json")
    save(tier1, "visatom_tier1.json")
    save(tier2, "visatom_tier2.json")
    save(tier3, "visatom_tier3.json")

    print("Copying images:")
    image_paths = collect_images(base, tier1, tier2, tier3)
    copy_images(image_paths)

    print("Done.")


if __name__ == "__main__":
    main()
