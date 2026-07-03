"""Positional-shortcut robustness control (audit 2026-07-03, confound lens).

The baseline induction task uses a fixed block length, so the induction target sits at a
constant query->target offset; on that probe a content-based induction head and a
hypothetical fixed-offset positional-copy head are attribution-indistinguishable. Here we
re-run EAP-IG head recovery on a JITTERED task (per-example block length ~ U[15,35), offset
varies per example) against the SAME Olsson oracle. If the induction heads are still
recovered at the same AUROC, the recovery is not a fixed-offset artifact.

Run: PYTHONPATH=$PWD HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
     python3 -m implementation.induction_discovery.robustness --device mps
"""
from __future__ import annotations

import argparse
import numpy as np
from scipy import stats as ss

from implementation.eap_ig.config import ModelConfig, AttrConfig
from implementation.eap_ig.model import Model
from implementation.eap_ig.attribution import score_nodes
from implementation.eap_ig import utils
from implementation.induction_discovery import oracle as O
from implementation.induction_discovery import task as T
from implementation.induction_discovery.discover import head_abs_scores, _auroc
from implementation.induction_discovery.run import Config

STUDY = "induction-discovery"


def _recovery(scores, prefix, oset):
    mh = head_abs_scores(scores)
    keys = [k for k in mh if k in prefix]
    sp = ss.spearmanr([mh[k] for k in keys], [prefix[k] for k in keys]).statistic
    return {"auroc": _auroc(mh, set(oset)), "spearman_vs_oracle": float(sp)}


def main(cfg: Config, jitter=(15, 35)):
    utils.set_determinism(0)
    orc = O.compute_oracle(cfg)
    prefix, oset = orc["prefix"], orc["induction_set"]
    M = Model(ModelConfig(name=cfg.model_name, device=cfg.device, dtype=cfg.dtype))
    out = {"fixed": [], "jitter": []}
    for seed in cfg.task_seeds:
        for kind, jit in (("fixed", None), ("jitter", jitter)):
            b = T.build_induction(M.tok, n_examples=cfg.task_n_examples, seed=seed,
                                  block_len=cfg.block_len, id_lo=cfg.id_lo, id_hi=cfg.id_hi,
                                  jitter=jit).to(cfg.device)
            s = score_nodes(M, b, AttrConfig(method="eap_ig", m_ig=cfg.m_ig))
            out[kind].append(_recovery(s, prefix, oset))
    res = {}
    for kind in ("fixed", "jitter"):
        au = [r["auroc"] for r in out[kind]]
        sp = [r["spearman_vs_oracle"] for r in out[kind]]
        res[kind] = {"auroc_mean": float(np.mean(au)), "auroc_per_seed": au,
                     "spearman_mean": float(np.mean(sp))}
    delta = res["jitter"]["auroc_mean"] - res["fixed"]["auroc_mean"]
    res["auroc_delta_jitter_minus_fixed"] = float(delta)
    res["oracle_set"] = oset
    res["jitter"]["range"] = list(jitter)
    print(f"EAP-IG recovery AUROC — fixed {res['fixed']['auroc_mean']:.3f} "
          f"vs jitter{jitter} {res['jitter']['auroc_mean']:.3f} (Δ={delta:+.3f})")
    print(f"  spearman_vs_oracle — fixed {res['fixed']['spearman_mean']:.3f} "
          f"vs jitter {res['jitter']['spearman_mean']:.3f}")
    utils.save_json(utils.REPO_ROOT / "artifacts" / STUDY / "robustness" / "positional.json", res)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu")
    a = ap.parse_args()
    main(Config(device=a.device))
