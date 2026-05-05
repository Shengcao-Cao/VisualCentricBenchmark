# Coreset Project Guide

## Directory Structure

```
coreset/
├── client.py              # VLM client abstraction (OpenAI, Gemini, Claude, Bedrock, OpenRouter)
├── utils.py               # Shared utilities (message building, JSON I/O, async batch runner)
├── run_pipeline.py        # CLI entry point for all pipeline tasks
├── api_key.sh             # API keys (source before running)
├── tasks/                 # Pipeline task implementations
│   ├── answer.py          # Tier0: answer questions with original images
│   ├── answer_tier1.py    # Tier1: answer visual perception MCQs (A/B/C/D)
│   ├── answer_tier2.py    # Tier2: answer pruned questions with original images
│   ├── answer_tier3.py    # Tier3: answer edited questions with regenerated diagrams
│   │                       # Also: answer_tier3_pruned (tier3 pruned questions)
│   ├── better_judge.py    # Tier0: judge with answer extraction + retries
│   ├── better_judge_tier2.py  # Tier2: judge pruned question answers
│   ├── better_judge_tier3.py  # Tier3: judge edited question answers
│   │                          # Also: better_judge_tier3_pruned (tier3 pruned scoring)
│   ├── judge.py           # Basic judge (deprecated in favor of better_judge)
│   ├── trivial_tier2.py   # Identify trivial tier2 rewrites (no meaningful pruning)
│   ├── generate_tier1.py  # Generate tier1 perception questions
│   ├── reference_answer_tier1.py  # Collect reference votes for tier1
│   ├── caption.py         # Generate per-image captions
│   ├── difficulty.py      # Rate difficulty (1-5)
│   ├── perception.py      # Perception evaluation
│   ├── prune.py           # Question pruning
│   └── structured.py      # Structured captions
├── data/                  # All JSON data files + image directories
│   ├── all_figures/       # Original dataset images
│   ├── tier3_figures/     # Tier3 PNG images (transparent background - deprecated)
│   ├── tier3_figures_jpg/ # Tier3 JPG images (white background - use these)
│   ├── chemistry_figures_jpg/  # Chemistry JPG images
│   └── *.json             # All data files (see Data Files section)
├── scripts/               # Data processing scripts
│   ├── fix_tier1.py       # Fix tier1 schema (image_index, question_id)
│   ├── fix_tier2.py       # Fix tier2 (parse cache → structured tier2_questions)
│   ├── fix_tier3.py       # Fix tier3 (flatten, filter approved, add image tag)
│   ├── fix_tier3_jpg.py   # Fix tier3 → JPG (white background, no transparency)
│   ├── fix_tier3_jpg_pruned.py  # Fix tier3+pruned (merge original + tier3 + pruned)
│   ├── fix_chemistry_jpg.py     # Fix chemistry data → JPG
│   ├── filter_trivial_tier2.py  # Remove trivial tier2 problems
│   ├── filter_needs_review_split.py  # Split needs-review into shards
│   ├── filter_tier1_needs_review.py  # Flag tier1 disagreements
│   ├── filter_tier2_needs_review.py  # Flag tier2 issues
│   ├── consolidate_tier3_pruned.py  # Consolidate annotated tier3 pruned → tier3_2
│   ├── merge_annotated.py  # Merge annotator files + originals into full dataset
│   ├── apply_minor_fixes.py  # Apply 170 minor_fix annotations to T1 questions
│   ├── clean_merged.py     # Clean merged dataset (apply verdicts, filter T2)
│   ├── copy_old_results.py  # Copy old predictions into new clean dataset files
│   ├── merge.py, sample.py, sample_100.py, deduplicate.py, ...
│   └── test_tier1_raw.py  # Test model raw responses on tier1
├── shells/                # Shell scripts for batch inference
│   ├── tier1.sh           # Tier1 inference (old, on no_review_needed)
│   ├── tier2.sh           # Tier2 inference + judging (old, on no_review_needed_substantive)
│   ├── tier1+2_clean.sh   # Tier1+2 inference + judging on clean full dataset
│   ├── tier3.sh           # Tier3 inference + judging (JPG images)
│   ├── tier3_2.sh         # Tier3_2 inference + judging (pruned questions)
│   ├── eval_hard.sh       # Tier0 inference + judging
│   ├── judge.sh           # Re-judge all tier0 with better_judge
│   ├── trivial_tier2.sh   # Run trivial detection + filtering
│   ├── merge_annotated.sh # Merge annotators → trivial → fix → clean pipeline
│   └── fix_*.sh, filter_*.sh, ...
├── annotation/            # Annotation UIs + servers
│   ├── annotate_server.py          # Server for tier1/tier2 annotation
│   ├── annotate_tier3_server.py    # Server for tier3 annotation
│   ├── annotate_chemistry_server.py # Server for chemistry annotation
│   ├── annotator.html              # Tier1/tier2 annotation UI
│   ├── annotator_tier3.html        # Tier3 annotation UI
│   ├── annotator_chemistry.html    # Chemistry annotation UI
│   └── viewer*.html                # Read-only viewers
├── results/               # Evaluation results
│   ├── check_tier0_results.py      # Generate tier0_results.md
│   ├── check_tier1_results.py      # Generate tier1_results.md
│   ├── check_tier2_results.py      # Generate tier2_results.md
│   ├── check_tier3_results.py      # Generate tier3_results.md (PNG)
│   ├── check_tier3_jpg_results.py  # Generate tier3_jpg_results.md (JPG)
│   ├── check_tier3_2_results.py    # Generate tier3_2_results.md (edited+pruned)
│   └── tier*_results.md            # Markdown result reports
├── logs/                  # All inference/judging log files
└── visualizations/        # Distribution plots, dedup visualizations
```

## Evaluation Tiers

| Tier | What it tests | Images | Question source |
|------|--------------|--------|----------------|
| **Tier 0** | Original problem-solving | Original images | Original question |
| **Tier 1** | Visual perception (MCQ) | Original images | Generated A/B/C/D sub-questions |
| **Tier 2** | Image reliance (pruned text) | Original images | Pruned question (textual cues removed) |
| **Tier 3** | Diagram formalization | Regenerated JPG diagrams | Edited question for new diagram |
| **Tier 3_2** | Diagram formalization + pruning | Regenerated JPG diagrams | Pruned version of tier3 edited question |

## Models (11 total)

| Slug | Model | Provider |
|------|-------|----------|
| `gpt_5_4` | gpt-5.4 | OpenAI |
| `gpt_5_4_mini` | gpt-5.4-mini | OpenAI |
| `gemini_3_1_pro_preview` | gemini-3.1-pro-preview | Google |
| `gemini_3_1_flash_lite_preview` | gemini-3.1-flash-lite-preview | Google |
| `gemma_4_31b` | gemma-4-31b-it | Google |
| `claude_opus_4_6` | us.anthropic.claude-opus-4-6-v1 | AWS Bedrock |
| `claude_sonnet_4_6` | us.anthropic.claude-sonnet-4-6 | AWS Bedrock |
| `qwen3_vl_235b_a22b` | qwen.qwen3-vl-235b-a22b | AWS Bedrock |
| `kimi_k2_5` | moonshotai.kimi-k2.5 | AWS Bedrock |
| `nova_2_lite` | us.amazon.nova-2-lite-v1:0 | AWS Bedrock |
| `open_router_qwen3_5_397b_a17b` | qwen/qwen3.5-397b-a17b | OpenRouter |

## Key Data Files

All in `data/`. Key files:

### Base dataset
- `filtered_data_with_solution_hard.json` — 2,711 hard problems (base dataset)
- `filtered_data_with_solution_hard_tier1_fixed.json` — tier1 perception questions (all 2,711)
- `filtered_data_with_solution_hard_tier2_fixed.json` — tier2 pruned questions (2,615)
- `filtered_data_with_solution_hard_tier3_fixed_jpg.json` — 313 tier3 problems (JPG)
- `filtered_data_with_solution_hard_tier3_2.json` — 283 tier3_2 problems (consolidated, filtered, pruned)

### Annotation split (old)
- `no_review_needed.json` — 1,035 clean tier1/tier2 problems (no annotation flags)
- `no_review_needed_substantive.json` — 348 substantive tier2 problems (subset of above)
- `needs_review_shard_01.json` through `_05.json` — 1,676 flagged problems (5 shards)
- `needs_review_[name].json` — annotator files (david, ji, mingye, shengcao, zheyu)

### Clean full dataset (current, for evaluation)
- `filtered_data_with_solution_hard_tier1+2_clean.json` — 2,711 items, 11,094 T1 sub-Qs, 1,035 T2 entries
  - Merged from originals + annotator fixes + trivial filtering
  - T1: dropped 435 bad sub-Qs, applied 170 minor fixes, set `gt_answer` on all
  - T2: removed 1,580 trivial/non-prunable entries, applied corrected pruned questions

### Intermediate merge files
- `merged_full.json` — full merge of tier1_fixed + tier2_fixed + annotator files
- `merged_full_trivial.json` — above with trivial_tier2 judgments on all T2 entries
- `merged_full_trivial_fixed.json` — above with 170 minor_fix annotations applied

Model outputs: `*_tier1_[model_slug].json`, `*_tier2_[model_slug].json`, judged: `*_tier2_[model_slug]_judged.json`

## Common Workflows

### Run inference (Tier 1 + 2 on clean dataset)
```bash
source api_key.sh
# See shells/tier1+2_clean.sh for all 11 models
# Tier 1 (no thinking — perception MCQ)
python run_pipeline.py answer_tier1 -i data/filtered_data_with_solution_hard_tier1+2_clean_tier1_gpt_5_4.json -o data/filtered_data_with_solution_hard_tier1+2_clean_tier1_gpt_5_4.json --model-name gpt-5.4 --thinking-effort none --api-key $OPENAI_API_KEY --concurrency 25 --save-interval 50 --skip-existing

# Tier 2 (thinking enabled)
python run_pipeline.py answer_tier2 -i data/filtered_data_with_solution_hard_tier1+2_clean_tier2_gpt_5_4.json -o data/filtered_data_with_solution_hard_tier1+2_clean_tier2_gpt_5_4.json --model-name gpt-5.4 --thinking-effort high --api-key $OPENAI_API_KEY --concurrency 25 --save-interval 50 --skip-existing

# Tier 3 / Tier 3_2
python run_pipeline.py answer_tier3 -i data/filtered_data_with_solution_hard_tier3_fixed_jpg.json -o data/output.json --model-name gpt-5.4 --thinking-effort high --api-key $OPENAI_API_KEY --skip-existing
python run_pipeline.py answer_tier3_pruned -i data/filtered_data_with_solution_hard_tier3_2.json -o data/output.json --model-name gpt-5.4 --thinking-effort high --api-key $OPENAI_API_KEY --skip-existing
```

### Judge answers
```bash
# Tier 2 judging (uses gemini-3.1-flash-lite-preview by default)
python run_pipeline.py better_judge_tier2 -i data/filtered_data_with_solution_hard_tier1+2_clean_tier2_gpt_5_4.json -o data/filtered_data_with_solution_hard_tier1+2_clean_tier2_gpt_5_4_judged.json --model-name gpt-5.4 --judge-api-key $GOOGLE_API_KEY --concurrency 50 --save-interval 100 --skip-existing

# Tier 1 needs no LLM judge — compare directly against gt_answer
python results/check_tier1_results.py
```

### Check results
```bash
python results/check_tier0_results.py   # → results/tier0_results.md
python results/check_tier1_results.py   # → results/tier1_results.md
python results/check_tier2_results.py   # → results/tier2_results.md
python results/check_tier3_results.py   # → results/tier3_results.md
python results/check_tier3_jpg_results.py  # → results/tier3_jpg_results.md
python results/check_tier3_2_results.py    # → results/tier3_2_results.md
```

### Annotation UIs
```bash
# Tier1/Tier2 review
python annotation/annotate_server.py --port 8000
# → http://localhost:8000/annotation/annotator.html?shard=data/needs_review_shard_01.json

# Tier3 review
python annotation/annotate_tier3_server.py --port 8001
# → http://localhost:8001/annotation/annotator_tier3.html?file=data/filtered_data_with_solution_hard_tier3_jpg_pruned_fixed_shard_01.json

# Chemistry review
python annotation/annotate_chemistry_server.py --port 8002
# → http://localhost:8002/annotation/annotator_chemistry.html?file=data/chemistry_unreviewed_fixed.json
```

### Merge annotator data → clean evaluation dataset
```bash
conda activate dataset

# 1. Merge originals + annotator files into full dataset
python scripts/merge_annotated.py -o data/merged_full.json

# 2. Run trivial_tier2 on all T2 entries (skip already-judged)
python run_pipeline.py trivial_tier2 -i data/merged_full.json -o data/merged_full_trivial.json --judge-model gemini-3.1-flash-lite-preview --judge-api-key $GOOGLE_API_KEY --concurrency 25 --save-interval 50 --skip-existing

# 3. Apply 170 minor_fix annotations to T1 questions
python scripts/apply_minor_fixes.py -i data/merged_full_trivial.json -o data/merged_full_trivial_fixed.json

# 4. Clean: drop bad T1, filter trivial/non-prunable T2, set gt_answer
python scripts/clean_merged.py -i data/merged_full_trivial_fixed.json -o data/filtered_data_with_solution_hard_tier1+2_clean.json

# 5. Seed old predictions into new files
python scripts/copy_old_results.py
```

### Fix/process data
```bash
conda activate dataset

# Fix tier3 → JPG (white background)
python scripts/fix_tier3_jpg.py -i data/filtered_data_with_solution_hard_tier3.json -o data/filtered_data_with_solution_hard_tier3_fixed_jpg.json --hard data/filtered_data_with_solution_hard.json

# Consolidate tier3 pruned annotations → tier3_2
python scripts/consolidate_tier3_pruned.py -o data/filtered_data_with_solution_hard_tier3_2.json
```

## Known Issues

- **Tier3 PNG transparency**: 312/313 tier3 PNGs have transparent backgrounds (RGBA). Models (especially GPT, Qwen) render transparent regions as black and claim images are blank. Use JPG versions (`tier3_figures_jpg/`) instead.
- **OpenRouter Qwen3.5 reasoning default**: OpenRouter enables reasoning by default for Qwen3.5-397B even without `reasoning.enabled` param. The `OpenRouterClient` now explicitly passes `{"reasoning": {"enabled": False}}` when `thinking_effort="none"`. Old T1 results for this model (run before 2026-05-04) had reasoning inadvertently enabled and were re-run.
- **Bedrock Converse thinking_effort**: The `BedrockConverseClient` does not pass `thinking_effort` to the Converse API. Qwen3-VL, Kimi K2.5, and Nova 2 Lite always use their default behavior. Kimi K2.5 supports `reasoning_config` as a flat string via `additionalModelRequestFields` (e.g., `{"reasoning_config": "high"}`) but this is not currently wired in.
- **better_judge_tier2 on full dataset**: The judge crashes with `IndexError` on items without T2 entries (`tier2_questions: []`). The errors are logged but harmless — items with T2 are still judged correctly. Affects runs on the 2,711-item clean file (1,676 items have no T2).
- **Gemma rate limits**: 30 RPM limit on Gemma-4-31B causes many tier1 sub-questions to fail after 5 retries. Re-run with `--skip-existing` and lower concurrency (`--concurrency 10`).
- **Gemini-3.1-Pro T0 variance**: Original T0 run scored 70.3%; rerun scored 75.2% (+4.9pp). The rerun is now the canonical file.

## Environment

- **Conda env**: `dataset`
- **Python**: 3.12
- **Key packages**: `cairosvg`, `PIL`, `openai`, `google-genai`, `boto3`, `json_repair`
