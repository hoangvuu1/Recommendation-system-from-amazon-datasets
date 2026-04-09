# content_based_engine

Bản tối giản hơn, bám sát notebook hơn.

## Có gì bên trong
- load `embeddings.npy` + `id2idx.pkl`
- load FAISS/HNSW index + ids
- retrieval top-k
- 3 thuật toán:
  - weighted average
  - negative feedback
  - attention
- fallback profile khi user không có history usable
- rule nhỏ:
  - nếu positive quá ít nhưng có nhiều item 3 sao, ép 3 sao thành positive

## File
- `config.py`: cấu hình chung
- `schemas.py`: input / output
- `stores.py`: load embedding + FAISS vector DB
- `models.py`: attention model
- `profiles.py`: logic build profile cho 3 thuật toán
- `engine.py`: class chính để backend gọi
- `utils.py`: normalize + format output

## Quick start
```python
from engine import ContentBasedEngine, EngineConfig, Interaction, UserContext

config = EngineConfig(
    top_k=20,
    negative_lambda=0.3,
    attention_mix_alpha=0.5,
    fallback_strategy="mean",
)

engine = ContentBasedEngine.from_files(
    embedding_path="embeddings.npy",
    id2idx_path="id2idx.pkl",
    faiss_index_path="products_hnsw.index",
    faiss_ids_path="products_ids.pkl",
    attention_checkpoint_path="attention_profile_model.pth",
    config=config,
)

user = UserContext(
    user_id="u1",
    interactions=[
        Interaction(item_id="B00000JBLQ", rating=5),
        Interaction(item_id="B00004S7P0", rating=5),
        Interaction(item_id="B00008VF1V", rating=2),
        Interaction(item_id="B00006IEI4", rating=3),
        Interaction(item_id="B00007L6C2", rating=3),
        Interaction(item_id="B00008Y2EK", rating=3),
    ],
)

recs = engine.recommend(user, algorithm="attention", top_k=10)
for x in recs:
    print(x.rank, x.item_id, round(x.score, 4))
```
