INPUT=no_review_needed.json
PREFIX=no_review_needed_tier1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_gpt_5_4.json \
    --model-name gpt-5.4 \
    --thinking-effort none \
    --api-key $OPENAI_API_KEY \
    --concurrency 25 --save-interval 50 \
    --skip-existing \
    > ${PREFIX}_gpt_5_4.log 2>&1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_gpt_5_4_mini.json \
    --model-name gpt-5.4-mini \
    --thinking-effort none \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > ${PREFIX}_gpt_5_4_mini.log 2>&1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort none \
    --api-key $GOOGLE_API_KEY \
    --concurrency 100 --save-interval 100 \
    --skip-existing \
    > ${PREFIX}_gemini_3_1_pro_preview.log 2>&1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_gemini_3_1_flash_lite_preview.json \
    --model-name gemini-3.1-flash-lite-preview \
    --thinking-effort none \
    --api-key $GOOGLE_API_KEY \
    --concurrency 100 --save-interval 100 \
    --skip-existing \
    > ${PREFIX}_gemini_3_1_flash_lite_preview.log 2>&1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_gemma_4_31b.json \
    --model-name gemma-4-31b-it \
    --thinking-effort none \
    --api-key $GOOGLE_API_KEY \
    --concurrency 100 --save-interval 100 \
    --skip-existing \
    > ${PREFIX}_gemma_4_31b.log 2>&1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_claude_opus_4_6.json \
    --model-name us.anthropic.claude-opus-4-6-v1 \
    --thinking-effort none \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > ${PREFIX}_claude_opus_4_6.log 2>&1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_claude_sonnet_4_6.json \
    --model-name us.anthropic.claude-sonnet-4-6 \
    --thinking-effort none \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > ${PREFIX}_claude_sonnet_4_6.log 2>&1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_qwen3_vl_235b_a22b.json \
    --model-name qwen.qwen3-vl-235b-a22b \
    --api-key $AWS_BEARER_TOKEN_BEDROCK \
    --region us-east-2 \
    --max-tokens 8000 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > ${PREFIX}_qwen3_vl_235b_a22b.log 2>&1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_kimi_k2_5.json \
    --model-name moonshotai.kimi-k2.5 \
    --api-key $AWS_BEARER_TOKEN_BEDROCK \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > ${PREFIX}_kimi_k2_5.log 2>&1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_nova_2_lite.json \
    --model-name us.amazon.nova-2-lite-v1:0 \
    --api-key $AWS_BEARER_TOKEN_BEDROCK \
    --region us-east-2 \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > ${PREFIX}_nova_2_lite.log 2>&1

python run_pipeline.py answer_tier1 \
    -i $INPUT -o ${PREFIX}_open_router_qwen3_5_397b_a17b.json \
    --model-name qwen/qwen3.5-397b-a17b \
    --open-router \
    --api-key $OPENROUTER_API_KEY \
    --concurrency 20 --save-interval 20 \
    --skip-existing \
    > ${PREFIX}_open_router_qwen3_5_397b_a17b.log 2>&1
