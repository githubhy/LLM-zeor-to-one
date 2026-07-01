"""The four SAE candidates, sharing a uniform interface (survey Section 6.2, Appendix D).

Each SAE exposes:
    encode(x)  -> f            feature activations (batch, d_sae), non-negative, sparse
    decode(f)  -> x_hat        linear reconstruction (batch, d_model)
    forward(x) -> (x_hat, telemetry)
    loss(x, **kw) -> (total, parts)   reconstruction + variant sparsity term

Variants: relu (ReLU+L1 baseline), gated, topk, jumprelu. All are pure given
(config, params, input); randomness enters only through explicit init seeds.
"""
from __future__ import annotations

import torch
import torch.nn as nn

from .config import SAEConfig
from .utils import STE_BANDWIDTH, unit_normalize


# --------------------------------------------------------------------------- #
# Straight-through estimators for the JumpReLU discontinuities (survey Eq D-4)  #
# --------------------------------------------------------------------------- #
class _JumpReLU(torch.autograd.Function):
    """f = pre * H(pre - theta). Backward: passthrough to pre where active;
    STE (rectangle kernel of half-width `bw`) to theta with jump-height `theta`."""

    @staticmethod
    def forward(ctx, pre, theta, bw):
        ctx.save_for_backward(pre, theta)
        ctx.bw = bw
        return pre * (pre > theta).to(pre.dtype)

    @staticmethod
    def backward(ctx, g):
        pre, theta = ctx.saved_tensors
        gate = (pre > theta).to(pre.dtype)
        kernel = ((pre - theta).abs() < ctx.bw).to(pre.dtype) / (2.0 * ctx.bw)
        grad_pre = g * gate
        grad_theta = (g * (-theta) * kernel).sum(dim=0)
        return grad_pre, grad_theta, None


class _StepL0(torch.autograd.Function):
    """H(pre - theta) for the L0 penalty. Backward: STE to theta only."""

    @staticmethod
    def forward(ctx, pre, theta, bw):
        ctx.save_for_backward(pre, theta)
        ctx.bw = bw
        return (pre > theta).to(pre.dtype)

    @staticmethod
    def backward(ctx, g):
        pre, theta = ctx.saved_tensors
        kernel = ((pre - theta).abs() < ctx.bw).to(pre.dtype) / (2.0 * ctx.bw)
        grad_theta = (g * (-1.0) * kernel).sum(dim=0)
        return None, grad_theta, None


# --------------------------------------------------------------------------- #
# Base                                                                          #
# --------------------------------------------------------------------------- #
class SAE(nn.Module):
    """Shared encoder/decoder scaffold. Subclasses override `encode` and `sparsity`."""

    def __init__(self, cfg: SAEConfig):
        super().__init__()
        self.cfg = cfg
        dt = torch.float64 if cfg.dtype == "float64" else torch.float32
        g = torch.Generator().manual_seed(cfg.seed)
        d, m = cfg.d_sae, cfg.d_model
        # decoder columns ~ unit norm; encoder tied to decoder transpose at init
        W_dec = torch.randn(m, d, generator=g, dtype=dt)
        W_dec = unit_normalize(W_dec, dim=0)
        self.W_dec = nn.Parameter(W_dec)
        self.W_enc = nn.Parameter(W_dec.t().clone())
        self.b_enc = nn.Parameter(torch.zeros(d, dtype=dt))
        self.b_dec = nn.Parameter(torch.zeros(m, dtype=dt))

    # -- shared ------------------------------------------------------------- #
    def preactivation(self, x: torch.Tensor) -> torch.Tensor:
        return (x - self.b_dec) @ self.W_enc.t() + self.b_enc

    def decode(self, f: torch.Tensor) -> torch.Tensor:
        return f @ self.W_dec.t() + self.b_dec

    def decoder_norms(self) -> torch.Tensor:
        return self.W_dec.norm(dim=0)  # (d_sae,)

    def forward(self, x: torch.Tensor):
        f = self.encode(x)
        x_hat = self.decode(f)
        telem = {
            "f": f,
            "l0": (f > 0).sum(dim=1).float().mean().item(),
            "recon_mse": ((x - x_hat) ** 2).sum(dim=1).mean().item(),
        }
        return x_hat, telem

    def recon_loss(self, x: torch.Tensor, x_hat: torch.Tensor) -> torch.Tensor:
        return ((x - x_hat) ** 2).sum(dim=1).mean()

    # -- to be overridden --------------------------------------------------- #
    def encode(self, x: torch.Tensor) -> torch.Tensor:  # pragma: no cover
        raise NotImplementedError

    def loss(self, x: torch.Tensor, **kw):  # pragma: no cover
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# 1. ReLU + L1 (baseline; survey Eq 6-1/6-2)                                    #
# --------------------------------------------------------------------------- #
class ReLUSAE(SAE):
    def encode(self, x):
        return torch.relu(self.preactivation(x))

    def loss(self, x, **kw):
        f = self.encode(x)
        x_hat = self.decode(f)
        recon = self.recon_loss(x, x_hat)
        # decoder-norm-scaled L1 (prevents the shrink-the-decoder degenerate solution)
        l1 = (f * self.decoder_norms()).sum(dim=1).mean()
        total = recon + self.cfg.l1_coeff * l1
        return total, {"recon": recon.item(), "l1": l1.item(), "sparsity_term": (self.cfg.l1_coeff * l1).item()}


# --------------------------------------------------------------------------- #
# 2. TopK (Gao et al.; exact L0 = k, no shrinkage on survivors)                #
# --------------------------------------------------------------------------- #
class TopKSAE(SAE):
    def encode(self, x):
        pre = torch.relu(self.preactivation(x))
        k = self.cfg.k
        vals, idx = pre.topk(k, dim=1)
        f = torch.zeros_like(pre)
        f.scatter_(1, idx, vals)
        return f

    def loss(self, x, dead_mask: torch.Tensor | None = None, **kw):
        f = self.encode(x)
        x_hat = self.decode(f)
        recon = self.recon_loss(x, x_hat)
        parts = {"recon": recon.item(), "l1": 0.0}
        total = recon
        # AuxK: top-k_aux DEAD latents reconstruct the residual error (revives dead latents)
        if dead_mask is not None and dead_mask.any() and self.cfg.aux_coeff > 0:
            pre = torch.relu(self.preactivation(x))
            pre_dead = pre.masked_fill(~dead_mask.unsqueeze(0), 0.0)
            k_aux = min(self.cfg.k_aux, int(dead_mask.sum().item()))
            if k_aux > 0:
                vals, idx = pre_dead.topk(k_aux, dim=1)
                f_aux = torch.zeros_like(pre_dead)
                f_aux.scatter_(1, idx, vals)
                e = (x - x_hat).detach()
                e_hat = f_aux @ self.W_dec.t()
                aux = ((e - e_hat) ** 2).sum(dim=1).mean()
                total = recon + self.cfg.aux_coeff * aux
                parts["auxk"] = aux.item()
        return total, parts


# --------------------------------------------------------------------------- #
# 3. JumpReLU (learned threshold + STE; survey Eq D-3/D-4)                      #
# --------------------------------------------------------------------------- #
class JumpReLUSAE(SAE):
    def __init__(self, cfg: SAEConfig):
        super().__init__(cfg)
        dt = self.W_dec.dtype
        init = torch.log(torch.tensor(cfg.jumprelu_init_threshold, dtype=dt))
        self.log_theta = nn.Parameter(torch.full((cfg.d_sae,), float(init), dtype=dt))

    @property
    def theta(self) -> torch.Tensor:
        return torch.exp(self.log_theta)

    def encode(self, x):
        pre = torch.relu(self.preactivation(x))
        return _JumpReLU.apply(pre, self.theta, STE_BANDWIDTH)

    def loss(self, x, **kw):
        pre = torch.relu(self.preactivation(x))
        f = _JumpReLU.apply(pre, self.theta, STE_BANDWIDTH)
        x_hat = self.decode(f)
        recon = self.recon_loss(x, x_hat)
        # direct L0 penalty (count of active features), STE grad to theta
        l0 = _StepL0.apply(pre, self.theta, STE_BANDWIDTH).sum(dim=1).mean()
        total = recon + self.cfg.l1_coeff * l0
        return total, {"recon": recon.item(), "l0_penalty": l0.item(), "sparsity_term": (self.cfg.l1_coeff * l0).item()}


# --------------------------------------------------------------------------- #
# 4. Gated (decouple detection from magnitude; Rajamanoharan et al.)           #
# --------------------------------------------------------------------------- #
class GatedSAE(SAE):
    def __init__(self, cfg: SAEConfig):
        super().__init__(cfg)
        dt = self.W_dec.dtype
        # magnitude path shares W_enc direction, rescaled per-feature by exp(r_mag)
        self.r_mag = nn.Parameter(torch.zeros(cfg.d_sae, dtype=dt))
        self.b_mag = nn.Parameter(torch.zeros(cfg.d_sae, dtype=dt))

    def _paths(self, x):
        centered = x - self.b_dec
        pi_gate = centered @ self.W_enc.t() + self.b_enc
        W_mag = torch.exp(self.r_mag).unsqueeze(1) * self.W_enc  # (d_sae, d_model)
        pi_mag = centered @ W_mag.t() + self.b_mag
        return pi_gate, pi_mag

    def encode(self, x):
        pi_gate, pi_mag = self._paths(x)
        gate = (pi_gate > 0).to(pi_gate.dtype)          # hard binary detection
        return gate * torch.relu(pi_mag)                # magnitude where gate on

    def loss(self, x, **kw):
        pi_gate, pi_mag = self._paths(x)
        gate = (pi_gate > 0).to(pi_gate.dtype)
        f = gate * torch.relu(pi_mag)
        x_hat = self.decode(f)
        recon = self.recon_loss(x, x_hat)
        gate_relu = torch.relu(pi_gate)
        # L1 on the gate pre-activation (decoder-norm-scaled), NOT on the magnitude
        l1 = (gate_relu * self.decoder_norms().detach()).sum(dim=1).mean()
        # auxiliary: gate-only reconstruction with a FROZEN decoder ties the gate to reconstruction
        x_hat_aux = gate_relu @ self.W_dec.t().detach() + self.b_dec.detach()
        aux = self.recon_loss(x, x_hat_aux)
        total = recon + self.cfg.l1_coeff * l1 + aux
        return total, {"recon": recon.item(), "l1": l1.item(), "aux": aux.item(), "sparsity_term": (self.cfg.l1_coeff * l1).item()}


_REGISTRY = {"relu": ReLUSAE, "gated": GatedSAE, "topk": TopKSAE, "jumprelu": JumpReLUSAE}


def build_sae(cfg: SAEConfig) -> SAE:
    """Factory: the ONLY way candidates are constructed (P2-1 registry contract)."""
    return _REGISTRY[cfg.variant](cfg)
