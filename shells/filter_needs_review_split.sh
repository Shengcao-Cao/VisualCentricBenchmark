python filter_needs_review_split.py \
    --tier1 data/filtered_data_with_solution_hard_tier1_fixed.json \
    --tier2 data/filtered_data_with_solution_hard_tier2_fixed.json \
    -n 5 \
    -o data/needs_review_shard \
    --clean-output data/no_review_needed.json
