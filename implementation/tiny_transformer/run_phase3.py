"""Phase 3 — toy baseline training across seeds (Gate G2).

Resumable + argv-driven so it fits the foreground time budget (each call trains a
small chunk; artifacts accumulate; a final `--aggregate` builds the summary).
Trains 2-layer attention-only induction models (5 seeds) + a 1-layer control (H1),
saving per-seed history + weights (for Phase 4/5) + CIs to
artifacts/induction-tiny/phase3/. Deterministic given seeds.

Reduced config (n_ctx=64, batch=128, 800 steps) — converges to the induction
head fast on CPU; the full-scale config (n_ctx=256, 20k steps) is deferred to a
GPU host (todos/2026-07-02-tiny-transformer-gpu-host-rungs.md).

Usage:
  python run_phase3.py 2:0 2:1 2:2      # train these (layers:seed) jobs
  python run_phase3.py --aggregate      # build phase3_summary.json from artifacts
"""
import glob
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "implementation"))

from tiny_transformer.config import model_config, TrainConfig      # noqa: E402
from tiny_transformer.model import build_toy, train_toy            # noqa: E402
from tiny_transformer.utils import bootstrap_ci, save_json         # noqa: E402

ART = os.path.join(REPO, "artifacts", "induction-tiny", "phase3")
CFG = dict(n_ctx=64, batch=128, steps=800, eval_every=50, threads=14)


def _seed_path(n_layers, seed):
    return os.path.join(ART, f"seed_{n_layers}L_{seed}.json")


def train_seed(job):
    n_layers, seed = job
    torch.set_num_threads(CFG["threads"])
    try:
        mcfg = model_config("induction", n_layers=n_layers, n_ctx=CFG["n_ctx"], seed=seed)
        m = build_toy(mcfg)
        tc = TrainConfig(lr=1e-3, batch_size=CFG["batch"], n_steps=CFG["steps"],
                         eval_every=CFG["eval_every"], eval_batch=512, seed=seed)
        t0 = time.time()
        h = train_toy(m, tc, log=lambda s: None)
        dur = time.time() - t0
        steps, acc = h["step"], h["ind_acc"]
        pc = next((steps[i] for i in range(len(acc)) if acc[i] >= 0.5), None)
        rec = dict(n_layers=n_layers, seed=seed, config=CFG, duration_s=dur,
                   final_ind_acc=acc[-1], final_ind_loss=h["ind_loss"][-1],
                   final_induction_score=h["induction_score"][-1],
                   final_prev_token_score=h["prev_token_score"][-1],
                   phase_change_step=pc)
        save_json(dict(rec, history=h), _seed_path(n_layers, seed))
        torch.save(m.state_dict(), os.path.join(ART, f"model_{n_layers}L_{seed}.pt"))
        return rec
    except Exception as e:
        return dict(n_layers=n_layers, seed=seed, error=repr(e))


def aggregate():
    recs = []
    for p in sorted(glob.glob(os.path.join(ART, "seed_*.json"))):
        with open(p) as f:
            d = json.load(f)
        recs.append({k: d[k] for k in d if k != "history"})
    acc2 = [r["final_ind_acc"] for r in recs if r["n_layers"] == 2]
    is2 = [r["final_induction_score"] for r in recs if r["n_layers"] == 2]
    pv2 = [r["final_prev_token_score"] for r in recs if r["n_layers"] == 2]
    pc2 = [r["phase_change_step"] for r in recs
           if r["n_layers"] == 2 and r["phase_change_step"] is not None]
    acc1 = [r["final_ind_acc"] for r in recs if r["n_layers"] == 1]
    summary = dict(
        config=CFG, n_seeds_2L=len(acc2),
        twolayer_ind_acc=bootstrap_ci(acc2) if acc2 else None,
        twolayer_induction_score=bootstrap_ci(is2) if is2 else None,
        twolayer_prev_token_score=bootstrap_ci(pv2) if pv2 else None,
        twolayer_phase_change_step=bootstrap_ci(pc2) if pc2 else None,
        onelayer_ind_acc=acc1,
        H1_pass=bool(acc2 and acc1 and (np.mean(acc2) - np.mean(acc1) > 0.4)),
        per_seed=recs,
    )
    save_json(summary, os.path.join(ART, "phase3_summary.json"))
    print("PHASE3 SUMMARY:", json.dumps(dict(
        twolayer_ind_acc=summary["twolayer_ind_acc"], onelayer_ind_acc=acc1,
        H1_pass=summary["H1_pass"], phase_change=summary["twolayer_phase_change_step"],
        n_seeds_2L=len(acc2)), default=str))


def main(argv):
    os.makedirs(ART, exist_ok=True)
    if "--aggregate" in argv:
        aggregate()
        return
    jobs = []
    for a in argv:
        if ":" in a:
            L, s = a.split(":")
            jobs.append((int(L), int(s)))
    if not jobs:
        jobs = [(2, s) for s in range(5)] + [(1, 0)]
    todo = [j for j in jobs if not os.path.exists(_seed_path(*j))]
    skipped = [j for j in jobs if j not in todo]
    if skipped:
        print("skip (already done):", skipped)
    if not todo:
        print("nothing to train")
        return
    t0 = time.time()
    # Sequential (not parallel): avoids torch CPU oversubscription, and each
    # train_seed saves its artifact on completion so partial progress survives a
    # kill (resumable via the skip-if-exists check above).
    for j in todo:
        r = train_seed(j)
        tag = f"{r['n_layers']}L:{r['seed']}"
        if "error" in r:
            print(f"  {tag} ERROR {r['error']}", flush=True)
        else:
            print(f"  {tag} ind_acc={r['final_ind_acc']:.3f} "
                  f"ind_score={r['final_induction_score']:.3f} "
                  f"prev={r['final_prev_token_score']:.3f} pc={r['phase_change_step']} "
                  f"({r['duration_s']:.0f}s)", flush=True)
    print(f"chunk done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
