python run_pipeline.py perception \
    -i atomic_captions3.json -o atomic_captions3_perception.json \
    --model-name gpt-5.4 \
    --thinking-effort medium \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 1000 \
    > atomic_captions3_perception.log 2>&1

python run_pipeline.py perception \
    -i atomic_captions3_perception.json -o atomic_captions3_perception.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort medium \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 1000 \
    >> atomic_captions3_perception.log 2>&1
