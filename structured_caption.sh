python run_pipeline.py structured \
    -i playground/data/sampled_100.json -o playground/saves/structured/sampled_100.json \
    --model-name gpt-5.4 \
    --api-key $OPENAI_API_KEY \
    --concurrency 32
