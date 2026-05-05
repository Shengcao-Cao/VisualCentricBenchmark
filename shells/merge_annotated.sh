python scripts/merge_annotated.py \
    -o data/merged_full.json

python run_pipeline.py trivial_tier2 \
    -i data/merged_full.json \
    -o data/merged_full_trivial.json \
    --model-name gemini-3.1-flash-lite-preview \
    --judge-model gemini-3.1-flash-lite-preview \
    --api-key $GOOGLE_API_KEY \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 25 \
    --save-interval 50 \
    --skip-existing
