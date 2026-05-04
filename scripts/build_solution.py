"""Build filtered_data_with_solution.json by adding top-level solution fields."""

import json
import os
from collections import Counter

import pyarrow.parquet as pq

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "coreset", "filtered_data.json")
OUTPUT_WITH_PATH = os.path.join(BASE_DIR, "coreset", "filtered_data_with_solution.json")
OUTPUT_WITHOUT_PATH = os.path.join(BASE_DIR, "coreset", "filtered_data_without_solution.json")

# Model priority order (by accuracy, highest first)
MODEL_PRIORITY = [
    "gemini-3.1-flash-lite-preview",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "gpt-5-nano",
]


def build_olympiadbench_lookup() -> dict[tuple[str, str], str]:
    """Build (category, id) -> solution lookup from OlympiadBench parquets."""
    base = os.path.join(BASE_DIR, "raw", "OlympiadBench", "OlympiadBench")
    lookup = {}
    for subdir in os.listdir(base):
        path = os.path.join(base, subdir, subdir + ".parquet")
        if not os.path.exists(path):
            continue
        t = pq.read_table(path, columns=["id", "solution"])
        for i in range(len(t)):
            pid = str(t.column("id")[i].as_py())
            sol = t.column("solution")[i].as_py()
            if isinstance(sol, list):
                sol = "\n".join(s for s in sol if s)
            lookup[(subdir, pid)] = sol or None
    return lookup


def build_superchem_lookup() -> dict[str, str]:
    """Build uuid -> explanation_en lookup from SUPERChem parquet."""
    path = os.path.join(BASE_DIR, "raw", "SUPERChem", "SUPERChem-500.parquet")
    t = pq.read_table(path, columns=["uuid", "explanation_en"])
    lookup = {}
    for i in range(len(t)):
        uuid = t.column("uuid")[i].as_py()
        expl = t.column("explanation_en")[i].as_py()
        lookup[uuid] = expl or None
    return lookup


def get_original_solution(item: dict, ob_lookup: dict, sc_lookup: dict) -> str | None:
    """Try to extract an original solution for the item."""
    ds = item["dataset"]
    extra = item.get("extra", {})
    original = extra.get("original", {})

    if ds == "OlympiadBench":
        source_file = extra.get("metadata", {}).get("source_file", "")
        category = source_file.split("/")[0] if source_file else None
        num_id = item["id"].split("-")[-1]
        if category:
            return ob_lookup.get((category, num_id))
        return None

    if ds in ("OlympicArena", "EMMA"):
        sol = original.get("solution")
        if sol and isinstance(sol, str) and sol.strip():
            return sol.strip()
        return None

    if ds == "MMMU":
        expl = original.get("explanation")
        if expl and isinstance(expl, str) and expl.strip():
            return expl.strip()
        return None

    if ds == "SUPERChem":
        uuid = original.get("id")
        if uuid:
            return sc_lookup.get(uuid)
        return None

    if ds == "PuzzleVQA":
        explanation = extra.get("explanation", "")
        deduction = extra.get("deduction", "")
        if explanation or deduction:
            parts = []
            if explanation:
                parts.append(f"Explanation: {explanation}")
            if deduction:
                parts.append(f"Deduction: {deduction}")
            return "\n\n".join(parts)
        return None

    return None


def get_model_solution(item: dict) -> tuple[str | None, str | None]:
    """Get the best correct model answer. Returns (solution, source)."""
    models = item.get("model", {})
    for model_name in MODEL_PRIORITY:
        entry = models.get(model_name, {})
        judge = entry.get("judge", {})
        if judge.get("correct"):
            answer = entry.get("answer", "")
            if answer and isinstance(answer, str) and answer.strip():
                return answer.strip(), f"model:{model_name}"
    return None, None


def main():
    with open(INPUT_PATH) as f:
        data = json.load(f)

    ob_lookup = build_olympiadbench_lookup()
    sc_lookup = build_superchem_lookup()
    print(f"OlympiadBench lookup: {len(ob_lookup)} entries")
    print(f"SUPERChem lookup: {len(sc_lookup)} entries")

    source_counts = Counter()
    dataset_source = Counter()
    with_solution = []
    without_solution = []

    for item in data:
        sol = get_original_solution(item, ob_lookup, sc_lookup)
        if sol:
            item["solution"] = sol
            item["solution_source"] = "original"
            source_counts["original"] += 1
            dataset_source[(item["dataset"], "original")] += 1
            with_solution.append(item)
        else:
            model_sol, model_src = get_model_solution(item)
            if model_sol:
                item["solution"] = model_sol
                item["solution_source"] = model_src
                source_counts[model_src] += 1
                dataset_source[(item["dataset"], model_src)] += 1
                with_solution.append(item)
            else:
                item["solution"] = None
                item["solution_source"] = None
                source_counts["none"] += 1
                dataset_source[(item["dataset"], "none")] += 1
                without_solution.append(item)

    with open(OUTPUT_WITH_PATH, "w") as f:
        json.dump(with_solution, f, indent=2, ensure_ascii=False)

    with open(OUTPUT_WITHOUT_PATH, "w") as f:
        json.dump(without_solution, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(with_solution)} items to {OUTPUT_WITH_PATH}")
    print(f"Wrote {len(without_solution)} items to {OUTPUT_WITHOUT_PATH}")
    print("\n--- Summary by source ---")
    for src, count in source_counts.most_common():
        print(f"  {src}: {count}")

    print("\n--- Summary by dataset x source ---")
    datasets = sorted(set(item["dataset"] for item in data))
    for ds in datasets:
        parts = []
        for key, count in sorted(dataset_source.items()):
            if key[0] == ds:
                parts.append(f"{key[1]}={count}")
        print(f"  {ds}: {', '.join(parts)}")


if __name__ == "__main__":
    main()
