"""Phase 2 record: oracle checks (P0-5) + determinism probe (P0-1) → study manifest.

Run:  PYTHONPATH=implementation python -m sae_frontier.run_phase2
"""
from __future__ import annotations

import json
from pathlib import Path

import torch

from . import oracle
from .config import SAEConfig, SyntheticConfig, TrainConfig
from .manifest import ARTIFACTS, append_phase
from .saes import build_sae
from .synthetic import generate
from .train import train_sae
from .utils import tensor_hash


def determinism_probe() -> dict:
    """P0-1: run each candidate's training twice; assert bit-identical output hashes."""
    data = generate(SyntheticConfig(n_features=48, d_model=12, n_samples=500, seed=0))
    out = {}
    for v in ("relu", "gated", "topk", "jumprelu"):
        hashes = []
        for _ in range(2):
            s = build_sae(SAEConfig(variant=v, d_model=12, expansion=4, seed=0, k=6))
            train_sae(s, data.x, TrainConfig(steps=120, seed=0))
            xh, _ = s(data.x)
            hashes.append(tensor_hash(xh))
        out[v] = {"hash_run1": hashes[0], "hash_run2": hashes[1], "deterministic": hashes[0] == hashes[1]}
    return out


def main() -> None:
    oracle_checks = {v: oracle.run_oracle_checks(v) for v in ("relu", "gated", "topk", "jumprelu")}
    det = determinism_probe()
    all_oracle_pass = all(r["passed"] for r in oracle_checks.values())
    all_det_pass = all(d["deterministic"] for d in det.values())

    phase_dir = ARTIFACTS / "phase2"
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "oracle_checks.json").write_text(json.dumps(oracle_checks, indent=2))
    (phase_dir / "determinism.json").write_text(json.dumps(det, indent=2))

    append_phase(2, "implementation", {
        "gate": "G1",
        "candidates": ["relu", "gated", "topk", "jumprelu"],
        "oracle_check_all_passed": all_oracle_pass,      # P0-5
        "determinism_all_passed": all_det_pass,          # P0-1
        "artifacts": ["phase2/oracle_checks.json", "phase2/determinism.json"],
    })
    print(f"Phase 2 recorded. oracle_pass={all_oracle_pass} determinism_pass={all_det_pass}")
    assert all_oracle_pass and all_det_pass, "G1 proposed-mode gates (P0-5/P0-1) FAILED"


if __name__ == "__main__":
    main()
