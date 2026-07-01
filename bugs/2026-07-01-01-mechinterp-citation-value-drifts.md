---
id: 2026-07-01-01
title: Two drifted numeric values in the mechanistic-interpretability survey (ROME AIE attribution; RepE LoRRA deltas)
severity: med
status: fixed
date: 2026-07-01
component: surveys/mechanistic-interpretability
---

## Symptom
Citation-audit (Sonnet verifiers vs. acquired local PDFs) flagged two load-bearing numeric
claims in the draft survey that did not match their primary sources:

1. **ROME causal tracing (§5.1 worked anchor).** Draft: "peak indirect effect $\approx 8.7\%$ at
   layer 15" attributed to **MLP restoration**. Source [31] (Meng et al. 2022, Sec. 2.2 / Fig. 2):
   8.7% is the peak for restoring an **individual hidden state** (Fig. 2a); the **MLP-specific**
   peak is **6.6%** (Fig. 2b) and **attention** is **1.6%** (Fig. 2c). ATE = 18.6% was correct.
2. **RepE LoRRA (§7.2).** Draft parenthetical: "LoRRA +6.6%/+13.1% (7B/13B)". Source [48] (Zou et
   al. 2023, Table 2): LoRRA raises Llama-2-Chat TruthfulQA 31.0→42.3 (7B, **+11.3 pp**) and
   35.9→47.5 (13B, **+11.6 pp**). The +18.1 pp unsupervised-honesty figure WAS correct.

## Root cause
Both drifted values entered via **secondary sources during Phase-3 evidence gathering** (the
evidence ledger had explicitly flagged both: the ROME "6.6-vs-8.7" ambiguity, and the LoRRA
+6.6/+13.1 as "from the GRATH secondary paper, not confirmed against primary"). They were written
into the draft with an inline "verify in citation-audit pass" flag rather than omitted — the
citation-integrity rule's gap-marking fallback working as intended, caught at the audit gate.

## Fix
- §5.1: rewrote to state ATE 18.6%, individual-state peak 8.7% @ layer 15, MLP peak 6.6%,
  attention 1.6% — a sharper, correct statement of the mid-layer-MLP-dominance finding.
- §7.2: replaced +6.6/+13.1 with the verified +11.3 pp / +11.6 pp (with baseline→post values).
- Both inline flags updated to "verified against [primary] in the citation-audit pass".
- No commit yet (survey pending sign-off); SHA to be added on landing.

## Regression test
none — prose citation values; the mechanism is the `citation-audit` gate itself (which caught
these). The verified values are now traceable to the acquired PDFs in `download/`.

## Refs
- Citation-audit workflow `wf_f9750bd8-8f4` (10 verifiers, 25 checks, 21 matched, these 2 + one
  false alarm). Field note: `field-notes/2026-07-01-mechinterp-survey.md`.
- Related: `bugs/2026-06-20-01` (same class — a config/derived value over-attributed to a paper,
  caught by citation-audit).
