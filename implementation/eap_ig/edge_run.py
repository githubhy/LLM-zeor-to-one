"""Edge-level EAP/EAP-IG study: re-run IOI + SVA at 32,491-edge granularity with greedy search,
and check whether the per-task ordering flips to Hanna Fig 3's — closing the node-level study's
§7 divergence.

Fig 3 targets: IOI -> EAP ~= EAP-IG (small gap, both plateau); SVA -> EAP catastrophic at small n
(pruned near-nothing) while EAP-IG faithful. Smoking gun (Hanna p.7): on SVA, EAP misses the
embed->m0 edge that EAP-IG ranks high.

Run: PYTHONPATH=$PWD HF_HUB_OFFLINE=1 python3 -m implementation.eap_ig.edge_run [--device cpu]
"""
from __future__ import annotations

import argparse
import numpy as np

from .config import ModelConfig, TaskConfig
from .model import Model
from .edge_model import EdgeModel
from . import edge_attribution as EA
from .edge_greedy import greedy_circuit, prune
from .tasks import build_task
from .metrics import normalized_faithfulness
from . import utils

STUDY = "eap-ig-edge"
ART = "artifacts/eap-ig-edge"
NGRID = (50, 100, 200, 400, 700, 1000)
TASKS = ("ioi", "sva")


def _rank_of_edge(scores: dict, edge: tuple) -> int:
    """1-based rank of an edge by |score| (1 = most important). None if absent."""
    order = sorted(scores, key=lambda e: abs(scores[e]), reverse=True)
    return order.index(edge) + 1 if edge in scores else None


def _boot_ci(per_example, b, bp, seed=0, n_boot=10000):
    """Bootstrap 95% CI of normalized faithfulness over eval examples (per-example metric array)."""
    x = np.asarray(per_example, dtype=float)
    r = np.random.default_rng(seed)
    idx = r.integers(0, x.size, size=(n_boot, x.size))
    fb = (x[idx].mean(1) - bp) / (b - bp)
    lo, hi = np.percentile(fb, [2.5, 97.5])
    return [float(lo), float(hi)]


def run_task(M, EM, task: str, n_examples: int, seed: int) -> dict:
    batch = build_task(M.tok, TaskConfig(task=task, n_examples=n_examples, seed=seed)).to(M.cfg.device)
    b = batch.metric(M.model(batch.clean_ids, attention_mask=batch.attn_mask).logits).mean().item()
    bp = batch.metric(M.model(batch.corrupt_ids, attention_mask=batch.attn_mask).logits).mean().item()
    out = {"task": task, "b_clean": b, "b_corrupt": bp, "curves": {}, "smoking_gun": {}}
    emb_m0 = ("embed", "m0.in")   # the crucial input->MLP0 edge (Hanna p.7)
    for method in ("eap", "eap_ig"):
        scores = EA.score_edges(M, EM, batch, method=method, m_ig=5)
        faiths, kept, ci = [], [], []
        for n in NGRID:
            C = prune(greedy_circuit(scores, n))
            per_ex = batch.metric(EM.patched_logits_edges(batch, C)).detach().cpu().numpy()
            faiths.append(normalized_faithfulness(float(per_ex.mean()), b, bp))
            ci.append(_boot_ci(per_ex, b, bp))
            kept.append(len(C))
        out["curves"][method] = {"n": list(NGRID), "faith": faiths, "faith_ci95": ci,
                                 "kept_edges": kept}
        out["smoking_gun"][method] = {"embed_to_m0_rank": _rank_of_edge(scores, emb_m0),
                                      "embed_to_m0_abs_score": float(abs(scores.get(emb_m0, 0.0)))}
        print(f"  [{task}/{method}] faith@n={list(zip(NGRID, [round(f,3) for f in faiths]))}")
        print(f"      kept={kept}  embed->m0 rank={out['smoking_gun'][method]['embed_to_m0_rank']}")
    return out


def _verification(M, EM) -> dict:
    """Persist the correctness-gate numbers (measured, not prose) — logits-match, edge->node
    identity, ablation boundaries — on a small fixed batch."""
    from implementation.eap_ig.attribution import score_nodes
    from implementation.eap_ig.config import AttrConfig
    from implementation.induction_discovery.task import build_induction
    from . import edges as _E
    b = build_induction(M.tok, n_examples=5, seed=1, block_len=8).to(M.cfg.device)
    lm = EM.logits_match(b.clean_ids, b.attn_mask)
    e2n = {}
    for m in ("eap", "eap_ig"):
        node = score_nodes(M, b, AttrConfig(method=m, m_ig=5))
        rec = EA.node_from_edges(EA.score_edges(M, EM, b, method=m, m_ig=5), M)
        e2n[m] = max(abs(node[u] - rec[u]) for u in M.names)
    allc = set(_E.edges(M.n_layer, M.n_head))
    mc = b.metric(M.model(b.clean_ids, attention_mask=b.attn_mask).logits).mean().item()
    mx = b.metric(M.model(b.corrupt_ids, attention_mask=b.attn_mask).logits).mean().item()
    return {"logits_match_maxabs": lm,
            "edge_to_node_maxabs": e2n,
            "all_in_metric_vs_clean": abs(b.metric(EM.patched_logits_edges(b, allc)).mean().item() - mc),
            "all_out_metric_vs_corrupt": abs(b.metric(EM.patched_logits_edges(b, set())).mean().item() - mx),
            "note": "edge->node validates the per-source aggregate (necessary, not sufficient); "
                    "per-edge scores validated by sign-vs-exact-ablation in tests"}


def main(device="cpu", n_examples=15, seed=0):
    M = Model(ModelConfig(name="gpt2", device=device, dtype="float32"))
    EM = EdgeModel(M)
    print(f"[{STUDY}] device={device} tasks={TASKS} n_grid={NGRID} n_examples={n_examples}")
    verification = _verification(M, EM)
    print(f"verification: {verification}")
    results = {t: run_task(M, EM, t, n_examples, seed) for t in TASKS}

    # ---- divergence-closing verdict -------------------------------------------
    # IOI: EAP ~= EAP-IG at the largest n (small gap). SVA: EAP << EAP-IG at small n.
    ioi = results["ioi"]["curves"]
    sva = results["sva"]["curves"]
    # IOI: EAP ~= EAP-IG (small gap at the plateau). SVA: EAP-IG dramatically more faithful than
    # EAP at the mid-range operating point where EAP-IG has converged but EAP is still catastrophic.
    ioi_gap_top = abs(ioi["eap"]["faith"][-1] - ioi["eap_ig"]["faith"][-1])
    sva_gap = [sva["eap_ig"]["faith"][i] - sva["eap"]["faith"][i] for i in range(len(NGRID))]
    sva_max_gap = max(sva_gap)
    # EAP's best faithfulness at small n (<=200) — catastrophic if it stays near zero there
    sva_eap_small = max(sva["eap"]["faith"][i] for i in range(len(NGRID)) if NGRID[i] <= 200)
    sm = results["sva"]["smoking_gun"]
    verdict = {
        "ioi_eap_approx_eapig": bool(ioi_gap_top < 0.15),
        "ioi_gap_at_top_n": ioi_gap_top,
        "sva_eap_catastrophic": bool(sva_max_gap > 0.4 and sva_eap_small < 0.2),
        "sva_max_eapig_minus_eap": sva_max_gap,
        "sva_max_gap_at_n": NGRID[int(np.argmax(sva_gap))],
        "sva_eap_best_faith_small_n": sva_eap_small,
        "sva_smoking_gun_eapig_ranks_embed_m0_higher": bool(
            (sm["eap_ig"]["embed_to_m0_rank"] or 10**9) < (sm["eap"]["embed_to_m0_rank"] or 10**9)),
        "sva_embed_m0_rank_eap": sm["eap"]["embed_to_m0_rank"],
        "sva_embed_m0_rank_eap_ig": sm["eap_ig"]["embed_to_m0_rank"],
    }
    verdict["divergence_closed"] = bool(
        verdict["ioi_eap_approx_eapig"] and verdict["sva_eap_catastrophic"]
        and verdict["sva_smoking_gun_eapig_ranks_embed_m0_higher"])
    from .edges import edge_count
    summary = {"study": STUDY, "n_examples": n_examples, "seed": seed, "n_grid": list(NGRID),
               "edge_count": edge_count(M.n_layer, M.n_head), "verification": verification,
               "results": results, "verdict": verdict, "env": _env(M)}
    utils.save_json(utils.REPO_ROOT / ART / "summary.json", summary)
    print(f"\nverdict: {verdict}")
    print(f"saved -> {ART}/summary.json")
    return summary


def _env(M):
    try:
        return utils.environment()
    except Exception:
        return {}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--n-examples", type=int, default=15)
    a = ap.parse_args()
    main(device=a.device, n_examples=a.n_examples)
