python run_pipeline.py answer \
    -i filtered_data_with_solution_hard.json -o filtered_data_with_solution_hard_gpt_5_4.json \
    --model-name gpt-5.4 \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 25 --save-interval 50 \
    --skip-existing \
    > filtered_data_with_solution_hard_gpt_5_4.log 2>&1

python run_pipeline.py judge \
    -i filtered_data_with_solution_hard_gpt_5_4.json -o filtered_data_with_solution_hard_gpt_5_4.json \
    --model-name gpt-5.4 \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 25 --save-interval 50 \
    >> filtered_data_with_solution_hard_gpt_5_4.log 2>&1

python run_pipeline.py answer \
    -i filtered_data_with_solution_hard.json -o filtered_data_with_solution_hard_gpt_5_4_mini.json \
    --model-name gpt-5.4-mini \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > filtered_data_with_solution_hard_gpt_5_4_mini.log 2>&1

python run_pipeline.py judge \
    -i filtered_data_with_solution_hard_gpt_5_4_mini.json -o filtered_data_with_solution_hard_gpt_5_4_mini.json \
    --model-name gpt-5.4-mini \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 100 \
    >> filtered_data_with_solution_hard_gpt_5_4_mini.log 2>&1

python run_pipeline.py answer \
    -i filtered_data_with_solution_hard.json -o filtered_data_with_solution_hard_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 100 --save-interval 100 \
    --skip-existing \
    > filtered_data_with_solution_hard_gemini_3_1_pro_preview.log 2>&1

python run_pipeline.py judge \
    -i filtered_data_with_solution_hard_gemini_3_1_pro_preview.json -o filtered_data_with_solution_hard_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 100 --save-interval 100 \
    >> filtered_data_with_solution_hard_gemini_3_1_pro_preview.log 2>&1

python run_pipeline.py answer \
    -i filtered_data_with_solution_hard.json -o filtered_data_with_solution_hard_gemini_3_1_flash_lite_preview.json \
    --model-name gemini-3.1-flash-lite-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 100 --save-interval 100 \
    --skip-existing \
    > filtered_data_with_solution_hard_gemini_3_1_flash_lite_preview.log 2>&1

python run_pipeline.py judge \
    -i filtered_data_with_solution_hard_gemini_3_1_flash_lite_preview.json -o filtered_data_with_solution_hard_gemini_3_1_flash_lite_preview.json \
    --model-name gemini-3.1-flash-lite-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 100 --save-interval 100 \
    >> filtered_data_with_solution_hard_gemini_3_1_flash_lite_preview.log 2>&1

# Opus 4.6 is too slow
# python run_pipeline.py answer \
#     -i filtered_data_with_solution_hard.json -o filtered_data_with_solution_hard_claude_opus_4_6.json \
#     --model-name us.anthropic.claude-opus-4-6-v1 \
#     --thinking-effort high \
#     --api-key $ANTHROPIC_API_KEY \
#     --region us-east-2 \
#     --concurrency 100 --save-interval 100 \
#     --skip-existing \
#     --max-tokens 128000 \
#     > filtered_data_with_solution_hard_claude_opus_4_6.log 2>&1

# python run_pipeline.py judge \
#     -i filtered_data_with_solution_hard_claude_opus_4_6.json -o filtered_data_with_solution_hard_claude_opus_4_6.json \
#     --model-name us.anthropic.claude-opus-4-6-v1 \
#     --thinking-effort high \
#     --api-key $ANTHROPIC_API_KEY \
#     --region us-east-2 \
#     --concurrency 100 --save-interval 100 \
#     >> filtered_data_with_solution_hard_claude_opus_4_6.log 2>&1

python run_pipeline.py answer \
    -i filtered_data_with_solution_hard.json -o filtered_data_with_solution_hard_claude_sonnet_4_6.json \
    --model-name us.anthropic.claude-sonnet-4-6 \
    --thinking-effort high \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 10 --save-interval 20 \
    --skip-existing \
    > filtered_data_with_solution_hard_claude_sonnet_4_6.log 2>&1

python run_pipeline.py judge \
    -i filtered_data_with_solution_hard_claude_sonnet_4_6.json -o filtered_data_with_solution_hard_claude_sonnet_4_6.json \
    --model-name us.anthropic.claude-sonnet-4-6 \
    --thinking-effort high \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 10 --save-interval 20 \
    >> filtered_data_with_solution_hard_claude_sonnet_4_6.log 2>&1
