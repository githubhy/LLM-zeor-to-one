# Proposed-mode addendum — Phase 6 (load on demand)

Apply each block iff `proposed` is set OR its id is in the active `flags` set (`P1-2`, `P2-2`, `P2-4`).

**[P1-2] Explicit multi-metric aggregation.** Before the winner / runner-up table, report the
full per-metric, per-candidate result grid (e.g. accuracy, pass@k, perplexity, latency, memory).
If a composite score is used to pick a winner, state the weighting EXPLICITLY and show a
**sensitivity-to-weights** check: does the winner survive reasonable re-weightings, or is the
ranking an artifact of an arbitrary weight choice? Aggregating across metrics is a decision (a
social-choice problem), not a given — surface it rather than hiding it inside a single number.

**[P2-2] Reproduce-from-artifacts validator + raw-output release.** Ship a script (sibling to
`validate_gate.py`, or per-study under `artifacts/<study>/`) that regenerates the headline
summary numbers **from the stored artifacts alone** — no recompute — and release the per-trial
raw outputs (the HELM/MLPerf transparency practice — per-item model generations and scored
traces), not just aggregates. This lets an independent party re-audit the recommendation without
rerunning the study. With flag `P2-2`, `validate_gate.py --flags P2-2` checks the reproduce-validator
script and the per-trial raw outputs exist and that the validator's numbers match `summary.json`.

**[P2-4] Pareto-front / dominance analysis.** P1-2 collapses multiple metrics into a weighted
score and stress-tests the weights, but a single composite reports one winner for one weight
vector: on its own it cannot *certify* that a near-winner is Pareto-dominated (hence suboptimal
under **every** positive weighting), nor enumerate the full set of candidates that are defensible
under **some** weighting. (And a zero weight on the axis where a candidate is worst, or an
accidentally mis-oriented axis, can even let a dominated candidate tie or win the composite.)
Complement it with the non-scalarized view: over the chosen objective axes (e.g. accuracy vs
compute-cost vs precision-cost — orient each so "larger is better"), compute the **non-dominated
(Pareto-optimal) set**. A candidate A *dominates* B iff A is at least as good on every axis and
strictly better on at least one. Report which candidates are Pareto-optimal and which are dominated
(naming the dominator), and apply any scalarization (P1-2) **only within the front**. A
Pareto-dominated candidate must never be the recommendation; the front is exactly the set of
candidates that are optimal for some positive weighting — the weight-free robustness statement
P1-2's grid can miss. (Non-dominated sorting / NSGA-style design-space exploration.) No gate check
— this is a report-quality item, like P1-2.
