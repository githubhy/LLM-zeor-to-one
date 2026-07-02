"""Task metrics and the normalized-faithfulness transform (Hanna §4.2).

All metrics take model logits at the final answer position and per-example answer-token
index tensors carried by the TaskBatch. Higher = more clean-like (matches the paper's M).
"""
from __future__ import annotations

import torch

# Numerical-safety floor for log/softmax paths (named constant, RIS rule).
EPS = 1e-9


def _last_token_logits(logits: torch.Tensor, last_idx: torch.Tensor) -> torch.Tensor:
    """logits: (B, T, V); last_idx: (B,) index of the answer position -> (B, V)."""
    b = torch.arange(logits.shape[0], device=logits.device)
    return logits[b, last_idx]  # (B, V)


def logit_diff(logits: torch.Tensor, last_idx: torch.Tensor,
               pos_ids: torch.Tensor, neg_ids: torch.Tensor) -> torch.Tensor:
    """M = logit(correct) - logit(foil), per example (B,). IOI: logit(IO) - logit(S)."""
    lg = _last_token_logits(logits, last_idx)               # (B, V)
    b = torch.arange(lg.shape[0], device=lg.device)
    return lg[b, pos_ids] - lg[b, neg_ids]                  # (B,)


def prob_diff(logits: torch.Tensor, last_idx: torch.Tensor,
              pos_mask: torch.Tensor, neg_mask: torch.Tensor) -> torch.Tensor:
    """M = sum p(good) - sum p(bad), per example (B,).

    pos_mask/neg_mask: (B, V) boolean over the vocabulary (GT: years > start vs <= start;
    SVA: agreeing vs disagreeing verb forms)."""
    lg = _last_token_logits(logits, last_idx)               # (B, V)
    p = torch.softmax(lg.float(), dim=-1)                   # (B, V)
    return (p * pos_mask).sum(-1) - (p * neg_mask).sum(-1)  # (B,)


def normalized_faithfulness(m_circuit: float, b_clean: float, b_corrupt: float) -> float:
    """faith = (m - b') / (b - b'); =1 at full circuit, =0 at empty circuit (Hanna §4.2)."""
    denom = b_clean - b_corrupt
    if abs(denom) < EPS:
        return float("nan")
    return (m_circuit - b_corrupt) / denom
