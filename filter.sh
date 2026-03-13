python embedding.py \
    --input all_data.json --output embeddings.npz \
    --workers 50 --batch-size 100

python cosine_similarity.py \
    --input embeddings.npz \
    --output cosine_sim.npz
