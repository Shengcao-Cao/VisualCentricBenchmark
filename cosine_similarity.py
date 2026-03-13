#!/usr/bin/env python3
"""Compute pairwise cosine similarity matrix from embeddings.

Processes in row-blocks to limit peak memory. Saves the upper-triangle
in sparse format (row, col, sim) for pairs above a threshold, or the
full dense matrix if --dense is specified.

Usage:
    python cosine_similarity.py                          # defaults
    python cosine_similarity.py --input embeddings.npz --output cosine_sim.npz
    python cosine_similarity.py --block-size 4096        # adjust block size
"""

import argparse
from pathlib import Path

import numpy as np
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser(
        description="Compute pairwise cosine similarity matrix."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("embeddings.npz"),
        help="Input embeddings npz (default: embeddings.npz)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("cosine_sim.npz"),
        help="Output npz file (default: cosine_sim.npz)",
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=4096,
        help="Row block size for chunked computation (default: 4096)",
    )
    args = parser.parse_args()

    data = np.load(args.input, allow_pickle=True)
    ids = data["ids"]
    emb = data["embeddings"].astype(np.float32)
    n, dim = emb.shape
    print(f"Loaded {n:,} embeddings (dim={dim})")

    # L2-normalize once
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    emb_norm = emb / norms
    del emb, norms

    # Pre-allocate output matrix
    mem_gb = n * n * 4 / 1e9
    print(f"Allocating {n}x{n} float32 similarity matrix ({mem_gb:.1f} GB)")
    sim = np.empty((n, n), dtype=np.float32)

    # Compute in row-blocks: sim[i:i+bs, :] = emb_norm[i:i+bs] @ emb_norm.T
    num_blocks = (n + args.block_size - 1) // args.block_size
    for b in tqdm(range(num_blocks), desc="Computing cosine sim", unit="block"):
        start = b * args.block_size
        end = min(start + args.block_size, n)
        sim[start:end] = emb_norm[start:end] @ emb_norm.T

    np.savez(args.output, ids=ids, cosine_sim=sim)
    print(f"Saved to {args.output} (ids: {ids.shape}, cosine_sim: {sim.shape})")


if __name__ == "__main__":
    main()
