python filter_needs_review_split.py \
    --tier1 filtered_data_with_solution_hard_tier1_fixed.json \
    --tier2 filtered_data_with_solution_hard_tier2_fixed.json \
    -n 5 \
    -o needs_review_shard \
    --clean-output no_review_needed.json
