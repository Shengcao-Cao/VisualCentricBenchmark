# Tier 1 Evaluation Results

Total items: **1035**, total sub-questions: **3609**

Accuracy is measured against the majority vote from 3 reference models
(gpt-5.4, claude-opus-4-6, gemini-3.1-pro-preview).

## Overall Accuracy

| Model | Items | Questions | Answered | Correct | Accuracy |
|---|---|---|---|---|---|
| gpt_5_4 | — | — | — | — | — |
| gpt_5_4_mini | — | — | — | — | — |
| gemini_3_1_pro_preview | — | — | — | — | — |
| gemini_3_1_flash_lite_preview | — | — | — | — | — |
| gemma_4_31b | — | — | — | — | — |
| claude_opus_4_6 | — | — | — | — | — |
| claude_sonnet_4_6 | — | — | — | — | — |
| qwen3_vl_235b_a22b | — | — | — | — | — |
| kimi_k2_5 | — | — | — | — | — |
| nova_2_lite | — | — | — | — | — |
| open_router_qwen3_5_397b_a17b | — | — | — | — | — |

## Accuracy by Question Type

| Model | A: Entity Recognition | B: Spatial Reasoning | C: Attribute Identification |
|---|---|---|---|
| gpt_5_4 | — | — | — |
| gpt_5_4_mini | — | — | — |
| gemini_3_1_pro_preview | — | — | — |
| gemini_3_1_flash_lite_preview | — | — | — |
| gemma_4_31b | — | — | — |
| claude_opus_4_6 | — | — | — |
| claude_sonnet_4_6 | — | — | — |
| qwen3_vl_235b_a22b | — | — | — |
| kimi_k2_5 | — | — | — |
| nova_2_lite | — | — | — |
| open_router_qwen3_5_397b_a17b | — | — | — |

## Notes

- Tier1 questions are simple MCQ (A/B/C/D) about visual perception
- No LLM judge needed — direct comparison against majority vote
- Thinking disabled for all models (perception-only, no reasoning required)
- Question type distribution: A (Entity Recognition), B (Spatial Reasoning), C (Attribute Identification)
