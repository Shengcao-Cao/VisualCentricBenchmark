# Tier 3 Evaluation Results

Total tier3 problems: **313**

## Accuracy (judged by gemini-3.1-flash-lite-preview)

| Model | Total | Correct | Incorrect | Accuracy |
|---|---|---|---|---|
| gpt_5_4 | 313 | 212 | 101 | 67.7% |
| gpt_5_4_mini | 313 | 185 | 128 | 59.1% |
| gemini_3_1_pro_preview | 313 | 291 | 22 | 93.0% |
| gemini_3_1_flash_lite_preview | 313 | 237 | 76 | 75.7% |
| gemma_4_31b | 313 | 253 | 60 | 80.8% |
| claude_opus_4_6 | 313 | 231 | 82 | 73.8% |
| claude_sonnet_4_6 | 313 | 238 | 75 | 76.0% |
| qwen3_vl_235b_a22b | 313 | 174 | 139 | 55.6% |
| kimi_k2_5 | 313 | 201 | 112 | 64.2% |
| nova_2_lite | 313 | 108 | 205 | 34.5% |
| open_router_qwen3_5_397b_a17b | 313 | 233 | 80 | 74.4% |

## Unreadable image complaints

Number of items where the model's answer text suggests it couldn't read the image.
All 313 images render correctly; these are false negatives from the models.

| Model | Unreadable | % |
|---|---|---|
| gpt_5_4 | 19 | 6.1% |
| gpt_5_4_mini | 18 | 5.8% |
| gemini_3_1_pro_preview | 6 | 1.9% |
| gemini_3_1_flash_lite_preview | 2 | 0.6% |
| gemma_4_31b | 2 | 0.6% |
| claude_opus_4_6 | 93 | 29.7% |
| claude_sonnet_4_6 | 88 | 28.1% |
| qwen3_vl_235b_a22b | 43 | 13.7% |
| kimi_k2_5 | 7 | 2.2% |
| nova_2_lite | 19 | 6.1% |
| open_router_qwen3_5_397b_a17b | 62 | 19.8% |

Items flagged by 5+ models (8):

| Problem ID | Models flagging |
|---|---|
| MathVision-test-2873 | 8 |
| MathVision-test-1698 | 6 |
| MME_Reasoning-train-159 | 5 |
| MathVision-test-1236 | 5 |
| EMMA-test-1994 | 5 |
| Geometry3k-train-940 | 5 |
| Geometry3k-train-951 | 5 |
| EMMA-test-1596 | 5 |

## Comparison with original images

Accuracy on the same 313 problems using original images vs tier3 regenerated diagrams.

| Model | Original | Tier3 | Delta |
|---|---|---|---|
| gpt_5_4 | 94.2% | 67.7% | -26.5% |
| gpt_5_4_mini | 72.8% | 59.1% | -13.7% |
| gemini_3_1_pro_preview | 87.9% | 93.0% | +5.1% |
| gemini_3_1_flash_lite_preview | 62.6% | 75.7% | +13.1% |
| gemma_4_31b | 76.7% | 80.8% | +4.2% |
| claude_opus_4_6 | 68.4% | 73.8% | +5.4% |
| claude_sonnet_4_6 | 64.2% | 76.0% | +11.8% |
| qwen3_vl_235b_a22b | 39.3% | 55.6% | +16.3% |
| kimi_k2_5 | 49.8% | 64.2% | +14.4% |
| nova_2_lite | 13.7% | 34.5% | +20.8% |
| open_router_qwen3_5_397b_a17b | 84.7% | 74.4% | -10.2% |

## Notes

- 312/313 tier3 PNGs have transparent backgrounds (RGBA). Models may render transparent regions as black,
  contributing to false "blank/black image" complaints. Consider flattening alpha to white.
- Judge model: gemini-3.1-flash-lite-preview (default in tier3.sh)
- All tier3 images were converted from inline SVGs via cairosvg
