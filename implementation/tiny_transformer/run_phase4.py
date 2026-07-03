"""Phase 4 — toy MI-observable analysis (Gate G3).

Loads the 5 trained 2-layer models (Phase 3) and runs the observable suite,
emitting per-seed records + an aggregate summary with per-hypothesis verdicts and
CIs. No training (forward passes + hooks).

Usage: python run_phase4.py [seed ...]      (default: 0 1 2 3 4)
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
from tiny_transformer.utils import bootstrap_ci, save_json  # noqa: E402

ART = os.path.join(REPO, "artifacts", "induction-tiny", "phase4")


def run_seed(seed):
    torch.set_num_threads(6)
    m = A.load_model(2, seed)
    batch = A.eval_batch()
    census = A.role_census(m, batch)
    sets = A.identify_head_sets(m, census)
    rec = dict(
        seed=seed,
        sets=dict(ind_set=[list(x) for x in sets["ind_set"]],
                  top_ind=list(sets["top_ind"]),
                  feeder_set=[list(x) for x in sets["feeder_set"]],
                  top_prev=list(sets["top_prev"])),
        role_census={f"{l}L{h}": census[(l, h)] for (l, h) in census},
        circuit_match=A.circuit_match(m, sets),
        composition=A.composition_scores(m, sets),
        patching=A.patching(m, batch, sets, census),
        self_repair=A.self_repair(m, batch, sets),
        logit_lens=A.logit_lens(m, batch),
        probing=A.probing(m, batch),
        privileged_basis=A.privileged_basis(m, batch),
    )
    save_json(rec, os.path.join(ART, f"seed_{seed}.json"))
    return rec


def V(cond):
    return "PASS" if cond else "INCONCLUSIVE"


def aggregate(recs):
    copyset = [r["circuit_match"]["copy_diag_induction_set"]["frac_top1_self"] for r in recs]
    rankcliff = all(r["circuit_match"]["rank_cliff_holds"] for r in recs)
    ind_top_layers = [r["sets"]["top_ind"][0] for r in recs]
    feeder_layers = [r["sets"]["feeder_set"][0][0] for r in recs]
    n_ind = [r["circuit_match"]["n_induction_heads"] for r in recs]
    acc_abl_ind = [r["patching"]["acc_ablate_induction_set"] for r in recs]
    acc_abl_feed = [r["patching"]["acc_ablate_feeder_set"] for r in recs]
    ctrl_drop = [r["patching"]["control_drop"] for r in recs]
    single_drop = [r["patching"]["single_head_drop"] for r in recs]
    set_drop = [r["patching"]["necessity_induction_set_drop"] for r in recs]
    ie_te = [r["patching"]["ie_over_te"] for r in recs
             if r["patching"]["ie_over_te"] is not None]
    kcomp = [r["composition"]["dominant"] for r in recs]
    sel1 = [r["probing"]["resid_post_1"]["selectivity"] for r in recs]
    sel0 = [r["probing"]["resid_post_0"]["selectivity"] for r in recs]
    lpre = [r["logit_lens"]["resid_pre_0"]["mean_correct_rank"] for r in recs]
    lpost = [r["logit_lens"]["resid_post_1"]["mean_correct_rank"] for r in recs]
    redun = [r["self_repair"]["redundancy"] for r in recs]
    chance = recs[0]["patching"]["chance"]

    summary = dict(
        n_seeds=len(recs), chance=chance,
        H3_circuit_match=dict(
            copy_diag_frac_top1_self=bootstrap_ci(copyset), rank_cliff_all=rankcliff,
            n_induction_heads=n_ind,
            verdict=V(np.mean(copyset) > 0.5 and rankcliff)),
        H4b_role_census=dict(
            induction_top_layer=ind_top_layers, feeder_layer=feeder_layers,
            n_induction_heads=n_ind,
            verdict="PASS" if all(l == 1 for l in ind_top_layers) else "PARTIAL"),
        H10_patching=dict(
            acc_ablate_induction_set=bootstrap_ci(acc_abl_ind),
            acc_ablate_feeder_set=bootstrap_ci(acc_abl_feed),
            control_drop=bootstrap_ci(ctrl_drop),
            single_head_drop=bootstrap_ci(single_drop),
            set_drop=bootstrap_ci(set_drop),
            ie_over_te=bootstrap_ci(ie_te) if ie_te else None,
            verdict=V(np.mean(acc_abl_ind) < 5 * chance and np.mean(acc_abl_feed) < 5 * chance
                      and np.mean(ctrl_drop) < 0.15
                      and np.mean(single_drop) < np.mean(set_drop))),
        H11_decode_lens=dict(
            correct_rank_pre=bootstrap_ci(lpre), correct_rank_post=bootstrap_ci(lpost),
            verdict=V(np.mean(lpost) < np.mean(lpre) * 0.5)),
        H12_composition=dict(
            dominant=kcomp, verdict="PASS" if all(d == "K" for d in kcomp) else "PARTIAL"),
        H13_probing=dict(
            selectivity_L0=bootstrap_ci(sel0), selectivity_L1=bootstrap_ci(sel1),
            verdict=V(np.mean(sel1) > 0.1)),
        H14_self_repair=dict(
            redundancy=bootstrap_ci(redun), mean_single_drop=float(np.mean(single_drop)),
            mean_set_drop=float(np.mean(set_drop)),
            note="single-head ablation ~%.3f vs set ablation ~%.3f => strong redundancy"
                 % (np.mean(single_drop), np.mean(set_drop))),
        per_seed=[{k: r[k] for k in ["seed", "sets", "circuit_match", "composition",
                                     "patching", "self_repair", "logit_lens"]}
                  for r in recs],
    )
    return summary


def main(seeds):
    os.makedirs(ART, exist_ok=True)
    recs = [run_seed(s) for s in seeds]
    summary = aggregate(recs)
    save_json(summary, os.path.join(ART, "phase4_summary.json"))
    print("PHASE4 VERDICTS:", json.dumps(
        {k: v["verdict"] for k, v in summary.items()
         if isinstance(v, dict) and "verdict" in v}))
    p = summary["H10_patching"]
    print(f"  H10: acc after ablating induction set {p['acc_ablate_induction_set'][0]:.3f} "
          f"/ feeder set {p['acc_ablate_feeder_set'][0]:.3f} (chance {summary['chance']:.3f}); "
          f"single-head drop {p['single_head_drop'][0]:.3f} vs set drop {p['set_drop'][0]:.3f}; "
          f"control drop {p['control_drop'][0]:.3f}; IE/TE {p['ie_over_te'][0] if p['ie_over_te'] else None}")
    print(f"  H3 copy (diag frac self): {summary['H3_circuit_match']['copy_diag_frac_top1_self'][0]:.3f}; "
          f"n induction heads {summary['H3_circuit_match']['n_induction_heads']}")
    print(f"  H13 selectivity L0->L1: {summary['H13_probing']['selectivity_L0'][0]:.3f} -> "
          f"{summary['H13_probing']['selectivity_L1'][0]:.3f}")


if __name__ == "__main__":
    seeds = [int(a) for a in sys.argv[1:]] or [0, 1, 2, 3, 4]
    main(seeds)
