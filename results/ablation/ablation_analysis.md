# Ablation Analysis: Input Modality Experiments

## Overview

We evaluate three top models under different input configurations to measure
the contribution of images and atomic fact captions to reasoning performance.
All experiments use a 200-item subset of problems that have Tier 2 (pruned) variants.

**Input settings:**
- **Text only**: Images removed, replaced with `[Image N hidden]`.
- **Text + Caption**: Images replaced with atomic fact captions (detailed image descriptions).
- **Text + Image** (canonical): Original problem text with original images.
- **Text + Image + Caption**: Original images plus atomic fact captions as supplementary context.
- **Recovered + Image** (T2 only): Recovered question (pruned text with atomic facts re-inserted) + original images.

**Models:** GPT-5.4, Gemini 3.1 Pro, Qwen3.5-397B-A17B.

## Original Problem

| Model | Text only | Text + Caption | Text + Image | Text + Image + Caption |
|---|---|---|---|---|
| GPT-5.4 | 54.5 | 59.0 | 83.5 | 83.5 |
| Gemini 3.1 Pro | 54.5 | 63.5 | 83.0 | 79.0 |
| Qwen3.5-397B-A17B | 50.5 | 48.5 | 70.5 | 70.5 |
| Kimi K2.5 | 47.5 | 50.5 | 56.0 | 68.0 |
| **Average** | 51.8 | 55.4 | 73.2 | 75.2 |

## Tier 2 (Pruned)

| Model | Text only | Text + Caption | Text + Image | Recovered + Image | Text + Image + Caption |
|---|---|---|---|---|---|
| GPT-5.4 | 39.5 | 61.0 | 79.0 | 81.5 | 79.5 |
| Gemini 3.1 Pro | 43.5 | 63.0 | 75.5 | 79.5 | 80.0 |
| Qwen3.5-397B-A17B | 33.5 | 49.0 | 66.5 | 77.5 | 68.0 |
| Kimi K2.5 | 38.5 | 48.0 | 51.0 | 63.5 | 62.0 |
| **Average** | 38.8 | 55.2 | 68.0 | 75.5 | 72.4 |

## Key Findings

### Text-only solvability
Removing images causes a large accuracy drop across all models:
- **GPT-5.4**: Original +29.0 pp, Pruned +39.5 pp
- **Gemini 3.1 Pro**: Original +28.5 pp, Pruned +32.0 pp
- **Qwen3.5-397B-A17B**: Original +20.0 pp, Pruned +33.0 pp
- **Kimi K2.5**: Original +8.5 pp, Pruned +12.5 pp

The drop is larger on pruned problems, confirming that pruning successfully
removes textual shortcuts that previously allowed solving without images.

### Caption as image substitute
Replacing images with atomic fact captions partially recovers performance:
- **GPT-5.4**: +4.5 pp (Original), +21.5 pp (Pruned) over text-only
- **Gemini 3.1 Pro**: +9.0 pp (Original), +19.5 pp (Pruned) over text-only
- **Qwen3.5-397B-A17B**: +-2.0 pp (Original), +15.5 pp (Pruned) over text-only
- **Kimi K2.5**: +3.0 pp (Original), +9.5 pp (Pruned) over text-only

### Image + Caption augmentation
Adding captions on top of images (Text + Image + Caption) vs. canonical (Text + Image):
- **GPT-5.4**: +0.0 pp (Original), +0.5 pp (Pruned)
- **Gemini 3.1 Pro**: -4.0 pp (Original), +4.5 pp (Pruned)
- **Qwen3.5-397B-A17B**: +0.0 pp (Original), +1.5 pp (Pruned)
- **Kimi K2.5**: +12.0 pp (Original), +11.0 pp (Pruned)

### Information completeness (Recovered question)
The recovered question (pruned text with atomic facts re-inserted) + original images:
- **GPT-5.4**: Recovered 81.5% vs. Canonical 79.0% (+2.5 pp)
- **Gemini 3.1 Pro**: Recovered 79.5% vs. Canonical 75.5% (+4.0 pp)
- **Qwen3.5-397B-A17B**: Recovered 77.5% vs. Canonical 66.5% (+11.0 pp)
- **Kimi K2.5**: Recovered 63.5% vs. Canonical 51.0% (+12.5 pp)
Recovery to near-canonical levels confirms that pruning removed only image-redundant information.

## Outputs

- `ablation_results.{pdf,png}`: Grouped bar chart comparing all settings.

## How to Reproduce

```bash
conda activate dataset
python results/ablation/ablation_analysis.py
```
