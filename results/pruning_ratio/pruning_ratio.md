# Pruning Ratio Analysis

## Overview

We stratify Tier 2 problems by the fraction of characters removed during pruning and examine whether heavier pruning causes larger accuracy drops. A positive correlation between pruning ratio and accuracy degradation confirms that the pruning signal is meaningful and proportional.

**Pruning ratio** = 1 − len(pruned_question) / len(original_question), measured in characters.

Items with valid pruning ratio (non-negative): **946** out of 1,035 T2 items. 89 items excluded because the pruned question is longer than the original (these are problems where the original text is minimal, e.g. `<image_1>`, and the pruning pipeline expanded it into explicit text).

Pruning ratio: mean = 22.3%, median = 19.5%, Q1 = 10.7%, Q3 = 31.2%.

Tercile boundaries: 15.0% and 30.0%.

## Outputs

### `pruning_ratio.{pdf,png}`

Two-panel figure. Left: original and pruned (T2) accuracy by pruning ratio tercile, pooled across all 10 models. Right: accuracy change (Δ = T2 − Original) by tercile.

## Pooled Results (across models)

| Pruning Ratio | n | Original (%) | Pruned (%) | Δ (pp) |
|--------------|---:|------------:|----------:|-------:|
| [0, 15%] | 3,650 | 62.0 | 59.5 | -2.6 |
| (15%, 30%] | 3,250 | 64.0 | 56.3 | -7.7 |
| (30%, 1] | 2,560 | 63.7 | 49.9 | -13.8 |

## Per-Model Correlation: Pruning Ratio vs. Accuracy Change

| Model | Original (%) | Pruned (%) | Δ (pp) | Pearson r | p-value | Spearman ρ | p-value |
|-------|------------:|----------:|-------:|----------:|--------:|-----------:|--------:|
| GPT-5.4 | 82.7 | 72.0 | -10.7 | -0.117 | 3.1e-04 | -0.110 | 6.8e-04 |
| GPT-5.4 mini | 60.3 | 52.6 | -7.6 | -0.081 | 1.2e-02 | -0.071 | 2.9e-02 |
| Gemini 3.1 Pro | 79.1 | 74.4 | -4.7 | -0.117 | 3.1e-04 | -0.105 | 1.3e-03 |
| Gemini 3.1 Flash-Lite | 51.8 | 45.6 | -6.2 | -0.137 | 2.5e-05 | -0.115 | 4.0e-04 |
| Gemma 4 31B | 57.2 | 51.9 | -5.3 | -0.108 | 8.8e-04 | -0.103 | 1.5e-03 |
| Claude Opus 4.6 | 69.3 | 58.2 | -11.1 | -0.121 | 2.0e-04 | -0.125 | 1.2e-04 |
| Claude Sonnet 4.6 | 64.1 | 55.9 | -8.1 | -0.141 | 1.4e-05 | -0.135 | 3.1e-05 |
| Qwen3-VL-235B-A22B | 35.6 | 30.3 | -5.3 | -0.041 | 2.1e-01 | -0.035 | 2.8e-01 |
| Kimi K2.5 | 59.5 | 49.7 | -9.8 | -0.041 | 2.1e-01 | -0.052 | 1.1e-01 |
| Qwen3.5-397B-A17B | 72.1 | 67.0 | -5.1 | -0.138 | 2.1e-05 | -0.119 | 2.3e-04 |

**Pooled correlation** (n=9,460): r = -0.102 (p = 2.7e-23), ρ = -0.095 (p = 1.4e-20)

## How to Reproduce

```bash
conda activate dataset
python results/pruning_ratio/pruning_ratio.py
```
