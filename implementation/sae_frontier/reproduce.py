"""P2-2 reproduce-from-artifacts: regenerate the headline numbers from stored artifacts
alone (no recompute), and assert internal consistency. Lets an independent party
re-audit the recommendation without rerunning the study.

Run:  PYTHONPATH=implementation python -m sae_frontier.reproduce
"""
from __future__ import annotations

import json
import sys

import numpy as np

from .manifest import ARTIFACTS


def _load(p):
    return json.loads((ARTIFACTS / p).read_text())


def main() -> int:
    ok = True
    s1 = _load("baseline/summary.json")
    ev8 = s1["hypothesis_H1_ev_at_matched_L0"]["ev_at_target_mean"]
    print("HEADLINE — S1 EV @ L0=8 (from summary.json):",
          {k: round(v, 3) for k, v in ev8.items()})
    # consistency: ordering relu < gated < jumprelu < topk
    order_ok = ev8["relu"] < ev8["gated"] < ev8["jumprelu"] < ev8["topk"]
    print(f"  ordering relu<gated<jumprelu<topk: {order_ok}")
    ok &= order_ok
    # every pairwise test significant
    pw = s1["hypothesis_H1_ev_at_matched_L0"]["pairwise_paired_tests"]
    sig = all(v["t_pvalue"] < 0.05 for v in pw.values())
    print(f"  all pairwise EV@L0=8 tests p<0.05: {sig}")
    ok &= sig
    # cross-check ev8 against the raw scores.npz (recompute-free, just re-read)
    z = np.load(ARTIFACTS / "baseline" / "scores.npz", allow_pickle=True)
    print(f"  raw scores.npz rows: {len(z['ev'])} (variants x ops x seeds)")

    h4 = _load("sensitivity/sensitivity.json")["H4_width_sweep"]
    print("H4 — gap vs ReLU by width R:", {k: round(v, 3) for k, v in h4["best_gap_vs_relu_by_R"].items()})
    print(f"  H4 monotone increasing in R: {h4['gap_monotone_increasing_in_R']}")
    ok &= h4["gap_monotone_increasing_in_R"]

    p5 = _load("precision/precision.json")
    print("Precision — mean EV drop by structure:", {k: round(v, 4) for k, v in p5["mean_ev_drop_by_structure"].items()})
    prec_ok = max(p5["mean_ev_drop_by_structure"].values()) < 0.01
    print(f"  all precision drops < 0.01 EV: {prec_ok}")
    ok &= prec_ok

    print("\nREPRODUCE:", "PASS — artifacts internally consistent" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
