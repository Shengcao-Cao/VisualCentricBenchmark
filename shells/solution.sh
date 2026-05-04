# Try to get solutions from original dataset and model responses
python coreset/build_solution.py

python run_pipeline.py answer \
    -i data/filtered_data_without_solution.json -o filtered_data_without_solution_gpt_5_4.json \
    --model-name gpt-5.4 \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 100 \
    > filtered_data_without_solution_gpt_5_4.log 2>&1

python run_pipeline.py judge \
    -i filtered_data_without_solution_gpt_5_4.json -o filtered_data_without_solution_gpt_5_4.json \
    --model-name gpt-5.4 \
    --thinking-effort high \
    --api-key $OPENAI_API_KEY \
    --concurrency 50 --save-interval 100 \
    > filtered_data_without_solution_gpt_5_4.log 2>&1

python run_pipeline.py answer \
    -i data/filtered_data_without_solution.json -o filtered_data_without_solution_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    > filtered_data_without_solution_gemini_3_1_pro_preview.log 2>&1

python run_pipeline.py judge \
    -i filtered_data_without_solution_gemini_3_1_pro_preview.json -o filtered_data_without_solution_gemini_3_1_pro_preview.json \
    --model-name gemini-3.1-pro-preview \
    --thinking-effort high \
    --api-key $GOOGLE_API_KEY \
    --concurrency 50 --save-interval 100 \
    > filtered_data_without_solution_gemini_3_1_pro_preview.log 2>&1

python coreset/merge_solutions.py \
    coreset/filtered_data_without_solution_gpt_5_4.json:gpt-5.4 \
    coreset/filtered_data_without_solution_gemini_3_1_pro_preview.json:gemini-3.1-pro-preview
