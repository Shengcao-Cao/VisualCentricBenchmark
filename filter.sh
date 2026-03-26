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
    --output filtered_data.json

python visualize.py \
    --input filtered_data.json \
    --output dist_filtered
