python embedding.py \
    --input all_data.json --output embeddings.npz \
    --workers 50 --batch-size 100

python cosine_similarity.py \
    --input embeddings.npz \
    --output cosine_sim.npz

python deduplicate.py \
    --input all_data.json \
    --embeddings cosine_sim.npz \
    --output deduped_data.json \
    --threshold 0.9
