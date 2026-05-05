# Tier 1 Evaluation Results

Total items: **2711**, total sub-questions: **11094**

Accuracy is measured against the ground truth answer (majority vote for
unanimous items, human-annotated answer for reviewed items).

## Overall Accuracy

| Model | Items | Questions | Answered | Correct | Accuracy |
|---|---|---|---|---|---|
| gpt_5_4 | 2711 | 11094 | 11094 | 10603 | 95.6% |
| gpt_5_4_mini | 2711 | 11094 | 11094 | 10127 | 91.3% |
| gemini_3_1_pro_preview | 2711 | 11094 | 11082 | 10726 | 96.8% |
| gemini_3_1_flash_lite_preview | 2711 | 11094 | 11077 | 10394 | 93.8% |
| gemma_4_31b | 2711 | 11094 | 11092 | 10532 | 95.0% |
| claude_opus_4_6 | 2711 | 11094 | 11094 | 10316 | 93.0% |
| claude_sonnet_4_6 | 2711 | 11094 | 11093 | 10216 | 92.1% |
| qwen3_vl_235b_a22b | 2711 | 11094 | 11093 | 10247 | 92.4% |
| kimi_k2_5 | 2711 | 11094 | 11093 | 9803 | 88.4% |
| nova_2_lite | 2711 | 11094 | 11094 | 9541 | 86.0% |
| open_router_qwen3_5_397b_a17b | 2711 | 11094 | 11092 | 10375 | 93.5% |

## Accuracy by Question Type

| Model | A: Entity Recognition | B: Spatial Reasoning | C: Attribute Identification |
|---|---|---|---|
| gpt_5_4 | 3755/3788 (99.1%) | 3582/3660 (97.9%) | 3266/3646 (89.6%) |
| gpt_5_4_mini | 3740/3788 (98.7%) | 3403/3660 (93.0%) | 2984/3646 (81.8%) |
| gemini_3_1_pro_preview | 3774/3788 (99.6%) | 3587/3660 (98.0%) | 3365/3646 (92.3%) |
| gemini_3_1_flash_lite_preview | 3741/3788 (98.8%) | 3512/3660 (96.0%) | 3141/3646 (86.1%) |
| gemma_4_31b | 3755/3788 (99.1%) | 3545/3660 (96.9%) | 3232/3646 (88.6%) |
| claude_opus_4_6 | 3726/3788 (98.4%) | 3417/3660 (93.4%) | 3173/3646 (87.0%) |
| claude_sonnet_4_6 | 3714/3788 (98.0%) | 3433/3660 (93.8%) | 3069/3646 (84.2%) |
| qwen3_vl_235b_a22b | 3731/3788 (98.5%) | 3455/3660 (94.4%) | 3061/3646 (84.0%) |
| kimi_k2_5 | 3640/3788 (96.1%) | 3197/3660 (87.3%) | 2966/3646 (81.3%) |
| nova_2_lite | 3626/3788 (95.7%) | 3190/3660 (87.2%) | 2725/3646 (74.7%) |
| open_router_qwen3_5_397b_a17b | 3740/3788 (98.7%) | 3523/3660 (96.3%) | 3112/3646 (85.4%) |

## Notes

- Tier1 questions are simple MCQ (A/B/C/D) about visual perception
- No LLM judge needed — direct comparison against ground truth
- Ground truth: majority vote (unanimous items) or human annotation (reviewed items)
- Thinking disabled for all models (perception-only, no reasoning required)
- Question type distribution: A (Entity Recognition), B (Spatial Reasoning), C (Attribute Identification)
