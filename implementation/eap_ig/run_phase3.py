"""Phase 3 → G2 baseline: faithfulness curves for all 4 candidates across 3 tasks x seeds,
with bootstrap CIs, paired-seed significance (P0-2), Wilson rate metrics (P0-4), cost
profiling (P1-4), a uniform metric key-set (P2-1), env pinning (P1-3), and raw .npz (P2-2)."""
from __future__ import annotations

import time
import numpy as np
import torch

from .config import ModelConfig, TaskConfig, AttrConfig
from .model import Model
from .tasks import build_task
from .attribution import score_nodes
from .faithfulness import baselines, faith_curve
from .registry import CANDIDATES, METRIC_KEYS
from . import stats as S
from . import manifest, utils

STUDY = "eap-ig-faithfulness"
TASKS = ("ioi", "greater_than", "sva")
SEEDS = (0, 1, 2)
SIZES = (3, 5, 10, 20, 40, 80, 157)
REF = 20
N_EX = 40
OP_COUNT = {"random": {"fwd": 0, "bwd": 0}, "eap": {"fwd": 2, "bwd": 1},
            "eap_ig": {"fwd": 6, "bwd": 5}, "exact_patch": {"fwd": 157, "bwd": 0}}
ASYMPTOTIC = {"random": "O(1)", "eap": "O(1) passes (2 fwd + 1 bwd)",
              "eap_ig": "O(m) passes (m=5)", "exact_patch": "O(nodes) passes (=157)"}


def _score(M, batch, method, seed):
    return score_nodes(M, batch, AttrConfig(method=method, m_ig=5, seed=seed))


def main() -> None:
    utils.set_determinism(0)
    M = Model(ModelConfig(name="gpt2", device="cpu", dtype="float32"))

    # pooled[method][task][size] = list of per-example faith across seeds
    pooled = {m: {t: {n: [] for n in SIZES} for t in TASKS} for m in CANDIDATES}
    corr = {m: [] for m in CANDIDATES}          # per-(task,seed) pearson vs exact
    for task in TASKS:
        for seed in SEEDS:
            batch = build_task(M.tok, TaskConfig(task=task, n_examples=N_EX, seed=seed)).to("cpu")
            b, bp = baselines(M, batch)
            scores = {m: _score(M, batch, m, seed) for m in CANDIDATES}
            for m in CANDIDATES:
                fc = faith_curve(M, batch, scores[m], list(SIZES), b, bp)
                for n in SIZES:
                    pooled[m][task][n].extend(fc[n].tolist())
                corr[m].append(S.correlate(scores[m], scores["exact_patch"])["pearson_r"])

    # ---- per-method uniform metrics (P2-1) + per-task detail ----
    methods_out = {}
    npz = {}
    for m in CANDIDATES:
        per_task = {}
        auc_list, ref_all, rec_all = [], [], []
        for task in TASKS:
            ref_vals = np.array(pooled[m][task][REF])
            auc = float(np.mean([np.mean(pooled[m][task][n]) for n in SIZES]))
            mean_ref, lo, hi = S.bootstrap_ci(ref_vals, seed=0)
            rate, rlo, rhi = S.wilson_ci(int((ref_vals >= 0.85).sum()), len(ref_vals))
            per_task[task] = {"auc": auc, "faith_at_ref_mean": mean_ref,
                              "faith_at_ref_ci95": [lo, hi], "recovery_rate": rate,
                              "recovery_ci95": [rlo, rhi]}
            auc_list.append(auc); ref_all.extend(ref_vals.tolist())
            npz[f"faith__{m}__{task}__ref"] = ref_vals
        ref_all = np.array(ref_all)
        methods_out[m] = {
            "metrics": {
                "auc_faithfulness": float(np.mean(auc_list)),
                "faith_at_ref": float(ref_all.mean()),
                "faith_at_ref_std": float(ref_all.std()),
                "recovery_rate": float((ref_all >= 0.85).mean()),
                "corr_to_exact_pearson": float(np.mean(corr[m])),
            },
            "per_task": per_task,
        }

    # ---- pairwise paired significance (P0-2): eap_ig vs eap, per task + overall ----
    pairwise = {}
    for task in TASKS:
        a = np.array(pooled["eap_ig"][task][REF]); b_ = np.array(pooled["eap"][task][REF])
        pairwise[f"eap_ig_vs_eap__{task}"] = S.paired_test(a, b_)
    a = np.concatenate([np.array(pooled["eap_ig"][t][REF]) for t in TASKS])
    b_ = np.concatenate([np.array(pooled["eap"][t][REF]) for t in TASKS])
    pairwise["eap_ig_vs_eap__overall"] = S.paired_test(a, b_)

    # ---- rate metrics (P0-4): recovery@0.85 with Wilson + error-event framing ----
    rate_metrics = []
    for m in CANDIDATES:
        vals = np.concatenate([np.array(pooled[m][t][REF]) for t in TASKS])
        succ = int((vals >= 0.85).sum()); tot = len(vals)
        rate, lo, hi = S.wilson_ci(succ, tot)
        rate_metrics.append({
            "name": f"recovery@0.85__{m}__ref{REF}", "error_count": tot - succ,
            "total_trials": tot, "stop_reason": "fixed_n", "ci_method": "wilson",
            "rate": rate, "ci95": [lo, hi],
        })

    # ---- cost profiling (P1-4): timed scoring, 2 sizes for measured_scaling ----
    cost = []
    for m in CANDIDATES:
        times = {}
        for nex in (20, 40):
            batch = build_task(M.tok, TaskConfig(task="ioi", n_examples=nex, seed=0)).to("cpu")
            reps = []
            for _ in range(3):
                t0 = time.perf_counter(); _score(M, batch, m, 0); reps.append(time.perf_counter() - t0)
            times[nex] = reps
        r40 = sorted(times[40])
        cost.append({
            "method": m, "repeats": 3,
            "percentiles": {"p50": float(np.median(r40)), "p90": float(np.quantile(r40, 0.9))},
            "op_count": OP_COUNT[m], "asymptotic_claim": ASYMPTOTIC[m],
            "measured_scaling": {"n20_p50": float(np.median(times[20])),
                                 "n40_p50": float(np.median(times[40])),
                                 "ratio": float(np.median(times[40]) / max(np.median(times[20]), 1e-9))},
        })

    summary = {
        "study": STUDY, "tasks": list(TASKS), "seeds": list(SEEDS), "sizes": list(SIZES),
        "ref_size": REF, "n_examples_per_seed": N_EX, "metric_keys": list(METRIC_KEYS),
        "methods": methods_out, "pairwise": pairwise, "rate_metrics": rate_metrics, "cost": cost,
    }
    base = utils.REPO_ROOT / "artifacts" / STUDY / "baseline"
    utils.save_json(base / "summary.json", summary)
    utils.save_npz(base / "scores.npz", **npz)

    m = manifest.ensure_env(manifest.load(STUDY))
    manifest.add_iteration(m, 3, "baseline: 4 candidates x 3 tasks x 3 seeds",
                           faith_at_ref={k: methods_out[k]["metrics"]["faith_at_ref"] for k in CANDIDATES},
                           eap_ig_vs_eap_p=pairwise["eap_ig_vs_eap__overall"]["p_value"])
    manifest.save(STUDY, m)
    print("faith_at_ref:", {k: round(methods_out[k]["metrics"]["faith_at_ref"], 3) for k in CANDIDATES})
    print("eap_ig>eap overall p=%.2e effect=%.2f" % (
        pairwise["eap_ig_vs_eap__overall"]["p_value"], pairwise["eap_ig_vs_eap__overall"]["effect_size"]))


if __name__ == "__main__":
    main()
