# Tier 3 Evaluation Results (JPG images)

Total tier3 problems: **313**

## Accuracy (judged by gemini-3.1-flash-lite-preview)

| Model | JPG Correct | JPG Acc | PNG Acc | JPG-PNG |
|---|---|---|---|---|
| gpt_5_4 | 286/313 | 91.4% | 67.7% | +23.6% |
| gpt_5_4_mini | 252/313 | 80.5% | 59.1% | +21.4% |
| gemini_3_1_pro_preview | 290/313 | 92.7% | 93.0% | -0.3% |
| gemini_3_1_flash_lite_preview | 231/313 | 73.8% | 75.7% | -1.9% |
| gemma_4_31b | 259/313 | 82.7% | 80.8% | +1.9% |
| claude_opus_4_6 | 235/313 | 75.1% | 73.8% | +1.3% |
| claude_sonnet_4_6 | 242/313 | 77.3% | 76.0% | +1.3% |
| qwen3_vl_235b_a22b | 168/313 | 53.7% | 55.6% | -1.9% |
| kimi_k2_5 | 205/313 | 65.5% | 64.2% | +1.3% |
| nova_2_lite | 92/313 | 29.4% | 34.5% | -5.1% |
| open_router_qwen3_5_397b_a17b | 274/313 | 87.5% | 74.4% | +13.1% |

## Unreadable image complaints (JPG vs PNG)

| Model | JPG | PNG | Reduction |
|---|---|---|---|
| gpt_5_4 | 1 | 19 | -18 (95%) |
| gpt_5_4_mini | 2 | 18 | -16 (89%) |
| gemini_3_1_pro_preview | 3 | 6 | -3 (50%) |
| gemini_3_1_flash_lite_preview | 0 | 2 | -2 (100%) |
| gemma_4_31b | 1 | 2 | -1 (50%) |
| claude_opus_4_6 | 90 | 93 | -3 (3%) |
| claude_sonnet_4_6 | 84 | 88 | -4 (5%) |
| qwen3_vl_235b_a22b | 30 | 43 | -13 (30%) |
| kimi_k2_5 | 3 | 7 | -4 (57%) |
| nova_2_lite | 11 | 19 | -8 (42%) |
| open_router_qwen3_5_397b_a17b | 19 | 62 | -43 (69%) |

## Comparison with original images (tier0)

Accuracy on the same 313 problems.

| Model | Original | JPG | PNG | Orig→JPG | Orig→PNG |
|---|---|---|---|---|---|
| gpt_5_4 | 94.2% | 91.4% | 67.7% | -2.9% | -26.5% |
| gpt_5_4_mini | 72.8% | 80.5% | 59.1% | +7.7% | -13.7% |
| gemini_3_1_pro_preview | 82.7% | 92.7% | 93.0% | +9.9% | +10.2% |
| gemini_3_1_flash_lite_preview | 62.6% | 73.8% | 75.7% | +11.2% | +13.1% |
| gemma_4_31b | 76.7% | 82.7% | 80.8% | +6.1% | +4.2% |
| claude_opus_4_6 | 68.4% | 75.1% | 73.8% | +6.7% | +5.4% |
| claude_sonnet_4_6 | 64.2% | 77.3% | 76.0% | +13.1% | +11.8% |
| qwen3_vl_235b_a22b | 35.1% | 53.7% | 55.6% | +18.5% | +20.4% |
| kimi_k2_5 | 49.8% | 65.5% | 64.2% | +15.7% | +14.4% |
| nova_2_lite | 13.7% | 29.4% | 34.5% | +15.7% | +20.8% |
| open_router_qwen3_5_397b_a17b | 84.7% | 87.5% | 74.4% | +2.9% | -10.2% |

## Notes

- JPG images have white backgrounds (no transparency)
- PNG images had transparent backgrounds (RGBA), causing "blank/black" complaints
- Judge model: gemini-3.1-flash-lite-preview
