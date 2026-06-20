---
id: 2026-06-20-01
title: Appendix E.5 over-attributed Llama-2-70B's 64-head count to the Llama-2 paper
severity: low
status: fixed
date: 2026-06-20
component: surveys/llms-for-coding/appendix-e-modern-dense.md
plan: plans/2026-06-19-llm-anatomy-appendix-series.md
---

## Symptom

Appendix E.5 read: "Llama-2 adopts GQA at its 34B and 70B sizes (with $H=64$,
$G=8$), keeping full MHA at 7B and 13B [63]." The parenthetical attributed two
specific per-model numbers — a 64-head count and 8 key/value groups — to
reference [63] (the Llama-2 paper). The citation-audit verifier pass over
appendices C–H (workflow `wf_1ce7741b-b4d`) flagged the 64-head figure
`wrong-value`: the Llama-2 paper's Table 1 has only Params / Context / GQA /
Tokens / LR columns and states no per-model head count or hidden dimension
anywhere in its text. The adversarial second reader confirmed it.

## Root cause

The values are themselves correct — Llama-2-70B genuinely has 64 attention heads
and 8 KV groups — but they are *derived* (the 70B is a width-8192 model at
`d_head=128`, so `H = 8192/128 = 64`) and come from the released model config and
the Llama-1 dimension table [65], not from the cited [63]. The "8 KV projections"
*is* stated in [63] (the GQA design); the 64-head count is not. Writing both
numbers behind a single `[63]` citation over-attributed the head count to a
source whose text does not state it — a violation of the citation-integrity rule
(every value attributed to a source must be traceable to that source's text),
even though the value is true.

## Fix

Reworded E.5 to "Llama-2 adopts grouped-query attention — $8$ key/value groups —
at its 34B and 70B sizes, keeping full MHA at 7B and 13B [63]", attributing to
[63] only what its text states (GQA at the larger sizes, MHA at the smaller, the
8-KV-projection design). The 64-head figure is dropped from the citation's scope;
where the 70B head count is actually used (F.3's KV-cache arithmetic) it is
derived from the dimensions, sourced to [65], not to [63]. Commit appended in the
audit report.

## Regression test

none — citation-attribution wording, not a code path. The standing guard is the
`citation-audit` skill (re-run reproduces the verifier verdicts) plus the
`check-citation-sources.py` source-tag invariant. No derivation consumed the
mis-attributed number, so no numeric regression is possible.

## Refs

- Audit report: `reports/citation-audit-appendices-c-h-2026-06-20.md` (Phases 4–5).
- Related rule: `.claude/rules/citation-integrity.md` (value-traceability).
- Conversation log: `prompts/2026-06-17-viewer-sync.md` (citation-audit turn).
- Impact: non-load-bearing — F.3's $262$ GB vs $33$ GB 70B KV-cache result derives
  `H=64` from the [65]-sourced dimensions and is unaffected.
