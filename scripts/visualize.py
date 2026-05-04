#!/usr/bin/env python3
"""Visualize dataset distributions for a given JSON file."""

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.patches import Patch

# Consistent style
BG_COLOR = "#FAFAFA"
GRID_COLOR = "#E0E0E0"
TITLE_SIZE = 15
LABEL_SIZE = 11
TICK_SIZE = 10
ANNOTATION_SIZE = 9

# Fixed domain -> color mapping (shared across domain.png and subdomain.png)
DOMAIN_COLORS = {
    "Math": "#4C72B0",
    "Physics": "#DD8452",
    "Chemistry": "#55A868",
    "Puzzle": "#C44E52",
    "Computer Science": "#8172B3",
    "Biology": "#937860",
    "Geography": "#DA8BC3",
    "Engineering": "#CCB974",
}
FALLBACK_PALETTE = ["#8C8C8C", "#64B5CD", "#D4A373", "#A1C9F4"]


def domain_color(name):
    if name in DOMAIN_COLORS:
        return DOMAIN_COLORS[name]
    extras = sorted(set([name]) - set(DOMAIN_COLORS))
    idx = extras.index(name) if name in extras else 0
    return FALLBACK_PALETTE[idx % len(FALLBACK_PALETTE)]


def style_ax(ax, xlabel=None, ylabel=None):
    ax.set_facecolor(BG_COLOR)
    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=LABEL_SIZE)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=LABEL_SIZE)
    ax.tick_params(labelsize=TICK_SIZE)


def plot_question_type(qtypes, out_dir):
    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_facecolor(BG_COLOR)

    order = ["free_form", "single_selection", "multiple_selection"]
    labels = [qt for qt in order if qt in qtypes]
    sizes = [qtypes[qt] for qt in labels]
    colors = ["#4C72B0", "#55A868", "#DD8452"]

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct=lambda p: f"{p:.1f}%",
        colors=colors[: len(labels)],
        explode=[0.02] * len(labels),
        startangle=90,
        textprops={"fontsize": ANNOTATION_SIZE},
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_fontweight("bold")
        at.set_color("white")

    legend_labels = [f"{l}  ({qtypes[l]:,})" for l in labels]
    ax.legend(
        wedges,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=len(labels),
        fontsize=TICK_SIZE,
        frameon=False,
    )
    ax.set_title(
        "Question Type Distribution", fontsize=TITLE_SIZE, fontweight="bold", pad=12
    )

    fig.savefig(
        out_dir / "question_type.png",
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    print("  -> question_type.png")


def plot_domain(domains, out_dir):
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(BG_COLOR)
    style_ax(ax, xlabel="Number of Items")

    dom_sorted = domains.most_common()
    labels = [d for d, _ in dom_sorted][::-1]
    counts = [c for _, c in dom_sorted][::-1]
    colors = [domain_color(d) for d in labels]

    bars = ax.barh(
        labels, counts, color=colors, edgecolor="white", linewidth=0.5, zorder=3
    )
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + max(counts) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{count:,}",
            va="center",
            fontsize=ANNOTATION_SIZE,
        )

    ax.set_xlim(0, max(counts) * 1.12)
    ax.set_title(
        "Domain Distribution", fontsize=TITLE_SIZE, fontweight="bold", pad=12
    )

    fig.savefig(
        out_dir / "domain.png",
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    print("  -> domain.png")


def plot_subdomain(subdomains, out_dir):
    n = min(30, len(subdomains))
    fig, ax = plt.subplots(figsize=(10, max(5, n * 0.35)))
    fig.patch.set_facecolor(BG_COLOR)
    style_ax(ax, xlabel="Number of Items")

    sub_top = subdomains.most_common(n)
    labels = [s for s, _ in sub_top][::-1]
    counts = [c for _, c in sub_top][::-1]

    colors = [domain_color(l.split(" / ")[0]) for l in labels]

    bars = ax.barh(
        labels, counts, color=colors, edgecolor="white", linewidth=0.5, zorder=3
    )
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + max(counts) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{count:,}",
            va="center",
            fontsize=ANNOTATION_SIZE - 1,
        )

    ax.set_xlim(0, max(counts) * 1.10)
    ax.tick_params(axis="y", labelsize=TICK_SIZE - 1)
    ax.set_title(
        f"Top {n} Subdomains (domain / subdomain)",
        fontsize=TITLE_SIZE,
        fontweight="bold",
        pad=12,
    )

    seen_domains = sorted(set(l.split(" / ")[0] for l in labels))
    legend_handles = [Patch(facecolor=domain_color(d), label=d) for d in seen_domains]
    ax.legend(
        handles=legend_handles,
        loc="lower right",
        fontsize=TICK_SIZE - 1,
        framealpha=0.9,
    )

    fig.savefig(
        out_dir / "subdomain.png",
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    print("  -> subdomain.png")


def plot_num_images(num_images, out_dir):
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(BG_COLOR)
    style_ax(ax, xlabel="Number of Images per Sample", ylabel="Number of Items (log scale)")

    img_sorted = sorted(num_images.items())
    xs = [k for k, _ in img_sorted]
    counts = [c for _, c in img_sorted]

    ax.bar(
        [str(x) for x in xs],
        counts,
        color="#4C72B0",
        edgecolor="white",
        linewidth=0.5,
        zorder=3,
    )
    for i, (x, count) in enumerate(zip(xs, counts)):
        ax.text(
            i,
            count * 1.15,
            f"{count:,}",
            ha="center",
            va="bottom",
            fontsize=ANNOTATION_SIZE - 1,
        )

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda v, _: f"{int(v):,}" if v >= 1 else "")
    )
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8, zorder=0)
    ax.set_title(
        "Number of Images per Sample", fontsize=TITLE_SIZE, fontweight="bold", pad=12
    )

    fig.savefig(
        out_dir / "num_images.png",
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    print("  -> num_images.png")


def plot_data_source(sources, out_dir):
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor(BG_COLOR)
    style_ax(ax, xlabel="Number of Items")

    src_sorted = sources.most_common()
    labels = [s for s, _ in src_sorted][::-1]
    counts = [c for _, c in src_sorted][::-1]

    cmap = plt.cm.Blues
    norm_vals = np.linspace(0.35, 0.85, len(labels))
    colors = [cmap(v) for v in norm_vals]

    bars = ax.barh(
        labels, counts, color=colors, edgecolor="white", linewidth=0.5, zorder=3
    )
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + max(counts) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{count:,}",
            va="center",
            fontsize=ANNOTATION_SIZE,
        )

    ax.set_xlim(0, max(counts) * 1.12)
    ax.set_title(
        "Data Source Distribution", fontsize=TITLE_SIZE, fontweight="bold", pad=12
    )

    fig.savefig(
        out_dir / "data_source.png",
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    print("  -> data_source.png")


def main():
    parser = argparse.ArgumentParser(description="Visualize dataset distributions.")
    parser.add_argument("--input", type=Path, help="Path to input JSON file")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory for figures (default: figures_dist/ next to input)",
    )
    args = parser.parse_args()

    out_dir = args.output or args.input.parent / "figures_dist"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.input) as f:
        items = json.load(f)
    print(f"Loaded {len(items):,} items from {args.input}")

    qtypes = Counter(it.get("question_type", "unknown") for it in items)
    domains = Counter(it.get("domain") for it in items if it.get("domain"))
    subdomains = Counter(
        f"{it['domain']} / {it['subdomain']}"
        for it in items
        if it.get("domain") and it.get("subdomain")
    )
    num_images = Counter(len(it.get("images", [])) for it in items)
    sources = Counter(it.get("dataset", "unknown") for it in items)

    plot_question_type(qtypes, out_dir)
    plot_domain(domains, out_dir)
    plot_subdomain(subdomains, out_dir)
    plot_num_images(num_images, out_dir)
    plot_data_source(sources, out_dir)

    print(f"\nAll figures saved to {out_dir}/")


if __name__ == "__main__":
    main()
