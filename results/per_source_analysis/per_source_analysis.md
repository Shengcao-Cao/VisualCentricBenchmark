# Per-Source-Dataset Analysis: Original vs. Tier 3 Accuracy

## Overview

We report accuracy on the original problem (Orig) and Tier 3 (T3) for each of the 10 source datasets represented in the 283-item Tier 3 subset, along with the accuracy change (Δ = T3 − Orig).

If problems from older, widely-distributed benchmarks (e.g., Geometry3k, OlympiadBench) show larger drops than recent benchmarks (e.g., HumanityLastExam), this provides circumstantial evidence that data contamination drives part of the generalization gap.

## Source Dataset Sizes (within Tier 3 subset)

| Source | Count |
|--------|------:|
| Geometry3k | 64 |
| MathVerse | 35 |
| MathVision | 84 |
| MathVista | 3 |
| OlympiadBench | 45 |
| OlympicArena | 4 |
| MMMU | 9 |
| EMMA | 29 |
| MME_Reasoning | 5 |
| HumanityLastExam | 5 |

## Per-Model Breakdown

### GPT-5.4

| Source | Orig (%) | T3 (%) | Δ (pp) |
|--------|--------:|------:|-------:|
| Geometry3k | 95.3 | 87.5 | -7.8 |
| MathVerse | 94.3 | 82.9 | -11.4 |
| MathVision | 98.8 | 86.9 | -11.9 |
| MathVista | 100.0 | 66.7 | -33.3 |
| OlympiadBench | 93.3 | 77.8 | -15.6 |
| OlympicArena | 100.0 | 100.0 | +0.0 |
| MMMU | 88.9 | 100.0 | +11.1 |
| EMMA | 100.0 | 72.4 | -27.6 |
| MME_Reasoning | 100.0 | 80.0 | -20.0 |
| HumanityLastExam | 100.0 | 100.0 | +0.0 |

### GPT-5.4 mini

| Source | Orig (%) | T3 (%) | Δ (pp) |
|--------|--------:|------:|-------:|
| Geometry3k | 78.1 | 82.8 | +4.7 |
| MathVerse | 62.9 | 65.7 | +2.9 |
| MathVision | 78.6 | 64.3 | -14.3 |
| MathVista | 66.7 | 100.0 | +33.3 |
| OlympiadBench | 75.6 | 71.1 | -4.4 |
| OlympicArena | 75.0 | 75.0 | +0.0 |
| MMMU | 100.0 | 77.8 | -22.2 |
| EMMA | 65.5 | 58.6 | -6.9 |
| MME_Reasoning | 80.0 | 60.0 | -20.0 |
| HumanityLastExam | 60.0 | 60.0 | +0.0 |

### Gemini 3.1 Pro

| Source | Orig (%) | T3 (%) | Δ (pp) |
|--------|--------:|------:|-------:|
| Geometry3k | 96.9 | 93.8 | -3.1 |
| MathVerse | 77.1 | 91.4 | +14.3 |
| MathVision | 91.7 | 90.5 | -1.2 |
| MathVista | 66.7 | 66.7 | +0.0 |
| OlympiadBench | 93.3 | 88.9 | -4.4 |
| OlympicArena | 100.0 | 100.0 | +0.0 |
| MMMU | 100.0 | 88.9 | -11.1 |
| EMMA | 79.3 | 75.9 | -3.4 |
| MME_Reasoning | 100.0 | 80.0 | -20.0 |
| HumanityLastExam | 100.0 | 80.0 | -20.0 |

### Gemini 3.1 Flash-Lite

| Source | Orig (%) | T3 (%) | Δ (pp) |
|--------|--------:|------:|-------:|
| Geometry3k | 59.4 | 68.8 | +9.4 |
| MathVerse | 65.7 | 80.0 | +14.3 |
| MathVision | 65.5 | 57.1 | -8.3 |
| MathVista | 33.3 | 66.7 | +33.3 |
| OlympiadBench | 80.0 | 64.4 | -15.6 |
| OlympicArena | 75.0 | 50.0 | -25.0 |
| MMMU | 66.7 | 77.8 | +11.1 |
| EMMA | 48.3 | 62.1 | +13.8 |
| MME_Reasoning | 80.0 | 40.0 | -40.0 |
| HumanityLastExam | 20.0 | 40.0 | +20.0 |

### Gemma 4 31B

| Source | Orig (%) | T3 (%) | Δ (pp) |
|--------|--------:|------:|-------:|
| Geometry3k | 81.2 | 75.0 | -6.2 |
| MathVerse | 68.6 | 85.7 | +17.1 |
| MathVision | 81.0 | 77.4 | -3.6 |
| MathVista | 33.3 | 33.3 | +0.0 |
| OlympiadBench | 75.6 | 82.2 | +6.7 |
| OlympicArena | 100.0 | 100.0 | +0.0 |
| MMMU | 77.8 | 77.8 | +0.0 |
| EMMA | 72.4 | 58.6 | -13.8 |
| MME_Reasoning | 80.0 | 60.0 | -20.0 |
| HumanityLastExam | 100.0 | 60.0 | -40.0 |

### Claude Opus 4.6

| Source | Orig (%) | T3 (%) | Δ (pp) |
|--------|--------:|------:|-------:|
| Geometry3k | 59.4 | 53.1 | -6.2 |
| MathVerse | 57.1 | 71.4 | +14.3 |
| MathVision | 81.0 | 65.5 | -15.5 |
| MathVista | 33.3 | 33.3 | +0.0 |
| OlympiadBench | 82.2 | 68.9 | -13.3 |
| OlympicArena | 100.0 | 50.0 | -50.0 |
| MMMU | 66.7 | 77.8 | +11.1 |
| EMMA | 65.5 | 48.3 | -17.2 |
| MME_Reasoning | 80.0 | 60.0 | -20.0 |
| HumanityLastExam | 60.0 | 80.0 | +20.0 |

### Claude Sonnet 4.6

| Source | Orig (%) | T3 (%) | Δ (pp) |
|--------|--------:|------:|-------:|
| Geometry3k | 56.2 | 60.9 | +4.7 |
| MathVerse | 57.1 | 80.0 | +22.9 |
| MathVision | 66.7 | 61.9 | -4.8 |
| MathVista | 0.0 | 33.3 | +33.3 |
| OlympiadBench | 82.2 | 75.6 | -6.7 |
| OlympicArena | 75.0 | 75.0 | +0.0 |
| MMMU | 88.9 | 77.8 | -11.1 |
| EMMA | 62.1 | 55.2 | -6.9 |
| MME_Reasoning | 80.0 | 80.0 | +0.0 |
| HumanityLastExam | 80.0 | 60.0 | -20.0 |

### Qwen3-VL-235B-A22B

| Source | Orig (%) | T3 (%) | Δ (pp) |
|--------|--------:|------:|-------:|
| Geometry3k | 31.2 | 42.2 | +10.9 |
| MathVerse | 45.7 | 65.7 | +20.0 |
| MathVision | 34.5 | 50.0 | +15.5 |
| MathVista | 0.0 | 0.0 | +0.0 |
| OlympiadBench | 68.9 | 57.8 | -11.1 |
| OlympicArena | 50.0 | 50.0 | +0.0 |
| MMMU | 77.8 | 66.7 | -11.1 |
| EMMA | 27.6 | 31.0 | +3.4 |
| MME_Reasoning | 40.0 | 60.0 | +20.0 |
| HumanityLastExam | 40.0 | 0.0 | -40.0 |

### Kimi K2.5

| Source | Orig (%) | T3 (%) | Δ (pp) |
|--------|--------:|------:|-------:|
| Geometry3k | 42.2 | 42.2 | +0.0 |
| MathVerse | 45.7 | 77.1 | +31.4 |
| MathVision | 60.7 | 57.1 | -3.6 |
| MathVista | 100.0 | 0.0 | -100.0 |
| OlympiadBench | 62.2 | 62.2 | +0.0 |
| OlympicArena | 0.0 | 25.0 | +25.0 |
| MMMU | 33.3 | 22.2 | -11.1 |
| EMMA | 44.8 | 34.5 | -10.3 |
| MME_Reasoning | 80.0 | 60.0 | -20.0 |
| HumanityLastExam | 20.0 | 40.0 | +20.0 |

### Qwen3.5-397B-A17B

| Source | Orig (%) | T3 (%) | Δ (pp) |
|--------|--------:|------:|-------:|
| Geometry3k | 92.2 | 90.6 | -1.6 |
| MathVerse | 80.0 | 88.6 | +8.6 |
| MathVision | 86.9 | 82.1 | -4.8 |
| MathVista | 100.0 | 66.7 | -33.3 |
| OlympiadBench | 93.3 | 77.8 | -15.6 |
| OlympicArena | 100.0 | 75.0 | -25.0 |
| MMMU | 88.9 | 88.9 | +0.0 |
| EMMA | 75.9 | 79.3 | +3.4 |
| MME_Reasoning | 80.0 | 80.0 | +0.0 |
| HumanityLastExam | 80.0 | 100.0 | +20.0 |

## Average Across Models

| Source | Count | Orig (%) | T3 (%) | Δ (pp) |
|--------|------:|--------:|------:|-------:|
| Geometry3k | 64 | 69.2 | 69.7 | +0.5 |
| MathVerse | 35 | 65.4 | 78.9 | +13.4 |
| MathVision | 84 | 74.5 | 69.3 | -5.2 |
| MathVista | 3 | 53.3 | 46.7 | -6.7 |
| OlympiadBench | 45 | 80.7 | 72.7 | -8.0 |
| OlympicArena | 4 | 77.5 | 70.0 | -7.5 |
| MMMU | 9 | 78.9 | 75.6 | -3.3 |
| EMMA | 29 | 64.1 | 57.6 | -6.6 |
| MME_Reasoning | 5 | 80.0 | 66.0 | -14.0 |
| HumanityLastExam | 5 | 66.0 | 62.0 | -4.0 |

## Compact Table: Δ (T3 − Orig) by Model and Source

| Model | Geometry3k (64) | MathVerse (35) | MathVision (84) | MathVista (3) | OlympiadBench (45) | OlympicArena (4) | MMMU (9) | EMMA (29) | MME_Reasoning (5) | HumanityLastExam (5) | All |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GPT-5.4 | -7.8 | -11.4 | -11.9 | -33.3 | -15.6 | +0.0 | +11.1 | -27.6 | -20.0 | +0.0 | -11.7 |
| GPT-5.4 mini | +4.7 | +2.9 | -14.3 | +33.3 | -4.4 | +0.0 | -22.2 | -6.9 | -20.0 | +0.0 | -2.7 |
| Gemini 3.1 Pro | -3.1 | +14.3 | -1.2 | +0.0 | -4.4 | +0.0 | -11.1 | -3.4 | -20.0 | -20.0 | -4.9 |
| Gemini 3.1 Flash-Lite | +9.4 | +14.3 | -8.3 | +33.3 | -15.6 | -25.0 | +11.1 | +13.8 | -40.0 | +20.0 | +1.3 |
| Gemma 4 31B | -6.2 | +17.1 | -3.6 | +0.0 | +6.7 | +0.0 | +0.0 | -13.8 | -20.0 | -40.0 | -6.0 |
| Claude Opus 4.6 | -6.2 | +14.3 | -15.5 | +0.0 | -13.3 | -50.0 | +11.1 | -17.2 | -20.0 | +20.0 | -7.7 |
| Claude Sonnet 4.6 | +4.7 | +22.9 | -4.8 | +33.3 | -6.7 | +0.0 | -11.1 | -6.9 | +0.0 | -20.0 | +1.1 |
| Qwen3-VL-235B-A22B | +10.9 | +20.0 | +15.5 | +0.0 | -11.1 | +0.0 | -11.1 | +3.4 | +20.0 | -40.0 | +0.8 |
| Kimi K2.5 | +0.0 | +31.4 | -3.6 | -100.0 | +0.0 | +25.0 | -11.1 | -10.3 | -20.0 | +20.0 | -6.9 |
| Qwen3.5-397B-A17B | -1.6 | +8.6 | -4.8 | -33.3 | -15.6 | -25.0 | +0.0 | +3.4 | +0.0 | +20.0 | -4.8 |
| **Average** | +0.5 | +13.4 | -5.2 | -6.7 | -8.0 | -7.5 | -3.3 | -6.6 | -14.0 | -4.0 | -4.1 |

## How to Reproduce

```bash
conda activate dataset
python results/per_source_analysis/per_source_analysis.py
```
