# Image Quality Effect Analysis

## Setup

On the 144-item equivalent-image subset (where the reproduced T3 image is semantically
equivalent to the original), we compare three conditions:

- **A. Orig text + orig image** — baseline (from T0 judged results)
- **B. Orig text + reproduced image** — isolates image quality effect
- **C. Edited text + reproduced image** — full Tier 3 setting (from T3_2 judged results, pruned_scoring)

If B > A, cleaner programmatic renderings help models. If C < B, question editing
(textual shortcut removal) degrades performance beyond the image swap.

## Results

| Model | A: Orig+Orig (%) | B: Orig+Repro (%) | C: Edit+Repro (%) | B−A (pp) | C−A (pp) | n |
|-------|--:|--:|--:|--:|--:|--:|
| GPT-5.4 | 97.1 | 91.2 | 89.2 | -5.9 | -7.8 | 102 |
| GPT-5.4 mini | 73.5 | 71.6 | 75.5 | -2.0 | +2.0 | 102 |
| Gemini 3.1 Pro | 91.2 | 84.3 | 88.2 | -6.9 | -2.9 | 102 |
| Gemini 3.1 Flash-Lite | 60.8 | 55.9 | 62.7 | -4.9 | +2.0 | 102 |
| Gemma 4 31B | 77.5 | 77.5 | 79.4 | +0.0 | +2.0 | 102 |
| Claude Opus 4.6 | 73.5 | 67.6 | 60.8 | -5.9 | -12.7 | 102 |
| Claude Sonnet 4.6 | 63.7 | 69.6 | 64.7 | +5.9 | +1.0 | 102 |
| Qwen3-VL-235B-A22B | 38.2 | 35.3 | 45.1 | -2.9 | +6.9 | 102 |
| Kimi K2.5 | 54.9 | 69.6 | 44.1 | +14.7 | -10.8 | 102 |
| Qwen3.5-397B-A17B | 91.2 | 83.3 | 90.2 | -7.8 | -1.0 | 102 |
| **Average** | 72.2 | 70.6 | 70.0 | -1.6 | -2.2 | — |

## How to Reproduce

```bash
conda activate dataset
python results/image_quality/image_quality.py
```
