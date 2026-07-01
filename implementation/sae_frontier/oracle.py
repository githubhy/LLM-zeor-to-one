"""P0-5 correctness anchoring — validate each candidate against an external oracle.

Every candidate must pass its `oracle_check` before entering the Phase-3 comparison; a
numerically-wrong implementation must not reach the frontier. Checks are analytical
(closed-form expected behavior of the activation) or metamorphic (necessary relations).
"""
from __future__ import annotations

import torch

from .config import SAEConfig
from .saes import build_sae


def _rec(type_, point, expected, measured, tol, passed):
    return {"type": type_, "point": point, "expected": expected,
            "measured": measured, "tolerance": tol, "passed": bool(passed)}


@torch.no_grad()
def run_oracle_checks(variant: str, d_model: int = 16, seed: int = 0) -> dict:
    """Return {variant, checks:[...], passed} — the oracle_check record for one candidate."""
    cfg = SAEConfig(variant=variant, d_model=d_model, expansion=4, seed=seed, dtype="float64", k=8)
    sae = build_sae(cfg)
    g = torch.Generator().manual_seed(seed + 1)
    x = torch.randn(64, d_model, generator=g, dtype=torch.float64)
    pre = torch.relu(sae.preactivation(x))
    f = sae.encode(x)
    checks = []

    # -- shared analytical anchors (exact) --------------------------------- #
    dec0 = sae.decode(torch.zeros(1, cfg.d_sae, dtype=torch.float64))
    err = (dec0 - sae.b_dec).abs().max().item()
    checks.append(_rec("analytical", "decode(0) == b_dec", 0.0, err, 1e-9, err < 1e-9))

    # non-negative code
    minf = f.min().item()
    checks.append(_rec("analytical", "features non-negative", ">=0", minf, 1e-9, minf >= -1e-9))

    # metamorphic: decoder is affine — decode(2f) - b_dec == 2(decode(f) - b_dec)
    lin = (sae.decode(2 * f) - sae.b_dec - 2 * (sae.decode(f) - sae.b_dec)).abs().max().item()
    checks.append(_rec("metamorphic", "decoder affine/linear", 0.0, lin, 1e-8, lin < 1e-8))

    # -- variant-specific exact properties --------------------------------- #
    if variant == "relu":
        d = (f - pre).abs().max().item()
        checks.append(_rec("analytical", "f == relu(preact)", 0.0, d, 1e-12, d < 1e-12))
    elif variant == "topk":
        maxact = (f > 0).sum(dim=1).max().item()
        checks.append(_rec("analytical", "active count <= k", f"<= {cfg.k}", maxact, 0, maxact <= cfg.k))
        # the survivors are the k largest of relu(preact)
        topk_vals = pre.topk(cfg.k, dim=1).values.sort(dim=1).values
        f_vals = f.sort(dim=1, descending=True).values[:, :cfg.k].sort(dim=1).values
        d = (topk_vals - f_vals).abs().max().item()
        checks.append(_rec("analytical", "survivors are top-k of relu(pre)", 0.0, d, 1e-10, d < 1e-10))
    elif variant == "jumprelu":
        theta = sae.theta
        active = pre > theta
        # where active, passthrough (NO shrink): f == relu(pre)
        d_active = (f[active] - pre[active]).abs().max().item() if active.any() else 0.0
        checks.append(_rec("analytical", "active f == pre (no shrink)", 0.0, d_active, 1e-12, d_active < 1e-12))
        d_inactive = f[~active].abs().max().item() if (~active).any() else 0.0
        checks.append(_rec("analytical", "inactive f == 0", 0.0, d_inactive, 1e-12, d_inactive < 1e-12))
    elif variant == "gated":
        pi_gate, pi_mag = sae._paths(x)
        off = pi_gate <= 0
        d_off = f[off].abs().max().item() if off.any() else 0.0
        checks.append(_rec("analytical", "f == 0 where gate closed", 0.0, d_off, 1e-12, d_off < 1e-12))
        on = pi_gate > 0
        d_on = (f[on] - torch.relu(pi_mag)[on]).abs().max().item() if on.any() else 0.0
        checks.append(_rec("analytical", "f == relu(mag) where gate open", 0.0, d_on, 1e-12, d_on < 1e-12))

    return {"variant": variant, "checks": checks, "passed": all(c["passed"] for c in checks)}
