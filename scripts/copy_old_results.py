"""Copy old T1/T2 predictions into the new clean dataset files.

For each model:
- T1: copies predictions from no_review_needed_tier1_[slug].json into
  filtered_data_with_solution_hard_tier1+2_clean_tier1_[slug].json
- T2: copies predictions+scoring from no_review_needed_substantive_tier2_[slug]_judged.json
  into filtered_data_with_solution_hard_tier1+2_clean_tier2_[slug].json

Only copies where question_id matches. New sub-questions without old predictions
are left untouched (for --skip-existing to pick up later).
"""

import json
from pathlib import Path

MODEL_SLUGS = [
    "claude_opus_4_6",
    "claude_sonnet_4_6",
    "gemini_3_1_flash_lite_preview",
    "gemini_3_1_pro_preview",
    "gemma_4_31b",
    "gpt_5_4",
    "gpt_5_4_mini",
    "kimi_k2_5",
    "nova_2_lite",
    "open_router_qwen3_5_397b_a17b",
    "qwen3_vl_235b_a22b",
]

CLEAN = "data/filtered_data_with_solution_hard_tier1+2_clean.json"
PREFIX = "data/filtered_data_with_solution_hard_tier1+2_clean"


def main() -> None:
    clean_data = json.loads(Path(CLEAN).read_text())
    print(f"Loaded {len(clean_data)} items from {CLEAN}")

    for slug in MODEL_SLUGS:
        # --- T1 ---
        old_t1_path = Path(f"data/no_review_needed_tier1_{slug}.json")
        out_t1_path = Path(f"{PREFIX}_tier1_{slug}.json")

        if old_t1_path.exists():
            old_t1 = json.loads(old_t1_path.read_text())
            old_t1_by_qid = {}
            for item in old_t1:
                for q in item.get("tier1_questions", []):
                    qid = q.get("question_id")
                    if qid:
                        old_t1_by_qid[qid] = q

            import copy
            t1_data = copy.deepcopy(clean_data)
            copied = 0
            total = 0
            for item in t1_data:
                for q in item.get("tier1_questions", []):
                    total += 1
                    qid = q.get("question_id")
                    if qid in old_t1_by_qid:
                        old_q = old_t1_by_qid[qid]
                        old_preds = old_q.get("predictions", {})
                        old_scoring = old_q.get("scoring", {})
                        if old_preds:
                            q.setdefault("predictions", {}).update(old_preds)
                            copied += 1
                        if old_scoring:
                            q.setdefault("scoring", {}).update(old_scoring)

            out_t1_path.write_text(json.dumps(t1_data, indent=2, ensure_ascii=False))
            print(f"T1 {slug}: copied {copied}/{total} predictions -> {out_t1_path}")
        else:
            print(f"T1 {slug}: {old_t1_path} not found, skipping")

        # --- T2 ---
        old_t2_path = Path(f"data/no_review_needed_substantive_tier2_{slug}_judged.json")
        out_t2_path = Path(f"{PREFIX}_tier2_{slug}.json")

        if old_t2_path.exists():
            old_t2 = json.loads(old_t2_path.read_text())
            old_t2_by_qid = {}
            for item in old_t2:
                for q in item.get("tier2_questions", []):
                    qid = q.get("question_id")
                    if qid:
                        old_t2_by_qid[qid] = q

            import copy
            t2_data = copy.deepcopy(clean_data)
            copied_pred = 0
            copied_score = 0
            total = 0
            for item in t2_data:
                for q in item.get("tier2_questions", []):
                    total += 1
                    qid = q.get("question_id")
                    if qid in old_t2_by_qid:
                        old_q = old_t2_by_qid[qid]
                        old_preds = old_q.get("predictions", {})
                        old_scoring = old_q.get("scoring", {})
                        if old_preds:
                            q.setdefault("predictions", {}).update(old_preds)
                            copied_pred += 1
                        if old_scoring:
                            q.setdefault("scoring", {}).update(old_scoring)
                            copied_score += 1

            out_t2_path.write_text(json.dumps(t2_data, indent=2, ensure_ascii=False))
            print(f"T2 {slug}: copied {copied_pred}/{total} predictions, {copied_score} scores -> {out_t2_path}")
        else:
            print(f"T2 {slug}: {old_t2_path} not found, skipping")


if __name__ == "__main__":
    main()
