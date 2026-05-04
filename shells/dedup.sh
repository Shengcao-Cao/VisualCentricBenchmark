python embedding.py \
    --input data/all_data.json --output embeddings.npz \
    --workers 50 --batch-size 100

python cosine_similarity.py \
    --input embeddings.npz \
    --output cosine_sim.npz

python deduplicate.py \
    --input data/all_data.json \
    --embeddings cosine_sim.npz \
    --output data/deduped_data.json \
    --threshold 0.9
