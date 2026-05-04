#!/usr/bin/env python3
"""
Stratified sampling script to extract ~1000 representative problems from all_data.json.

Strategy:
- Allocate fixed budget per domain (down-sample Math, up-sample rare domains)
- Within each domain, distribute proportionally across subdomains with a minimum floor
- Within each stratum, maintain question_type ratios
- Ensure every dataset source is represented
- Fixed random seed for reproducibility
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).parent
SEED = 42

# Domain budgets (total ~1000)
DOMAIN_BUDGET = {
    "Math": 400,
    "Physics": 200,
    "Chemistry": 150,
    "Puzzle": 100,
    "Computer Science": 60,
    "Biology": 40,
    "Geography": 30,
    "Engineering": 20,
}

# Minimum items per subdomain (if enough exist)
MIN_PER_SUBDOMAIN = 2


def allocate_subdomain_budgets(
    items_by_subdomain: Dict[str, List[dict]],
    total_budget: int,
) -> Dict[str, int]:
    """Proportionally allocate budget across subdomains with a minimum floor."""
    subdomains = sorted(items_by_subdomain.keys())

    if not subdomains:
        return {}

    total_items = sum(len(items_by_subdomain[sd]) for sd in subdomains)

    # First pass: proportional allocation with floor
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
        # Need to reduce — trim largest subdomains first
        while sum(raw.values()) > total_budget:
            # Find largest subdomain that can be reduced
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
        # Need to add more — add to subdomains that have room
        while sum(raw.values()) < total_budget:
            candidates = [
                sd for sd in subdomains if raw[sd] < len(items_by_subdomain[sd])
            ]
            if not candidates:
                break
            # Add to the subdomain with the largest remaining pool
            best = max(
                candidates,
                key=lambda sd: len(items_by_subdomain[sd]) - raw[sd],
            )
            raw[best] += 1

    return raw


def sample_stratum(items: List[dict], n: int, rng: random.Random) -> List[dict]:
    """Sample n items, maintaining question_type ratio and dataset coverage."""
    if n >= len(items):
        return list(items)

    # Group by question_type
    by_qtype = defaultdict(list)
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

    # Sample from each question_type group
    sampled = []
    for qt in qtypes:
        pool = by_qtype[qt]
        take = min(qtype_budgets.get(qt, 0), len(pool))
        sampled.extend(rng.sample(pool, take))

    return sampled


def main():
    rng = random.Random(SEED)

    with open(ROOT / "all_data.json") as f:
        data = json.load(f)

    print(f"Loaded {len(data):,} items")

    # Group by domain -> subdomain
    by_domain_subdomain = defaultdict(lambda: defaultdict(list))
    for item in data:
        domain = item["domain"]
        subdomain = str(item.get("subdomain") or "Unknown")
        by_domain_subdomain[domain][subdomain].append(item)

    sampled_all = []
    sampled_datasets = Counter()

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
            picked = sample_stratum(pool, sd_budget, rng)
            domain_sampled.extend(picked)

        sampled_all.extend(domain_sampled)
        for item in domain_sampled:
            sampled_datasets[item["dataset"]] += 1

        print(
            f"{domain:<25s} {budget:>7d} {len(domain_sampled):>8d} "
            f"{len(sd_budgets):>5d}/{len(items_by_sd)}"
        )

    print("-" * 55)
    print(f"{'TOTAL':<25s} {sum(DOMAIN_BUDGET.values()):>7d} {len(sampled_all):>8d}")

    # Verify dataset coverage
    original_datasets = set(item["dataset"] for item in data)
    missing_datasets = original_datasets - set(sampled_datasets.keys())

    if missing_datasets:
        print(f"\n⚠ Missing datasets: {missing_datasets}")
        # Force-add a few items from missing datasets
        for ds in missing_datasets:
            ds_items = [item for item in data if item["dataset"] == ds]
            add_n = min(3, len(ds_items))
            sampled_all.extend(rng.sample(ds_items, add_n))
            print(f"  Added {add_n} items from {ds}")

    # Print dataset coverage
    final_datasets = Counter(item["dataset"] for item in sampled_all)
    print(f"\n{'Dataset':<25s} {'Original':>9s} {'Sampled':>8s} {'Rate':>7s}")
    print("-" * 52)
    for ds, orig_count in sorted(
        Counter(item["dataset"] for item in data).items(), key=lambda x: -x[1]
    ):
        s = final_datasets.get(ds, 0)
        print(f"{ds:<25s} {orig_count:>9,d} {s:>8d} {s/orig_count:>6.1%}")

    # Print question type distribution
    final_qtypes = Counter(item["question_type"] for item in sampled_all)
    print(f"\n{'Question Type':<25s} {'Count':>6s} {'%':>7s}")
    print("-" * 40)
    for qt, c in final_qtypes.most_common():
        print(f"{qt:<25s} {c:>6d} {c/len(sampled_all):>6.1%}")

    # Print domain distribution
    final_domains = Counter(item["domain"] for item in sampled_all)
    print(f"\n{'Domain':<25s} {'Count':>6s} {'%':>7s}")
    print("-" * 40)
    for d, c in sorted(final_domains.items(), key=lambda x: -x[1]):
        print(f"{d:<25s} {c:>6d} {c/len(sampled_all):>6.1%}")

    # Deduplicate by object identity (same dict reference = same item)
    seen_ids = set()
    deduped = []
    for item in sampled_all:
        obj_id = id(item)
        if obj_id not in seen_ids:
            seen_ids.add(obj_id)
            deduped.append(item)
    sampled_all = deduped

    # Save
    out_path = ROOT / "sampled_1000.json"
    with open(out_path, "w") as f:
        json.dump(sampled_all, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(sampled_all)} items to {out_path}")


if __name__ == "__main__":
    main()
