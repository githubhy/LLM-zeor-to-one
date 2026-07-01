"""Phase 3 (S2): real-model realism confirmation on GPT-2-small residual activations.

Harvests GPT-2-small layer-6 residual-stream activations, traces a reduced frontier
(3 operating points x 3 paired seeds per candidate), and measures the survey's headline
cross-entropy loss-recovered (Eq 6-3) via a model-splice at each candidate's mid point.
Confirms the S1 H1 ordering on a real distribution. Heavier than S1 — run in background.

Run:  PYTHONPATH=implementation python -m sae_frontier.run_s2
"""
from __future__ import annotations

import itertools
import json
import warnings

import numpy as np
import torch

from .activations import ActivationConfig, harvest_activations, loss_recovered_on_model
from .config import SAEConfig, TrainConfig
from .experiment import train_eval
from .manifest import ARTIFACTS, append_phase
from .metrics import explained_variance, l0
from .saes import build_sae
from .train import train_sae
from . import stats as S

warnings.filterwarnings("ignore")

SEEDS = [0, 1, 2]
EXPANSION = 4
STEPS = 1200
# operating points tuned to bracket a comparable L0 range on GPT-2 residual acts
SWEEP = {
    "relu": [{"l1_coeff": v} for v in (0.5, 1.0, 2.0)],
    "gated": [{"l1_coeff": v} for v in (0.5, 1.0, 2.0)],
    "jumprelu": [{"l1_coeff": v} for v in (0.05, 0.1, 0.2)],
    "topk": [{"k": v} for v in (16, 32, 64)],
}
TARGET_L0 = 32.0


def main() -> None:
    acfg = ActivationConfig(model_name="gpt2", layer=6, n_sequences=160, seq_len=64, seed=0)
    print("harvesting GPT-2 activations...")
    X, meta = harvest_activations(acfg)
    d_model = meta["d_model"]
    # standardize scale (helps SAE training on real acts); keep a copy for splice compatibility
    X = X - X.mean(0, keepdim=True)
    print(f"  harvested {X.shape} at layer {acfg.layer}")

    rows = []
    for variant, ops in SWEEP.items():
        for op in ops:
            for seed in SEEDS:
                idx = torch.randperm(X.shape[0], generator=torch.Generator().manual_seed(seed))
                rows.append(train_eval(variant, op, seed, X[idx], None, d_model, EXPANSION, STEPS))
        print(f"  done {variant}")

    ev_at = {}
    for variant in SWEEP:
        per_seed = []
        for seed in SEEDS:
            pts = [(r["l0"], r["ev"]) for r in rows if r["variant"] == variant and r["seed"] == seed]
            per_seed.append(S.interp_at(pts, TARGET_L0))
        ev_at[variant] = per_seed
    pairwise = {f"{a}_vs_{b}": {"metric": "ev@L0=%g" % TARGET_L0, **S.paired_test(ev_at[a], ev_at[b])}
                for a, b in itertools.combinations(SWEEP, 2)}

    # loss-recovered via model-splice at each variant's mid operating point (seed 0)
    lr = {}
    print("measuring loss-recovered (model splice)...")
    for variant, ops in SWEEP.items():
        op = ops[len(ops) // 2]
        sae = build_sae(SAEConfig(variant=variant, d_model=d_model, expansion=EXPANSION, seed=0, **op))
        train_sae(sae, X, TrainConfig(steps=STEPS, seed=0))
        res = loss_recovered_on_model(sae, acfg, n_eval_seqs=32)
        lr[variant] = {"op": op, "l0": l0(sae.encode(X)), **res}
        print(f"    {variant}: loss_recovered={res['loss_recovered']:.3f}")

    base = ARTIFACTS / "baseline"
    base.mkdir(parents=True, exist_ok=True)
    summary = {
        "substrate": "S2-gpt2-small-layer6-residual",
        "activation_meta": meta,
        "protocol": {"expansion": EXPANSION, "steps": STEPS, "seeds": SEEDS, "target_l0": TARGET_L0},
        "H1_ev_at_matched_L0": {"mean": {v: float(np.mean(ev_at[v])) for v in SWEEP}, "pairwise": pairwise},
        "loss_recovered": lr,
        "seed_set_shared_across_candidates": True,
    }
    (base / "summary_s2.json").write_text(json.dumps(summary, indent=2))
    np.savez(base / "scores_s2.npz",
             variant=np.array([r["variant"] for r in rows]),
             seed=np.array([r["seed"] for r in rows]),
             l0=np.array([r["l0"] for r in rows], float),
             ev=np.array([r["ev"] for r in rows], float))
    append_phase(3, "baseline-s2", {"gate": "G2-realism", "substrate": "S2",
                                   "artifacts": ["baseline/summary_s2.json", "baseline/scores_s2.npz"],
                                   "loss_recovered": {v: lr[v]["loss_recovered"] for v in lr}})
    print("Phase 3 (S2) complete. loss_recovered:", {v: round(lr[v]["loss_recovered"], 3) for v in lr})


if __name__ == "__main__":
    main()
