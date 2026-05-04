python fix_tier3_jpg.py \
    -i filtered_data_with_solution_hard_tier3.json \
    -o filtered_data_with_solution_hard_tier3_fixed_jpg.json \
    --hard filtered_data_with_solution_hard.json

python fix_tier3_jpg_pruned.py \
    -i filtered_data_with_solution_hard_tier3_jpg_pruned.json \
    -o filtered_data_with_solution_hard_tier3_jpg_pruned_fixed.json \
    --hard filtered_data_with_solution_hard.json \
    --tier3-fixed filtered_data_with_solution_hard_tier3_fixed_jpg.json \
    -n 5 --seed 42
