#!/usr/bin/env python3
"""Merge all <dataset>/<split>.json files into one JSON + one figures folder."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
OUT_JSON = ROOT / "all_data.json"
OUT_FIGURES = ROOT / "all_figures"


def main():
    OUT_FIGURES.mkdir(exist_ok=True)

    all_items = []
    total_figures = 0
    missing = []

    for dataset_dir in sorted(ROOT.iterdir()):
        if not dataset_dir.is_dir():
            continue
        for jf in sorted(dataset_dir.glob("*.json")):
            with open(jf) as f:
                items = json.load(f)

            for item in items:
                new_images = []
                for img_path in item.get("images", []) or []:
                    # Resolve the actual source file
                    src = (dataset_dir / img_path).resolve()
                    if not src.exists():
                        src = (ROOT / img_path).resolve()
                    if not src.exists():
                        missing.append((item.get("id", "?"), img_path))
                        new_images.append(f"all_figures/{Path(img_path).name}")
                        continue
                    filename = src.name
                    dst = OUT_FIGURES / filename
                    if not dst.exists():
                        shutil.copy2(src, dst)
                        total_figures += 1
                    new_images.append(f"all_figures/{filename}")
                item["images"] = new_images

            all_items.extend(items)
            print(f"  {dataset_dir.name}/{jf.name}: {len(items)} items")

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_items, f, indent=2, ensure_ascii=False)

    print(f"\nMerged {len(all_items):,} items -> {OUT_JSON}")
    print(f"Copied {total_figures:,} figures -> {OUT_FIGURES}/")
    if missing:
        print(f"\nWARNING: {len(missing)} missing figure(s):")
        for item_id, path in missing[:10]:
            print(f"  {item_id}: {path}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")


if __name__ == "__main__":
    main()
