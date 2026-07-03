"""H15 automated circuit discovery — GPT-2-small induction (study: induction-discovery).

Tests whether node-level automated circuit discovery (EAP / EAP-IG, reusing the
`implementation.eap_ig` attribution engine read-only) recovers GPT-2-small's induction
heads, where the ground truth is a *computable* oracle — Olsson et al. (2022)
prefix-matching score per head — not a memorized head list. Closes H15 (§11) of the
tiny-transformer induction study at the GPT-2 rung.

Modules:
  oracle    : Olsson prefix-matching + previous-token per-head scores (ground truth)
  task      : minimal-pair induction TaskBatch for the eap_ig attribution engine
  discover  : head-recovery / AUROC / rank-consistency metrics
  run       : orchestrate oracle + 4 candidates x seeds, CIs, artifacts, manifest
"""
from __future__ import annotations

__all__ = ["oracle", "task", "discover", "run"]
