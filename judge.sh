# Re-judge all model answers using gemini-3.1-flash-lite-preview as the dedicated judge.
# Uses better_judge task: extracts final answer, robust JSON parsing, retries on parse failure.
# Results saved to new files (*_judged.json) to preserve original judge results.

# GPT-5.4
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_gpt_5_4.json -o filtered_data_with_solution_hard_gpt_5_4_judged.json \
    --model-name gpt-5.4 \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_gpt_5_4_judged.log 2>&1

# GPT-5.4 Mini
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_gpt_5_4_mini.json -o filtered_data_with_solution_hard_gpt_5_4_mini_judged.json \
    --model-name gpt-5.4-mini \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_gpt_5_4_mini_judged.log 2>&1

# Gemini 3.1 Pro Preview
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_gemini_3_1_pro_preview.json -o filtered_data_with_solution_hard_gemini_3_1_pro_preview_judged.json \
    --model-name gemini-3.1-pro-preview \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_gemini_3_1_pro_preview_judged.log 2>&1

# Gemini 3.1 Flash Lite Preview
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_gemini_3_1_flash_lite_preview.json -o filtered_data_with_solution_hard_gemini_3_1_flash_lite_preview_judged.json \
    --model-name gemini-3.1-flash-lite-preview \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_gemini_3_1_flash_lite_preview_judged.log 2>&1

# Gemma 4 31B
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_gemma_4_31b.json -o filtered_data_with_solution_hard_gemma_4_31b_judged.json \
    --model-name gemma-4-31b-it \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_gemma_4_31b_judged.log 2>&1

# Claude Opus 4.6
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_claude_opus_4_6.json -o filtered_data_with_solution_hard_claude_opus_4_6_judged.json \
    --model-name us.anthropic.claude-opus-4-6-v1 \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_claude_opus_4_6_judged.log 2>&1

# Claude Sonnet 4.6
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_claude_sonnet_4_6.json -o filtered_data_with_solution_hard_claude_sonnet_4_6_judged.json \
    --model-name us.anthropic.claude-sonnet-4-6 \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_claude_sonnet_4_6_judged.log 2>&1

# Qwen3 VL 235B (Bedrock)
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_qwen3_vl_235b_a22b.json -o filtered_data_with_solution_hard_qwen3_vl_235b_a22b_judged.json \
    --model-name qwen.qwen3-vl-235b-a22b \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_qwen3_vl_235b_a22b_judged.log 2>&1

# Kimi K2.5
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_kimi_k2_5.json -o filtered_data_with_solution_hard_kimi_k2_5_judged.json \
    --model-name moonshotai.kimi-k2.5 \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_kimi_k2_5_judged.log 2>&1

# Nova 2 Lite
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_nova_2_lite.json -o filtered_data_with_solution_hard_nova_2_lite_judged.json \
    --model-name us.amazon.nova-2-lite-v1:0 \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_nova_2_lite_judged.log 2>&1

# Qwen3.5 397B (OpenRouter)
python run_pipeline.py better_judge \
    -i filtered_data_with_solution_hard_open_router_qwen3_5_397b_a17b.json -o filtered_data_with_solution_hard_open_router_qwen3_5_397b_a17b_judged.json \
    --model-name "qwen/qwen3.5-397b-a17b" \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_open_router_qwen3_5_397b_a17b_judged.log 2>&1
