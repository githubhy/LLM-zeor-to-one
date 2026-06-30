---
id: 2026-06-30-02
title: §A.11 said a head has "six raw matrices"; a head has four (W_Q, W_K, W_V, W_O)
severity: low
status: fixed
date: 2026-06-30
component: surveys/llms-for-coding (appendix-a §A.11 + Figure A.11)
plan: n/a (reader-flagged during the §A.11 explicit-parameters enrichment)
---

## Symptom

§A.11 twice asserted the head is "meaningful only as the pair $(M, W_{OV})$,
never as the **six** raw matrices" — once in the prose (paragraph
`a11-…-4`) and once in the Figure A.11 caption — and the rendered figure's
left-panel title (`qkv-coadaptation.py` → `qkv-coadaptation.svg`) printed the
same "six raw matrices."

## Root cause

A miscount. A single attention head has **four** learnable projection
matrices: the QK path $W_Q, W_K$ and the value path $W_V, W_O$ (§A.4 makes this
explicit — the value-path gauge is $W_V \mapsto S^{-1}W_V$, $W_O \mapsto W_O S$,
and the total raw-matrix gauge is $d_k^2 + d_v^2$, i.e. two $\mathrm{GL}$
groups, one per circuit). The two circuits are products of these four:
$M = W_Q^\top W_K$ and $W_{OV} = W_O W_V$. There is no sixth (or fifth) matrix;
"six" has no basis. The error was localized to §A.11's framing (prose + caption
+ figure title); §A.4 and §A.12 state the count/relations correctly.

## Fix

"six raw matrices" → "four raw matrices $W_Q, W_K, W_V, W_O$" in:

- §A.11 prose (the co-adaptation paragraph),
- the Figure A.11 caption,
- `figures/qkv-coadaptation.py` (docstring + left-panel title), and the
  regenerated `figures/qkv-coadaptation.svg`.

Fixed as part of the §A.11 explicit-parameters enrichment (which also defines
$L$, names all four matrices in the setup, and adds the parameter-gradient
table). Commit SHA: (pending — not committed this turn unless asked).

## Regression test

none — prose / caption / figure-title text, not a computed value. The figure's
computed quantities (softmax weights, output, signed dots) are unchanged by the
title edit, and the script remains deterministic.

## Refs

- File: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.11
- Figure: `surveys/llms-for-coding/figures/qkv-coadaptation.{py,svg}`
- Corroborating count: §A.4 (gauge $d_k^2 + d_v^2$), §A.12 (the two circuits)
- Related decision: `2026-06-30-02` (cascade-free parameter-gradient table)
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 26
