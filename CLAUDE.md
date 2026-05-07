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
│   ├── physics_figures_jpg/    # Physics tier3 JPG images
│   └── *.json             # All data files (see Data Files section)
├── scripts/               # Data processing scripts
│   ├── fix_tier1.py       # Fix tier1 schema (image_index, question_id)
│   ├── fix_tier2.py       # Fix tier2 (parse cache → structured tier2_questions)
│   ├── fix_tier3.py       # Fix tier3 (flatten, filter approved, add image tag)
│   ├── fix_tier3_jpg.py   # Fix tier3 → JPG (white background, no transparency)
│   ├── fix_tier3_jpg_pruned.py  # Fix tier3+pruned (merge original + tier3 + pruned)
│   ├── fix_chemistry_jpg.py     # Fix chemistry data → JPG
│   ├── fix_physics_jpg.py       # Fix physics data → JPG (skip multi-image)
│   ├── translate_chemistry.py   # Translate Chinese chemistry items to English (Gemini)
│   ├── consolidate_physics.py   # Consolidate physics tier3 (filter both-fail, fix qt)
│   ├── consolidate_tier3_physics.py  # Merge physics pruned data for annotation
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
│   ├── tier3_physics.sh   # Tier3 physics inference + judging (regenerated diagrams)
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
│   ├── tier*_results.md            # Markdown result reports
│   ├── t1_correlation/             # T1 perception → reasoning correlation analysis
│   ├── per_source_analysis/        # Per-source-dataset T0 vs T3_2 analysis
│   └── pruning_ratio/              # Pruning ratio vs accuracy drop analysis
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
| **Tier 3 Physics** | Physics diagram formalization | Regenerated JPG diagrams (matplotlib/tikz/circuitikz) | Edited physics question for new diagram |
| **Tier 3_2 Physics** | Physics formalization + pruning | Regenerated JPG diagrams | Pruned version of physics tier3 edited question |

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

### Physics tier3
- `physics_approved.json` — 226 raw physics tier3 tasks (SVG + edited questions, all engines)
- `physics_approved_fixed.json` — 183 items after fix_physics_jpg (multi-image skipped)
- `filtered_data_with_solution_hard_tier3_physics.json` — 159 items (both-fail filtered, qt-fixed)
- `filtered_data_with_solution_hard_tier3_2_physics.json` — 158 items (pruned, for annotation)
- `tier3_physics_ver1_revised_stage4_gpt-5.4_10000.json` — raw model-pruned output (158 items)

### Chemistry tier3
- `chemistry_unreviewed_fixed.json` — 102 chemistry tier3 items (JPG images)
- `chemistry_unreviewed_fixed_chinese.json` — 54 Chinese-language subset
- `chemistry_unreviewed_fixed_chinese_translated.json` — above translated to English

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

# Physics pipeline: approved → JPG → filtered → pruned for annotation
python scripts/fix_physics_jpg.py -i data/physics_approved.json -o data/physics_approved_fixed.json
python scripts/consolidate_physics.py  # → filtered_data_with_solution_hard_tier3_physics.json (159 items)
python scripts/consolidate_tier3_physics.py  # → filtered_data_with_solution_hard_tier3_2_physics.json (158 items, for annotation)

# Translate Chinese chemistry items
python scripts/translate_chemistry.py -i data/chemistry_unreviewed_fixed_chinese.json -o data/chemistry_unreviewed_fixed_chinese_translated.json
```

## Known Issues

- **Physics tier3 multi-image**: 43/226 physics problems have multiple original images but only 1 SVG is generated per task. These are skipped in `fix_physics_jpg.py`.
- **Physics tier3 performance**: Models score *higher* on regenerated physics diagrams than originals (e.g. Flash-Lite +20%, Qwen3-VL +19%), suggesting clean renders are easier to parse than scanned/hand-drawn originals.
- **Tier3 PNG transparency**: 312/313 tier3 PNGs have transparent backgrounds (RGBA). Models (especially GPT, Qwen) render transparent regions as black and claim images are blank. Use JPG versions (`tier3_figures_jpg/`) instead.
- **OpenRouter Qwen3.5 reasoning default**: OpenRouter enables reasoning by default for Qwen3.5-397B even without `reasoning.enabled` param. The `OpenRouterClient` now explicitly passes `{"reasoning": {"enabled": False}}` when `thinking_effort="none"`. Old T1 results for this model (run before 2026-05-04) had reasoning inadvertently enabled and were re-run.
- **Bedrock Converse thinking_effort**: The `BedrockConverseClient` does not pass `thinking_effort` to the Converse API. Qwen3-VL and Nova 2 Lite always use their default behavior. `KimiClient` passes `reasoning_config` via `additionalModelRequestFields` when `thinking_effort != "none"`.
- **better_judge_tier2 on full dataset**: The judge crashes with `IndexError` on items without T2 entries (`tier2_questions: []`). The errors are logged but harmless — items with T2 are still judged correctly. Affects runs on the 2,711-item clean file (1,676 items have no T2).
- **Kimi K2.5 rerun with thinking**: Kimi T0/T2/T3_2 were rerun with `--thinking-effort high` (reasoning enabled). Old results (no thinking) preserved as `*_kimi_k2_5_old*.json`. Canonical files now use thinking.
- **Qwen3-VL rerun without token cap**: Qwen T0/T2/T3_2 were rerun without the 8000 max_tokens cap that truncated long answers. Old results preserved as `*_qwen3_vl_235b_a22b_old*.json`. Canonical files now use default max_tokens.
- **Gemma rate limits**: 30 RPM limit on Gemma-4-31B causes many tier1 sub-questions to fail after 5 retries. Re-run with `--skip-existing` and lower concurrency (`--concurrency 10`).
- **Gemini-3.1-Pro T0 variance**: Original T0 run scored 70.3%; rerun scored 75.2% (+4.9pp). The rerun is now the canonical file.

## Analysis Experiments

### T1 Perception → Reasoning Correlation
- `results/t1_correlation/t1_correlation.py` → `t1_correlation_binned.{pdf,png}`, `t1_correlation_scatter.{pdf,png}`, `t1_correlation.md`
- Correlates T1 perception scores with original/T2 reasoning accuracy. Per-problem correlation is near zero; model-level correlation is moderate (r≈0.7).

### Per-Source-Dataset Analysis
- `results/per_source_analysis/per_source_analysis.py` → `per_source_analysis.md`
- Reports T0 vs T3_2 accuracy grouped by source benchmark (OlympiadBench, Geometry3k, etc.).

### Pruning Ratio Analysis
- `results/pruning_ratio/pruning_ratio.py` → `pruning_ratio.{pdf,png}`, `pruning_ratio.md`
- Stratifies T2 problems by char-based pruning ratio and measures accuracy drop. Heavier pruning → larger drops.

### Image Quality Effect
- `tasks/answer_image_quality.py`, `shells/image_quality.sh`, `results/image_quality/`
- Original text + reproduced T3 image. Inference + judging done for all 10 models.
- Original `image_equivalence` annotation had 144 "equivalent" items, but manual review found 42 were not truly equivalent (some had edited problem text baked into the reproduced image, others had different diagram content). Annotation UI: `annotation/annotate_image_quality.py`.
- Corrected labels saved back to `data/filtered_data_with_solution_hard_tier3_2.json` (now 102 equivalent, 181 edited). Analysis uses `data/image_quality_equiv_subset_corrected.json` (102 items).
- Results: on the corrected 102-item subset, reproduced images cause a small average drop (B−A ≈ −1.6 pp), likely within noise. The image swap itself is not a major factor.

### Ablation Experiments (text-only / caption / image+caption)
- `tasks/answer_ablation.py`, `shells/ablation.sh`
- New pipeline tasks: `answer_ablation`, `answer_tier2_ablation`, `ablation_judge`, `ablation_judge_tier2` (use `--ablation-mode` flag)
- Three modes: `text_only`, `text_caption`, `text_image_caption`. Runs on T0 and T2 for GPT-5.4, Gemini 3.1 Pro, Qwen3.5-397B.
- Data: `data/ablation_subset_200.json` (200-item subset of T2 items)

## Environment

- **Conda env**: `dataset`
- **Python**: 3.12
- **Key packages**: `cairosvg`, `PIL`, `openai`, `google-genai`, `boto3`, `json_repair`
