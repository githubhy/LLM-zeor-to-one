"""Circuit faithfulness (Hanna §4.2): ablate out-of-circuit node outputs to corrupt,
measure the recovered task metric, normalize by (m-b')/(b-b'). Returns per-example
faithfulness tensors so §6 can attach bootstrap CIs."""
from __future__ import annotations

import torch

from .graph import top_n_circuit
from .metrics import EPS


@torch.no_grad()
def baselines(M, batch) -> tuple[float, float]:
    """b = clean full-model metric, b' = corrupted full-model metric (means)."""
    b = batch.metric(M.model(batch.clean_ids, attention_mask=batch.attn_mask).logits).mean().item()
    bp = batch.metric(M.model(batch.corrupt_ids, attention_mask=batch.attn_mask).logits).mean().item()
    return b, bp


@torch.no_grad()
def faith_curve(M, batch, scores: dict[str, float], sizes: list[int],
                b: float, bp: float) -> dict[int, torch.Tensor]:
    """For each circuit size n: per-example normalized faithfulness (B,) tensor."""
    _, corrupt_contribs = M.forward_cache(batch.corrupt_ids, batch.attn_mask)
    denom = (b - bp) if abs(b - bp) > EPS else float("nan")
    out: dict[int, torch.Tensor] = {}
    for n in sizes:
        circuit = top_n_circuit(scores, n)
        lg = M.patched_logits(batch.clean_ids, batch.attn_mask, corrupt_contribs, circuit)
        m = batch.metric(lg)                       # (B,)
        out[n] = (m - bp) / denom                  # per-example faithfulness
    return out
