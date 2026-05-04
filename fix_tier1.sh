python run_pipeline.py generate_tier1 \
    -i filtered_data_with_solution_hard_tier1_fixed.json -o filtered_data_with_solution_hard_tier1_fixed_output.json \
    --model-name gpt-5.4 \
    --thinking-effort none \
    --api-key $OPENAI_API_KEY \
    --concurrency 25 --save-interval 50 \
    --skip-existing \
    > filtered_data_with_solution_hard_tier1_fixed_output.log 2>&1

python fix_tier1.py -i filtered_data_with_solution_hard_tier1_fixed_output.json -o filtered_data_with_solution_hard_tier1_fixed.json
rm filtered_data_with_solution_hard_tier1_fixed_output.json

python run_pipeline.py reference_answer_tier1 \
    -i filtered_data_with_solution_hard_tier1_fixed.json -o filtered_data_with_solution_hard_tier1_fixed.json \
    --model-name gpt-5.4 \
    --thinking-effort none \
    --concurrency 25 --save-interval 50 \
    --skip-existing \
    > filtered_data_with_solution_hard_tier1_fixed_output.log 2>&1

python run_pipeline.py reference_answer_tier1 \
    -i filtered_data_with_solution_hard_tier1_fixed.json -o filtered_data_with_solution_hard_tier1_fixed.json \
    --model-name us.anthropic.claude-opus-4-6-v1 \
    --thinking-effort none \
    --concurrency 25 --save-interval 50 \
    --skip-existing \
    > filtered_data_with_solution_hard_tier1_fixed_output.log 2>&1

python run_pipeline.py reference_answer_tier1 \
    -i filtered_data_with_solution_hard_tier1_fixed.json -o filtered_data_with_solution_hard_tier1_fixed.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort low \
    --concurrency 25 --save-interval 50 \
    --skip-existing \
    > filtered_data_with_solution_hard_tier1_fixed_output.log 2>&1
