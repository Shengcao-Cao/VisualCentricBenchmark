# Tier 0 Evaluation Results (Original Images)

Results from `filtered_data_with_solution_hard_[model]_judged.json`.
Judge model: gemini-3.1-flash-lite-preview.

## Overall Accuracy

| Model | Total | Correct | Incorrect | Parse Errors | Accuracy |
|---|---|---|---|---|---|
| gpt_5_4 | 2711 | 2139 | 572 | 0 | 78.9% |
| gpt_5_4_mini | 2711 | 1561 | 1150 | 0 | 57.6% |
| gemini_3_1_pro_preview | 2711 | 2039 | 672 | 0 | 75.2% |
| gemini_3_1_flash_lite_preview | 2711 | 1322 | 1389 | 0 | 48.8% |
| gemma_4_31b | 2709 | 1508 | 1201 | 0 | 55.7% |
| claude_opus_4_6 | 2711 | 1654 | 1057 | 0 | 61.0% |
| claude_sonnet_4_6 | 2711 | 1569 | 1142 | 0 | 57.9% |
| qwen3_vl_235b_a22b | 2711 | 906 | 1805 | 0 | 33.4% |
| kimi_k2_5 | 2711 | 1520 | 1191 | 0 | 56.1% |
| nova_2_lite | 2711 | 449 | 2262 | 0 | 16.6% |
| open_router_qwen3_5_397b_a17b | 2711 | 1808 | 903 | 0 | 66.7% |

## Accuracy by Question Type

| Model | single_selection | free_form |
|---|---|---|
| gpt_5_4 | 735/941 (78.1%) | 1296/1611 (80.4%) |
| gpt_5_4_mini | 545/941 (57.9%) | 946/1611 (58.7%) |
| gemini_3_1_pro_preview | 738/941 (78.4%) | 1222/1611 (75.9%) |
| gemini_3_1_flash_lite_preview | 502/941 (53.3%) | 759/1611 (47.1%) |
| gemma_4_31b | 525/939 (55.9%) | 916/1611 (56.9%) |
| claude_opus_4_6 | 525/941 (55.8%) | 1036/1611 (64.3%) |
| claude_sonnet_4_6 | 504/941 (53.6%) | 986/1611 (61.2%) |
| qwen3_vl_235b_a22b | 364/941 (38.7%) | 498/1611 (30.9%) |
| kimi_k2_5 | 485/941 (51.5%) | 965/1611 (59.9%) |
| nova_2_lite | 230/941 (24.4%) | 207/1611 (12.8%) |
| open_router_qwen3_5_397b_a17b | 646/941 (68.7%) | 1101/1611 (68.3%) |

## Accuracy by Domain (top domains)

| Model | Physics | Math | Chemistry | Geography | Biology | Puzzle | Engineering | Computer Science |
|---|---|---|---|---|---|---|---|---|
| gpt_5_4 | 74% | 91% | 73% | 71% | 71% | 81% | 100% | 100% |
| gpt_5_4_mini | 55% | 69% | 50% | 51% | 48% | 50% | 67% | 90% |
| gemini_3_1_pro_preview | 72% | 86% | 66% | 72% | 71% | 85% | 75% | 90% |
| gemini_3_1_flash_lite_preview | 46% | 56% | 45% | 44% | 46% | 46% | 25% | 50% |
| gemma_4_31b | 48% | 70% | 48% | 49% | 54% | 77% | 33% | 80% |
| claude_opus_4_6 | 65% | 65% | 51% | 56% | 57% | 54% | 42% | 80% |
| claude_sonnet_4_6 | 61% | 64% | 48% | 52% | 51% | 69% | 8% | 70% |
| qwen3_vl_235b_a22b | 29% | 37% | 32% | 35% | 41% | 35% | 25% | 50% |
| kimi_k2_5 | 56% | 67% | 46% | 45% | 50% | 69% | 33% | 40% |
| nova_2_lite | 16% | 14% | 21% | 17% | 13% | 38% | 17% | 30% |
| open_router_qwen3_5_397b_a17b | 65% | 80% | 51% | 66% | 63% | 77% | 42% | 70% |

## Accuracy by Source Dataset

| Model | OlympiadBench | OlympicArena | SUPERChem | EMMA | MathVision | MMMU | Geometry3k | MathVerse | MME_Reasoning | HumanityLastExam | MathVista | PuzzleVQA |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt_5_4 | 76% | 70% | 62% | 91% | 98% | 91% | 91% | 90% | 97% | 93% | 59% | 82% |
| gpt_5_4_mini | 56% | 53% | 48% | 51% | 75% | 73% | 77% | 68% | 74% | 43% | 37% | 41% |
| gemini_3_1_pro_preview | 75% | 68% | 68% | 69% | 89% | 88% | 92% | 82% | 94% | 67% | 85% | 86% |
| gemini_3_1_flash_lite_preview | 49% | 46% | 44% | 44% | 55% | 66% | 55% | 65% | 52% | 26% | 44% | 41% |
| gemma_4_31b | 54% | 51% | 38% | 61% | 76% | 61% | 82% | 67% | 65% | 33% | 30% | 77% |
| claude_opus_4_6 | 72% | 59% | 37% | 54% | 71% | 71% | 48% | 56% | 62% | 47% | 37% | 50% |
| claude_sonnet_4_6 | 70% | 54% | 32% | 58% | 60% | 62% | 59% | 53% | 58% | 34% | 41% | 64% |
| qwen3_vl_235b_a22b | 34% | 36% | 26% | 30% | 34% | 46% | 29% | 35% | 29% | 26% | 33% | 32% |
| kimi_k2_5 | 63% | 52% | 42% | 51% | 68% | 46% | 66% | 61% | 59% | 31% | 70% | 73% |
| nova_2_lite | 16% | 15% | 25% | 18% | 11% | 30% | 7% | 15% | 14% | 10% | 11% | 41% |
| open_router_qwen3_5_397b_a17b | 71% | 61% | 46% | 62% | 84% | 77% | 87% | 76% | 71% | 41% | 56% | 77% |

## Notes

- Total problems: 2711
- Domain distribution: Physics (926), Math (827), Chemistry (568), Geography (174), Biology (168), Puzzle (26), Engineering (12), Computer Science (10)
- Dataset distribution: OlympiadBench (805), OlympicArena (722), SUPERChem (238), EMMA (216), MathVision (213), MMMU (142), Geometry3k (123), MathVerse (79), MME_Reasoning (66), HumanityLastExam (58), MathVista (27), PuzzleVQA (22)
- Judge model: gemini-3.1-flash-lite-preview
