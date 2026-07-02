"""Edge/node attribution scorers: eap, eap_ig, exact_patch, random.

Node granularity (heads + MLPs + embed). Score sign follows Hanna Eq 1/3 with loss L=-M:
  eap      score(u) = <z'_u - z_u, ∇_{z_u} L>              (1 fwd corrupt + 1 fwd/bwd clean)
  eap_ig   score(u) = <z'_u - z_u, mean_k ∇ L@interp_k>    (1 fwd corrupt + m fwd/bwd on IG path)
  exact    score(u) = M(clean) - M(patch u→corrupt)        (157 fwd; ground-truth node effect)
  random   iid Normal (seed)                               (floor)
All are exposed only through registry.build_scorer (P2-1 contract).
"""
from __future__ import annotations

import numpy as np
import torch

from .config import AttrConfig


def _dot(dz: torch.Tensor, g: torch.Tensor, mask: torch.Tensor) -> float:
    """mean over batch of sum_pos <dz,g>, masking pad positions. dz,g:(B,T,d) mask:(B,T)."""
    per = (dz.float() * g.float()).sum(-1) * mask.float()     # (B,T)
    return (per.sum() / mask.shape[0]).item()


def score_eap(M, batch) -> dict[str, float]:
    _, cc = M.forward_cache(batch.clean_ids, batch.attn_mask)
    _, xc = M.forward_cache(batch.corrupt_ids, batch.attn_mask)
    grads, _ = M.forward_grad(batch.clean_ids, batch.attn_mask, batch.metric,
                              sign=-1.0, ig_steps=1)
    return {u: _dot(xc[u] - cc[u], grads[u], batch.attn_mask) for u in M.names}


def score_eap_ig(M, batch, m_ig: int = 5) -> dict[str, float]:
    _, cc = M.forward_cache(batch.clean_ids, batch.attn_mask)
    _, xc = M.forward_cache(batch.corrupt_ids, batch.attn_mask)
    wte = M.model.transformer.wte
    z_clean = wte(batch.clean_ids)
    z_corrupt = wte(batch.corrupt_ids)
    grads, _ = M.forward_grad(batch.clean_ids, batch.attn_mask, batch.metric,
                              sign=-1.0, ig_steps=m_ig,
                              corrupt_embed=z_corrupt, clean_embed=z_clean)
    return {u: _dot(xc[u] - cc[u], grads[u], batch.attn_mask) for u in M.names}


@torch.no_grad()
def score_exact(M, batch) -> dict[str, float]:
    _, xc = M.forward_cache(batch.corrupt_ids, batch.attn_mask)
    clean_logits = M.model(batch.clean_ids, attention_mask=batch.attn_mask).logits
    m_clean = batch.metric(clean_logits).mean().item()
    allc = set(M.names)
    scores = {}
    for u in M.names:
        lg = M.patched_logits(batch.clean_ids, batch.attn_mask, xc, allc - {u})
        scores[u] = m_clean - batch.metric(lg).mean().item()   # metric drop when u corrupted
    return scores


def score_random(M, batch, seed: int = 0) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    return {u: float(rng.standard_normal()) for u in M.names}


def score_nodes(M, batch, cfg: AttrConfig) -> dict[str, float]:
    if cfg.method == "eap":
        return score_eap(M, batch)
    if cfg.method == "eap_ig":
        return score_eap_ig(M, batch, cfg.m_ig)
    if cfg.method == "exact_patch":
        return score_exact(M, batch)
    if cfg.method == "random":
        return score_random(M, batch, cfg.seed)
    raise KeyError(cfg.method)
