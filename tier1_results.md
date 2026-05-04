# Tier 1 Evaluation Results

Total items: **1035**, total sub-questions: **3609**

Accuracy is measured against the majority vote from 3 reference models
(gpt-5.4, claude-opus-4-6, gemini-3.1-pro-preview).

## Overall Accuracy

| Model | Items | Questions | Answered | Correct | Accuracy |
|---|---|---|---|---|---|
| gpt_5_4 | 1035 | 3609 | 3609 | 3588 | 99.4% |
| gpt_5_4_mini | 1035 | 3609 | 3609 | 3427 | 95.0% |
| gemini_3_1_pro_preview | 1035 | 3609 | 3598 | 3571 | 99.2% |
| gemini_3_1_flash_lite_preview | 1035 | 3609 | 3605 | 3517 | 97.6% |
| gemma_4_31b | 1035 | 3609 | 3174 | 3111 | 98.0% |
| claude_opus_4_6 | 1035 | 3609 | 3609 | 3588 | 99.4% |
| claude_sonnet_4_6 | 1035 | 3609 | 3608 | 3485 | 96.6% |
| qwen3_vl_235b_a22b | 1035 | 3609 | 3608 | 3473 | 96.3% |
| kimi_k2_5 | 1035 | 3609 | 3607 | 3347 | 92.8% |
| nova_2_lite | 1035 | 3609 | 3608 | 3259 | 90.3% |
| open_router_qwen3_5_397b_a17b | 1035 | 3609 | 3567 | 1740 | 48.8% |

## Accuracy by Question Type

| Model | A: Entity Recognition | B: Spatial Reasoning | C: Attribute Identification |
|---|---|---|---|
| gpt_5_4 | 1203/1203 (100.0%) | 1200/1203 (99.8%) | 1185/1203 (98.5%) |
| gpt_5_4_mini | 1195/1203 (99.3%) | 1138/1203 (94.6%) | 1094/1203 (90.9%) |
| gemini_3_1_pro_preview | 1202/1203 (99.9%) | 1191/1203 (99.0%) | 1178/1203 (97.9%) |
| gemini_3_1_flash_lite_preview | 1195/1203 (99.3%) | 1178/1203 (97.9%) | 1144/1203 (95.1%) |
| gemma_4_31b | 1066/1203 (88.6%) | 1027/1203 (85.4%) | 1018/1203 (84.6%) |
| claude_opus_4_6 | 1201/1203 (99.8%) | 1193/1203 (99.2%) | 1194/1203 (99.3%) |
| claude_sonnet_4_6 | 1191/1203 (99.0%) | 1170/1203 (97.3%) | 1124/1203 (93.4%) |
| qwen3_vl_235b_a22b | 1192/1203 (99.1%) | 1164/1203 (96.8%) | 1117/1203 (92.9%) |
| kimi_k2_5 | 1161/1203 (96.5%) | 1089/1203 (90.5%) | 1097/1203 (91.2%) |
| nova_2_lite | 1169/1203 (97.2%) | 1084/1203 (90.1%) | 1006/1203 (83.6%) |
| open_router_qwen3_5_397b_a17b | 944/1203 (78.5%) | 468/1203 (38.9%) | 328/1203 (27.3%) |

## Notes

- Tier1 questions are simple MCQ (A/B/C/D) about visual perception
- No LLM judge needed — direct comparison against majority vote
- Thinking disabled for all models (perception-only, no reasoning required)
- Question type distribution: A (Entity Recognition), B (Spatial Reasoning), C (Attribute Identification)
