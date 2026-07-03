"""H15 baseline: automated circuit discovery of GPT-2-small induction heads.

Oracle (Olsson prefix-matching) -> ground-truth induction-head set; then 4 candidates
(random / eap / eap_ig / exact_patch) x seeds are scored on the minimal-pair induction
task and evaluated for head recovery (Spearman rho, AUROC, recovery@k), rank-consistency
with exact patching, and circuit faithfulness. Bootstrap CIs on every cell; paired
EAP-IG vs EAP test. Artifacts + manifest under artifacts/induction-discovery/.

Run:  PYTHONPATH=$PWD HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
      python3 -m implementation.induction_discovery.run [--device mps]
"""
from __future__ import annotations

import argparse
import dataclasses
import time
from dataclasses import dataclass, field

import numpy as np

from implementation.eap_ig.config import ModelConfig, AttrConfig
from implementation.eap_ig.model import Model
from implementation.eap_ig.attribution import score_nodes
from implementation.eap_ig.faithfulness import baselines, faith_curve
from implementation.eap_ig import stats as S
from implementation.eap_ig import utils
from implementation.induction_discovery import oracle as O
from implementation.induction_discovery import task as T
from implementation.induction_discovery.discover import recovery_metrics, head_abs_scores

STUDY = "induction-discovery"
CANDIDATES = ("random", "eap", "eap_ig", "exact_patch")
SIZES = (3, 5, 10, 20, 40, 80, 157)
REF = 20


@dataclass(frozen=True)
class Config:
    model_name: str = "gpt2"
    device: str = "cpu"
    dtype: str = "float32"
    # oracle (Olsson App. (3): 25 tokens x 4 repeats + BOS)
    oracle_seeds: tuple = (0, 1, 2, 3, 4)
    oracle_n_examples: int = 30
    block_len: int = 25
    n_repeats: int = 4
    id_lo: int = 1000          # exclude the most-common (low-id) subwords ...
    id_hi: int = 40000         # ... and the least-common (high-id) rare tokens
    oracle_threshold: float = 0.35   # pre-registered (decision 2026-07-03-01): captures the top-5 cluster,
                                     # which independently reproduces the study's Phase-4b {5.1,5.5,6.9,7.2,7.10};
                                     # headline metrics (Spearman rho, AUROC vs continuous score) are threshold-free
    # task
    task_seeds: tuple = (0, 1, 2, 3, 4)
    task_n_examples: int = 32
    m_ig: int = 5

    def to_dict(self):
        return dataclasses.asdict(self)


def _score(M, batch, method, seed, m_ig):
    return score_nodes(M, batch, AttrConfig(method=method, m_ig=m_ig, seed=seed))


def build_pairwise(auroc_ig, auroc_ep, fseed_ig, fseed_ep, fpool_ig, fpool_ep, corr_ig, corr_ep):
    """Paired EAP-IG vs EAP block. The faith test is reported at TWO units of analysis:
    seed-level (n = #seeds, the honest significance — circuit is fixed per seed) and pooled
    per-example (n = #seeds x #examples, pseudo-replicated — kept only as an effect-size
    descriptor, NOT a significance claim; bug/audit 2026-07-03-02). auroc/corr are already
    seed-level. Shared by main() and refresh_stats() so the two paths cannot drift."""
    return {
        "auroc__eap_ig_vs_eap": S.paired_test(auroc_ig, auroc_ep),
        "faith_ref_seedlevel__eap_ig_vs_eap": S.paired_test(fseed_ig, fseed_ep),
        "faith_ref_pooled__eap_ig_vs_eap": S.paired_test(fpool_ig, fpool_ep),
        "corr_exact__eap_ig_vs_eap": S.paired_test(corr_ig, corr_ep),
    }


def compute_verdict(aur, spe, faith_gap, faith_gap_p, rand_aur):
    """Pre-registered H15 rubric (decision 2026-07-03-01). Gates faithfulness on the
    SEED-LEVEL p (honest unit), not the pooled per-example p."""
    if abs(aur - rand_aur) < 0.1:
        return "INCONCLUSIVE"
    if aur >= 0.90 and spe >= 0.5 and (faith_gap >= 0 and faith_gap_p < 0.05):
        return "PASS"
    return "PARTIAL"


def main(cfg: Config) -> dict:
    utils.set_determinism(0)
    print(f"[{STUDY}] device={cfg.device} dtype={cfg.dtype}")

    # ---- oracle: ground-truth induction heads ---------------------------------
    orc = O.compute_oracle(cfg)
    prefix, oset = orc["prefix"], orc["induction_set"]
    print(f"oracle induction set (prefix>= {cfg.oracle_threshold}): {oset}")
    top = sorted(prefix, key=lambda h: prefix[h], reverse=True)[:6]
    print("top-6 prefix-match heads:", [(h, round(prefix[h], 3)) for h in top])

    # ---- attribution engine (eap_ig, read-only) -------------------------------
    M = Model(ModelConfig(name=cfg.model_name, device=cfg.device, dtype=cfg.dtype))

    # per-seed records
    rec = {m: [] for m in CANDIDATES}                    # list of recovery-metric dicts
    faith_pool = {m: {n: [] for n in SIZES} for m in CANDIDATES}
    faith_ref_seed = {m: [] for m in CANDIDATES}         # per-seed mean faith @ REF (independent unit)
    head_pool = {m: {} for m in CANDIDATES}              # accumulate |score| per head across seeds
    base = []
    for seed in cfg.task_seeds:
        batch = T.build_induction(M.tok, n_examples=cfg.task_n_examples, seed=seed,
                                  block_len=cfg.block_len, id_lo=cfg.id_lo,
                                  id_hi=cfg.id_hi).to(cfg.device)
        b, bp = baselines(M, batch)
        base.append((b, bp))
        scores = {m: _score(M, batch, m, seed, cfg.m_ig) for m in CANDIDATES}
        for m in CANDIDATES:
            fc = faith_curve(M, batch, scores[m], list(SIZES), b, bp)
            for n in SIZES:
                faith_pool[m][n].extend(fc[n].tolist())
            faith_ref_seed[m].append(float(fc[REF].mean()))   # one value per seed (indep. unit)
            rec[m].append(recovery_metrics(scores[m], prefix, oset, scores["exact_patch"]))
            for h, v in head_abs_scores(scores[m]).items():
                head_pool[m][h] = head_pool[m].get(h, 0.0) + v / len(cfg.task_seeds)
        print(f"  seed {seed}: b={b:.3f} bp={bp:.3f} "
              f"eap_ig AUROC={rec['eap_ig'][-1]['auroc_vs_oracle_set']:.3f} "
              f"eap AUROC={rec['eap'][-1]['auroc_vs_oracle_set']:.3f}")

    # ---- aggregate recovery metrics with CIs (across seeds) --------------------
    METS = ("spearman_vs_oracle", "auroc_vs_oracle_set", "recovery_at_k",
            "spearman_vs_exact_heads", "pearson_vs_exact_allnodes")
    methods_out = {}
    for m in CANDIDATES:
        agg = {}
        for key in METS:
            vals = [r[key] for r in rec[m]]
            mean, lo, hi = S.bootstrap_ci(vals, seed=0)
            agg[key] = {"mean": mean, "ci95": [lo, hi], "per_seed": vals}
        # faithfulness at REF (pooled per-example across seeds)
        fref = np.array(faith_pool[m][REF])
        fmean, flo, fhi = S.bootstrap_ci(fref, seed=0)
        agg["faith_at_ref"] = {"mean": fmean, "ci95": [flo, fhi], "n": len(fref)}
        agg["auc_faithfulness"] = float(np.mean([np.mean(faith_pool[m][n]) for n in SIZES]))
        methods_out[m] = agg

    # ---- paired EAP-IG vs EAP (recovery + faithfulness) -----------------------
    pairwise = build_pairwise(
        [r["auroc_vs_oracle_set"] for r in rec["eap_ig"]],
        [r["auroc_vs_oracle_set"] for r in rec["eap"]],
        faith_ref_seed["eap_ig"], faith_ref_seed["eap"],
        faith_pool["eap_ig"][REF], faith_pool["eap"][REF],
        [r["pearson_vs_exact_allnodes"] for r in rec["eap_ig"]],
        [r["pearson_vs_exact_allnodes"] for r in rec["eap"]])

    # ---- cost profile ---------------------------------------------------------
    cost = {}
    batch0 = T.build_induction(M.tok, n_examples=cfg.task_n_examples, seed=0,
                               block_len=cfg.block_len, id_lo=cfg.id_lo,
                               id_hi=cfg.id_hi).to(cfg.device)
    for m in CANDIDATES:
        # 1 timed rep (exact_patch is 157 fwd — repeated profiling is pure overhead; the
        # O(1)/O(m)/O(nodes) hierarchy is asymptotic, one measurement suffices)
        t0 = time.perf_counter(); _score(M, batch0, m, 0, cfg.m_ig)
        cost[m] = {"p50_s": float(time.perf_counter() - t0), "reps": 1}

    # ---- H15 verdict (pre-registered rubric) ----------------------------------
    aur = methods_out["eap_ig"]["auroc_vs_oracle_set"]["mean"]
    spe = methods_out["eap_ig"]["spearman_vs_exact_heads"]["mean"]
    faith_gap_p = pairwise["faith_ref_seedlevel__eap_ig_vs_eap"]["p_value"]   # seed-level (honest)
    faith_gap = pairwise["faith_ref_seedlevel__eap_ig_vs_eap"]["mean_diff"]
    rand_aur = methods_out["random"]["auroc_vs_oracle_set"]["mean"]
    verdict = compute_verdict(aur, spe, faith_gap, faith_gap_p, rand_aur)
    print(f"\nH15 verdict: {verdict}  (eap_ig AUROC={aur:.3f}, spearman_vs_exact={spe:.3f}, "
          f"faith_gap={faith_gap:+.3f} p={faith_gap_p:.1e})")

    summary = {
        "study": STUDY, "config": cfg.to_dict(), "candidates": list(CANDIDATES),
        "sizes": list(SIZES), "ref_size": REF, "verdict": verdict,
        "oracle": {"prefix": prefix, "prev": orc["prev"], "induction_set": oset,
                   "threshold": cfg.oracle_threshold},
        "head_scores_meanabs": head_pool,
        "methods": methods_out, "pairwise": pairwise, "cost": cost,
        "baselines_per_seed": [{"b": b, "bp": bp} for b, bp in base],
        "env": utils.environment(),
    }
    out = utils.REPO_ROOT / "artifacts" / STUDY
    utils.save_json(out / "baseline" / "summary.json", summary)
    utils.save_npz(out / "baseline" / "faith.npz",
                   **{f"faith__{m}__{n}": np.array(faith_pool[m][n])
                      for m in CANDIDATES for n in SIZES})
    utils.save_json(out / "study-manifest.json",
                    {"study": STUDY, "seeds": list(cfg.task_seeds),
                     "oracle_seeds": list(cfg.oracle_seeds), "env": utils.environment(),
                     "verdict": verdict})
    print(f"saved -> {out/'baseline'/'summary.json'}")
    return summary


def refresh_stats() -> dict:
    """Rebuild ONLY the significance block (pairwise + verdict) of an existing baseline
    from its persisted artifact, WITHOUT re-running any attribution / exact-patch / faithfulness
    forward passes. This is deterministic and equivalent to a full re-run (same seeds -> the
    persisted faith.npz and per-seed recovery are byte-identical); it exists precisely because
    faith.npz is persisted so the statistical unit of analysis can be corrected without the
    ~1 hour of redundant forwards (audit 2026-07-03-02). The recovery block (methods.*),
    config, cost, oracle, and faith.npz are left untouched. Fails loudly if the artifact is
    missing the per-seed fields it needs, so it can never silently patch a stale schema."""
    import json
    base = utils.REPO_ROOT / "artifacts" / STUDY / "baseline"
    d = json.loads((base / "summary.json").read_text())
    z = np.load(base / "faith.npz", allow_pickle=True)
    ref = d["ref_size"]
    nseeds = len(d["config"]["task_seeds"])
    n_ex = d["config"]["task_n_examples"]

    def per_seed(metric, method):  # seed-level recovery values from the recovery block
        return d["methods"][method][metric]["per_seed"]

    def faith_seed(method):        # per-seed mean faith @ ref from persisted per-example array
        return z[f"faith__{method}__{ref}"].reshape(nseeds, n_ex).mean(axis=1).tolist()

    def faith_pool(method):        # pooled per-example faith @ ref (effect-size descriptor)
        return z[f"faith__{method}__{ref}"].tolist()

    d["pairwise"] = build_pairwise(
        per_seed("auroc_vs_oracle_set", "eap_ig"), per_seed("auroc_vs_oracle_set", "eap"),
        faith_seed("eap_ig"), faith_seed("eap"),
        faith_pool("eap_ig"), faith_pool("eap"),
        per_seed("pearson_vs_exact_allnodes", "eap_ig"), per_seed("pearson_vs_exact_allnodes", "eap"))

    aur = d["methods"]["eap_ig"]["auroc_vs_oracle_set"]["mean"]
    spe = d["methods"]["eap_ig"]["spearman_vs_exact_heads"]["mean"]
    fp = d["pairwise"]["faith_ref_seedlevel__eap_ig_vs_eap"]
    d["verdict"] = compute_verdict(aur, spe, fp["mean_diff"], fp["p_value"],
                                   d["methods"]["random"]["auroc_vs_oracle_set"]["mean"])
    utils.save_json(base / "summary.json", d)
    man = base.parent / "study-manifest.json"
    if man.exists():
        m = json.loads(man.read_text()); m["verdict"] = d["verdict"]; utils.save_json(man, m)
    print(f"refreshed stats -> verdict={d['verdict']}  "
          f"faith seed-level p={fp['p_value']:.4f} (mean_diff={fp['mean_diff']:+.3f}), "
          f"pooled p={d['pairwise']['faith_ref_pooled__eap_ig_vs_eap']['p_value']:.2e}")
    return d


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--dtype", default="float32")
    ap.add_argument("--quick", action="store_true", help="tiny run for smoke testing")
    ap.add_argument("--refresh-stats", action="store_true",
                    help="recompute only pairwise+verdict from the persisted artifact "
                         "(deterministic; no forward passes) — see refresh_stats() docstring")
    a = ap.parse_args()
    if a.refresh_stats:
        refresh_stats()
    else:
        kw = {"device": a.device, "dtype": a.dtype}
        if a.quick:
            kw.update(oracle_seeds=(0,), task_seeds=(0,), oracle_n_examples=10, task_n_examples=16)
        main(Config(**kw))
