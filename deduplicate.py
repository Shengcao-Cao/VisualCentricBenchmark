#!/usr/bin/env python3
"""Deduplicate dataset by removing one item from each high-similarity cross-dataset pair.

Only considers pairs across different data sources (same-dataset pairs are
excluded, since within-dataset similarity is expected).

Greedy approach: sort all cross-dataset pairs by descending cosine similarity,
then iterate. For each pair above the threshold, remove whichever item has more
remaining duplicates (i.e., more edges in the similarity graph), breaking ties
by keeping the item that appears earlier in the original dataset.

Usage (run from coreset directory):
    python deduplicate.py
    python deduplicate.py --threshold 0.95
    python deduplicate.py --input all_data.json --output deduped_data.json
"""

import argparse
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description="Deduplicate by embedding similarity.")
    parser.add_argument(
        "--input", type=Path, default=Path("all_data.json"),
        help="Input JSON file (default: all_data.json)",
    )
    parser.add_argument(
        "--embeddings", type=Path, default=Path("cosine_sim.npz"),
        help="Cosine similarity npz (default: cosine_sim.npz)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("deduped_data.json"),
        help="Output JSON file (default: deduped_data.json)",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.9,
        help="Cosine similarity threshold for deduplication (default: 0.9)",
    )
    args = parser.parse_args()

    # Load data
    with open(args.input) as f:
        items = json.load(f)
    id_to_idx = {item["id"]: i for i, item in enumerate(items)}
    print(f"Loaded {len(items):,} items from {args.input}")

    # Load similarity matrix
    sim_data = np.load(args.embeddings, allow_pickle=True)
    ids = sim_data["ids"]
    cosine = sim_data["cosine_sim"]
    n = len(ids)
    print(f"Loaded {n}x{n} similarity matrix")

    # Build id mapping: embedding index -> id string
    emb_id_list = [str(x) for x in ids]
    id_to_item = {item["id"]: item for item in items}

    # Build dataset label for each embedding index
    datasets = np.array([id_to_item[eid]["dataset"] for eid in emb_id_list])

    # Extract cross-dataset pairs above threshold
    ri, ci = np.triu_indices(n, k=1)
    vals = cosine[ri, ci]
    cross_mask = datasets[ri] != datasets[ci]
    threshold_mask = vals >= args.threshold
    mask = cross_mask & threshold_mask
    pair_ri = ri[mask]
    pair_ci = ci[mask]
    pair_vals = vals[mask]
    print(f"Cross-dataset pairs above threshold {args.threshold}: {len(pair_vals):,}"
          f" (excluded {(~cross_mask & threshold_mask).sum():,} same-dataset pairs)")

    if len(pair_vals) == 0:
        print("No duplicates found. Copying input to output.")
        with open(args.output, "w") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        return

    # Sort pairs by descending similarity
    order = np.argsort(-pair_vals)
    pair_ri = pair_ri[order]
    pair_ci = pair_ci[order]
    pair_vals = pair_vals[order]

    # Count degree (number of edges) for each node — used to decide which to remove
    degree = np.zeros(n, dtype=np.int32)
    for r, c in zip(pair_ri, pair_ci):
        degree[r] += 1
        degree[c] += 1

    # Greedy removal: process pairs from most to least similar
    removed: set[int] = set()
    removal_log: list[dict] = []

    for r, c, sim in zip(pair_ri, pair_ci, pair_vals):
        if r in removed or c in removed:
            continue

        id_r, id_c = emb_id_list[r], emb_id_list[c]
        orig_idx_r = id_to_idx.get(id_r, float("inf"))
        orig_idx_c = id_to_idx.get(id_c, float("inf"))

        # Remove the one with more remaining edges; tie-break by original order
        if degree[r] > degree[c]:
            victim, kept = r, c
        elif degree[c] > degree[r]:
            victim, kept = c, r
        else:
            # Same degree: keep the one earlier in the original dataset
            if orig_idx_r <= orig_idx_c:
                victim, kept = c, r
            else:
                victim, kept = r, c

        removed.add(victim)
        removal_log.append({
            "removed": emb_id_list[victim],
            "kept": emb_id_list[kept],
            "similarity": float(sim),
        })

    print(f"Removed {len(removed):,} items ({len(removed)/len(items)*100:.1f}%)")

    # Filter items
    removed_ids = {emb_id_list[i] for i in removed}
    deduped = [item for item in items if item["id"] not in removed_ids]
    print(f"Remaining: {len(deduped):,} items")

    # Save
    with open(args.output, "w") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    print(f"Saved to {args.output}")

    # Save removal log
    log_path = args.output.with_suffix(".removal_log.json")
    with open(log_path, "w") as f:
        json.dump(removal_log, f, ensure_ascii=False, indent=2)
    print(f"Removal log saved to {log_path} ({len(removal_log)} entries)")


if __name__ == "__main__":
    main()
