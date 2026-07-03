"""Render the H15 figure from persisted artifacts (regenerable, deterministic).

Panel A: circuit-faithfulness vs size (4 candidates, mean + bootstrap 95% CI band).
Panel B: per-head recovery scatter — oracle prefix-matching score (x) vs EAP-IG mean|score|
         (y, normalized), oracle induction heads highlighted + labeled.

Run: PYTHONPATH=$PWD python3 -m implementation.induction_discovery.figure
"""
from __future__ import annotations

import json

import numpy as np

from implementation.eap_ig import stats as S, utils

STUDY = "induction-discovery"
SIZES = (3, 5, 10, 20, 40, 80, 157)
COLORS = {"random": "#9aa0a6", "eap": "#e8710a", "eap_ig": "#1a73e8", "exact_patch": "#137333"}
LABELS = {"random": "random (floor)", "eap": "EAP", "eap_ig": "EAP-IG (m=5)", "exact_patch": "exact patching"}


def _hl(h: str) -> str:                      # "a5.h5" -> "5.5"
    return h[1:].replace(".h", ".")


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    base = utils.REPO_ROOT / "artifacts" / STUDY / "baseline"
    summ = json.load(open(base / "summary.json"))
    npz = np.load(base / "faith.npz")

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.5, 5.0))

    # ---- Panel A: faithfulness curves ----
    panelA = {}
    for m in ("random", "eap", "eap_ig", "exact_patch"):
        means, los, his = [], [], []
        for n in SIZES:
            v = npz[f"faith__{m}__{n}"]
            mu, lo, hi = S.bootstrap_ci(v, seed=0)
            means.append(mu); los.append(lo); his.append(hi)
        panelA[m] = {"size": list(SIZES), "mean": means, "lo": los, "hi": his}
        axA.plot(SIZES, means, "-o", color=COLORS[m], label=LABELS[m], lw=2, ms=4)
        axA.fill_between(SIZES, los, his, color=COLORS[m], alpha=0.15)
    axA.set_xscale("log"); axA.set_xticks(SIZES); axA.set_xticklabels(SIZES)
    axA.axhline(1.0, color="k", lw=0.6, ls=":"); axA.axhline(0.0, color="k", lw=0.6, ls=":")
    axA.set_xlabel("circuit size (# nodes)"); axA.set_ylabel("normalized faithfulness")
    axA.set_title("A · Circuit faithfulness vs size (GPT-2-small induction)")
    axA.legend(loc="lower right", fontsize=9); axA.grid(alpha=0.25)

    # ---- Panel B: head-recovery scatter ----
    prefix = summ["oracle"]["prefix"]
    oset = set(summ["oracle"]["induction_set"])
    eig = summ["head_scores_meanabs"]["eap_ig"]
    mx = max(eig.values()) or 1.0
    xs_o, ys_o, xs_b, ys_b, lab = [], [], [], [], []
    for h, ov in prefix.items():
        y = eig.get(h, 0.0) / mx
        if h in oset:
            xs_o.append(ov); ys_o.append(y); lab.append((ov, y, _hl(h)))
        else:
            xs_b.append(ov); ys_b.append(y)
    axB.scatter(xs_b, ys_b, s=18, color="#c0c4c9", alpha=0.7, label="other heads")
    axB.scatter(xs_o, ys_o, s=70, color="#d93025", edgecolor="k", lw=0.5, zorder=3,
                label="oracle induction heads")
    for x, y, t in lab:
        axB.annotate(t, (x, y), textcoords="offset points", xytext=(5, 3), fontsize=9, weight="bold")
    aur_eig = summ["methods"]["eap_ig"]["auroc_vs_oracle_set"]["mean"]
    aur_eap = summ["methods"]["eap"]["auroc_vs_oracle_set"]["mean"]
    sp = summ["methods"]["eap_ig"]["spearman_vs_exact_heads"]["mean"]
    axB.text(0.03, 0.97, f"AUROC  EAP-IG={aur_eig:.2f}  EAP={aur_eap:.2f}\n"
                         f"ρ(EAP-IG,exact)={sp:.2f}",
             transform=axB.transAxes, va="top", fontsize=9,
             bbox=dict(boxstyle="round", fc="white", ec="#ccc"))
    axB.set_xlabel("oracle prefix-matching score (Olsson 2022)")
    axB.set_ylabel("EAP-IG attribution |score| (normalized)")
    axB.set_title("B · Automated discovery recovers the induction heads")
    axB.legend(loc="lower right", fontsize=9); axB.grid(alpha=0.25)

    fig.tight_layout()
    outdir = base.parent / "figures"
    outdir.mkdir(parents=True, exist_ok=True)
    png = outdir / "h15-recovery.png"
    fig.savefig(png, dpi=150)
    # persist backing data (workflow.md diagram rule)
    json.dump({"panelA": panelA,
               "panelB": {"oracle_heads": [{"head": t, "prefix": x, "eap_ig_norm": y} for x, y, t in lab],
                          "auroc_eap_ig": aur_eig, "auroc_eap": aur_eap, "spearman_eap_ig_exact": sp}},
              open(outdir / "h15-recovery.data.json", "w"), indent=2)
    print(f"saved {png}")


if __name__ == "__main__":
    main()
