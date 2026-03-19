python merge.py
python validate_and_filter.py
python visualize.py all_data.json --output dist_all

python sample.py
python visualize.py sampled_1000.json --output dist_sampled_1000

python run_pipeline.py all \
    -i sampled_1000.json -o sampled_1000.json \
    --model-name gpt-5.4 \
    --api-key $OPENAI_API_KEY \
    --concurrency 50

python sample_100.py
python visualize.py sampled_100.json --output dist_sampled_100
