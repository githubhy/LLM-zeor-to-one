"""Phase 2 → G1 prep: verify determinism (P0-1) and correctness oracles (P0-5),
write them into the study manifest with the environment/provenance block (P1-3)."""
from __future__ import annotations

from .config import ModelConfig, TaskConfig
from .model import Model
from .tasks import build_task
from .attribution import score_eap
from .oracle import run_oracles
from . import manifest, utils

STUDY = "eap-ig-faithfulness"
TASKS = ("ioi", "greater_than", "sva")


def main() -> None:
    utils.set_determinism(0)
    M = Model(ModelConfig(name="gpt2", device="cpu", dtype="float32"))

    # P0-1 determinism: score each task twice, hashes must match
    det = {}
    for task in TASKS:
        batch = build_task(M.tok, TaskConfig(task=task, n_examples=16, seed=0)).to("cpu")
        h1 = utils.dict_hash(score_eap(M, batch))
        h2 = utils.dict_hash(score_eap(M, batch))
        det[task] = {"run_hashes": [h1, h2], "hashes_match": h1 == h2}

    # P0-5 oracles (representative task)
    batch = build_task(M.tok, TaskConfig(task="ioi", n_examples=24, seed=0)).to("cpu")
    oracle = run_oracles(M, batch)

    m = manifest.ensure_env(manifest.load(STUDY))
    m["determinism"] = det
    m["oracle_checks"] = oracle
    manifest.add_iteration(m, 2, "G1 prep: determinism + oracles",
                           det_all_match=all(v["hashes_match"] for v in det.values()),
                           oracle_all_pass=all(o["passed"] for o in oracle.values()))
    manifest.save(STUDY, m)
    print("determinism:", {k: v["hashes_match"] for k, v in det.items()})
    print("oracles:", {k: (v["type"], v["passed"]) for k, v in oracle.items()})


if __name__ == "__main__":
    main()
