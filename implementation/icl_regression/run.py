"""H9 baseline runner: Part A (von Oswald identity, exact) + Part B (trained softmax model
behaviorally tracks least-squares). Trains a depth sweep, evaluates in-context curves vs
classical learners, emits verdicts + artifact.

Run:  PYTHONPATH=$PWD python3 -m implementation.icl_regression.run [--device mps] [--quick]
"""
from __future__ import annotations

import argparse
import dataclasses
from dataclasses import dataclass, field

import numpy as np
import torch

from implementation.tiny_transformer.utils import save_json
from implementation.icl_regression import task as T
from implementation.icl_regression import construction as C
from implementation.icl_regression.model import (ICLModelConfig, ICLTrainConfig,
                                                 ICLRegressionTransformer, train,
                                                 in_context_predictions)
from implementation.icl_regression.eval import learner_curves, delta_norm_at, best_learner_at

STUDY = "icl-regression"
ARTIFACT = "artifacts/icl-regression"


@dataclass(frozen=True)
class Config:
    x_dim: int = 8
    d_model: int = 64                  # calibrated lean-fast config (converges <0.02 by ~8k steps)
    n_heads: int = 4
    d_mlp: int = 128
    depths: tuple = (1, 2, 4)          # H9-D depth sweep; deepest is the main model
    max_points: int = 20               # k_max; seq len 2*max_points; operating point n_star = 2*x_dim
    train_seeds: tuple = (0, 1, 2)     # training-seed envelope (main depth); others use seed 0
    steps: int = 12000
    batch: int = 128
    lr: float = 1e-3
    warmup: int = 300
    # eval
    n_eval_tasks: int = 1024
    eval_seed: int = 999
    noise_std_eval: float = 1.0        # noisy-eval variant (model trained noiseless): tracks OLS not ridge (Garg)
    ridge_lam: float = 1.0             # Bayes ridge lam = sigma^2/tau^2 = 1 at noise_std=1, tau=1
    gd_steps: int = 1                  # the "one GD step" contrast learner (H9-C)
    gd_lr: float = 0.1
    device: str = "cpu"

    @property
    def n_star(self):
        return 2 * self.x_dim

    def to_dict(self):
        d = dataclasses.asdict(self)
        d["n_star"] = self.n_star
        return d


def _tune_gd_lr(cfg: Config, rng) -> float:
    """Pick the GD step size that minimizes 1-step-GD error at n_star (a fair 'best 1-step GD'
    contrast for H9-C, so the comparison is not rigged by a bad lr)."""
    X, y, _ = T.make_regression_batch(rng, 256, cfg.max_points, cfg.x_dim)
    Xc, yc, xq, tgt = X[:, :cfg.n_star], y[:, :cfg.n_star], X[:, cfg.n_star], y[:, cfg.n_star]
    best_lr, best_mse = cfg.gd_lr, np.inf
    for lr in (0.02, 0.05, 0.1, 0.2, 0.3, 0.5):
        mse = float(np.mean((T.gd_predict(Xc, yc, xq, cfg.gd_steps, lr) - tgt) ** 2))
        if mse < best_mse:
            best_mse, best_lr = mse, lr
    return best_lr


def _train_one(cfg: Config, depth: int, seed: int, log):
    mcfg = ICLModelConfig(x_dim=cfg.x_dim, d_model=cfg.d_model, n_layers=depth,
                          n_heads=cfg.n_heads, d_mlp=cfg.d_mlp, max_points=cfg.max_points,
                          seed=seed)
    tcfg = ICLTrainConfig(steps=cfg.steps, batch=cfg.batch, lr=cfg.lr, warmup=cfg.warmup,
                          noise_std=0.0, eval_every=max(1, cfg.steps // 6), seed=seed)
    m = ICLRegressionTransformer(mcfg)
    hist = train(m, tcfg, device=cfg.device, log=log)
    return m, hist


def _curves_for(cfg, model, X, y, gd_lr):
    preds = in_context_predictions(model, X, y, device=cfg.device)
    return learner_curves(X, y, preds, ridge_lam=cfg.ridge_lam, gd_steps=cfg.gd_steps, gd_lr=gd_lr)


def main(cfg: Config) -> dict:
    torch.manual_seed(0)
    print(f"[{STUDY}] device={cfg.device} depths={cfg.depths} steps={cfg.steps} "
          f"x_dim={cfg.x_dim} n_star={cfg.n_star}")
    rng = np.random.default_rng(cfg.eval_seed)
    gd_lr = _tune_gd_lr(cfg, np.random.default_rng(7))
    print(f"tuned 1-step-GD lr = {gd_lr}")

    # ---- Part A: von Oswald identity (exact, no training) ----------------------
    a_res = []
    arng = np.random.default_rng(0)
    for i in range(200):
        Xs, ys, _w = T.make_regression_batch(arng, 1, 10, cfg.x_dim)
        xq = arng.standard_normal(cfg.x_dim)
        W0 = arng.standard_normal(cfg.x_dim) if i % 2 else np.zeros(cfg.x_dim)
        a_res.append(C.identity_max_abs_diff(Xs[0], ys[0], xq, W0=W0, eta=0.4))
    a_max = float(np.max(a_res))
    a_pass = a_max < 1e-5
    print(f"Part A (von Oswald identity): max|diff| over 200 tasks = {a_max:.2e}  "
          f"({'PASS' if a_pass else 'FAIL'})")

    # ---- Part B: train depth sweep --------------------------------------------
    # noiseless eval tasks (main), shared across depths/seeds
    Xe, ye, _ = T.make_regression_batch(rng, cfg.n_eval_tasks, cfg.max_points, cfg.x_dim)
    # noisy eval variant (same X, noisy y) for the OLS-vs-ridge-under-noise contrast
    Xen, yen, _ = T.make_regression_batch(np.random.default_rng(cfg.eval_seed + 1),
                                          cfg.n_eval_tasks, cfg.max_points, cfg.x_dim,
                                          noise_std=cfg.noise_std_eval)

    depth_spd_ols = {}      # H9-D: SPD-to-OLS at n_star per depth (seed 0)
    depth_curves = {}       # seed-0 curve per depth (for the depth-tightening figure)
    main_depth = max(cfg.depths)
    main_curves_per_seed = []
    for depth in cfg.depths:
        seeds = cfg.train_seeds if depth == main_depth else (cfg.train_seeds[0],)
        for seed in seeds:
            m, _ = _train_one(cfg, depth, seed,
                              log=(lambda s: None) if seed != cfg.train_seeds[0] else print)
            cur = _curves_for(cfg, m, Xe, ye, gd_lr)
            if depth == main_depth:
                main_curves_per_seed.append(cur)
            if seed == cfg.train_seeds[0]:
                depth_spd_ols[depth] = delta_norm_at(cur, cfg.n_star, "ols")
                depth_curves[depth] = cur
                if depth == main_depth:
                    main_noisy = _curves_for(cfg, m, Xen, yen, gd_lr)
            print(f"  depth {depth} seed {seed}: model_mse@n*={cur['mse_model'][cfg.n_star-1]:.4f} "
                  f"spd_vs_ols@n*={delta_norm_at(cur, cfg.n_star, 'ols'):.4f}")

    # ---- aggregate main-depth metrics with a training-seed envelope -----------
    # Honest unit = the trained model (one per seed); report mean + [min,max] envelope over
    # training seeds (NOT a bootstrap over eval tasks, which would ignore training variance and
    # over-state precision — the H15 pseudo-replication lesson). CI fields carry the envelope.
    def seed_stat(key, n):
        idx = main_curves_per_seed[0]["ns"].index(n)
        vals = [c[key][idx] for c in main_curves_per_seed]
        return (float(np.mean(vals)), float(np.min(vals)), float(np.max(vals)))

    ns = cfg.n_star
    dnorm_ols = seed_stat("spd_model_vs_ols", ns)
    dnorm_best_learner = best_learner_at(main_curves_per_seed[0], ns)
    dnorm_best = seed_stat(f"spd_model_vs_{dnorm_best_learner}", ns)
    mse_model_ns = seed_stat("mse_model", ns)
    mse_model_1 = seed_stat("mse_model", 1)
    spd_ols_ns = dnorm_ols[0]
    spd_gd_ns = seed_stat("spd_model_vs_gd", ns)[0]

    # ---- verdicts --------------------------------------------------------------
    decreasing = mse_model_ns[0] < 0.5 * mse_model_1[0]
    h9b = "PASS" if (decreasing and dnorm_best[0] < 0.10) else "INCONCLUSIVE"
    h9c = "PASS" if spd_ols_ns <= spd_gd_ns else "FAIL"
    h9d = "PASS" if depth_spd_ols[main_depth] <= depth_spd_ols[min(cfg.depths)] else "FAIL"
    h9a = "PASS" if a_pass else "FAIL"
    print(f"\nVerdicts: H9-A {h9a} | H9-B {h9b} (dnorm_best[{dnorm_best_learner}]={dnorm_best[0]:.3f}) "
          f"| H9-C {h9c} (ols {spd_ols_ns:.3f} vs gd1 {spd_gd_ns:.3f}) "
          f"| H9-D {h9d} (depth {min(cfg.depths)}->{main_depth}: "
          f"{depth_spd_ols[min(cfg.depths)]:.3f}->{depth_spd_ols[main_depth]:.3f})")

    summary = {
        "study": STUDY, "config": cfg.to_dict(), "gd_lr_tuned": gd_lr,
        "part_a": {"identity_max_abs_diff": a_max, "n_tasks": 200, "verdict": h9a,
                   "note": "von Oswald Prop-1 LINEAR-attention construction = 1 GD step (exact)"},
        "verdicts": {"H9_A": h9a, "H9_B": h9b, "H9_C": h9c, "H9_D": h9d},
        "operating_point_n_star": ns,
        "main_depth": main_depth, "n_train_seeds_main": len(cfg.train_seeds),
        "metrics": {
            # env_minmax = [min, max] over the training seeds (NOT a bootstrap CI — the honest
            # unit is the trained model; see seed_stat and report §6).
            "mse_model_at_n1": {"mean": mse_model_1[0], "env_minmax": [mse_model_1[1], mse_model_1[2]]},
            "mse_model_at_nstar": {"mean": mse_model_ns[0], "env_minmax": [mse_model_ns[1], mse_model_ns[2]]},
            "delta_norm_vs_ols_at_nstar": {"mean": dnorm_ols[0], "env_minmax": [dnorm_ols[1], dnorm_ols[2]]},
            "delta_norm_vs_best_at_nstar": {"mean": dnorm_best[0], "env_minmax": [dnorm_best[1], dnorm_best[2]],
                                            "best_learner": dnorm_best_learner},
            "spd_vs_ols_at_nstar": spd_ols_ns, "spd_vs_gd1_at_nstar": spd_gd_ns,
            "depth_spd_vs_ols_at_nstar": depth_spd_ols,
        },
        "noisy_eval": {   # model trained noiseless; does it track OLS or Bayes-ridge under noise?
            "spd_vs_ols_at_nstar": delta_norm_at(main_noisy, ns, "ols"),
            "spd_vs_ridge_at_nstar": delta_norm_at(main_noisy, ns, "ridge"),
            "note": "Garg: noiseless-trained model tracks OLS (double-descent), not Bayes ridge",
        },
        "curves_main_seed0": main_curves_per_seed[0],
        "depth_curves_seed0": {str(k): v for k, v in depth_curves.items()},
    }
    save_json(summary, f"{ARTIFACT}/baseline/summary.json")
    np.savez(f"{ARTIFACT}/baseline/curves.npz",
             ns=np.array(main_curves_per_seed[0]["ns"]),
             **{k: np.array([c[k] for c in main_curves_per_seed])
                for k in main_curves_per_seed[0] if k != "ns"})
    print(f"saved -> {ARTIFACT}/baseline/summary.json")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    kw = {"device": a.device}
    if a.quick:
        kw.update(depths=(1, 2), train_seeds=(0,), steps=800, n_eval_tasks=256)
    main(Config(**kw))
