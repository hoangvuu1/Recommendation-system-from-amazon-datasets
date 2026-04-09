from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class AttentionProfile(nn.Module):
    """
    Stable attention:
      - base_profile = mean(history embeddings)
      - attn_profile = weighted sum(history embeddings)
      - final_profile = mix(base_profile, attn_profile)
    """

    def __init__(self, emb_matrix: torch.Tensor, hidden_dim: int = 128, mix_alpha: float = 0.5):
        super().__init__()
        self.item_emb = nn.Embedding.from_pretrained(emb_matrix, freeze=True)
        d = emb_matrix.shape[1]
        self.mix_alpha = mix_alpha

        self.scorer = nn.Sequential(
            nn.Linear(d, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, hist_idx: torch.Tensor, mask: torch.Tensor):
        hist_emb = self.item_emb(hist_idx.clamp_min(0))
        hist_emb = F.normalize(hist_emb, dim=-1)

        masked_hist = hist_emb * mask.unsqueeze(-1)
        denom = mask.sum(dim=1, keepdim=True).clamp_min(1)

        base_profile = masked_hist.sum(dim=1) / denom
        base_profile = F.normalize(base_profile, dim=-1)

        logits = self.scorer(hist_emb).squeeze(-1)
        logits = logits.masked_fill(~mask, -1e9)
        attn = torch.softmax(logits, dim=1)

        attn_profile = torch.sum(hist_emb * attn.unsqueeze(-1), dim=1)
        attn_profile = F.normalize(attn_profile, dim=-1)

        profile = (1 - self.mix_alpha) * base_profile + self.mix_alpha * attn_profile
        profile = F.normalize(profile, dim=-1)
        return profile, attn

    def get_item_emb(self, item_idx: torch.Tensor) -> torch.Tensor:
        emb = self.item_emb(item_idx)
        return F.normalize(emb, dim=-1)
