"""Phase 5: reduced-precision realisation of the SAEs (G4).

P2-3 design-of-experiments: sweep precision (bf16 / fp16 / int8) x quantization
structure (per-tensor vs per-channel scaling; weight-only) with saturation-aware
clipping, and quantify graceful degradation (EV drop vs fp32) per structure. SAE
inference is post-training quantization (PTQ) of the trained decoder/encoder weights.

Run:  PYTHONPATH=implementation python -m sae_frontier.run_phase5
"""
from __future__ import annotations

import copy
import json

import numpy as np
import torch

from .config import SAEConfig, SyntheticConfig, TrainConfig
from .experiment import VARIANTS
from .manifest import ARTIFACTS, append_phase
from .metrics import explained_variance
from .saes import build_sae
from .synthetic import generate
from .train import train_sae

warnings = __import__("warnings"); warnings.filterwarnings("ignore")

FP16_MAX = 65504.0
OP = {"relu": {"l1_coeff": 0.2}, "gated": {"l1_coeff": 0.2},
      "jumprelu": {"l1_coeff": 0.1}, "topk": {"k": 8}}  # matched ~L0=8 operating point


def _int8_quantize(w: torch.Tensor, per_channel: bool, pct: float = 99.9):
    """Saturation-aware symmetric RTN int8 quantize→dequantize. Returns (w_deq, n_clipped)."""
    if per_channel:  # scale per output row (dim 0)
        amax = torch.quantile(w.abs().reshape(w.shape[0], -1), pct / 100.0, dim=1).clamp_min(1e-8)
        scale = (amax / 127.0).reshape(-1, *([1] * (w.dim() - 1)))
    else:            # per-tensor
        amax = torch.quantile(w.abs().flatten(), pct / 100.0).clamp_min(1e-8)
        scale = amax / 127.0
    q = torch.round(w / scale)
    n_clipped = int((q.abs() > 127).sum().item())
    q = q.clamp(-127, 127)
    return q * scale, n_clipped


@torch.no_grad()
def eval_precision(sae, X, mode: str) -> dict:
    ref = build_sae(sae.cfg)
    ref.load_state_dict(sae.state_dict())
    sat = 0
    if mode == "fp32":
        pass
    elif mode in ("bf16", "fp16"):
        dt = torch.bfloat16 if mode == "bf16" else torch.float16
        for p in ref.parameters():
            if mode == "fp16":
                sat += int((p.abs() > FP16_MAX).sum().item())
            p.data = p.data.to(dt).to(torch.float32)   # simulate cast round-trip
        Xd = X.to(dt).to(torch.float32) if mode == "bf16" else X.clamp(-FP16_MAX, FP16_MAX)
        x_hat, _ = ref(Xd)
        return {"ev": explained_variance(X, x_hat), "saturation_events": sat}
    elif mode.startswith("int8"):
        per_channel = mode.endswith("per_channel")
        for name in ("W_enc", "W_dec"):
            w = getattr(ref, name).data
            wq, nc = _int8_quantize(w, per_channel)
            getattr(ref, name).data = wq
            sat += nc
    x_hat, _ = ref(X)
    return {"ev": explained_variance(X, x_hat), "saturation_events": sat}


def main():
    d = generate(SyntheticConfig(n_features=64, d_model=32, feature_prob=0.06, n_samples=6000, seed=0))
    modes = ["fp32", "bf16", "fp16", "int8_per_tensor", "int8_per_channel"]
    results = {}
    for v in VARIANTS:
        sae = build_sae(SAEConfig(variant=v, d_model=32, expansion=4, seed=0, **OP[v]))
        train_sae(sae, d.x, TrainConfig(steps=1500, seed=0))
        ref_ev = eval_precision(sae, d.x, "fp32")["ev"]
        results[v] = {}
        for m in modes:
            r = eval_precision(sae, d.x, m)
            r["ev_drop_vs_fp32"] = ref_ev - r["ev"]
            results[v][m] = r
        print(f"  {v}: " + " ".join(f"{m}={results[v][m]['ev']:.3f}" for m in modes))

    # graceful-degradation ranking: mean EV drop across variants per structure
    struct_drop = {m: float(np.mean([results[v][m]["ev_drop_vs_fp32"] for v in VARIANTS])) for m in modes}
    total_sat = {m: int(sum(results[v][m]["saturation_events"] for v in VARIANTS)) for m in modes}

    prec = ARTIFACTS / "precision"
    prec.mkdir(parents=True, exist_ok=True)
    summary = {
        "doe": "precision {bf16,fp16,int8} x structure {per-tensor, per-channel}; weight-only PTQ",
        "operating_point": OP, "modes": modes,
        "per_variant": results,
        "mean_ev_drop_by_structure": struct_drop,
        "saturation_events_by_structure": total_sat,
        "most_graceful": min(struct_drop, key=struct_drop.get),
        "least_graceful": max(struct_drop, key=struct_drop.get),
    }
    (prec / "precision.json").write_text(json.dumps(summary, indent=2))
    np.savez(prec / "precision_sweep.npz",
             mode=np.array([m for v in VARIANTS for m in modes]),
             variant=np.array([v for v in VARIANTS for m in modes]),
             ev=np.array([results[v][m]["ev"] for v in VARIANTS for m in modes], float),
             ev_drop=np.array([results[v][m]["ev_drop_vs_fp32"] for v in VARIANTS for m in modes], float))
    append_phase(5, "precision", {"gate": "G4", "artifacts": ["precision/precision.json", "precision/precision_sweep.npz"],
                                  "mean_ev_drop_by_structure": struct_drop, "saturation_events": total_sat})
    print("Phase 5 complete. mean EV drop by structure:", {m: round(x, 4) for m, x in struct_drop.items()})


if __name__ == "__main__":
    main()
