from __future__ import annotations

import numpy as np

from .schemas import RecommendationResult


def l2_normalize(vec: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    return vec / (np.linalg.norm(vec) + eps)


def to_results(pairs: list[tuple[str, float]]) -> list[RecommendationResult]:
    return [
        RecommendationResult(item_id=item_id, score=score, rank=rank + 1)
        for rank, (item_id, score) in enumerate(pairs)
    ]
