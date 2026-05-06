#!/bin/bash
# Image quality effect: original question text + reproduced (tier3) image
# on the 144-item equivalent-image subset.
# All 10 models (excluding Nova 2 Lite).

set -e

INPUT=data/image_quality_equiv_subset.json
PREFIX=data/image_quality

# ── Inference ──

python run_pipeline.py answer_image_quality \
    -i ${INPUT} -o ${PREFIX}_gpt_5_4.json \
    --model-name gpt-5.4 \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 25 --save-interval 50 \
    --skip-existing \
    > logs/image_quality_gpt_5_4.log 2>&1

python run_pipeline.py answer_image_quality \
    -i ${INPUT} -o ${PREFIX}_gpt_5_4_mini.json \
    --model-name gpt-5.4-mini \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 50 \
    --skip-existing \
    > logs/image_quality_gpt_5_4_mini.log 2>&1

python run_pipeline.py answer_image_quality \
    -i ${INPUT} -o ${PREFIX}_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 50 \
    --skip-existing \
    > logs/image_quality_gemini_3_1_pro_preview.log 2>&1

python run_pipeline.py answer_image_quality \
    -i ${INPUT} -o ${PREFIX}_gemini_3_1_flash_lite_preview.json \
    --model-name gemini-3.1-flash-lite-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 50 \
    --skip-existing \
    > logs/image_quality_gemini_3_1_flash_lite_preview.log 2>&1

python run_pipeline.py answer_image_quality \
    -i ${INPUT} -o ${PREFIX}_gemma_4_31b.json \
    --model-name gemma-4-31b-it \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 10 --save-interval 20 \
    --skip-existing \
    > logs/image_quality_gemma_4_31b.log 2>&1

python run_pipeline.py answer_image_quality \
    -i ${INPUT} -o ${PREFIX}_claude_opus_4_6.json \
    --model-name us.anthropic.claude-opus-4-6-v1 \
    --thinking-effort high \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/image_quality_claude_opus_4_6.log 2>&1

python run_pipeline.py answer_image_quality \
    -i ${INPUT} -o ${PREFIX}_claude_sonnet_4_6.json \
    --model-name us.anthropic.claude-sonnet-4-6 \
    --thinking-effort high \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/image_quality_claude_sonnet_4_6.log 2>&1

python run_pipeline.py answer_image_quality \
    -i ${INPUT} -o ${PREFIX}_qwen3_vl_235b_a22b.json \
    --model-name qwen.qwen3-vl-235b-a22b \
    --thinking-effort high \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/image_quality_qwen3_vl_235b_a22b.log 2>&1

python run_pipeline.py answer_image_quality \
    -i ${INPUT} -o ${PREFIX}_kimi_k2_5.json \
    --model-name moonshotai.kimi-k2.5 \
    --thinking-effort high \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/image_quality_kimi_k2_5.log 2>&1

python run_pipeline.py answer_image_quality \
    -i ${INPUT} -o ${PREFIX}_open_router_qwen3_5_397b_a17b.json \
    --model-name qwen/qwen3.5-397b-a17b \
    --open-router \
    --thinking-effort high \
    --api-key $OPENROUTER_API_KEY \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/image_quality_open_router_qwen3_5_397b_a17b.log 2>&1

# ── Judging ──

for MODEL_SLUG in gpt_5_4 gpt_5_4_mini gemini_3_1_pro_preview gemini_3_1_flash_lite_preview gemma_4_31b claude_opus_4_6 claude_sonnet_4_6 qwen3_vl_235b_a22b kimi_k2_5 open_router_qwen3_5_397b_a17b; do
    case $MODEL_SLUG in
        gpt_5_4)             MODEL_NAME="gpt-5.4" ;;
        gpt_5_4_mini)        MODEL_NAME="gpt-5.4-mini" ;;
        gemini_3_1_pro_preview)    MODEL_NAME="gemini-3.1-pro-preview" ;;
        gemini_3_1_flash_lite_preview) MODEL_NAME="gemini-3.1-flash-lite-preview" ;;
        gemma_4_31b)         MODEL_NAME="gemma-4-31b-it" ;;
        claude_opus_4_6)     MODEL_NAME="us.anthropic.claude-opus-4-6-v1" ;;
        claude_sonnet_4_6)   MODEL_NAME="us.anthropic.claude-sonnet-4-6" ;;
        qwen3_vl_235b_a22b)  MODEL_NAME="qwen.qwen3-vl-235b-a22b" ;;
        kimi_k2_5)           MODEL_NAME="moonshotai.kimi-k2.5" ;;
        open_router_qwen3_5_397b_a17b) MODEL_NAME="qwen/qwen3.5-397b-a17b" ;;
    esac

    python run_pipeline.py better_judge \
        -i ${PREFIX}_${MODEL_SLUG}.json \
        -o ${PREFIX}_${MODEL_SLUG}_judged.json \
        --model-name ${MODEL_NAME} \
        --judge-api-key $GOOGLE_API_KEY \
        --concurrency 50 --save-interval 50 \
        --skip-existing \
        > logs/image_quality_${MODEL_SLUG}_judged.log 2>&1
done

echo "Image quality experiments complete."
