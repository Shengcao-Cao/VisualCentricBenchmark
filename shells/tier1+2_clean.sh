PREFIX=data/filtered_data_with_solution_hard_tier1+2_clean

# ---- Tier 1: answer (no thinking needed) ----

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_gpt_5_4.json -o ${PREFIX}_tier1_gpt_5_4.json \
    --model-name gpt-5.4 \
    --thinking-effort none \
    --api-key $OPENAI_API_KEY \
    --concurrency 25 --save-interval 50 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_gpt_5_4.log 2>&1

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_gpt_5_4_mini.json -o ${PREFIX}_tier1_gpt_5_4_mini.json \
    --model-name gpt-5.4-mini \
    --thinking-effort none \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_gpt_5_4_mini.log 2>&1

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_gemini_3_1_pro_preview.json -o ${PREFIX}_tier1_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort low \
    --api-key $GOOGLE_API_KEY \
    --concurrency 100 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_gemini_3_1_pro_preview.log 2>&1

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_gemini_3_1_flash_lite_preview.json -o ${PREFIX}_tier1_gemini_3_1_flash_lite_preview.json \
    --model-name gemini-3.1-flash-lite-preview \
    --thinking-effort none \
    --api-key $GOOGLE_API_KEY \
    --concurrency 100 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_gemini_3_1_flash_lite_preview.log 2>&1

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_gemma_4_31b.json -o ${PREFIX}_tier1_gemma_4_31b.json \
    --model-name gemma-4-31b-it \
    --thinking-effort none \
    --api-key $GOOGLE_API_KEY \
    --concurrency 10 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_gemma_4_31b.log 2>&1

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_claude_opus_4_6.json -o ${PREFIX}_tier1_claude_opus_4_6.json \
    --model-name us.anthropic.claude-opus-4-6-v1 \
    --thinking-effort none \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_claude_opus_4_6.log 2>&1

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_claude_sonnet_4_6.json -o ${PREFIX}_tier1_claude_sonnet_4_6.json \
    --model-name us.anthropic.claude-sonnet-4-6 \
    --thinking-effort none \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_claude_sonnet_4_6.log 2>&1

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_qwen3_vl_235b_a22b.json -o ${PREFIX}_tier1_qwen3_vl_235b_a22b.json \
    --model-name qwen.qwen3-vl-235b-a22b \
    --thinking-effort none \
    --api-key $AWS_BEARER_TOKEN_BEDROCK \
    --region us-east-2 \
    --max-tokens 8000 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_qwen3_vl_235b_a22b.log 2>&1

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_kimi_k2_5.json -o ${PREFIX}_tier1_kimi_k2_5.json \
    --model-name moonshotai.kimi-k2.5 \
    --thinking-effort none \
    --api-key $AWS_BEARER_TOKEN_BEDROCK \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_kimi_k2_5.log 2>&1

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_nova_2_lite.json -o ${PREFIX}_tier1_nova_2_lite.json \
    --model-name us.amazon.nova-2-lite-v1:0 \
    --thinking-effort none \
    --api-key $AWS_BEARER_TOKEN_BEDROCK \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_nova_2_lite.log 2>&1

python run_pipeline.py answer_tier1 \
    -i ${PREFIX}_tier1_open_router_qwen3_5_397b_a17b.json -o ${PREFIX}_tier1_open_router_qwen3_5_397b_a17b.json \
    --model-name qwen/qwen3.5-397b-a17b \
    --thinking-effort none \
    --open-router \
    --api-key $OPENROUTER_API_KEY \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier1_open_router_qwen3_5_397b_a17b.log 2>&1

# ---- Tier 2: answer (thinking needed) ----

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_gpt_5_4.json -o ${PREFIX}_tier2_gpt_5_4.json \
    --model-name gpt-5.4 \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 25 --save-interval 50 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_gpt_5_4.log 2>&1

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_gpt_5_4_mini.json -o ${PREFIX}_tier2_gpt_5_4_mini.json \
    --model-name gpt-5.4-mini \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_gpt_5_4_mini.log 2>&1

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_gemini_3_1_pro_preview.json -o ${PREFIX}_tier2_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_gemini_3_1_pro_preview.log 2>&1

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_gemini_3_1_flash_lite_preview.json -o ${PREFIX}_tier2_gemini_3_1_flash_lite_preview.json \
    --model-name gemini-3.1-flash-lite-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_gemini_3_1_flash_lite_preview.log 2>&1

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_gemma_4_31b.json -o ${PREFIX}_tier2_gemma_4_31b.json \
    --model-name gemma-4-31b-it \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_gemma_4_31b.log 2>&1

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_claude_opus_4_6.json -o ${PREFIX}_tier2_claude_opus_4_6.json \
    --model-name us.anthropic.claude-opus-4-6-v1 \
    --thinking-effort high \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_claude_opus_4_6.log 2>&1

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_claude_sonnet_4_6.json -o ${PREFIX}_tier2_claude_sonnet_4_6.json \
    --model-name us.anthropic.claude-sonnet-4-6 \
    --thinking-effort high \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_claude_sonnet_4_6.log 2>&1

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_qwen3_vl_235b_a22b.json -o ${PREFIX}_tier2_qwen3_vl_235b_a22b.json \
    --model-name qwen.qwen3-vl-235b-a22b \
    --api-key $AWS_BEARER_TOKEN_BEDROCK \
    --region us-east-2 \
    --max-tokens 8000 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_qwen3_vl_235b_a22b.log 2>&1

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_kimi_k2_5.json -o ${PREFIX}_tier2_kimi_k2_5.json \
    --model-name moonshotai.kimi-k2.5 \
    --api-key $AWS_BEARER_TOKEN_BEDROCK \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_kimi_k2_5.log 2>&1

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_nova_2_lite.json -o ${PREFIX}_tier2_nova_2_lite.json \
    --model-name us.amazon.nova-2-lite-v1:0 \
    --api-key $AWS_BEARER_TOKEN_BEDROCK \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_nova_2_lite.log 2>&1

python run_pipeline.py answer_tier2 \
    -i ${PREFIX}_tier2_open_router_qwen3_5_397b_a17b.json -o ${PREFIX}_tier2_open_router_qwen3_5_397b_a17b.json \
    --model-name qwen/qwen3.5-397b-a17b \
    --open-router \
    --api-key $OPENROUTER_API_KEY \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_open_router_qwen3_5_397b_a17b.log 2>&1

# ---- Tier 2: judge all model answers ----

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_gpt_5_4.json -o ${PREFIX}_tier2_gpt_5_4_judged.json \
    --model-name gpt-5.4 \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_gpt_5_4_judged.log 2>&1

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_gpt_5_4_mini.json -o ${PREFIX}_tier2_gpt_5_4_mini_judged.json \
    --model-name gpt-5.4-mini \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_gpt_5_4_mini_judged.log 2>&1

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_gemini_3_1_pro_preview.json -o ${PREFIX}_tier2_gemini_3_1_pro_preview_judged.json \
    --model-name gemini-3.1-pro-preview \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_gemini_3_1_pro_preview_judged.log 2>&1

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_gemini_3_1_flash_lite_preview.json -o ${PREFIX}_tier2_gemini_3_1_flash_lite_preview_judged.json \
    --model-name gemini-3.1-flash-lite-preview \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_gemini_3_1_flash_lite_preview_judged.log 2>&1

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_gemma_4_31b.json -o ${PREFIX}_tier2_gemma_4_31b_judged.json \
    --model-name gemma-4-31b-it \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_gemma_4_31b_judged.log 2>&1

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_claude_opus_4_6.json -o ${PREFIX}_tier2_claude_opus_4_6_judged.json \
    --model-name us.anthropic.claude-opus-4-6-v1 \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_claude_opus_4_6_judged.log 2>&1

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_claude_sonnet_4_6.json -o ${PREFIX}_tier2_claude_sonnet_4_6_judged.json \
    --model-name us.anthropic.claude-sonnet-4-6 \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_claude_sonnet_4_6_judged.log 2>&1

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_qwen3_vl_235b_a22b.json -o ${PREFIX}_tier2_qwen3_vl_235b_a22b_judged.json \
    --model-name qwen.qwen3-vl-235b-a22b \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_qwen3_vl_235b_a22b_judged.log 2>&1

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_kimi_k2_5.json -o ${PREFIX}_tier2_kimi_k2_5_judged.json \
    --model-name moonshotai.kimi-k2.5 \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_kimi_k2_5_judged.log 2>&1

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_nova_2_lite.json -o ${PREFIX}_tier2_nova_2_lite_judged.json \
    --model-name us.amazon.nova-2-lite-v1:0 \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_nova_2_lite_judged.log 2>&1

python run_pipeline.py better_judge_tier2 \
    -i ${PREFIX}_tier2_open_router_qwen3_5_397b_a17b.json -o ${PREFIX}_tier2_open_router_qwen3_5_397b_a17b_judged.json \
    --model-name "qwen/qwen3.5-397b-a17b" \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > logs/tier1+2_clean_tier2_open_router_qwen3_5_397b_a17b_judged.log 2>&1
