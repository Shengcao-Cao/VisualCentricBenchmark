#!/bin/bash
# Ablation experiments: text-only, text+caption, text+image+caption
# on original (T0) and pruned (T2) questions.
# 200-item subset of T2 problems.
# Models: GPT-5.4, Gemini 3.1 Pro, Qwen3.5-397B

set -e

INPUT=data/ablation_subset_200.json
PREFIX=data/ablation

# ──────────────────────────────────────────────────────────
# GPT-5.4
# ──────────────────────────────────────────────────────────

for MODE in text_only text_caption text_image_caption; do
    # T0 (original question)
    python run_pipeline.py answer_ablation \
        -i ${INPUT} -o ${PREFIX}_t0_${MODE}_gpt_5_4.json \
        --model-name gpt-5.4 \
        --ablation-mode ${MODE} \
        --thinking-effort high \
        --api-key $OPENAI_API_KEY \
        --concurrency 50 --save-interval 50 \
        --skip-existing \
        > logs/ablation_t0_${MODE}_gpt_5_4.log 2>&1

    # T2 (pruned question)
    python run_pipeline.py answer_tier2_ablation \
        -i ${INPUT} -o ${PREFIX}_t2_${MODE}_gpt_5_4.json \
        --model-name gpt-5.4 \
        --ablation-mode ${MODE} \
        --thinking-effort high \
        --api-key $OPENAI_API_KEY \
        --concurrency 50 --save-interval 50 \
        --skip-existing \
        > logs/ablation_t2_${MODE}_gpt_5_4.log 2>&1
done

# ──────────────────────────────────────────────────────────
# Gemini 3.1 Pro
# ──────────────────────────────────────────────────────────

for MODE in text_only text_caption text_image_caption; do
    python run_pipeline.py answer_ablation \
        -i ${INPUT} -o ${PREFIX}_t0_${MODE}_gemini_3_1_pro_preview.json \
        --model-name gemini-3.1-pro-preview \
        --ablation-mode ${MODE} \
        --thinking-effort high \
        --api-key $GOOGLE_API_KEY \
        --concurrency 50 --save-interval 50 \
        --skip-existing \
        > logs/ablation_t0_${MODE}_gemini_3_1_pro_preview.log 2>&1

    python run_pipeline.py answer_tier2_ablation \
        -i ${INPUT} -o ${PREFIX}_t2_${MODE}_gemini_3_1_pro_preview.json \
        --model-name gemini-3.1-pro-preview \
        --ablation-mode ${MODE} \
        --thinking-effort high \
        --api-key $GOOGLE_API_KEY \
        --concurrency 50 --save-interval 50 \
        --skip-existing \
        > logs/ablation_t2_${MODE}_gemini_3_1_pro_preview.log 2>&1
done

# ──────────────────────────────────────────────────────────
# Qwen3.5-397B (OpenRouter)
# ──────────────────────────────────────────────────────────

for MODE in text_only text_caption text_image_caption; do
    python run_pipeline.py answer_ablation \
        -i ${INPUT} -o ${PREFIX}_t0_${MODE}_open_router_qwen3_5_397b_a17b.json \
        --model-name qwen/qwen3.5-397b-a17b \
        --open-router \
        --ablation-mode ${MODE} \
        --thinking-effort high \
        --api-key $OPENROUTER_API_KEY \
        --concurrency 100 --save-interval 50 \
        --skip-existing \
        > logs/ablation_t0_${MODE}_open_router_qwen3_5_397b_a17b.log 2>&1

    python run_pipeline.py answer_tier2_ablation \
        -i ${INPUT} -o ${PREFIX}_t2_${MODE}_open_router_qwen3_5_397b_a17b.json \
        --model-name qwen/qwen3.5-397b-a17b \
        --open-router \
        --ablation-mode ${MODE} \
        --thinking-effort high \
        --api-key $OPENROUTER_API_KEY \
        --concurrency 100 --save-interval 50 \
        --skip-existing \
        > logs/ablation_t2_${MODE}_open_router_qwen3_5_397b_a17b.log 2>&1
done

# ──────────────────────────────────────────────────────────
# T2 Recovered question + original image (all 3 models)
# ──────────────────────────────────────────────────────────

python run_pipeline.py answer_tier2_recovered \
    -i ${INPUT} -o ${PREFIX}_t2_recovered_gpt_5_4.json \
    --model-name gpt-5.4 \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 50 \
    --skip-existing \
    > logs/ablation_t2_recovered_gpt_5_4.log 2>&1

python run_pipeline.py answer_tier2_recovered \
    -i ${INPUT} -o ${PREFIX}_t2_recovered_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 50 \
    --skip-existing \
    > logs/ablation_t2_recovered_gemini_3_1_pro_preview.log 2>&1

python run_pipeline.py answer_tier2_recovered \
    -i ${INPUT} -o ${PREFIX}_t2_recovered_open_router_qwen3_5_397b_a17b.json \
    --model-name qwen/qwen3.5-397b-a17b \
    --open-router \
    --thinking-effort high \
    --api-key $OPENROUTER_API_KEY \
    --concurrency 100 --save-interval 50 \
    --skip-existing \
    > logs/ablation_t2_recovered_open_router_qwen3_5_397b_a17b.log 2>&1

# ──────────────────────────────────────────────────────────
# Judging (all ablation outputs)
# ──────────────────────────────────────────────────────────

for MODEL_SLUG in gpt_5_4 gemini_3_1_pro_preview open_router_qwen3_5_397b_a17b; do
    if [ "$MODEL_SLUG" = "gpt_5_4" ]; then
        MODEL_NAME="gpt-5.4"
    elif [ "$MODEL_SLUG" = "gemini_3_1_pro_preview" ]; then
        MODEL_NAME="gemini-3.1-pro-preview"
    elif [ "$MODEL_SLUG" = "open_router_qwen3_5_397b_a17b" ]; then
        MODEL_NAME="qwen/qwen3.5-397b-a17b"
    fi

    for MODE in text_only text_caption text_image_caption; do
        # Judge T0
        python run_pipeline.py ablation_judge \
            -i ${PREFIX}_t0_${MODE}_${MODEL_SLUG}.json \
            -o ${PREFIX}_t0_${MODE}_${MODEL_SLUG}_judged.json \
            --model-name ${MODEL_NAME} \
            --judge-api-key $GOOGLE_API_KEY \
            --concurrency 100 --save-interval 100 \
            --skip-existing \
            > logs/ablation_t0_${MODE}_${MODEL_SLUG}_judged.log 2>&1

        # Judge T2
        python run_pipeline.py ablation_judge_tier2 \
            -i ${PREFIX}_t2_${MODE}_${MODEL_SLUG}.json \
            -o ${PREFIX}_t2_${MODE}_${MODEL_SLUG}_judged.json \
            --model-name ${MODEL_NAME} \
            --judge-api-key $GOOGLE_API_KEY \
            --concurrency 100 --save-interval 100 \
            --skip-existing \
            > logs/ablation_t2_${MODE}_${MODEL_SLUG}_judged.log 2>&1
    done

    # Judge T2 recovered
    python run_pipeline.py ablation_judge_tier2 \
        -i ${PREFIX}_t2_recovered_${MODEL_SLUG}.json \
        -o ${PREFIX}_t2_recovered_${MODEL_SLUG}_judged.json \
        --model-name ${MODEL_NAME} \
        --judge-api-key $GOOGLE_API_KEY \
        --concurrency 100 --save-interval 100 \
        --skip-existing \
        > logs/ablation_t2_recovered_${MODEL_SLUG}_judged.log 2>&1
done

echo "All ablation experiments complete."
