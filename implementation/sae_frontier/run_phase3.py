"""Phase 3: multi-seed fidelity–sparsity frontier on the synthetic-oracle substrate (S1).

Trains all four candidates across a sparsity sweep and >=5 paired seeds, aggregates with
95% t-CIs, runs pairwise paired-significance tests at matched L0 (P0-2), profiles runtime
(P1-4), and writes the G2 artifacts (summary.json, scores.npz, interactive frontier.html).

Run:  PYTHONPATH=implementation python -m sae_frontier.run_phase3
"""
from __future__ import annotations

import itertools
import json
import time
import warnings
from pathlib import Path

import numpy as np
import torch

from .experiment import SWEEPS, VARIANTS, train_eval
from .manifest import ARTIFACTS, append_phase
from .saes import build_sae
from .config import SAEConfig
from .synthetic import generate
from .config import SyntheticConfig
from . import stats as S

warnings.filterwarnings("ignore")

# S1 substrate + protocol
D_MODEL, N_FEATURES, EXPANSION = 32, 64, 4      # d_sae = 128 (2x the 64 true atoms)
FEATURE_PROB, N_SAMPLES, STEPS = 0.06, 6000, 1500
SEEDS = [0, 1, 2, 3, 4]                          # paired: same set for every candidate
TARGET_L0 = 8.0                                  # matched-L0 point for the H1 significance test


def runtime_profile() -> dict:
    """P1-4: forward-pass latency distribution + op count + asymptotic (O(d_sae)) cross-check."""
    x = torch.randn(512, D_MODEL)
    prof = {}
    for v in VARIANTS:
        sae = build_sae(SAEConfig(variant=v, d_model=D_MODEL, expansion=EXPANSION, seed=0, k=8))
        for _ in range(5):  # warmup
            sae.encode(x)
        ts = []
        for _ in range(30):
            t0 = time.perf_counter(); sae(x); ts.append((time.perf_counter() - t0) * 1e3)
        ts = np.array(ts)
        # asymptotic check: forward time at d_sae vs 2*d_sae (expect ~linear)
        big = build_sae(SAEConfig(variant=v, d_model=D_MODEL, expansion=2 * EXPANSION, seed=0, k=8))
        for _ in range(5):
            big.encode(x)
        tb = np.median([(lambda t0: (big(x), (time.perf_counter() - t0) * 1e3)[1])(time.perf_counter()) for _ in range(30)])
        prof[v] = {
            "ms_median": float(np.median(ts)), "ms_p10": float(np.percentile(ts, 10)),
            "ms_p90": float(np.percentile(ts, 90)), "repeats": 30,
            "op_count_multiplies_per_token": 2 * D_MODEL * (EXPANSION * D_MODEL),  # enc + dec
            "asymptotic_claim": "O(d_sae) forward",
            "measured_scaling_ratio_2x": float(tb / (np.median(ts) + 1e-9)),  # expect ~2
        }
    return prof


def main() -> None:
    rows: list[dict] = []
    # generate one dataset per seed (shared across candidates → paired design)
    datasets = {s: generate(SyntheticConfig(n_features=N_FEATURES, d_model=D_MODEL,
                                            feature_prob=FEATURE_PROB, n_samples=N_SAMPLES, seed=s))
                for s in SEEDS}
    for variant in VARIANTS:
        for op in SWEEPS[variant]:
            for seed in SEEDS:
                data = datasets[seed]
                rows.append(train_eval(variant, op, seed, data.x, data.true_features,
                                       D_MODEL, EXPANSION, STEPS))
        print(f"  done {variant}")

    # --- aggregate per (variant, operating point) ---
    agg = []
    for variant in VARIANTS:
        for i, op in enumerate(SWEEPS[variant]):
            sub = [r for r in rows if r["variant"] == variant and r["op"] == op]
            entry = {"variant": variant, "op": op, "op_index": i}
            for metric in ("l0", "ev", "shrinkage", "mmcs", "frac_recovered", "n_dead"):
                vals = [r[metric] for r in sub if metric in r]
                if vals:
                    entry[metric] = S.aggregate(vals)
            agg.append(entry)

    # --- H1: pairwise paired significance of EV at matched L0 (P0-2) ---
    ev_at_target = {}  # variant -> [per-seed interpolated EV at TARGET_L0]
    for variant in VARIANTS:
        per_seed = []
        for seed in SEEDS:
            pts = [(r["l0"], r["ev"]) for r in rows if r["variant"] == variant and r["seed"] == seed]
            per_seed.append(S.interp_at(pts, TARGET_L0))
        ev_at_target[variant] = per_seed
    pairwise = {}
    for a, b in itertools.combinations(VARIANTS, 2):
        pairwise[f"{a}_vs_{b}"] = {"metric": "ev@L0=%g" % TARGET_L0, **S.paired_test(ev_at_target[a], ev_at_target[b])}

    # --- H3: feature recovery (mmcs) at matched L0, paired ---
    mmcs_at_target = {}
    for variant in VARIANTS:
        per_seed = []
        for seed in SEEDS:
            pts = [(r["l0"], r.get("mmcs", float("nan"))) for r in rows if r["variant"] == variant and r["seed"] == seed]
            per_seed.append(S.interp_at(pts, TARGET_L0))
        mmcs_at_target[variant] = per_seed
    mmcs_pairwise = {}
    for a, b in itertools.combinations(VARIANTS, 2):
        mmcs_pairwise[f"{a}_vs_{b}"] = {"metric": "mmcs@L0=%g" % TARGET_L0, **S.paired_test(mmcs_at_target[a], mmcs_at_target[b])}

    prof = runtime_profile()

    # --- persist ---
    base = ARTIFACTS / "baseline"
    base.mkdir(parents=True, exist_ok=True)
    methods = {v: [e for e in agg if e["variant"] == v] for v in VARIANTS}
    summary = {
        "substrate": "S1-synthetic-superposition",
        "protocol": {"d_model": D_MODEL, "n_features": N_FEATURES, "expansion": EXPANSION,
                     "d_sae": EXPANSION * D_MODEL, "feature_prob": FEATURE_PROB,
                     "n_samples": N_SAMPLES, "steps": STEPS, "seeds": SEEDS, "target_l0": TARGET_L0},
        "methods": methods,          # per-candidate aggregated frontier (mean/std/CI) — G2 shape
        "aggregated": agg,
        "hypothesis_H1_ev_at_matched_L0": {
            "ev_at_target_mean": {v: float(np.mean(ev_at_target[v])) for v in VARIANTS},
            "pairwise_paired_tests": pairwise,
        },
        "hypothesis_H3_feature_recovery": {
            "mmcs_at_target_mean": {v: float(np.mean(mmcs_at_target[v])) for v in VARIANTS},
            "pairwise_paired_tests": mmcs_pairwise,
        },
        "runtime_profile_P1_4": prof,
        "P0_4_rate_metrics": "n/a — all metrics are continuous (EV/L0/mmcs/shrinkage), no Bernoulli proportion",
        "seed_set_shared_across_candidates": True,   # paired design (P0-2)
    }
    (base / "summary.json").write_text(json.dumps(summary, indent=2))
    # long-form scores
    keys = ["l0", "ev", "shrinkage", "mmcs", "frac_recovered", "n_dead", "final_loss", "train_s"]
    np.savez(base / "scores.npz",
             variant=np.array([r["variant"] for r in rows]),
             seed=np.array([r["seed"] for r in rows]),
             op=np.array([json.dumps(r["op"]) for r in rows]),
             **{k: np.array([r.get(k, np.nan) for r in rows], float) for k in keys})
    _figure(agg, base / "frontier.html")

    append_phase(3, "baseline", {"gate": "G2", "substrate": "S1",
                                "artifacts": ["baseline/summary.json", "baseline/scores.npz", "baseline/frontier.html"],
                                "H1_ev_at_matched_L0_mean": summary["hypothesis_H1_ev_at_matched_L0"]["ev_at_target_mean"]})
    print("Phase 3 (S1) complete. EV@L0=%g:" % TARGET_L0,
          {v: round(np.mean(ev_at_target[v]), 3) for v in VARIANTS})


def _figure(agg, path: Path) -> None:
    import plotly.graph_objects as go
    fig = go.Figure()
    colors = {"relu": "#d62728", "gated": "#2ca02c", "topk": "#1f77b4", "jumprelu": "#9467bd"}
    for variant in VARIANTS:
        pts = sorted([e for e in agg if e["variant"] == variant], key=lambda e: e["l0"]["mean"])
        x = [e["l0"]["mean"] for e in pts]
        y = [e["ev"]["mean"] for e in pts]
        yerr = [e["ev"]["ci95_hi"] - e["ev"]["mean"] for e in pts]
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=variant,
                                 line=dict(color=colors[variant]),
                                 error_y=dict(type="data", array=yerr, visible=True),
                                 hovertemplate=f"{variant}<br>L0=%{{x:.1f}}<br>EV=%{{y:.3f}}<extra></extra>"))
    fig.update_layout(title="SAE fidelity–sparsity frontier (S1 synthetic-oracle, 5 seeds, 95% CI)",
                      xaxis_title="L0 (mean active features / token)",
                      yaxis_title="Explained variance (fidelity)", template="plotly_white")
    fig.write_html(str(path), include_plotlyjs="cdn")   # cdn keeps the artifact ~KB, not ~MB


if __name__ == "__main__":
    main()
