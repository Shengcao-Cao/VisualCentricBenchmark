python run_pipeline.py all \
    -i sampled_1000.json -o sampled_1000_gpt_5_nano.json \
    --model-name gpt-5-nano \
    --api-key $OPENAI_API_KEY \
    --concurrency 50

python run_pipeline.py all \
    -i sampled_1000.json -o sampled_1000_gemini_3_1_flash_lite_preview.json \
    --model-name gemini-3.1-flash-lite-preview \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50

python run_pipeline.py all \
    -i sampled_1000.json -o sampled_1000_claude_haiku_4_5.json \
    --model-name us.anthropic.claude-haiku-4-5-20251001-v1:0 \
    --api-key $ANTHROPIC_API_KEY \
    --region us-east-2 \
    --concurrency 50
