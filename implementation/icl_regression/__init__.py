"""H9 — Algorithmic ICL (forward-pass-as-online-optimizer), commodity-scale.

Two source-separated evidence classes (plan `plans/2026-07-04-h9-algorithmic-icl.md`):

- Part A (`construction.py`) — the von Oswald (2023) Proposition-1 construction: a *linear*
  self-attention layer with hand-set weights whose forward pass IS one gradient-descent step
  on the in-context MSE loss (bit-exact identity; no training). Mechanistic.

- Part B (`model.py` + `run.py`) — a small *trained softmax* regression transformer whose
  in-context predictions on linear regression BEHAVIORALLY track least-squares (OLS/ridge),
  tightening with context length and depth (Garg 2022 / Akyürek 2023). Behavioral match, NOT
  a mechanism claim.

The contrast between A (linear+constructed = exact GD mechanism) and B (softmax+trained =
behavioral match only) is the H9 deliverable. Task + closed-form learners in `task.py`.
"""

__all__ = ["task", "construction", "model", "run"]
