"""Fix physics_approved.json:

Convert the physics pipeline output into the standard tier3_fixed format
with JPG images (white background).

Physics schema differences from the standard tier3 format:
- ``svg_content`` instead of ``svg``
- ``edited_question/edited_options/edited_answer/edited_captions`` instead of ``edited_problem``
- ``status`` instead of ``verification_status`` (all are ``completed``)
- ``original_problem`` embedded in each task (no separate hard file needed)
- Multi-image originals are skipped (only 1 SVG generated per task)
"""

import argparse
import io
import json
from pathlib import Path

import cairosvg
from PIL import Image


def _svg_to_jpg(svg_str: str, out_path: Path) -> None:
    """Convert an SVG string to a JPG file with white background."""
    png_data = cairosvg.svg2png(bytestring=svg_str.encode("utf-8"))
    img = Image.open(io.BytesIO(png_data))
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")
    img.save(out_path, format="JPEG", quality=95)


def _build_tier3_entry(task: dict, image_path: str) -> dict:
    question = task.get("edited_question") or ""
    options = task.get("edited_options")

    # Ensure the question text includes the image tag
    if "<image_1>" not in question:
        question = question.rstrip() + "\n<image_1>"

    # Infer question_type from the edited problem's options
    question_type = "single_selection" if options else "free_form"

    pid = task.get("problem_id") or task.get("task_key")
    return {
        "question_id": f"{pid}_tier3_1",
        "tier": 3,
        "question_type": question_type,
        "question": question,
        "options": options,
        "answer": task.get("edited_answer"),
        "images": [image_path],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix physics questions JSON (JPG output)")
    parser.add_argument("-i", "--input", required=True, help="Input physics JSON path")
    parser.add_argument("-o", "--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--figures-dir",
        default="data/physics_figures_jpg",
        help="Directory for converted JPG files (default: data/physics_figures_jpg)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    figures_dir = Path(args.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)

    raw = json.loads(input_path.read_text())
    tasks = raw.get("tasks") or raw
    if isinstance(tasks, dict):
        tasks = list(tasks.values())
    print(f"Loaded {len(tasks)} tasks from {input_path}")

    out: list[dict] = []
    skipped_multi_image = 0
    image_tag_added = 0
    svg_converted = 0
    svg_failed = 0

    for task in tasks:
        pid = task.get("problem_id") or task.get("task_key")

        # Skip problems whose original had multiple images
        orig = task.get("original_problem") or {}
        if len(orig.get("images") or []) > 1:
            skipped_multi_image += 1
            continue

        # Convert inline SVG to JPG
        svg_str = task.get("svg_content") or ""
        jpg_name = f"{pid}.jpg"
        jpg_path = figures_dir / jpg_name
        try:
            _svg_to_jpg(svg_str, jpg_path)
            svg_converted += 1
        except Exception as e:
            print(f"  WARNING: SVG conversion failed for {pid}: {e}")
            svg_failed += 1
            continue

        image_rel_path = f"physics_figures_jpg/{jpg_name}"

        question = task.get("edited_question") or ""
        if "<image_1>" not in question:
            image_tag_added += 1

        entry = _build_tier3_entry(task, image_rel_path)
        record = {
            "id": pid,
            "dataset": orig.get("dataset"),
            "domain": orig.get("domain"),
            "subdomain": orig.get("subdomain"),
            "question_type": orig.get("question_type"),
            "question": orig.get("question"),
            "options": orig.get("options"),
            "answer": orig.get("answer"),
            "images": orig.get("images"),
            "tier3_questions": [entry],
        }
        out.append(record)

    print(f"\nResults:")
    print(f"  Items written:           {len(out)}")
    print(f"  Skipped (multi-image):   {skipped_multi_image}")
    print(f"  Image tag appended:      {image_tag_added}")
    print(f"  SVGs converted:          {svg_converted}")
    print(f"  SVG conversion failed:   {svg_failed}")

    output_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
