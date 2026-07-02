"""Phase 5 → G4 reduced precision: recompute EAP / EAP-IG attribution + faithfulness under
fp16 and bf16 forward/backward (>=2 realisation structures, P2-3), with saturation detection
(nan/inf in scores or faith). Attribution uses gradients, so it is the precision-fragile path."""
from __future__ import annotations

import numpy as np

from .config import ModelConfig, TaskConfig, AttrConfig
from .model import Model
from .tasks import build_task
from .attribution import score_nodes
from .faithfulness import baselines, faith_curve
from . import manifest, utils

STUDY = "eap-ig-faithfulness"
TASKS = ("ioi", "greater_than", "sva")
REF = 20
N_EX = 32
STRUCTURES = ("float16", "bfloat16")


def _faith_at_ref(M, method):
    out = {}
    for task in TASKS:
        batch = build_task(M.tok, TaskConfig(task=task, n_examples=N_EX, seed=0)).to(M.cfg.device)
        b, bp = baselines(M, batch)
        sc = score_nodes(M, batch, AttrConfig(method=method, m_ig=5, seed=0))
        fc = faith_curve(M, batch, sc, [REF], b, bp)[REF]
        out[task] = {"faith": float(fc.mean()),
                     "score_nan": bool(np.isnan(list(sc.values())).any()),
                     "score_inf": bool(np.isinf(list(sc.values())).any())}
    return out


def main() -> None:
    utils.set_determinism(0)
    # fp32 reference
    M32 = Model(ModelConfig(name="gpt2", device="cpu", dtype="float32"))
    ref32 = {m: _faith_at_ref(M32, m) for m in ("eap", "eap_ig")}

    results = {"structures": list(STRUCTURES), "reference_dtype": "float32",
               "reference_faith": {m: {t: ref32[m][t]["faith"] for t in TASKS} for m in ref32},
               "by_structure": {}}
    npz = {}
    for t in TASKS:
        for m in ("eap", "eap_ig"):
            npz[f"faith32__{m}__{t}"] = np.array([ref32[m][t]["faith"]])

    for dtype in STRUCTURES:
        entry = {"saturation": False, "note": "", "methods": {}}
        try:
            Md = Model(ModelConfig(name="gpt2", device="cpu", dtype=dtype))
            for m in ("eap", "eap_ig"):
                r = _faith_at_ref(Md, m)
                sat = any(v["score_nan"] or v["score_inf"] for v in r.values())
                entry["saturation"] = entry["saturation"] or sat
                drift = {t: r[t]["faith"] - ref32[m][t]["faith"] for t in TASKS}
                entry["methods"][m] = {"faith": {t: r[t]["faith"] for t in TASKS},
                                       "drift_vs_fp32": drift,
                                       "max_abs_drift": float(max(abs(d) for d in drift.values()))}
                for t in TASKS:
                    npz[f"faith_{dtype}__{m}__{t}"] = np.array([r[t]["faith"]])
        except Exception as e:               # a dtype that overflows / is unsupported = saturation
            entry["saturation"] = True
            entry["note"] = f"{type(e).__name__}: {e}"
        results["by_structure"][dtype] = entry

    art = utils.REPO_ROOT / "artifacts" / STUDY / "precision"
    utils.save_json(art / "precision.json", results)
    utils.save_npz(art / "precision_sweep.npz", **npz)

    m = manifest.ensure_env(manifest.load(STUDY))
    manifest.add_iteration(m, 5, "precision: fp16 / bf16 attribution stability",
                           saturation={d: results["by_structure"][d]["saturation"] for d in STRUCTURES})
    manifest.save(STUDY, m)
    print("precision saturation:", {d: results["by_structure"][d]["saturation"] for d in STRUCTURES})
    for d in STRUCTURES:
        e = results["by_structure"][d]
        if e["methods"]:
            print(f"  {d}: max|drift| eap_ig =",
                  round(e["methods"]["eap_ig"]["max_abs_drift"], 4))


if __name__ == "__main__":
    main()
