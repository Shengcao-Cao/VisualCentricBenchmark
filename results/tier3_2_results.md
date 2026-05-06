# Tier 3_2 Evaluation Results (edited + pruned, JPG images)

Total tier3_2 problems: **283**

## Tier 3_2 Accuracy (judged by gemini-3.1-flash-lite-preview)

| Model | Correct | Accuracy |
|---|---|---|
| gpt_5_4 | 238/283 | 84.1% |
| gpt_5_4_mini | 198/283 | 70.0% |
| gemini_3_1_pro_preview | 252/283 | 89.0% |
| gemini_3_1_flash_lite_preview | 182/283 | 64.3% |
| gemma_4_31b | 215/283 | 76.0% |
| claude_opus_4_6 | 176/283 | 62.2% |
| claude_sonnet_4_6 | 187/283 | 66.1% |
| qwen3_vl_235b_a22b | 138/283 | 48.8% |
| kimi_k2_5 | 148/283 | 52.3% |
| nova_2_lite | 75/283 | 26.5% |
| open_router_qwen3_5_397b_a17b | 238/283 | 84.1% |

## Comparison: Tier 0 vs Tier 3 vs Tier 3_2

Accuracy on the same 283 problems (tier3_2 subset).

| Model | Tier 0 | Tier 3 | Tier 3_2 | T0→T3 | T0→T3_2 | T3→T3_2 |
|---|---|---|---|---|---|---|
| gpt_5_4 | 96.5% | 91.9% | 84.1% | -4.6pp | -12.4pp | -7.8pp |
| gpt_5_4_mini | 74.9% | 80.2% | 70.0% | +5.3pp | -4.9pp | -10.2pp |
| gemini_3_1_pro_preview | 90.5% | 92.9% | 89.0% | +2.5pp | -1.4pp | -3.9pp |
| gemini_3_1_flash_lite_preview | 64.0% | 73.5% | 64.3% | +9.5pp | +0.4pp | -9.2pp |
| gemma_4_31b | 77.7% | 83.7% | 76.0% | +6.0pp | -1.8pp | -7.8pp |
| claude_opus_4_6 | 70.7% | 76.3% | 62.2% | +5.7pp | -8.5pp | -14.1pp |
| claude_sonnet_4_6 | 65.7% | 78.4% | 66.1% | +12.7pp | +0.4pp | -12.4pp |
| qwen3_vl_235b_a22b | 41.3% | 53.7% | 48.8% | +12.4pp | +7.4pp | -4.9pp |
| kimi_k2_5 | 51.6% | 65.4% | 52.3% | +13.8pp | +0.7pp | -13.1pp |
| nova_2_lite | 14.1% | 29.7% | 26.5% | +15.5pp | +12.4pp | -3.2pp |
| open_router_qwen3_5_397b_a17b | 87.3% | 88.0% | 84.1% | +0.7pp | -3.2pp | -3.9pp |
## T0 → T3_2 Breakdown by Relative Difficulty

Problem counts: same=213, easier=30, harder=40

| Model | same (T0) | same (T3_2) | same Δ | easier (T0) | easier (T3_2) | easier Δ | harder (T0) | harder (T3_2) | harder Δ |
|---|---|---|---|---|---|---|---|---|---|
| gpt_5_4 | 97.2% | 85.0% | -12.2pp | 90.0% | 83.3% | -6.7pp | 97.5% | 80.0% | -17.5pp |
| gpt_5_4_mini | 75.6% | 69.0% | -6.6pp | 56.7% | 76.7% | +20.0pp | 85.0% | 70.0% | -15.0pp |
| gemini_3_1_pro_preview | 91.5% | 89.7% | -1.9pp | 80.0% | 86.7% | +6.7pp | 92.5% | 87.5% | -5.0pp |
| gemini_3_1_flash_lite_preview | 64.3% | 63.4% | -0.9pp | 56.7% | 86.7% | +30.0pp | 67.5% | 52.5% | -15.0pp |
| gemma_4_31b | 78.9% | 75.6% | -3.3pp | 66.7% | 86.7% | +20.0pp | 80.0% | 70.0% | -10.0pp |
| claude_opus_4_6 | 70.9% | 62.9% | -8.0pp | 63.3% | 70.0% | +6.7pp | 75.0% | 52.5% | -22.5pp |
| claude_sonnet_4_6 | 67.6% | 67.1% | -0.5pp | 53.3% | 66.7% | +13.3pp | 65.0% | 60.0% | -5.0pp |
| qwen3_vl_235b_a22b | 42.3% | 48.4% | +6.1pp | 26.7% | 50.0% | +23.3pp | 47.5% | 50.0% | +2.5pp |
| kimi_k2_5 | 53.1% | 54.5% | +1.4pp | 46.7% | 50.0% | +3.3pp | 47.5% | 42.5% | -5.0pp |
| nova_2_lite | 13.1% | 25.4% | +12.2pp | 20.0% | 36.7% | +16.7pp | 15.0% | 25.0% | +10.0pp |
| open_router_qwen3_5_397b_a17b | 86.9% | 83.6% | -3.3pp | 80.0% | 90.0% | +10.0pp | 95.0% | 82.5% | -12.5pp |

## T0 → T3_2 Breakdown by Image Equivalence

Problem counts: equivalent=102, edited=181

| Model | equiv (T0) | equiv (T3_2) | equiv Δ | edited (T0) | edited (T3_2) | edited Δ |
|---|---|---|---|---|---|---|
| gpt_5_4 | 97.1% | 89.2% | -7.8pp | 96.1% | 81.2% | -14.9pp |
| gpt_5_4_mini | 73.5% | 75.5% | +2.0pp | 75.7% | 66.9% | -8.8pp |
| gemini_3_1_pro_preview | 91.2% | 88.2% | -2.9pp | 90.1% | 89.5% | -0.6pp |
| gemini_3_1_flash_lite_preview | 60.8% | 62.7% | +2.0pp | 65.7% | 65.2% | -0.6pp |
| gemma_4_31b | 77.5% | 79.4% | +2.0pp | 77.9% | 74.0% | -3.9pp |
| claude_opus_4_6 | 73.5% | 60.8% | -12.7pp | 69.1% | 63.0% | -6.1pp |
| claude_sonnet_4_6 | 63.7% | 64.7% | +1.0pp | 66.9% | 66.9% | +0.0pp |
| qwen3_vl_235b_a22b | 38.2% | 45.1% | +6.9pp | 43.1% | 50.8% | +7.7pp |
| kimi_k2_5 | 54.9% | 44.1% | -10.8pp | 49.7% | 56.9% | +7.2pp |
| nova_2_lite | 11.8% | 18.6% | +6.9pp | 15.5% | 30.9% | +15.5pp |
| open_router_qwen3_5_397b_a17b | 91.2% | 90.2% | -1.0pp | 85.1% | 80.7% | -4.4pp |

## Notes

- Tier 3_2 uses pruned questions with regenerated JPG diagrams
- Pruning removes textual cues that describe diagram content
- 283 problems after filtering: removed image_has_text (14), rejected (8), both-models-fail (8) from 313
- **relative_difficulty**: annotator judgment of whether pruning made the problem same/easier/harder
- **image_equivalence**: whether the regenerated diagram is semantically equivalent or edited from the original
- Judge model: gemini-3.1-flash-lite-preview
