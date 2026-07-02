"""P2-2: regenerate the headline numbers FROM the released artifacts alone (no model,
no recompute of the network) — the reproduce-from-artifacts validator."""
from __future__ import annotations

import json
import numpy as np

from .utils import REPO_ROOT

STUDY = "eap-ig-faithfulness"
TASKS = ("ioi", "greater_than", "sva")
CANDIDATES = ("random", "eap", "eap_ig", "exact_patch")


def main() -> int:
    base = REPO_ROOT / "artifacts" / STUDY / "baseline"
    summary = json.loads((base / "summary.json").read_text())
    npz = np.load(base / "scores.npz")
    ok = True
    for m in CANDIDATES:
        ref_all = np.concatenate([npz[f"faith__{m}__{t}__ref"] for t in TASKS])
        recomputed = float(ref_all.mean())
        stored = summary["methods"][m]["metrics"]["faith_at_ref"]
        match = abs(recomputed - stored) < 1e-6
        ok = ok and match
        print(f"{m:12s} faith_at_ref stored={stored:.6f} from-artifacts={recomputed:.6f} "
              f"{'OK' if match else 'MISMATCH'}")
    # headline: eap_ig > eap margin from artifacts
    ig = np.concatenate([npz[f"faith__eap_ig__{t}__ref"] for t in TASKS]).mean()
    ep = np.concatenate([npz[f"faith__eap__{t}__ref"] for t in TASKS]).mean()
    print(f"\nHEADLINE (from artifacts): eap_ig - eap faith@ref{summary['ref_size']} = {ig - ep:+.4f}")
    print("REPRODUCE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
