# Tier 2 Evaluation Results

Total tier2 substantive problems: **1035**

## Accuracy (judged by gemini-3.1-flash-lite-preview)

| Model | Total | Done | Correct | Incorrect | Accuracy |
|---|---|---|---|---|---|
| gpt_5_4 | 1035 | 1035 | 754 | 281 | 72.9% |
| gpt_5_4_mini | 1035 | 1035 | 549 | 486 | 53.0% |
| gemini_3_1_pro_preview | 1035 | 1035 | 774 | 261 | 74.8% |
| gemini_3_1_flash_lite_preview | 1035 | 1035 | 484 | 551 | 46.8% |
| gemma_4_31b | 1035 | 1035 | 534 | 501 | 51.6% |
| claude_opus_4_6 | 1035 | 1035 | 606 | 429 | 58.6% |
| claude_sonnet_4_6 | 1035 | 1035 | 580 | 455 | 56.0% |
| qwen3_vl_235b_a22b | 1035 | 1035 | 315 | 720 | 30.4% |
| kimi_k2_5 | 1035 | 1035 | 518 | 517 | 50.0% |
| nova_2_lite | 1035 | 1035 | 154 | 881 | 14.9% |
| open_router_qwen3_5_397b_a17b | 1035 | 1035 | 692 | 343 | 66.9% |

## Accuracy by Question Type

| Model | single_selection | free_form |
|---|---|---|
| gpt_5_4 | 215/297 (72.4%) | 507/687 (73.8%) |
| gpt_5_4_mini | 163/297 (54.9%) | 369/687 (53.7%) |
| gemini_3_1_pro_preview | 227/297 (76.4%) | 523/687 (76.1%) |
| gemini_3_1_flash_lite_preview | 158/297 (53.2%) | 303/687 (44.1%) |
| gemma_4_31b | 165/297 (55.6%) | 348/687 (50.7%) |
| claude_opus_4_6 | 161/297 (54.2%) | 419/687 (61.0%) |
| claude_sonnet_4_6 | 150/297 (50.5%) | 404/687 (58.8%) |
| qwen3_vl_235b_a22b | 115/297 (38.7%) | 187/687 (27.2%) |
| kimi_k2_5 | 137/297 (46.1%) | 363/687 (52.8%) |
| nova_2_lite | 77/297 (25.9%) | 73/687 (10.6%) |
| open_router_qwen3_5_397b_a17b | 198/297 (66.7%) | 475/687 (69.1%) |

## Comparison with original (tier0)

Accuracy on the same 1035 problems: original question vs tier2 pruned question.

| Model | Original | Tier2 | Delta |
|---|---|---|---|
| gpt_5_4 | 82.6% | 72.9% | -9.8% |
| gpt_5_4_mini | 60.1% | 53.0% | -7.1% |
| gemini_3_1_pro_preview | 78.7% | 74.8% | -4.0% |
| gemini_3_1_flash_lite_preview | 52.0% | 46.8% | -5.2% |
| gemma_4_31b | 57.5% | 51.6% | -5.9% |
| claude_opus_4_6 | 69.6% | 58.6% | -11.0% |
| claude_sonnet_4_6 | 64.3% | 56.0% | -8.2% |
| qwen3_vl_235b_a22b | 35.8% | 30.4% | -5.4% |
| kimi_k2_5 | 59.1% | 50.0% | -9.1% |
| nova_2_lite | 17.8% | 14.9% | -2.9% |
| open_router_qwen3_5_397b_a17b | 72.2% | 66.9% | -5.3% |

## Notes

- Substantive tier2 problems: 1035
- Filtered trivial rewrites and non-prunable items; includes human-annotated corrections
- Tier2 uses pruned questions with original images
- Judge model: gemini-3.1-flash-lite-preview
