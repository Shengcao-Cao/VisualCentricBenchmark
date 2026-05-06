#!/bin/bash
# Ablation timing test: 100 samples, one mode per model to estimate cost/time.
# Runs text_only (cheapest — no images) for each model on T0 only.

set -e

INPUT=data/ablation_subset_100.json
PREFIX=data/ablation_test

# GPT-5.4
echo "=== GPT-5.4 text_only (100 samples) ==="
time python run_pipeline.py answer_ablation \
    -i ${INPUT} -o ${PREFIX}_t0_text_only_gpt_5_4.json \
    --model-name gpt-5.4 \
    --ablation-mode text_only \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 25 --save-interval 50 \
    > logs/ablation_test_gpt_5_4.log 2>&1

echo "=== GPT-5.4 text_image_caption (100 samples) ==="
time python run_pipeline.py answer_ablation \
    -i ${INPUT} -o ${PREFIX}_t0_text_image_caption_gpt_5_4.json \
    --model-name gpt-5.4 \
    --ablation-mode text_image_caption \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 25 --save-interval 50 \
    > logs/ablation_test_gpt_5_4_tic.log 2>&1

# Gemini 3.1 Pro
echo "=== Gemini 3.1 Pro text_only (100 samples) ==="
time python run_pipeline.py answer_ablation \
    -i ${INPUT} -o ${PREFIX}_t0_text_only_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --ablation-mode text_only \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    > logs/ablation_test_gemini_3_1_pro.log 2>&1

echo "=== Gemini 3.1 Pro text_image_caption (100 samples) ==="
time python run_pipeline.py answer_ablation \
    -i ${INPUT} -o ${PREFIX}_t0_text_image_caption_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --ablation-mode text_image_caption \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    > logs/ablation_test_gemini_3_1_pro_tic.log 2>&1

# Qwen3.5-397B (OpenRouter)
echo "=== Qwen3.5-397B text_only (100 samples) ==="
time python run_pipeline.py answer_ablation \
    -i ${INPUT} -o ${PREFIX}_t0_text_only_open_router_qwen3_5_397b_a17b.json \
    --model-name qwen/qwen3.5-397b-a17b \
    --open-router \
    --ablation-mode text_only \
    --thinking-effort high \
    --api-key $OPENROUTER_API_KEY \
    --concurrency 20 --save-interval 20 \
    > logs/ablation_test_qwen3_5.log 2>&1

echo "=== Qwen3.5-397B text_image_caption (100 samples) ==="
time python run_pipeline.py answer_ablation \
    -i ${INPUT} -o ${PREFIX}_t0_text_image_caption_open_router_qwen3_5_397b_a17b.json \
    --model-name qwen/qwen3.5-397b-a17b \
    --open-router \
    --ablation-mode text_image_caption \
    --thinking-effort high \
    --api-key $OPENROUTER_API_KEY \
    --concurrency 20 --save-interval 20 \
    > logs/ablation_test_qwen3_5_tic.log 2>&1

echo "All timing tests complete."
