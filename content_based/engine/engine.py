from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from .config import EngineConfig
from .models import AttentionProfile
from .profiles import attention_profile, negative_feedback_profile, weighted_average_profile
from .schemas import RecommendationResult, UserContext
from .stores import EmbeddingStore, FaissVectorStore
from .utils import to_results


class ContentBasedEngine:
    """
    Single entry point for:
      - weighted_avg
      - negative_feedback
      - attention
    It includes:
      - embedding loading
      - FAISS retrieval
      - fallback profile
      - 3-star promotion rule
    """

    def __init__(
        self,
        embedding_store: EmbeddingStore,
        vector_store: FaissVectorStore,
        config: EngineConfig,
        attention_checkpoint_path: str | None = None,
        attention_hidden_dim: int = 128,
        device: str | None = None,
    ) -> None:
        self.embedding_store = embedding_store
        self.vector_store = vector_store
        self.config = config
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.attention_model = None
        if attention_checkpoint_path is not None:
            emb_tensor = torch.tensor(np.asarray(embedding_store.emb_matrix, dtype=np.float32), dtype=torch.float32)
            model = AttentionProfile(
                emb_matrix=emb_tensor,
                hidden_dim=attention_hidden_dim,
                mix_alpha=config.attention_mix_alpha,
            ).to(self.device)
            state = torch.load(attention_checkpoint_path, map_location=self.device)
            model.load_state_dict(state)
            model.eval()
            self.attention_model = model

    @classmethod
    def from_files(
        cls,
        embedding_path: str,
        id2idx_path: str,
        faiss_index_path: str,
        faiss_ids_path: str,
        config: EngineConfig,
        attention_checkpoint_path: str | None = None,
        attention_hidden_dim: int = 128,
        device: str | None = None,
    ) -> "ContentBasedEngine":
        embedding_store = EmbeddingStore.from_files(embedding_path, id2idx_path)
        vector_store = FaissVectorStore.from_files(faiss_index_path, faiss_ids_path)
        return cls(
            embedding_store=embedding_store,
            vector_store=vector_store,
            config=config,
            attention_checkpoint_path=attention_checkpoint_path,
            attention_hidden_dim=attention_hidden_dim,
            device=device,
        )

    def build_profile(self, context: UserContext, algorithm: str) -> np.ndarray:
        if algorithm == "weighted_avg":
            return weighted_average_profile(context, self.embedding_store, self.config)

        if algorithm == "negative_feedback":
            return negative_feedback_profile(context, self.embedding_store, self.config)

        if algorithm == "attention":
            if self.attention_model is None:
                raise ValueError("attention_checkpoint_path is required for algorithm='attention'")
            return attention_profile(
                context=context,
                embedding_store=self.embedding_store,
                model=self.attention_model,
                device=self.device,
                config=self.config,
            )

        raise ValueError(f"Unknown algorithm: {algorithm}")

    def recommend(self, context: UserContext, algorithm: str = "weighted_avg", top_k: int | None = None) -> list[RecommendationResult]:
        profile = self.build_profile(context, algorithm=algorithm)
        top_k = top_k or self.config.top_k

        exclude_ids = set()
        if self.config.exclude_history_items:
            exclude_ids = {x.item_id for x in context.interactions}

        pairs = self.vector_store.search(query_vector=profile, top_k=top_k, exclude_ids=exclude_ids)
        return to_results(pairs)

    def inspect_attention(self, context: UserContext) -> list[tuple[str, float]]:
        if self.attention_model is None:
            raise ValueError("attention model is not loaded")

        usable = [x for x in context.interactions if self.embedding_store.has(x.item_id)]
        usable = usable[-self.config.max_context:]
        if len(usable) == 0:
            return []

        idxs = [self.embedding_store.get_index(x.item_id) for x in usable]
        hist_idx = torch.tensor([idxs], dtype=torch.long, device=self.device)
        mask = torch.ones_like(hist_idx, dtype=torch.bool, device=self.device)

        with torch.no_grad():
            _, attn = self.attention_model(hist_idx, mask)

        weights = attn[0].detach().cpu().numpy().tolist()
        return [(x.item_id, float(w)) for x, w in zip(usable, weights)]
