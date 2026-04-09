from engine import ContentBasedEngine, EngineConfig, Interaction, UserContext

config = EngineConfig(
    top_k=5,
    negative_lambda=0.3,
    attention_mix_alpha=0.5,
    fallback_strategy="mean",
)

engine = ContentBasedEngine.from_files(
    embedding_path="engine/embedding_matrix/embeddings.npy",
    id2idx_path="engine/embedding_matrix/id2idx.pkl",
    faiss_index_path="engine/faiss/products_hnsw.index",
    faiss_ids_path="engine/faiss/products_ids.pkl",
    attention_checkpoint_path="engine/attention_profile_model.pth",
    config=config,
)

user = UserContext(
    user_id="demo_user",
    interactions=[
        Interaction(item_id="B00000JBLQ", rating=5),
        Interaction(item_id="B00004S7P0", rating=5),
        Interaction(item_id="B00008VF1V", rating=2),
        Interaction(item_id="B00006IEI4", rating=3),
        Interaction(item_id="B00007L6C2", rating=3),
        Interaction(item_id="B00008Y2EK", rating=3),
    ],
)

for algo in ["weighted_avg", "negative_feedback", "attention"]:
    print(f"\n=== {algo} ===")
    recs = engine.recommend(user, algorithm=algo, top_k=5)
    for x in recs:
        print(x.rank, x.item_id, round(x.score, 4))
