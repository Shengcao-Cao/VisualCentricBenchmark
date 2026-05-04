# Tier 2 Evaluation Results

Total tier2 substantive problems: **348**

## Accuracy (judged by gemini-3.1-flash-lite-preview)

| Model | Total | Done | Correct | Incorrect | Accuracy |
|---|---|---|---|---|---|
| gpt_5_4 | 348 | 348 | 265 | 83 | 76.1% |
| gpt_5_4_mini | 348 | 348 | 187 | 161 | 53.7% |
| gemini_3_1_pro_preview | 348 | 348 | 275 | 73 | 79.0% |
| gemini_3_1_flash_lite_preview | 348 | 348 | 179 | 169 | 51.4% |
| gemma_4_31b | 348 | 348 | 193 | 155 | 55.5% |
| claude_opus_4_6 | 348 | 348 | 225 | 123 | 64.7% |
| claude_sonnet_4_6 | 348 | 348 | 215 | 133 | 61.8% |
| qwen3_vl_235b_a22b | 348 | 348 | 97 | 251 | 27.9% |
| kimi_k2_5 | 348 | 348 | 148 | 200 | 42.5% |
| nova_2_lite | 348 | 348 | 62 | 286 | 17.8% |
| open_router_qwen3_5_397b_a17b | 348 | 348 | 239 | 109 | 68.7% |

## Accuracy by Question Type

| Model | single_selection | free_form |
|---|---|---|
| gpt_5_4 | 83/109 (76.1%) | 171/221 (77.4%) |
| gpt_5_4_mini | 62/109 (56.9%) | 120/221 (54.3%) |
| gemini_3_1_pro_preview | 87/109 (79.8%) | 177/221 (80.1%) |
| gemini_3_1_flash_lite_preview | 65/109 (59.6%) | 106/221 (48.0%) |
| gemma_4_31b | 67/109 (61.5%) | 120/221 (54.3%) |
| claude_opus_4_6 | 68/109 (62.4%) | 146/221 (66.1%) |
| claude_sonnet_4_6 | 60/109 (55.0%) | 142/221 (64.3%) |
| qwen3_vl_235b_a22b | 35/109 (32.1%) | 55/221 (24.9%) |
| kimi_k2_5 | 49/109 (45.0%) | 92/221 (41.6%) |
| nova_2_lite | 31/109 (28.4%) | 30/221 (13.6%) |
| open_router_qwen3_5_397b_a17b | 80/109 (73.4%) | 150/221 (67.9%) |

## Comparison with original (tier0)

Accuracy on the same 348 problems: original question vs tier2 pruned question.

| Model | Original | Tier2 | Delta |
|---|---|---|---|
| gpt_5_4 | 81.9% | 76.1% | -5.7% |
| gpt_5_4_mini | 60.1% | 53.7% | -6.3% |
| gemini_3_1_pro_preview | 74.7% | 79.0% | +4.3% |
| gemini_3_1_flash_lite_preview | 54.9% | 51.4% | -3.4% |
| gemma_4_31b | 58.9% | 55.5% | -3.4% |
| claude_opus_4_6 | 73.0% | 64.7% | -8.3% |
| claude_sonnet_4_6 | 69.0% | 61.8% | -7.2% |
| qwen3_vl_235b_a22b | 36.5% | 27.9% | -8.6% |
| kimi_k2_5 | 46.6% | 42.5% | -4.0% |
| nova_2_lite | 19.5% | 17.8% | -1.7% |
| open_router_qwen3_5_397b_a17b | 74.7% | 68.7% | -6.0% |

## Notes

- Substantive tier2 problems: 348 (after filtering 657 trivial rewrites from 1005)
- Tier2 uses pruned questions with original images
- Judge model: gemini-3.1-flash-lite-preview
