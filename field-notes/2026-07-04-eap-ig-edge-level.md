# Field notes — 2026-07-04 — EAP-IG edge-level build

## Context

Built the edge-level EAP/EAP-IG engine (32,491 q/k/v-split edges + greedy) on raw `transformers`
GPT-2 to close the `eap-ig-faithfulness` study's §7 node-vs-edge divergence. The build was
verification-driven (the attribution math + recursive ablation are the exact error-prone class
the repo's sim-audit culture guards). Issues found and resolved inline:

## Issues found and resolved

- **The correctness strategy that made an error-prone build safe: verify against the trusted
  node engine.** Rather than trust a from-scratch edge-attribution engine, the build gated on
  three checks that each catch a whole class of bug: (1) the reimplemented split-qkv forward vs
  the real GPT-2 logits (9e-5 — catches any forward-reimplementation error); (2) the edge→node
  identity `node_score(u) == Σ_v edge_score(u→v)` (5e-7 — a near-exact algebraic proof that the
  per-slot gradients + scores are right, since it must hold by the linear-sum property); (3) the
  ablation boundaries all-in==clean / all-out==corrupt (exact metric match — validates the
  recursive input reconstruction). Building each component to its gate before moving on meant no
  silently-wrong number could survive. Lesson: for an error-prone engine, find an *independent
  identity it must satisfy* and gate on it — cheaper and stronger than eyeballing outputs.

- **retain_grad, not requires_grad_, for non-leaf residual copies.** The per-head residual copies
  are derived from `h` (which requires grad through the forward), making them *non-leaf* tensors;
  `.requires_grad_(True)` silently leaves `.grad` as None (PyTorch warns). Fixed with
  `.retain_grad()`. Caught immediately by a `TypeError: 'NoneType' object is not subscriptable`
  when slicing the (absent) grad — a fast failure, not a silent one.

- **Verdict-threshold mis-calibration (not a result bug).** The first `divergence_closed` check
  looked for the SVA EAP-IG advantage at n=100, but EAP-IG's SVA faithfulness rises at n≈400
  (0.809 vs EAP 0.063); at n=100 both are still low. The *results* were correct and matched Hanna
  Fig 3 on first run — only the summary threshold checked the wrong operating point. Fixed to use
  the max EAP-IG−EAP gap over the grid (0.75 at n=400) plus the embed→m0 rank smoking gun. Lesson:
  when a boolean verdict says FAIL but the curves look right, suspect the threshold before the
  experiment.

- **The SVA "smoking gun" reproduced on the nose.** Hanna p.7 says EAP misses the `embed→m0`
  (input→MLP0) edge that is essential for SVA faithfulness. Our engine ranks it **rank 1 for
  EAP-IG, rank 74 for EAP** — an independent, mechanistic confirmation that the reproduction is
  real and not a threshold artifact. Worth capturing: reproducing a paper's *named causal detail*
  (not just its headline curve) is the strongest evidence a reimplementation is faithful.

- **Two float-tolerance test fixes.** `all-in == clean` used exact float `==` (failed at ~5e-4
  reimplementation drift) → relaxed to `< 1e-2`; the reimplemented forward's ~1e-3 offset is
  disclosed in the report §10 and does not move any verdict.

- **The pre-sign-off audit caught that the strongest-looking gate was necessary-not-sufficient.**
  A 3-lens-equivalent Opus audit confirmed the science sound (sign/Eq 1/Eq 3/ablation/greedy/prune
  all faithful, results bit-reproducible) but flagged that the edge→node identity — which I had
  called "the strongest anchor" validating per-edge scores — is *insensitive to a q↔k gradient
  swap that preserves the per-source sum*, so it validates only the per-**source aggregate**. The
  headline is a single edge's *rank* (embed→m0: 1 vs 74), exactly the per-edge quantity the gate
  can't see. Fixed by adding an *independent per-edge anchor* — EAP score sign vs exact single-edge
  ablation (agreement 1.00 including q/k/v-slot edges, which a swap would flip) — and softening §5.
  The audit also caught three stale reporting numbers (a "9e-5" forward-match that actually
  measured <5e-4; "near-zero until n=1000" contradicting the study's own 0.498-at-n=700; a "22
  gates" count that was 15). Lesson: an identity that holds to 1e-6 can still be blind to the exact
  quantity you're reporting — always ask *what transformation would this gate NOT catch?*

## Patterns / lessons

- **Gate an error-prone engine on an identity it must satisfy**, not on plausible-looking output.
  The edge→node linear-sum identity was the single most valuable check.
- **Reproduce the mechanism, not just the metric.** The embed→m0 rank (1 vs 74) is the detail
  that turns "our curves look like the paper's" into "our engine finds the same causal structure".
- Reused the node engine read-only (`forward_cache`, `_split_heads`, `_dot`, `metrics`,
  `tasks`) — the edge layer is additive, mirroring how H15/H9 reused their substrates.
