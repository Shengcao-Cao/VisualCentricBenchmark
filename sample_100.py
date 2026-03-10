#!/usr/bin/env python3
"""
Subsample 100 items from sampled_1000.json.

Strategy:
- Maintain the original domain ratio (scaled to 100)
- Within each domain, prioritize harder questions (difficulty >= 3 first)
- Maintain subdomain and question_type coverage where possible
- Ensure every dataset source is represented
- Fixed random seed for reproducibility
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
SEED = 42

# Domain budgets scaled from original 1000 → 100, keeping ratios
# Original: Math 400, Physics 200, Chemistry 150, Puzzle 100, CS 60, Bio 40, Geo 30, Eng 20
DOMAIN_BUDGET = {
    "Math": 40,
    "Physics": 20,
    "Chemistry": 15,
    "Puzzle": 10,
    "Computer Science": 6,
    "Biology": 4,
    "Geography": 3,
    "Engineering": 2,
}

MIN_PER_SUBDOMAIN = 0  # No floor — strict budget adherence at 100 scale


def difficulty_sort_key(item: dict) -> tuple:
    """Sort key: higher difficulty first, then random tiebreak."""
    model_data = item.get("model", {})
    diff = -1
    for mv in model_data.values():
        d = mv.get("difficulty", {})
        if d:
            diff = d.get("difficulty", -1)
            break
    return -diff  # negative so higher difficulty comes first


def get_difficulty(item: dict) -> int:
    for mv in item.get("model", {}).values():
        d = mv.get("difficulty", {})
        if d:
            return d.get("difficulty", -1)
    return -1


def sample_stratum_hard_first(
    items: list[dict], n: int, rng: random.Random
) -> list[dict]:
    """Sample n items, prioritizing harder questions while maintaining question_type ratio."""
    if n >= len(items):
        return list(items)

    # Group by question_type
    by_qtype: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_qtype[item["question_type"]].append(item)

    # Allocate proportionally by question_type
    qtypes = sorted(by_qtype.keys())
    total = len(items)
    qtype_budgets = {}
    for qt in qtypes:
        qtype_budgets[qt] = max(1, round(n * len(by_qtype[qt]) / total))

    # Adjust to hit n exactly
    current = sum(qtype_budgets.values())
    while current > n:
        largest_qt = max(qtypes, key=lambda qt: qtype_budgets[qt])
        qtype_budgets[largest_qt] -= 1
        current -= 1
    while current < n:
        candidates = [qt for qt in qtypes if qtype_budgets[qt] < len(by_qtype[qt])]
        if not candidates:
            break
        best_qt = max(candidates, key=lambda qt: len(by_qtype[qt]) - qtype_budgets[qt])
        qtype_budgets[best_qt] += 1
        current += 1

    # Within each question_type, sort by difficulty (hard first), then sample top-n
    # with slight randomization among same-difficulty items
    sampled = []
    for qt in qtypes:
        pool = by_qtype[qt]
        take = min(qtype_budgets.get(qt, 0), len(pool))
        # Shuffle first for random tiebreaking, then stable-sort by difficulty desc
        rng.shuffle(pool)
        pool.sort(key=difficulty_sort_key)
        sampled.extend(pool[:take])

    return sampled


def allocate_subdomain_budgets(
    items_by_subdomain: dict[str, list[dict]],
    total_budget: int,
) -> dict[str, int]:
    """Proportionally allocate budget across subdomains with a minimum floor."""
    subdomains = sorted(items_by_subdomain.keys())
    if not subdomains:
        return {}

    total_items = sum(len(items_by_subdomain[sd]) for sd in subdomains)

    raw = {}
    for sd in subdomains:
        n_available = len(items_by_subdomain[sd])
        proportional = max(1, round(total_budget * n_available / total_items))
        raw[sd] = min(proportional, n_available)

    # Apply minimum floor
    for sd in subdomains:
        n_available = len(items_by_subdomain[sd])
        raw[sd] = max(raw[sd], min(MIN_PER_SUBDOMAIN, n_available))

    # Adjust to hit total_budget
    current_total = sum(raw.values())
    if current_total > total_budget:
        while sum(raw.values()) > total_budget:
            candidates = [
                sd
                for sd in subdomains
                if raw[sd] > min(MIN_PER_SUBDOMAIN, len(items_by_subdomain[sd]))
            ]
            if not candidates:
                break
            largest = max(candidates, key=lambda sd: raw[sd])
            raw[largest] -= 1
    elif current_total < total_budget:
        while sum(raw.values()) < total_budget:
            candidates = [
                sd for sd in subdomains if raw[sd] < len(items_by_subdomain[sd])
            ]
            if not candidates:
                break
            best = max(
                candidates,
                key=lambda sd: len(items_by_subdomain[sd]) - raw[sd],
            )
            raw[best] += 1

    return raw


def main():
    rng = random.Random(SEED)

    with open(ROOT / "sampled_1000.json") as f:
        data = json.load(f)

    print(f"Loaded {len(data):,} items from sampled_1000.json")

    # Group by domain -> subdomain
    by_domain_subdomain: dict[str, dict[str, list[dict]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for item in data:
        domain = item["domain"]
        subdomain = str(item.get("subdomain") or "Unknown")
        by_domain_subdomain[domain][subdomain].append(item)

    sampled_all = []

    print(f"\n{'Domain':<25s} {'Budget':>7s} {'Sampled':>8s} {'Subdomains':>11s}")
    print("-" * 55)

    for domain, budget in sorted(DOMAIN_BUDGET.items(), key=lambda x: -x[1]):
        items_by_sd = by_domain_subdomain[domain]

        if not items_by_sd:
            print(f"{domain:<25s} {budget:>7d} {'SKIP':>8s}")
            continue

        sd_budgets = allocate_subdomain_budgets(items_by_sd, budget)

        domain_sampled = []
        for sd, sd_budget in sorted(sd_budgets.items(), key=lambda x: -x[1]):
            pool = items_by_sd[sd]
            picked = sample_stratum_hard_first(pool, sd_budget, rng)
            domain_sampled.extend(picked)

        sampled_all.extend(domain_sampled)

        print(
            f"{domain:<25s} {budget:>7d} {len(domain_sampled):>8d} "
            f"{len(sd_budgets):>5d}/{len(items_by_sd)}"
        )

    print("-" * 55)
    print(
        f"{'TOTAL':<25s} {sum(DOMAIN_BUDGET.values()):>7d} {len(sampled_all):>8d}"
    )

    # Verify dataset coverage — force-add from missing datasets
    sampled_ids = {id(item) for item in sampled_all}
    original_datasets = set(item["dataset"] for item in data)
    sampled_datasets = set(item["dataset"] for item in sampled_all)
    missing_datasets = original_datasets - sampled_datasets

    if missing_datasets:
        print(f"\n⚠ Missing datasets: {missing_datasets}")
        for ds in sorted(missing_datasets):
            # Pick hardest available item from this dataset not already sampled
            ds_items = [
                item
                for item in data
                if item["dataset"] == ds and id(item) not in sampled_ids
            ]
            ds_items.sort(key=difficulty_sort_key)
            if ds_items:
                sampled_all.append(ds_items[0])
                sampled_ids.add(id(ds_items[0]))
                print(f"  Added 1 item from {ds}")

    # Deduplicate
    seen_ids = set()
    deduped = []
    for item in sampled_all:
        obj_id = id(item)
        if obj_id not in seen_ids:
            seen_ids.add(obj_id)
            deduped.append(item)
    sampled_all = deduped

    # Print difficulty distribution
    diff_counter = Counter(get_difficulty(item) for item in sampled_all)
    print(f"\n{'Difficulty':<15s} {'Count':>6s} {'%':>7s}")
    print("-" * 30)
    for d in sorted(diff_counter.keys()):
        c = diff_counter[d]
        print(f"Level {d:<9d} {c:>6d} {c / len(sampled_all):>6.1%}")

    # Print dataset coverage
    final_datasets = Counter(item["dataset"] for item in sampled_all)
    orig_datasets = Counter(item["dataset"] for item in data)
    print(f"\n{'Dataset':<25s} {'Orig':>6s} {'Sampled':>8s} {'Rate':>7s}")
    print("-" * 50)
    for ds, orig_count in sorted(orig_datasets.items(), key=lambda x: -x[1]):
        s = final_datasets.get(ds, 0)
        print(f"{ds:<25s} {orig_count:>6d} {s:>8d} {s / orig_count:>6.1%}")

    # Print question type distribution
    final_qtypes = Counter(item["question_type"] for item in sampled_all)
    print(f"\n{'Question Type':<25s} {'Count':>6s} {'%':>7s}")
    print("-" * 40)
    for qt, c in final_qtypes.most_common():
        print(f"{qt:<25s} {c:>6d} {c / len(sampled_all):>6.1%}")

    # Print domain distribution
    final_domains = Counter(item["domain"] for item in sampled_all)
    print(f"\n{'Domain':<25s} {'Count':>6s} {'%':>7s}")
    print("-" * 40)
    for d, c in sorted(final_domains.items(), key=lambda x: -x[1]):
        print(f"{d:<25s} {c:>6d} {c / len(sampled_all):>6.1%}")

    # Save
    out_path = ROOT / "sampled_100.json"
    with open(out_path, "w") as f:
        json.dump(sampled_all, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(sampled_all)} items to {out_path}")


if __name__ == "__main__":
    main()
