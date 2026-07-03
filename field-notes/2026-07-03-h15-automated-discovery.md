# Field notes — 2026-07-03 — H15 automated-discovery sub-study

## Context

Picked up H15 (automated circuit discovery) from the Mac handoff backlog and ran it
end-to-end: reused the `eap_ig` engine read-only to test whether EAP/EAP-IG recover
GPT-2-small's induction heads against a computed Olsson prefix-matching oracle. Several
issues surfaced and were resolved inline within the session; capturing them here.

## Issues found and resolved

- **Olsson "preceded/followed" wording near-miss (citation).** The Understand-phase agent
  quoted Olsson's prefix-matching score as attention "back to the tokens that preceded the
  same token," which — read literally — points at the *predecessor* of the previous
  occurrence, the opposite of the induction direction. Resolved by reading the source myself:
  the definition (p5, "the token which induction would suggest comes next"), the erratum
  (p48, 2022-09-20 corrected exactly this preceded/followed wording), and the empirical
  check (my metric attends to the *follower* and recovers the canonical heads). No-todo
  because it was fully reconciled and the code direction was validated. A clean example of
  why citation-integrity says read the source, not the paraphrase.

- **Quick-run vs full-run artifact confusion.** After launching the full run I read
  `summary.json` and nearly reported its numbers — but it was the *quick* run's output
  (threshold 0.15, 1 seed, n=16); the full run writes `summary.json` only at completion, and
  an intervening kill left stale data. Caught by checking `threshold`/`nseeds`/`head_scores`
  before trusting any number. Lesson: for a study whose artifact is overwritten only at the
  end, always verify the artifact's own provenance fields before quoting it.

- **MPS cost-measurement artifact.** 1-rep cost timing put EAP (3 passes) at 50 s > EAP-IG
  (11 passes) at 9.6 s — impossible by op-count; the first-timed method ate a one-time MPS
  scheduling cost. Escalated to `bugs/2026-07-03-01` (not just a field note) because it is a
  wrong-looking number a reader would trip on; resolved by reporting cost via op-count.

- **MPS runtime badly underestimated.** Estimated ~20 s/seed; actual ~90 s/seed — the
  exact-patching + faithfulness protocol fires ~270 hooked forward passes per seed and MPS
  per-op synchronization dominates. Trimmed the run (batch 64→32, cost reps 3→1) mid-flight
  to keep it tractable. Lesson: hooked, small-batch, many-forward workloads are *not*
  MPS-friendly; the eap_ig study ran them on CPU for a reason.

- **Pre-sign-off adversarial audit earned its keep.** A 4-lens Opus audit (re-derivation /
  stats / confound / citations) caught three real reporting defects the solo pass missed:
  (1) a *pseudo-replicated* faithfulness p-value — pooling 160 per-example values as
  independent when the circuit is fixed per seed inflated significance from the honest
  seed-level p=0.024 to p=5e-29 (→ bug `2026-07-03-02`); (2) stale sample sizes in the report
  (5×50/5×64, the function defaults) after I trimmed the run to 5×30/5×32 — the report even
  self-contradicted its own "160 pooled"; (3) selective reporting — the modest full-head
  Spearman-vs-oracle (~0.55, even exact 0.54) was computed but omitted, over-implying the
  AUROC=0.97 meant full-ranking agreement when it means top-5 separation. All three were
  fixed; the PASS verdict survived (the gate held at the honest p=0.024). Also caught: my
  §10 confound rebuttal was itself *wrong* ("a positional head would depress AUROC") — the
  oracle shares the fixed-offset structure, so I ran an actual jittered-offset robustness
  control to design the confound out instead of hand-waving it. One lens (re-derivation)
  died on a StructuredOutput schema retry, but its coverage overlapped the stats/confound
  lenses which independently verified the task + metric math.

- **Artifact reconciliation without a re-run.** The corrected seed-level faith stat had to land
  in the committed `summary.json`, but the MPS re-run stalled (~30 min, zero seed output — the
  MPS-pathology again) and a CPU re-run projected to ~45–75 min to recompute *byte-identical*
  deterministic values, changing only the representation of one JSON block. Resolved by noticing
  the raw per-example faithfulness was already persisted in `faith.npz` and the recovery block
  already carried the audit-added `spearman_vs_oracle` — so the fix was a pure function of data
  on disk. Added `run.py --refresh-stats` (shared `build_pairwise`/`compute_verdict` helpers so
  the main and refresh paths cannot drift) to recompute the pairwise block + verdict in <5 s with
  no forward passes. No-bug because nothing was *wrong* — it is a reproducibility affordance the
  `faith.npz` persistence was designed to enable; captured as decision `2026-07-04-01`. Lesson:
  when a study persists its raw intermediate arrays, a "re-run to fix the stats" is usually a
  recompute-from-cache, not a recompute-from-scratch — check what's on disk before paying for
  compute.

## Patterns / lessons

- Verify at every substrate boundary: paraphrase→source (citations), artifact→provenance
  fields (which run wrote this?), measured→deterministic (op-count sanity on any timing).
- For a research study, let the data force the honest nuance: H15's headline is AUROC 0.97,
  but recovery@5 = 0.6 and the EAP-vs-EAP-IG head-recovery tie are the parts that make the
  claim credible — report them, don't smooth them.
