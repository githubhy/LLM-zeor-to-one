"""H9 figure: (A) in-context MSE vs #examples for the trained model and the classical learners
(model tracks least-squares, beats one GD step); (B) model-vs-OLS agreement tightening with
depth. Reads the artifact; regenerable without retraining.

Run: PYTHONPATH=$PWD python3 -m implementation.icl_regression.figure
"""
from __future__ import annotations

import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from implementation.tiny_transformer.utils import save_json

ART = "artifacts/icl-regression"


def main():
    os.makedirs(f"{ART}/figures", exist_ok=True)
    d = json.load(open(f"{ART}/baseline/summary.json"))
    z = np.load(f"{ART}/baseline/curves.npz")
    ns = z["ns"]
    nstar = d["operating_point_n_star"]
    cur0 = d["curves_main_seed0"]

    # model MSE mean + envelope across training seeds
    mm = z["mse_model"]                       # (n_seeds, n)
    m_mean, m_lo, m_hi = mm.mean(0), mm.min(0), mm.max(0)

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11, 4.2))

    # Panel A — MSE vs #examples
    axA.plot(ns, cur0["mse_ols"], "k-", lw=2, label="OLS (min-norm)")
    axA.plot(ns, cur0["mse_ridge"], color="tab:green", ls="--", label="ridge($\\lambda$=1)")
    axA.plot(ns, cur0["mse_gd"], color="tab:orange", ls=":", label="1-step GD")
    axA.plot(ns, m_mean, color="tab:blue", lw=2, label="trained transformer")
    axA.fill_between(ns, m_lo, m_hi, color="tab:blue", alpha=0.2)
    axA.axvline(nstar, color="gray", ls=":", lw=1)
    axA.set_yscale("log")
    axA.set_xlabel("# in-context examples $n$")
    axA.set_ylabel("prediction MSE (to truth)")
    axA.set_title("A · In-context error vs examples")
    axA.legend(fontsize=8, loc="upper right")
    axA.annotate(f"$n^*=2d={nstar}$", (nstar, axA.get_ylim()[1]), fontsize=8,
                 ha="center", va="top", color="gray")

    # Panel B — model-vs-OLS agreement (normalized SPD) tightening with depth
    dc = d["depth_curves_seed0"]
    for depth in sorted(dc, key=int):
        c = dc[depth]
        axB.plot(c["ns"], c["spd_model_vs_ols"], marker="o", ms=3, label=f"depth {depth}")
    axB.axvline(nstar, color="gray", ls=":", lw=1)
    axB.set_yscale("log")
    axB.set_xlabel("# in-context examples $n$")
    axB.set_ylabel("normalized dev. from OLS (SPD)")
    axB.set_title("B · OLS-agreement tightens with depth")
    axB.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(f"{ART}/figures/h9-icl-regression.png", dpi=140, bbox_inches="tight")
    save_json({"ns": ns.tolist(), "model_mse_mean": m_mean.tolist(),
               "model_mse_env": [m_lo.tolist(), m_hi.tolist()],
               "ols_mse": cur0["mse_ols"], "ridge_mse": cur0["mse_ridge"], "gd_mse": cur0["mse_gd"],
               "depth_spd_vs_ols": {k: v["spd_model_vs_ols"] for k, v in dc.items()},
               "n_star": int(nstar)},
              f"{ART}/figures/h9-icl-regression.data.json")
    print(f"saved -> {ART}/figures/h9-icl-regression.png")


if __name__ == "__main__":
    main()
