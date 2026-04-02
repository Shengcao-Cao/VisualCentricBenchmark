python run_pipeline.py prune \
    -i atomic_captions3.json -o atomic_captions3_prune.json \
    --model-name gpt-5.4 \
    --thinking-effort medium \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 1000 \
    > atomic_captions3_prune.log 2>&1

python run_pipeline.py prune \
    -i atomic_captions3_prune.json -o atomic_captions3_prune.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort medium \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 1000 \
    >> atomic_captions3_prune.log 2>&1
