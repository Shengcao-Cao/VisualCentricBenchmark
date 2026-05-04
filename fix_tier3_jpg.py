"""Fix filtered_data_with_solution_hard_tier3.json (JPG variant):

Same as fix_tier3.py but converts inline SVGs to JPG files with a white
background, avoiding the transparent-PNG issue that causes many models to
see "blank/black" images.

Output: tier3_figures_jpg/ directory + tier3_fixed JSON with .jpg paths.
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
    ep = task.get("edited_problem") or {}
    question = ep.get("question") or ""
    options = ep.get("options")

    # Ensure the question text includes the image tag
    if "<image_1>" not in question:
        question = question.rstrip() + "\n<image_1>"

    # Infer question_type from the edited problem's options
    question_type = "single_selection" if options else "free_form"

    return {
        "question_id": f"{task['problem_id']}_tier3_1",
        "tier": 3,
        "question_type": question_type,
        "question": question,
        "options": options,
        "answer": ep.get("answer"),
        "images": [image_path],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix tier3 questions JSON (JPG output)")
    parser.add_argument("-i", "--input", required=True, help="Input tier3 JSON path")
    parser.add_argument("-o", "--output", required=True, help="Output JSON path")
    parser.add_argument(
        "--hard",
        required=True,
        help="Path to filtered_data_with_solution_hard.json (for image count filtering)",
    )
    parser.add_argument(
        "--figures-dir",
        default="tier3_figures_jpg",
        help="Directory for converted JPG files (default: tier3_figures_jpg)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    hard_path = Path(args.hard)
    figures_dir = Path(args.figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)

    raw = json.loads(input_path.read_text())
    tasks = raw.get("tasks") or raw
    if isinstance(tasks, dict):
        tasks = list(tasks.values())
    print(f"Loaded {len(tasks)} tasks from {input_path}")

    hard = json.loads(hard_path.read_text())
    hard_map = {h["id"]: h for h in hard}
    print(f"Loaded {len(hard)} items from {hard_path}")

    out: list[dict] = []
    status_counts: dict[str, int] = {}
    skipped_multi_image = 0
    image_tag_added = 0
    svg_converted = 0
    svg_failed = 0

    for task in tasks:
        pid = task.get("problem_id") or task.get("task_key")
        status = task.get("verification_status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

        if status != "approved":
            continue

        # Skip problems whose original had multiple images
        orig = hard_map.get(pid, {})
        if len(orig.get("images") or []) > 1:
            skipped_multi_image += 1
            continue

        # Convert inline SVG to JPG
        svg_str = task.get("svg") or ""
        jpg_name = f"{pid}.jpg"
        jpg_path = figures_dir / jpg_name
        try:
            _svg_to_jpg(svg_str, jpg_path)
            svg_converted += 1
        except Exception as e:
            print(f"  WARNING: SVG conversion failed for {pid}: {e}")
            svg_failed += 1
            continue

        image_rel_path = f"{figures_dir.name}/{jpg_name}"

        ep = task.get("edited_problem") or {}
        question = ep.get("question") or ""
        if "<image_1>" not in question:
            image_tag_added += 1

        entry = _build_tier3_entry(task, image_rel_path)
        out.append({
            "id": pid,
            "tier3_questions": [entry],
        })

    print(f"\nResults:")
    print(f"  Items written:           {len(out)}")
    print(f"  Verification status:     {status_counts}")
    print(f"  Skipped (multi-image):   {skipped_multi_image}")
    print(f"  Image tag appended:      {image_tag_added}")
    print(f"  SVGs converted:          {svg_converted}")
    print(f"  SVG conversion failed:   {svg_failed}")

    output_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
