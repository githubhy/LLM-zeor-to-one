"""Phase 4: sensitivity & optimisation (G3).

- H4 (pre-registered): does the fidelity gap {variant - ReLU} at matched L0 GROW with
  dictionary width R? OFAT sweep over R (the hypothesised factor).
- Robustness: does the ranking hold as data sparsity (feature_prob) varies?
- P0-3 global sensitivity: a manual Morris elementary-effects screening over
  {R, feature_prob, lr, steps} (SALib absent -> the sanctioned "or equivalent" path).
- P1-1: switch rule -> GRID (the sparsity knob is 1-D and each eval is cheap ~1.7s;
  Bayesian HPO is not warranted; documented, not run).

Run:  PYTHONPATH=implementation python -m sae_frontier.run_phase4
"""
from __future__ import annotations

import itertools
import json

import numpy as np
import torch

from .config import SAEConfig, SyntheticConfig, TrainConfig
from .experiment import VARIANTS
from .manifest import ARTIFACTS, append_phase
from .metrics import explained_variance, feature_recovery, l0
from .saes import build_sae
from .synthetic import generate
from .train import train_sae
from . import stats as S

warnings = __import__("warnings"); warnings.filterwarnings("ignore")

D_MODEL, N_FEATURES = 32, 64
TARGET_L0 = 8.0
BASE = dict(feature_prob=0.06, lr=3e-4, steps=1500, expansion=4, n_samples=6000)

# per-variant sweep to reach ~TARGET_L0 (short grids; evals are cheap)
def _op_grid(variant):
    return {"relu": [{"l1_coeff": v} for v in (0.1, 0.2, 0.4, 0.8)],
            "gated": [{"l1_coeff": v} for v in (0.1, 0.2, 0.4, 0.8)],
            "jumprelu": [{"l1_coeff": v} for v in (0.05, 0.1, 0.4, 0.8)],
            "topk": [{"k": v} for v in (4, 8, 12, 16)]}[variant]


def _ev_at_target(variant, expansion, X, tf, feature_prob, lr, steps, seed):
    pts = []
    for op in _op_grid(variant):
        cfg = SAEConfig(variant=variant, d_model=D_MODEL, expansion=expansion, seed=seed, **op)
        s = build_sae(cfg)
        train_sae(s, X, TrainConfig(steps=steps, seed=seed, lr=lr))
        with torch.no_grad():
            pts.append((l0(s.encode(X)), explained_variance(X, s(X)[0])))
    return S.interp_at(pts, TARGET_L0)


def h4_width_sweep(seeds=(0, 1, 2)):
    out = {}
    for R in (2, 4, 8, 16):
        per = {v: [] for v in VARIANTS}
        for seed in seeds:
            d = generate(SyntheticConfig(n_features=N_FEATURES, d_model=D_MODEL,
                                         feature_prob=BASE["feature_prob"], n_samples=BASE["n_samples"], seed=seed))
            for v in VARIANTS:
                per[v].append(_ev_at_target(v, R, d.x, d.true_features, BASE["feature_prob"],
                                            BASE["lr"], BASE["steps"], seed))
        out[R] = {v: S.aggregate(per[v]) for v in VARIANTS}
        out[R]["gap_vs_relu"] = {v: float(np.mean(per[v]) - np.mean(per["relu"])) for v in VARIANTS if v != "relu"}
        print(f"  R={R} done")
    return out


def robustness_sweep(seeds=(0, 1, 2)):
    out = {}
    for fp in (0.03, 0.06, 0.12):
        per = {v: [] for v in VARIANTS}
        for seed in seeds:
            d = generate(SyntheticConfig(n_features=N_FEATURES, d_model=D_MODEL, feature_prob=fp,
                                         n_samples=BASE["n_samples"], seed=seed))
            for v in VARIANTS:
                per[v].append(_ev_at_target(v, BASE["expansion"], d.x, d.true_features, fp,
                                            BASE["lr"], BASE["steps"], seed))
        out[fp] = {v: float(np.mean(per[v])) for v in VARIANTS}
        out[fp]["winner"] = max(VARIANTS, key=lambda v: np.mean(per[v]))
        print(f"  feature_prob={fp} done")
    return out


def morris_screening(n_traj=4):
    """Manual Morris elementary-effects: rank factor influence on TopK EV@target-L0."""
    # factors normalized to [0,1] over discrete levels
    levels = {"R": [2, 4, 8, 16], "feature_prob": [0.03, 0.06, 0.12],
              "lr": [1e-4, 3e-4, 1e-3], "steps": [800, 1500, 2500]}
    names = list(levels)
    rng = np.random.default_rng(0)

    def obj(pt):
        d = generate(SyntheticConfig(n_features=N_FEATURES, d_model=D_MODEL,
                                     feature_prob=pt["feature_prob"], n_samples=4000, seed=0))
        return _ev_at_target("topk", pt["R"], d.x, d.true_features, pt["feature_prob"], pt["lr"], pt["steps"], 0)

    ees = {n: [] for n in names}
    for _ in range(n_traj):
        base_idx = {n: int(rng.integers(0, len(levels[n]) - 1)) for n in names}  # leave room to step up
        base = {n: levels[n][base_idx[n]] for n in names}
        y0 = obj(base)
        for n in names:
            up = dict(base); up[n] = levels[n][base_idx[n] + 1]
            y1 = obj(up)
            delta = 1.0 / (len(levels[n]) - 1)   # normalized step
            ees[n].append((y1 - y0) / delta)
    return {n: {"mu_star": float(np.mean(np.abs(ees[n]))), "sigma": float(np.std(ees[n]))} for n in names}


def main():
    print("Phase 4: H4 width sweep..."); h4 = h4_width_sweep()
    print("Phase 4: robustness..."); rob = robustness_sweep()
    print("Phase 4: Morris screening (P0-3)..."); morris = morris_screening()

    # H4 test: is the mean gap {best-variant - relu} monotone increasing in R?
    Rs = sorted(h4)
    best_gap = [max(h4[R]["gap_vs_relu"].values()) for R in Rs]
    h4_monotone = all(best_gap[i + 1] >= best_gap[i] - 1e-3 for i in range(len(best_gap) - 1))

    sens = ARTIFACTS / "sensitivity"
    sens.mkdir(parents=True, exist_ok=True)
    summary = {
        "H4_width_sweep": {"by_R": h4, "best_gap_vs_relu_by_R": dict(zip(map(str, Rs), best_gap)),
                           "gap_monotone_increasing_in_R": h4_monotone},
        "robustness_feature_prob": rob,
        "P0_3_morris_elementary_effects": {"objective": "topk EV @ L0=8", "factors": morris,
                                           "note": "SALib absent; manual Morris (mu*/sigma). Rank by mu*."},
        "P1_1_hpo_decision": "GRID (sparsity knob is 1-D, eval ~1.7s cheap => Bayesian HPO not warranted per the switch rule)",
    }
    (sens / "sensitivity.json").write_text(json.dumps(summary, indent=2))
    _figure(h4, Rs, sens / "sensitivity.html")
    append_phase(4, "sensitivity", {"gate": "G3",
                                    "artifacts": ["sensitivity/sensitivity.json", "sensitivity/sensitivity.html"],
                                    "H4_gap_monotone_in_R": h4_monotone,
                                    "morris_top_factor": max(morris, key=lambda n: morris[n]["mu_star"])})
    print("Phase 4 complete. H4 gap monotone in R:", h4_monotone,
          "| best gap by R:", {R: round(g, 3) for R, g in zip(Rs, best_gap)})


def _figure(h4, Rs, path):
    import plotly.graph_objects as go
    fig = go.Figure()
    for v in ("gated", "topk", "jumprelu"):
        fig.add_trace(go.Scatter(x=Rs, y=[h4[R]["gap_vs_relu"][v] for R in Rs],
                                 mode="lines+markers", name=f"{v} - relu"))
    fig.update_layout(title="H4: fidelity gap over ReLU at matched L0, vs dictionary width R",
                      xaxis_title="expansion factor R (d_sae = R·d_model)", xaxis_type="log",
                      yaxis_title="EV gap over ReLU @ L0=8", template="plotly_white")
    fig.write_html(str(path), include_plotlyjs="cdn")


if __name__ == "__main__":
    main()
