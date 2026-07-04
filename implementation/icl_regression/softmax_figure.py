"""H9 softmax two-head figure (von Oswald §A.9): (A) normalized error vs score-scale beta for the
single-head best-case, the honest two-head, and the idealized construction; (B) the two-head vs
single-head floors and their ratio vs context length N (the two-head O(1/N) advantage widening).

Reads artifacts/icl-regression-softmax/summary.json; regenerable without recomputation.
Run: PYTHONPATH=$PWD python3 -m implementation.icl_regression.softmax_figure
"""
from __future__ import annotations

import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from implementation.tiny_transformer.utils import save_json

ART = "artifacts/icl-regression-softmax"


def main():
    os.makedirs(f"{ART}/figures", exist_ok=True)
    d = json.load(open(f"{ART}/summary.json"))
    bs = d["beta_sweep"]
    betas = np.array(bs["beta"])
    single = np.array([r["err"] for r in bs["single_best"]])
    single_ci = np.array([r["err_ci"] for r in bs["single_best"]]).T   # (2, nbeta)
    two = np.array([r["err"] for r in bs["two_head"]])
    two_ci = np.array([r["err_ci"] for r in bs["two_head"]]).T
    ideal = np.array([r["err_absrms"] for r in bs["two_ideal"]])
    ns = d["n_sweep"]
    Ns = np.array(ns["N"])
    sf = np.array(ns["single_floor"])
    tf = np.array(ns["two_floor"])
    ver = d["verdict"]

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.5, 4.4))

    # Panel A — normalized error vs beta (headline N)
    axA.plot(betas, single, "o-", color="tab:red", lw=2, ms=4, label="single head (best-case $c^*$)")
    axA.fill_between(betas, single_ci[0], single_ci[1], color="tab:red", alpha=0.15)
    axA.plot(betas, two, "s-", color="tab:blue", lw=2, ms=4, label="two heads (matched $c$)")
    axA.fill_between(betas, two_ci[0], two_ci[1], color="tab:blue", alpha=0.15)
    axA.plot(betas, np.maximum(ideal, 1e-16), "^--", color="tab:green", lw=1.5, ms=4,
             label="idealized two-head (Eq 19–21)")
    cent = ver["two_floor_headline"]
    axA.axhline(cent, color="tab:blue", ls=":", lw=1)
    axA.annotate("centering floor $O(1/N)$", (betas[0], cent), fontsize=8, va="bottom",
                 color="tab:blue")
    axA.set_xscale("log")
    axA.set_yscale("log")
    axA.set_xlabel(r"score scale $\beta$ (inverse temperature)")
    axA.set_ylabel("normalized error vs one GD step")
    axA.set_title(r"A · single head fails, two heads recover (N=%d)" % d["config"]["N_headline"])
    axA.legend(fontsize=8, loc="lower left")

    # Panel B — floors + ratio vs N (asymptotic-only: two-head O(1/N))
    axB.plot(Ns, sf, "o-", color="tab:red", lw=2, ms=5, label="single-head floor")
    axB.plot(Ns, tf, "s-", color="tab:blue", lw=2, ms=5, label="two-head floor")
    axB.plot(Ns, tf[0] * Ns[0] / Ns, "k:", lw=1, label=r"$O(1/N)$ guide")
    axB.set_xscale("log")
    axB.set_yscale("log")
    axB.set_xlabel("context length $N$")
    axB.set_ylabel("best-case normalized error floor")
    axB.set_title("B · two-head advantage widens with $N$")
    axB.legend(fontsize=8, loc="lower left")
    for x, s, t in zip(Ns, sf, tf):
        axB.annotate(f"{s/t:.0f}×", (x, t), fontsize=7, ha="center", va="top", color="gray")

    fig.tight_layout()
    fig.savefig(f"{ART}/figures/h9-softmax-two-head.png", dpi=140, bbox_inches="tight")
    save_json({"beta": betas.tolist(), "single_err": single.tolist(), "two_err": two.tolist(),
               "ideal_rms": ideal.tolist(), "N": Ns.tolist(), "single_floor": sf.tolist(),
               "two_floor": tf.tolist(), "ratio": (sf / tf).tolist(),
               "verdict": ver},
              f"{ART}/figures/h9-softmax-two-head.data.json")
    print(f"saved -> {ART}/figures/h9-softmax-two-head.png")


if __name__ == "__main__":
    main()
