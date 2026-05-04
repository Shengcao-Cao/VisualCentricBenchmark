python run_pipeline.py trivial_tier2 \
    -i no_review_needed.json \
    -o no_review_needed_trivial.json \
    --model-name gemini-3.1-flash-lite-preview \
    --judge-model gemini-3.1-flash-lite-preview \
    --api-key $GOOGLE_API_KEY \
    --judge-api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    --skip-existing \
    > no_review_needed_trivial.log 2>&1

python filter_trivial_tier2.py \
    -i no_review_needed_trivial.json \
    -o no_review_needed_substantive.json
