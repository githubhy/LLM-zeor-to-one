"""Metric functions — the ONE shared set every candidate is scored by (P2-1 contract).

Fidelity/sparsity metrics (survey Section 10.3), the synthetic-oracle feature-recovery
metric, and the direct shrinkage-ratio measurement that tests the survey's Appendix-D.1
soft-threshold mechanism (hypothesis H2).
"""
from __future__ import annotations

import torch

from .utils import EPS_VAR, EPS_NORM


def l0(f: torch.Tensor) -> float:
    """Mean number of nonzero features per row."""
    return (f > 0).sum(dim=1).float().mean().item()


def explained_variance(x: torch.Tensor, x_hat: torch.Tensor) -> float:
    """1 - ||x - x_hat||^2 / ||x - mean(x)||^2  (scale-invariant fidelity)."""
    num = ((x - x_hat) ** 2).sum().item()
    den = ((x - x.mean(dim=0, keepdim=True)) ** 2).sum().item()
    return 1.0 - num / (den + EPS_VAR)


def normalized_mse(x: torch.Tensor, x_hat: torch.Tensor) -> float:
    """Fraction of variance UNexplained (= 1 - explained_variance); the frontier y-axis."""
    return 1.0 - explained_variance(x, x_hat)


def loss_recovered(l_orig: float, l_recon: float, l_zero: float) -> float:
    """(L_zero - L_recon) / (L_zero - L_orig)  — survey Eq 6-3 (real-model substrate)."""
    denom = (l_zero - l_orig)
    if abs(denom) < EPS_VAR:
        return float("nan")
    return (l_zero - l_recon) / denom


def feature_recovery(learned_dec: torch.Tensor, true_features: torch.Tensor) -> dict:
    """How well the learned decoder atoms match the ground-truth dictionary (S1 oracle).

    learned_dec: (d_model, d_sae); true_features: (d_model, n_features), unit-norm columns.
    Returns mean-max-cosine both directions + the fraction of true features hit above 0.9.
    """
    L = learned_dec / (learned_dec.norm(dim=0, keepdim=True) + EPS_NORM)   # (m, d_sae)
    T = true_features / (true_features.norm(dim=0, keepdim=True) + EPS_NORM)  # (m, n)
    cos = (T.t() @ L).abs()                       # (n_true, d_sae)
    true_to_learned = cos.max(dim=1).values       # best learned atom per true feature
    learned_to_true = cos.max(dim=0).values       # best true feature per learned atom
    return {
        "mmcs_true_to_learned": true_to_learned.mean().item(),
        "mmcs_learned_to_true": learned_to_true.mean().item(),
        "frac_true_recovered_0.9": (true_to_learned > 0.9).float().mean().item(),
    }


@torch.no_grad()
def shrinkage_ratio(sae, x: torch.Tensor, max_rows: int = 256) -> float:
    """Mean (SAE activation / least-squares-optimal activation) over active features.

    Directly measures the survey Eq D-2 soft-threshold bias: on each row we solve the
    UNPENALIZED least-squares magnitudes on the SAE's own active support, and compare.
    < 1 ⇒ shrinkage (ReLU+L1); ≈ 1 ⇒ unbiased (TopK/JumpReLU).
    """
    f = sae.encode(x[:max_rows])
    W = sae.W_dec.detach()          # (m, d_sae)
    b = sae.b_dec.detach()
    ratios = []
    for i in range(f.shape[0]):
        support = (f[i] > 0).nonzero(as_tuple=True)[0]
        if support.numel() == 0:
            continue
        Ws = W[:, support]                                   # (m, |S|)
        target = (x[i] - b).unsqueeze(1)                     # (m, 1)
        f_ls = torch.linalg.lstsq(Ws, target).solution.squeeze(1)  # (|S|,)
        f_sae = f[i, support]
        # restrict to the non-negative regime the soft-threshold (Eq D-2) governs:
        # a positive least-squares target where the SAE also fires.
        ok = (f_ls > 1e-3) & (f_sae > 1e-3)
        if ok.any():
            ratios.append((f_sae[ok] / f_ls[ok]).mean().item())
    return float(sum(ratios) / len(ratios)) if ratios else float("nan")
