"""Deterministic SAE training loop (pure given config + seed + data)."""
from __future__ import annotations

import torch

from .config import TrainConfig
from .saes import SAE
from .utils import rng, unit_normalize, set_determinism


def train_sae(sae: SAE, X: torch.Tensor, tcfg: TrainConfig) -> dict:
    """Train `sae` on activation matrix X (n, d_model). Returns a telemetry dict.

    Decoder columns are unit-normalized every step (standard; removes the
    shrink-the-decoder degenerate solution so the L1 term is a clean sparsity signal).
    """
    set_determinism(tcfg.seed)
    opt = torch.optim.Adam(sae.parameters(), lr=tcfg.lr)
    r = rng(tcfg.seed)
    n = X.shape[0]
    d_sae = sae.cfg.d_sae
    steps_since_fire = torch.zeros(d_sae)
    is_topk = sae.cfg.variant == "topk"
    trace = []

    with torch.no_grad():
        sae.W_dec.data = unit_normalize(sae.W_dec.data, dim=0)

    for step in range(tcfg.steps):
        idx = torch.from_numpy(r.integers(0, n, size=tcfg.batch_size))
        xb = X[idx]
        dead_mask = (steps_since_fire > sae.cfg.dead_steps_threshold) if is_topk else None
        total, parts = sae.loss(xb, dead_mask=dead_mask) if is_topk else sae.loss(xb)
        opt.zero_grad()
        total.backward()
        opt.step()
        with torch.no_grad():
            sae.W_dec.data = unit_normalize(sae.W_dec.data, dim=0)
            # firing stats only matter for TopK's AuxK dead-latent revival; skip the
            # extra forward pass for the other variants (a ~2x training speedup).
            if is_topk:
                fired = (sae.encode(xb) > 0).any(dim=0)
                steps_since_fire = torch.where(fired, torch.zeros_like(steps_since_fire), steps_since_fire + 1.0)
        if step % max(1, tcfg.steps // 20) == 0 or step == tcfg.steps - 1:
            trace.append({"step": step, "total": float(total.item()), **parts})

    with torch.no_grad():
        ever_fired = (sae.encode(X[: min(4096, n)]) > 0).any(dim=0)
    n_dead = int((~ever_fired).sum().item())
    return {"trace": trace, "n_dead": n_dead, "final_loss": trace[-1]["total"]}
