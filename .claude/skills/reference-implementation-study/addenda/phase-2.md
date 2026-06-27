# Proposed-mode addendum — Phase 2 (load on demand)

Apply each block iff `proposed` is set OR its id is in the active `flags` set (`P0-1`, `P0-5`, `P2-1`).

**[P0-1] Determinism-verification gate.** After implementing each candidate, run it TWICE
with identical config + seed (and identical decoding params) and assert the two outputs are
bit-identical (or within a tiny named tolerance for unavoidable float-reduction nondeterminism,
e.g. non-deterministic CUDA reductions or atomic adds). This is the single most cross-validated
landscape lesson: no tracking tool guarantees *semantic* determinism — it must be verified, not
asserted. Store both run hashes in the manifest. With flag `P0-1`, `validate_gate.py G1 --flags
P0-1` re-runs the determinism probe; a non-deterministic candidate must FAIL G1.

**[P0-5] Correctness anchoring against an oracle (G1).** Determinism (P0-1), a shared contract
(P2-1), and reproducibility (P1-3/P2-2) all pass for an implementation that is internally
consistent yet *numerically wrong* — none of them anchor correctness. Before any candidate enters
the Phase-3 comparison, validate it against at least one EXTERNAL oracle and record an
`oracle_check` block per candidate (in the manifest or a Phase-2 summary). Oracle types, in
priority order:

1. **`analytical`** — a closed-form result or theoretical bound for a special case (e.g. softmax of
   a constant logit vector is uniform, `1/V` per class; the entropy / perplexity floor of a uniform
   next-token predictor over vocabulary `V` is `log V` / `V`; a LayerNorm output has zero mean and
   unit variance; RoPE preserves the query/key norm). Compare measured vs expected within a stated
   tolerance.
2. **`reference`** — a trusted third-party / golden output (a vetted library such as a HuggingFace
   `transformers` module or a reference FlashAttention kernel, a published benchmark curve, or a
   prior accepted result): differential testing against an authority.
3. **`metamorphic`** — when no numeric oracle exists, assert necessary relations across paired runs
   (e.g. adding a constant to every logit leaves the softmax distribution unchanged — shift
   invariance; a positive temperature scale `c>1` sharpens but preserves the greedy argmax; a
   permutation of the vocabulary permutes the output distribution identically; a larger
   compute / few-shot budget must not, on average, decrease benchmark accuracy).

Record per candidate: `type`, the point(s) tested, `expected`, `measured`, `tolerance`, `passed`.
A candidate whose `oracle_check` fails must FAIL G1 — a wrong implementation must not reach the
comparison. With flag `P0-5`, `validate_gate.py G1 --flags P0-5` requires a passing `oracle_check`
record for every candidate. (Test-oracle problem; metamorphic / differential testing for numerical
software.)

**[P2-1] Harness orchestration-layer separation.** Enforce a uniform DATA + METRIC contract,
not just a uniform call interface: a single central config (loaded once) drives identical
scenario data (the same prompts / eval items / few-shot exemplars) and identical metric functions
for every candidate, via a candidate / data / metric registry. No candidate may smuggle in its own
data loader, prompt template, or metric. With flag `P2-1`, `validate_gate.py --flags P2-1` checks
that all candidates resolve through one registry / shared scenario-data + metric module.
