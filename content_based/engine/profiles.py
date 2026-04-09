from __future__ import annotations

import numpy as np
import torch

from .config import EngineConfig
from .schemas import Interaction, UserContext
from .stores import EmbeddingStore
from .utils import l2_normalize


def split_history(interactions: list[Interaction], config: EngineConfig) -> tuple[list[Interaction], list[Interaction], list[Interaction]]:
    positives, negatives, neutrals = [], [], []
    for x in interactions:
        if x.rating >= config.positive_threshold:
            positives.append(x)
        elif x.rating <= config.negative_threshold:
            negatives.append(x)
        else:
            neutrals.append(x)
    return positives, negatives, neutrals


def promote_neutral_if_needed(
    positives: list[Interaction],
    negatives: list[Interaction],
    neutrals: list[Interaction],
    config: EngineConfig,
) -> tuple[list[Interaction], list[Interaction]]:
    if len(positives) >= config.min_positive_items:
        return positives, negatives

    if len(neutrals) >= config.neutral_promote_threshold:
        promoted = positives + neutrals
        return promoted, negatives

    return positives, negatives


def fallback_profile(embedding_store: EmbeddingStore, config: EngineConfig) -> np.ndarray:
    if config.fallback_strategy == "random":
        rng = np.random.default_rng(config.random_seed)
        vec = rng.normal(size=embedding_store.dim).astype(np.float32)
        return l2_normalize(vec)

    mean_vec = np.asarray(embedding_store.emb_matrix, dtype=np.float32).mean(axis=0)
    return l2_normalize(mean_vec.astype(np.float32))


def weighted_average_profile(context: UserContext, embedding_store: EmbeddingStore, config: EngineConfig) -> np.ndarray:
    interactions = sorted(context.interactions, key=lambda x: (x.timestamp is None, x.timestamp))
    interactions = interactions[-config.max_context:]

    item_ids = [x.item_id for x in interactions if embedding_store.has(x.item_id)]
    weights = np.asarray([float(x.rating) for x in interactions if embedding_store.has(x.item_id)], dtype=np.float32)

    if len(item_ids) == 0:
        return fallback_profile(embedding_store, config)

    _, vecs = embedding_store.get_vectors(item_ids)
    profile = np.average(vecs, axis=0, weights=weights)
    return l2_normalize(profile.astype(np.float32))


def negative_feedback_profile(context: UserContext, embedding_store: EmbeddingStore, config: EngineConfig) -> np.ndarray:
    interactions = sorted(context.interactions, key=lambda x: (x.timestamp is None, x.timestamp))
    interactions = interactions[-config.max_context:]

    positives, negatives, neutrals = split_history(interactions, config)
    positives, negatives = promote_neutral_if_needed(positives, negatives, neutrals, config)

    pos_ids = [x.item_id for x in positives if embedding_store.has(x.item_id)]
    neg_ids = [x.item_id for x in negatives if embedding_store.has(x.item_id)]

    if len(pos_ids) == 0 and len(neg_ids) == 0:
        return fallback_profile(embedding_store, config)

    if len(pos_ids) == 0:
        # if only negatives exist, still start from fallback and subtract negative profile lightly
        _, neg_vecs = embedding_store.get_vectors(neg_ids)
        neg_profile = neg_vecs.mean(axis=0)
        profile = fallback_profile(embedding_store, config) - config.negative_lambda * neg_profile
        return l2_normalize(profile.astype(np.float32))

    _, pos_vecs = embedding_store.get_vectors(pos_ids)
    pos_profile = pos_vecs.mean(axis=0)

    if len(neg_ids) == 0:
        return l2_normalize(pos_profile.astype(np.float32))

    _, neg_vecs = embedding_store.get_vectors(neg_ids)
    neg_profile = neg_vecs.mean(axis=0)

    profile = pos_profile - config.negative_lambda * neg_profile
    return l2_normalize(profile.astype(np.float32))


def attention_profile(
    context: UserContext,
    embedding_store: EmbeddingStore,
    model,
    device: str,
    config: EngineConfig,
) -> np.ndarray:
    interactions = sorted(context.interactions, key=lambda x: (x.timestamp is None, x.timestamp))
    interactions = interactions[-config.max_context:]

    positives, negatives, neutrals = split_history(interactions, config)
    positives, negatives = promote_neutral_if_needed(positives, negatives, neutrals, config)

    # For attention inference, keep full usable context, but if there are too few positives and many 3-star,
    # the promotion rule already changes how downstream algorithms interpret them.
    usable = positives + negatives + [x for x in neutrals if x not in positives]
    usable = sorted(usable, key=lambda x: (x.timestamp is None, x.timestamp))

    item_ids = [x.item_id for x in usable if embedding_store.has(x.item_id)]
    if len(item_ids) == 0:
        return fallback_profile(embedding_store, config)

    idxs = [embedding_store.get_index(x) for x in item_ids]
    hist_idx = torch.tensor([idxs], dtype=torch.long, device=device)
    mask = torch.ones_like(hist_idx, dtype=torch.bool, device=device)

    with torch.no_grad():
        profile, _ = model(hist_idx, mask)

    vec = profile[0].detach().cpu().numpy().astype(np.float32)
    return l2_normalize(vec)
