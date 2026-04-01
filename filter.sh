# Stage 1: Use lightweight models with low thinking effort to filter out easy samples
python run_pipeline.py all \
    -i deduped_data.json -o deduped_data_gpt_5_nano.json \
    --model-name gpt-5-nano \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --skip-existing --save-interval 1000 \
    > deduped_data_gpt_5_nano.log 2>&1

python run_pipeline.py all \
    -i deduped_data.json -o deduped_data_gemini_3_1_flash_lite_preview.json \
    --model-name gemini-3.1-flash-lite-preview \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50 --skip-existing --save-interval 1000 \
    > deduped_data_gemini_3_1_flash_lite_preview.log 2>&1

python run_pipeline.py all \
    -i deduped_data.json -o deduped_data_claude_haiku_4_5.json \
    --model-name us.anthropic.claude-haiku-4-5-20251001-v1:0 \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 50 --skip-existing --save-interval 1000 \
    > deduped_data_claude_haiku_4_5.log 2>&1

python filter_easy.py \
    --input deduped_data_gpt_5_nano.json deduped_data_gemini_3_1_flash_lite_preview.json deduped_data_claude_haiku_4_5.json \
    --output filtered_data.json \
    --splits

python visualize.py \
    --input filtered_data.json \
    --output dist_filtered

python visualize.py \
    --input filtered_data_hard.json \
    --output dist_filtered_hard

# Deprecated: Too slow and expensive
# # Stage 2: Use intermediate models with medium thinking effort to further filter samples
# python run_pipeline.py filter \
#     -i filtered_data.json -o filtered_data_gpt_5_4_mini.json \
#     --model-name gpt-5.4-mini \
#     --thinking-effort medium \
#     --api-key $OPENAI_API_KEY \
#     --concurrency 50 --skip-existing --save-interval 1000 \
#     > filtered_data_gpt_5_4_mini.log 2>&1

# python run_pipeline.py filter \
#     -i filtered_data.json -o filtered_data_gemini_3_flash_preview.json \
#     --model-name gemini-3-flash-preview \
#     --thinking-effort medium \
#     --api-key $GOOGLE_API_KEY \
#     --concurrency 50 --skip-existing --save-interval 1000 \
#     > filtered_data_gemini_3_flash_preview.log 2>&1

# python run_pipeline.py filter \
#     -i filtered_data.json -o filtered_data_claude_sonnet_4_6.json \
#     --model-name us.anthropic.claude-sonnet-4-6 \
#     --thinking-effort medium \
#     --api-key $ANTHROPIC_API_KEY \
#     --region us-east-2 \
#     --concurrency 50 --skip-existing --save-interval 1000 \
#     > filtered_data_claude_sonnet_4_6.log 2>&1
