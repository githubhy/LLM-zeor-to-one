"""B1 baseline: FastV vision-token pruning on SmolVLM-256M. Measures (H1) per-layer image-token
attention efficiency, and (H2/H3) accuracy vs prune-ratio for attention-ranked vs random pruning,
with the (H4) Eq-5 FLOP-reduction overlay. Ranking is cached per example (one attention forward)."""
from __future__ import annotations

import os
import numpy as np
import torch

from .core import FastVModel, synthetic_dataset, flop_reduction
from implementation.eap_ig.stats import wilson_ci
from implementation.eap_ig.utils import REPO_ROOT, save_json, save_npz, environment, git_commit

STUDY = "fastv-pruning"
K = 2                     # FastV headline: prune after layer 2
RS = (0.0, 0.3, 0.5, 0.7, 0.9)
DEVICE = os.environ.get("FASTV_DEVICE") or ("mps" if torch.backends.mps.is_available() else "cpu")


def main() -> None:
    M = FastVModel(device=DEVICE)
    ds = synthetic_dataset(n_per=4)          # 16 examples (4 colors x 4)
    n = len(ds)

    # H1: attention efficiency averaged over a few examples
    eff_img, eff_txt = [], []
    for ex in ds[:4]:
        ei, et, n_img = M.attention_efficiency(ex)
        eff_img.append(ei); eff_txt.append(et)
    eff_img = np.mean(eff_img, 0); eff_txt = np.mean(eff_txt, 0)

    # cache the layer-K ranking per example (one attention forward each)
    cache = [M.rank(ex, K) for ex in ds]

    # H2/H3: accuracy vs prune ratio, attn-ranked vs random
    results = {crit: {} for crit in ("attn", "random")}
    for crit in ("attn", "random"):
        for R in RS:
            correct = 0
            for (inp, ranked), ex in zip(cache, ds):
                r = ranked
                if crit == "random":
                    g = torch.Generator().manual_seed(0)
                    r = ranked[torch.randperm(len(ranked), generator=g)]
                n_prune = int(R * len(ranked))
                ans = M.answer(inp, r[:n_prune] if n_prune else None)
                correct += int(ans.startswith(ex.answer))
            acc, lo, hi = wilson_ci(correct, n)
            results[crit][R] = {"acc": acc, "ci95": [lo, hi], "correct": correct,
                                "flop_reduction": flop_reduction(K, R, n_img, inp["input_ids"].shape[1])}

    summary = {
        "study": STUDY, "model": "SmolVLM-256M-Instruct", "device": DEVICE, "K": K,
        "n_examples": n, "n_image_tokens": n_img, "n_total_tokens": inp["input_ids"].shape[1],
        "eval": "synthetic color-ID (ground-truth)",
        "attention_efficiency": {"image": eff_img.tolist(), "text": eff_txt.tolist(),
                                 "deep_ratio_txt_over_img_L20": float(eff_txt[20] / max(eff_img[20], 1e-9))},
        "methods": {crit: {"metrics": {"acc_at_R50": results[crit][0.5]["acc"],
                                       "acc_at_R90": results[crit][0.9]["acc"],
                                       "flop_at_R50": results[crit][0.5]["flop_reduction"]}}
                    for crit in results},
        "sweep": results,
    }
    base = REPO_ROOT / "artifacts" / STUDY
    save_json(base / "baseline" / "summary.json", summary)
    save_npz(base / "baseline" / "curves.npz",
             R=np.array(RS),
             acc_attn=np.array([results["attn"][R]["acc"] for R in RS]),
             acc_random=np.array([results["random"][R]["acc"] for R in RS]),
             flop=np.array([results["attn"][R]["flop_reduction"] for R in RS]),
             eff_img=eff_img, eff_txt=eff_txt)
    save_json(base / "study-manifest.json", {
        "study": STUDY, "environment": environment(), "git_commit": git_commit(),
        "iterations": [{"phase": 3, "note": "FastV attention-efficiency + prune-accuracy/FLOP curves",
                        "acc_attn": {R: results["attn"][R]["acc"] for R in RS},
                        "acc_random": {R: results["random"][R]["acc"] for R in RS}}]})
    print(f"n_img={n_img}/{inp['input_ids'].shape[1]}  deep txt/img attn ratio (L20)="
          f"{eff_txt[20]/max(eff_img[20],1e-9):.0f}x")
    print("R:            " + " ".join(f"{R:6.1f}" for R in RS))
    print("acc(attn):    " + " ".join(f"{results['attn'][R]['acc']:6.2f}" for R in RS))
    print("acc(random):  " + " ".join(f"{results['random'][R]['acc']:6.2f}" for R in RS))
    print("flop_reduc:   " + " ".join(f"{results['attn'][R]['flop_reduction']:6.2f}" for R in RS))


if __name__ == "__main__":
    main()
