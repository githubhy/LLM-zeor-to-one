"""Track-C extension candidates for the SAE fidelity–sparsity frontier study — the
adaptive-count variants the parent study's red-team (Sec. 10) predicted would beat exact-k
TopK on heavy-tailed / dense activations. Reuses the verified `SAE` base (saes.py) unchanged.

- BatchTopK (Bussmann et al. 2024): one threshold for the whole batch (k·B total actives),
  so per-example sparsity varies — better on heavy-tailed activation mass than fixed per-example k.
- Matryoshka (Bussmann et al. 2025): nested-prefix reconstruction — the first m latents must
  reconstruct alone, so early atoms carry coarse/general structure and feature-splitting drops.
- AdaptiveJumpReLU: STE bandwidth scales with the per-batch pre-activation std (closes bug
  2026-07-02-01 — the fixed-bandwidth ranking was bandwidth-conditional).
"""
from __future__ import annotations

import torch

from .config import SAEConfig
from .saes import SAE, _JumpReLU, _StepL0


class BatchTopKSAE(SAE):
    """One global threshold per batch: keep the top (k · batch) pre-activations overall."""

    def encode(self, x):
        pre = torch.relu(self.preactivation(x))       # (B, d_sae)
        B = pre.shape[0]
        k_total = min(self.cfg.k * B, pre.numel())
        thresh = pre.flatten().topk(k_total).values.min() if k_total > 0 else pre.max() + 1
        return pre * (pre >= thresh).to(pre.dtype)

    def loss(self, x, **kw):
        f = self.encode(x)
        x_hat = self.decode(f)
        recon = self.recon_loss(x, x_hat)
        return recon, {"recon": recon.item(), "l0": (f > 0).sum(1).float().mean().item()}


class MatryoshkaSAE(SAE):
    """TopK encode; loss = sum of reconstruction at nested dictionary prefixes."""

    PREFIXES = (0.25, 0.5, 1.0)

    def _topk(self, x):
        pre = torch.relu(self.preactivation(x))
        vals, idx = pre.topk(self.cfg.k, dim=1)
        f = torch.zeros_like(pre)
        f.scatter_(1, idx, vals)
        return f

    def encode(self, x):
        return self._topk(x)                          # full dictionary at inference

    def loss(self, x, **kw):
        f = self._topk(x)
        total = torch.zeros((), dtype=x.dtype)
        parts = {}
        for frac in self.PREFIXES:
            m = max(1, int(frac * self.cfg.d_sae))
            x_hat = f[:, :m] @ self.W_dec[:, :m].t() + self.b_dec
            r = self.recon_loss(x, x_hat)
            total = total + r
            parts[f"recon_{m}"] = r.item()
        return total, parts


class AdaptiveJumpReLUSAE(SAE):
    """JumpReLU whose STE bandwidth = `bw_frac` × per-batch pre-activation std (data-adaptive)."""

    def __init__(self, cfg: SAEConfig, bw_frac: float = 0.5):
        super().__init__(cfg)
        dt = self.W_dec.dtype
        init = torch.log(torch.tensor(cfg.jumprelu_init_threshold, dtype=dt))
        self.log_theta = torch.nn.Parameter(torch.full((cfg.d_sae,), float(init), dtype=dt))
        self.bw_frac = bw_frac

    @property
    def theta(self):
        return torch.exp(self.log_theta)

    def _bw(self, pre):
        return max(float(self.bw_frac * pre.detach().std().item()), 1e-4)

    def encode(self, x):
        pre = torch.relu(self.preactivation(x))
        return _JumpReLU.apply(pre, self.theta, self._bw(pre))

    def loss(self, x, **kw):
        pre = torch.relu(self.preactivation(x))
        bw = self._bw(pre)
        f = _JumpReLU.apply(pre, self.theta, bw)
        x_hat = self.decode(f)
        recon = self.recon_loss(x, x_hat)
        l0 = _StepL0.apply(pre, self.theta, bw).sum(dim=1).mean()
        total = recon + self.cfg.l1_coeff * l0
        return total, {"recon": recon.item(), "l0_penalty": l0.item(), "bandwidth": bw}


_EXT = {"batchtopk": BatchTopKSAE, "matryoshka": MatryoshkaSAE, "adaptive_jumprelu": AdaptiveJumpReLUSAE}


def build_ext(variant: str, d_model: int, expansion: int = 4, seed: int = 0, k: int = 16,
              l1_coeff: float = 0.05):
    # variant="topk" only satisfies SAEConfig's Literal validation; the ext class is built directly.
    cfg = SAEConfig(variant="topk", d_model=d_model, expansion=expansion, seed=seed, k=k,
                    l1_coeff=l1_coeff)
    return _EXT[variant](cfg)
