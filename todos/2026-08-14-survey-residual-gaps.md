---
slug: survey-residual-gaps
date_filed: 2026-08-14
status: open
---

# Residual gaps after closing the `llms-for-coding` follow-ups

## Context

`todos/2026-08-14-llms-for-coding-followups.md` is closed: all six items done. The
completeness critics that reviewed each evidence cluster named specific residual work that
did not block writing any section but is worth having. These are small, bounded lookups —
none is a research question.

## What is left

### 1. Denominator checks on one paper's per-task movements (§7.5)

`code-data-training-stage-reasoning-2023.pdf` reports a headline "logic" gain of 36.36 → 40.90.
That benchmark has **N = 22** — verified arithmetically, since every reported value is an exact
multiple of $1/22$ — so the improvement is **one question**, Wilson interval roughly [21%, 55%].
§7.5 says so. What is *not* checked is whether the same paper's other 2–4 point movements
(E-KAR, ScienceQA, JEC-QA) are also one- or two-example artifacts. JEC-QA is pinned at N ≈ 1000;
E-KAR and ScienceQA test-set sizes are unresolved. One lookup each. Until then §7.5's treatment
of those tasks should be read as uncertain-N.

Also unrecovered: that paper's code-to-text pretraining ratio, lost to a truncated agent payload.

### 2. Truncated extraction payloads

Two agent returns were cut mid-record and their evidence was reconstructed by the critic from
the PDFs rather than by the extractor:

- **CoIR** — zero records returned despite the paper being read. §11.2's numbers (best model
  56.26 average NDCG@10, BM25 29.79, hardest subset 26.52) come from the critic's direct read.
  They are verified but not independently double-extracted.
- **SWE-Debate** — every record missing from the payload; its content survives only in the
  critic's prose. §12.7's use of it (207/500 vs 194/500, and the relative-versus-absolute
  reporting inconsistency) rests on that single read.

Neither is wrong; both are single-sourced where the design intended two passes. Re-extract if
either is ever load-bearing for a stronger claim than the current hedged one.

### 3. An arithmetic error in an external paper, noted but not reported upstream

`copilot-security-replication-2023.pdf` states its 2021 baseline as 36.54%, which does not
reconcile with the original's published 219/571 = 38.35%. The discrepancy traces to a single
mis-transcribed cell in its own comparison table (one scenario recorded as 22 valid / 1
vulnerable where the original gives 21 / 11). §16.1 uses the original's published figure and
notes the discrepancy parenthetically.

**Deliberately not filed under `bugs/`** — `bugs/` records defects in *this* repo's work, and
this survey did not propagate the error. If a future pass wants to be a good citizen, the
finding is worth an email to the authors.

### 4. Sources still named-but-unacquired

The per-cluster `## Sources worth acquiring` lists are now mostly consumed, but a few remain,
none load-bearing for any current claim: the OpenAI post retiring SWE-bench Verified (a vendor
blog, cited in §13.5 as reported-not-verified), the UTBoost test-augmentation audit, and a
primary court-docket source for the licensing posture in §16.4 (currently secondary).

### 5. Research gaps — tracked in the survey, not here

The five open replication questions now live in **§18.6** of the survey itself, which is the
right home for them: they are contributions, not chores. This todo does not duplicate them.

## Acceptance

- E-KAR and ScienceQA test-set sizes resolved, and §7.5's uncertain-N caveat either tightened
  or confirmed.
- CoIR and SWE-Debate evidence double-extracted if either becomes load-bearing.
- The remaining acquisition list either fetched or explicitly retired.

## Refs

- `todos/2026-08-14-llms-for-coding-followups.md` — the closed parent.
- `surveys/llms-for-coding/_scratch/max-c*.md`, `_scratch/audit/packet-*.md` — the evidence and
  verification artifacts.
- `field-notes/2026-08-14-citation-audit-and-followups.md` — the session retrospective.
