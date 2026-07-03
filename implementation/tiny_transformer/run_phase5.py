"""Phase 5 — int8/int4 quantization circuit-survival study (Gate G4).

Post-training weight quantization (per-tensor + per-channel) of the trained toy
models vs fp32; tests whether the induction circuit survives — induction accuracy,
induction attention score, and OV copy-diagonal — with a float-vs-low-bit knee
table + CIs across the 5 seeds. Checks weight saturation.

Usage: python run_phase5.py
"""
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "implementation"))

from tiny_transformer import analysis as A                 # noqa: E402
from tiny_transformer import circuits as C                 # noqa: E402
from tiny_transformer.model import induction_accuracy, head_attention_scores  # noqa: E402
from tiny_transformer.utils import bootstrap_ci, save_json  # noqa: E402

ART = os.path.join(REPO, "artifacts", "induction-tiny", "phase5")

# quantize weight matrices (W_*), leave LayerNorm + biases (standard PTQ).
WKEYS = ("W_E", "W_pos", "W_Q", "W_K", "W_V", "W_O", "W_U")
SCHEMES = [("fp32", None, False), ("int8_pertensor", 8, False),
           ("int8_perchannel", 8, True), ("int4_pertensor", 4, False),
           ("int4_perchannel", 4, True)]


def quantize_tensor(W, bits, per_channel):
    qmax = 2 ** (bits - 1) - 1
    if per_channel and W.dim() > 1:
        dims = tuple(range(1, W.dim()))
        scale = W.abs().amax(dim=dims, keepdim=True) / qmax
    else:
        scale = W.abs().max() / qmax
    scale = scale.clamp(min=1e-12)
    q = torch.round(W / scale).clamp(-qmax - 1, qmax) * scale
    sat = float((torch.round(W / scale).abs() >= qmax).float().mean())
    return q, sat


def quantized_sd(sd, bits, per_channel):
    out, sats = {}, []
    for k, v in sd.items():
        if any(w in k for w in WKEYS) and v.dtype.is_floating_point:
            q, sat = quantize_tensor(v, bits, per_channel)
            out[k] = q; sats.append(sat)
        else:
            out[k] = v
    return out, (float(np.mean(sats)) if sats else 0.0)


def metrics(model, batch):
    toks, tgt, ind, ap = batch
    c, n = induction_accuracy(model, toks, tgt, ind)
    prev, indm = head_attention_scores(model, toks, ind, ap)
    census = A.role_census(model, batch)
    sets = A.identify_head_sets(model, census)
    cm = A.circuit_match(model, sets)
    return dict(ind_acc=c / max(1, n), induction_score=float(indm.max()),
                copy_diag=cm["copy_diag_induction_set"]["frac_top1_self"])


def main():
    os.makedirs(ART, exist_ok=True)
    torch.set_num_threads(6)
    seeds = range(5)
    batch = A.eval_batch()
    per_scheme = {name: {"ind_acc": [], "induction_score": [], "copy_diag": [],
                         "saturation": []} for name, _, _ in SCHEMES}
    for seed in seeds:
        base = A.load_model(2, seed)
        sd = base.state_dict()
        for name, bits, pc in SCHEMES:
            m = A.load_model(2, seed)
            if bits is not None:
                qsd, sat = quantized_sd(sd, bits, pc)
                m.load_state_dict(qsd)
            else:
                sat = 0.0
            mt = metrics(m, batch)
            for k in ("ind_acc", "induction_score", "copy_diag"):
                per_scheme[name][k].append(mt[k])
            per_scheme[name]["saturation"].append(sat)

    knee = {}
    for name, _, _ in SCHEMES:
        d = per_scheme[name]
        knee[name] = dict(
            ind_acc=bootstrap_ci(d["ind_acc"]),
            induction_score=bootstrap_ci(d["induction_score"]),
            copy_diag=bootstrap_ci(d["copy_diag"]),
            mean_saturation=float(np.mean(d["saturation"])))
    fp = np.mean(per_scheme["fp32"]["ind_acc"])
    survives = {name: bool(np.mean(per_scheme[name]["ind_acc"]) > 0.9 * fp)
                for name, _, _ in SCHEMES}
    summary = dict(n_seeds=5, knee_table=knee, circuit_survives=survives,
                   verdict="PASS" if survives["int8_perchannel"] else "SEE-KNEE")
    save_json(summary, os.path.join(ART, "phase5_summary.json"))
    print("PHASE5 knee table (ind_acc / induction_score / copy_diag / saturation):")
    for name, _, _ in SCHEMES:
        k = knee[name]
        print(f"  {name:16s} acc {k['ind_acc'][0]:.3f} "
              f"[{k['ind_acc'][1]:.3f},{k['ind_acc'][2]:.3f}] | "
              f"ind_score {k['induction_score'][0]:.3f} | copy {k['copy_diag'][0]:.3f} | "
              f"sat {k['mean_saturation']:.3f} | survives={survives[name]}")


if __name__ == "__main__":
    main()
