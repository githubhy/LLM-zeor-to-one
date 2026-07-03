---
id: 2026-07-03-01
title: H15 executed at node granularity with a computed oracle, in a standalone sub-study report
status: accepted
date: 2026-07-03
plan: plans/2026-07-03-h15-automated-discovery.md
---

## Context

H15 ("automated discovery recovers the manual §A.9 induction K-edge, rank-consistent with
the patching deltas") was pre-registered in the tiny-transformer study
(`plans/2026-06-30-tiny-transformer-induction-study.md:37,151`) and DEFERRED to a GPU host
(`docs/tiny-transformer-induction-study.md:114,171`). Executing it on the Mac (MPS) surfaced
three judgment calls the plan did not pre-decide:

1. **Granularity.** The reusable attribution engine (`implementation/eap_ig/`) is **node-level**
   (heads/MLPs/embed), not edge-level — it has no per-edge score anywhere (verified by reading
   `graph.py`/`attribution.py`). H15's literal "K-*edge*" is an *edge* between a prev-token head
   and an induction head.
2. **Oracle.** No acquired source names GPT-2-small's induction heads (Olsson names only
   GPT-2-XL 21.20 / GPT-Neo 12.0; verified in `download/olsson-induction-heads-2022.pdf` p48/58).
   So the "ground-truth circuit" to recover cannot be cited — it must be computed.
3. **Where the writeup lands.** The Understand-phase map recommended extending the main report
   §6/§7/§11 rather than a new doc.

## Decision

Execute H15 **at node granularity** as **induction-*head* recovery** (recover the *nodes*, with
the prev-token→induction *composition edge* identified indirectly via a companion previous-token
score and full edge-level recovery explicitly deferred); use a **computed oracle** — Olsson's
prefix-matching score per head (pre-registered positive-set threshold **0.35**, which captures the
top-5 cluster {5.1, 5.5, 6.9, 7.2, 7.10}); and write it up as a **standalone sub-study report**
`docs/h15-automated-discovery-study.md`, with the parent report's §6 H15 row updated to
resolved-with-pointer.

## Alternatives considered

- **Edge-level attribution (literal K-edge).** Rejected for this pass: needs a genuinely new
  per-(source,dest) edge-scoring layer, not a config change — a separate study. Deferred to `todos/`.
- **Arbitrary oracle threshold.** Rejected: 0.35 is justified by *convergent validation* — the
  top-5 by the independent Olsson oracle exactly reproduce the parent study's Phase-4b head set and
  the literature's canonical cluster. The headline metrics (Spearman ρ, AUROC vs the *continuous*
  oracle, correlation to exact patching) are threshold-free, so the verdict does not hinge on 0.35.
- **Extend the main report in place (map's recommendation).** Rejected in favor of a standalone
  doc: this is a full GPT-2-rung experiment (4 candidates × 5 seeds, its own oracle, protocol
  matrix, CIs, cost) matching the repo's one-study-per-doc precedent (`docs/eap-ig-…`,
  `docs/sae-frontier-…`); the parent §6 table row is not sized for it. The parent report still gets
  a resolved H15 verdict + pointer, so nothing is orphaned.

## Consequences

- Enables a clean, self-contained, MPS-feasible H15 result with no external download and no
  memory-sourced citation.
- Forecloses (this pass) the edge-level K-composition recovery and ACDC/AtP* — filed in `todos/`.
- The report must disclose the node-vs-edge granularity as a graded protocol status
  (IDEALIZED/DEVIATED), mirroring the eap-ig study's own §7 node-vs-edge caveat.

## Refs

- Plan `plans/2026-07-03-h15-automated-discovery.md`; parent `docs/tiny-transformer-induction-study.md` §11.
- Engine map (Understand workflow), `implementation/eap_ig/` (read-only reuse).
- Source `download/olsson-induction-heads-2022.pdf` (defn p5, evaluators p58, erratum p48).
- Conversation log `prompts/2026-07-03-mac-handoff-orientation.md`.
