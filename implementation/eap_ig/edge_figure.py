"""Edge-level EAP vs EAP-IG faithfulness curves (IOI + SVA) — the closed §7 divergence.

Run: PYTHONPATH=$PWD python3 -m implementation.eap_ig.edge_figure
"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import utils

ART = "artifacts/eap-ig-edge"


def main():
    os.makedirs(f"{ART}/figures", exist_ok=True)
    d = json.load(open(f"{ART}/summary.json"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, task, title in ((axes[0], "ioi", "A · IOI — EAP ≈ EAP-IG (small gap)"),
                            (axes[1], "sva", "B · SVA — EAP catastrophic, EAP-IG faithful")):
        cur = d["results"][task]["curves"]
        for method, color in (("eap", "tab:orange"), ("eap_ig", "tab:blue")):
            c = cur[method]
            ax.plot(c["n"], c["faith"], marker="o", ms=4, color=color,
                    label=("EAP-IG" if method == "eap_ig" else "EAP"))
        ax.axhline(0.85, color="gray", ls=":", lw=1, label="faithful (0.85)")
        ax.axhline(0.0, color="k", lw=0.5)
        ax.set_xlabel("greedy circuit size $n$ (edges)")
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=8, loc="upper left")
    axes[0].set_ylabel("normalized faithfulness")
    fig.tight_layout()
    fig.savefig(f"{ART}/figures/eap-ig-edge.png", dpi=140, bbox_inches="tight")
    utils.save_json(utils.REPO_ROOT / ART / "figures" / "eap-ig-edge.data.json",
                    {"ioi": d["results"]["ioi"]["curves"], "sva": d["results"]["sva"]["curves"],
                     "verdict": d["verdict"]})
    print(f"saved -> {ART}/figures/eap-ig-edge.png")


if __name__ == "__main__":
    main()
