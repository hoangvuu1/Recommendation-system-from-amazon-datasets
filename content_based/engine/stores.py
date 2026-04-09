from __future__ import annotations

from pathlib import Path
import pickle

import faiss
import numpy as np


class EmbeddingStore:
    def __init__(self, emb_matrix: np.ndarray, id2idx: dict[str, int]) -> None:
        self.emb_matrix = emb_matrix
        self.id2idx = id2idx
        self._ids = [None] * len(id2idx)
        for item_id, idx in id2idx.items():
            self._ids[idx] = item_id

    @classmethod
    def from_files(cls, embedding_path: str | Path, id2idx_path: str | Path, mmap_mode: str | None = "r") -> "EmbeddingStore":
        emb_matrix = np.load(embedding_path, mmap_mode=mmap_mode)
        with open(id2idx_path, "rb") as f:
            id2idx = pickle.load(f)
        return cls(emb_matrix=emb_matrix, id2idx=id2idx)

    @property
    def dim(self) -> int:
        return int(self.emb_matrix.shape[1])

    @property
    def item_ids(self) -> list[str]:
        return self._ids

    def has(self, item_id: str) -> bool:
        return item_id in self.id2idx

    def get_index(self, item_id: str) -> int:
        return self.id2idx[item_id]

    def get_vector(self, item_id: str) -> np.ndarray:
        return np.asarray(self.emb_matrix[self.id2idx[item_id]], dtype=np.float32)

    def get_vectors(self, item_ids: list[str]) -> tuple[list[str], np.ndarray]:
        kept_ids = [x for x in item_ids if x in self.id2idx]
        if not kept_ids:
            return [], np.empty((0, self.dim), dtype=np.float32)
        idxs = [self.id2idx[x] for x in kept_ids]
        vecs = np.asarray(self.emb_matrix[idxs], dtype=np.float32)
        return kept_ids, vecs


class FaissVectorStore:
    def __init__(self, index: faiss.Index, ids: list[str]) -> None:
        self.index = index
        self.ids = ids

    @classmethod
    def from_files(cls, index_path: str | Path, ids_path: str | Path) -> "FaissVectorStore":
        index = faiss.read_index(str(index_path))
        with open(ids_path, "rb") as f:
            ids = pickle.load(f)
        return cls(index=index, ids=ids)

    def search(self, query_vector: np.ndarray, top_k: int = 100, exclude_ids: set[str] | None = None) -> list[tuple[str, float]]:
        xq = np.asarray(query_vector, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(xq)
        scores, idx = self.index.search(xq, top_k + (len(exclude_ids) if exclude_ids else 0) + 20)

        results: list[tuple[str, float]] = []
        exclude_ids = exclude_ids or set()

        for score, i in zip(scores[0], idx[0]):
            if i == -1:
                continue
            item_id = self.ids[i]
            if item_id in exclude_ids:
                continue
            results.append((item_id, float(score)))
            if len(results) >= top_k:
                break
        return results
