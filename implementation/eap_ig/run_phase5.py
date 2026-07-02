"""Phase 5 → G4 reduced precision (P2-3): two realisation structures over the attribution
artifact — storing/transmitting the edge scores at reduced precision, then rebuilding circuits:
  1. bf16_scores — attribution scores quantised to bfloat16 (8-bit exp, 7-bit mantissa)
  2. fp16_scores — attribution scores quantised to float16 (5-bit exp, 10-bit mantissa)
Reports faith drift vs fp32 + saturation (nan/inf) per structure. This is the realistic reduced-
precision realisation of the attribution output (caching/serialising scores); reduced-precision
*compute* (bf16/fp16 forward+backward) is deferred — MPS lacks support for some attribution ops and
fp16 matmul is emulated-slow on CPU (documented limitation, §10/§11)."""
from __future__ import annotations

import os
import numpy as np
import torch

from .config import ModelConfig, TaskConfig, AttrConfig
from .model import Model
from .tasks import build_task
from .attribution import score_nodes
from .faithfulness import baselines, faith_curve
from . import manifest, utils

STUDY = "eap-ig-faithfulness"
TASKS = ("ioi", "greater_than", "sva")
REF = 20
N_EX = 24
STRUCTURES = ("bf16_scores", "fp16_scores")
_DT = {"bf16_scores": torch.bfloat16, "fp16_scores": torch.float16}
DEVICE = os.environ.get("EAP_DEVICE") or "cpu"


def _quant(v: float, dtype) -> float:
    return float(torch.tensor(float(v), dtype=torch.float32).to(dtype).float())


def _faith(M, method, quant_dtype=None):
    out = {}
    for task in TASKS:
        batch = build_task(M.tok, TaskConfig(task=task, n_examples=N_EX, seed=0)).to(M.cfg.device)
        b, bp = baselines(M, batch)
        sc = score_nodes(M, batch, AttrConfig(method=method, m_ig=5, seed=0))
        if quant_dtype is not None:
            sc = {k: _quant(v, quant_dtype) for k, v in sc.items()}
        vals = np.array(list(sc.values()), dtype=float)
        fc = faith_curve(M, batch, sc, [REF], b, bp)[REF]
        out[task] = {"faith": float(fc.mean()),
                     "score_nan": bool(np.isnan(vals).any()),
                     "score_inf": bool(np.isinf(vals).any())}
    return out


def main() -> None:
    utils.set_determinism(0)
    print(f"precision study on device={DEVICE}")
    M = Model(ModelConfig(name="gpt2", device=DEVICE, dtype="float32"))
    ref = {m: _faith(M, m) for m in ("eap", "eap_ig")}

    results = {"structures": list(STRUCTURES), "reference_dtype": "float32",
               "reference_faith": {m: {t: ref[m][t]["faith"] for t in TASKS} for m in ref},
               "by_structure": {}}
    npz = {}
    for t in TASKS:
        for m in ("eap", "eap_ig"):
            npz[f"faith32__{m}__{t}"] = np.array([ref[m][t]["faith"]])

    for name in STRUCTURES:
        entry = {"saturation": False, "methods": {}}
        for m in ("eap", "eap_ig"):
            r = _faith(M, m, quant_dtype=_DT[name])
            sat = any(v["score_nan"] or v["score_inf"] for v in r.values())
            entry["saturation"] = entry["saturation"] or sat
            drift = {t: r[t]["faith"] - ref[m][t]["faith"] for t in TASKS}
            entry["methods"][m] = {"faith": {t: r[t]["faith"] for t in TASKS},
                                   "drift_vs_fp32": drift,
                                   "max_abs_drift": float(max(abs(d) for d in drift.values()))}
            for t in TASKS:
                npz[f"faith_{name}__{m}__{t}"] = np.array([r[t]["faith"]])
        results["by_structure"][name] = entry

    art = utils.REPO_ROOT / "artifacts" / STUDY / "precision"
    utils.save_json(art / "summary.json", results)          # P2-3 gate reads precision/summary.json
    utils.save_npz(art / "precision_sweep.npz", **npz)

    m = manifest.ensure_env(manifest.load(STUDY))
    manifest.add_iteration(m, 5, "precision: bf16/fp16 attribution-score storage",
                           saturation={d: results["by_structure"][d]["saturation"] for d in STRUCTURES},
                           max_drift={d: max(results["by_structure"][d]["methods"][mm]["max_abs_drift"]
                                             for mm in ("eap", "eap_ig")) for d in STRUCTURES})
    manifest.save(STUDY, m)
    for d in STRUCTURES:
        e = results["by_structure"][d]
        md = max(e["methods"][mm]["max_abs_drift"] for mm in ("eap", "eap_ig"))
        print(f"  {d}: saturation={e['saturation']} max|drift|={round(md,5)}")


if __name__ == "__main__":
    main()
