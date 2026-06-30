---
id: 2026-06-30-01
title: Figure A.10 caption reuses the symbol d_k for two scales (demo d_k=8 vs grounded d_k=64) within one caption, reading as a contradiction
severity: low
status: fixed
date: 2026-06-30
component: surveys/llms-for-coding (appendix-a, Figure A.10 caption)
plan: n/a (reader-flagged)
---

## Symptom

Figure A.10's caption (`surveys/llms-for-coding/appendix-a-qkv-first-principles.md`
§A.10) stated, for the right panel, "Eight independent QK circuits … each
genuinely of rank $\le d_k = 8$", and three sentences later "the conserved
budget $h\,d_k = 8\times 64 = 512 = d_{\text{model}}$". A reader (correctly)
flagged the `8` vs `64`: the same symbol $d_k$ carries two different values in
one caption with no flag that the scale switched, which reads as an arithmetic
error.

## Root cause

Not a wrong value — a symbol collision. The figure deliberately mixes two
scales (qkv-multihead-sum.py docstring 31–33):

- **Right panel (Panel B)** is a *reduced demo* — `d=64, dk=8, hB=8, T=9`
  (qkv-multihead-sum.py:74). Each $M^{(\ell)} = W_Q^{(\ell)\top}W_K^{(\ell)}$ has
  $W_Q^{(\ell)}, W_K^{(\ell)} \in \mathbb{R}^{8\times 64}$, so rank $\le 8$; the
  script verifies the ranks via `np.linalg.matrix_rank` (qkv-multihead-sum.py:94,
  236). So "rank $\le d_k = 8$" is accurate *for the demo that ran*.
- **Budget strip + left panel** use the grounded base-Transformer dims —
  `d_model=512, h=8, d_k=d_v=64` (qkv-multihead-sum.py:60, 179), so
  $h\,d_k = 8\times 64 = 512$.

The caption disclosed the demo's reduced $T = 9$ but not its reduced $d_k = 8$,
and let the demo's $d_k$ and the grounded $d_k$ share the bare symbol. Both
numbers are correct; the caption just failed the figure-operating-conditions
disclosure (`.claude/rules/figure-operating-conditions.md`) by not stating the
demo dims numerically and not marking which scale each $d_k$ belongs to.

## Fix

Caption-only edit (no figure rerun — the rendered numbers were already right):

- rank clause → "each genuinely of rank $\le 8$ — the *reduced demo's* $d_k$
  (demo scale: width $d = 64$, $h = 8$, $d_k = 8$, $T = 9$; distinct from the
  grounded $d_k = 64$ used by the left panel and the budget strip below) —".
- budget-strip clause → "the conserved budget at the *grounded* base-Transformer
  scale ($d_k = 64$), $h\,d_k = 8\times 64 = 512 = d_{\text{model}}$".

Commit SHA: (pending — not committed this turn unless asked).

## Regression test

none — prose/caption clarity, not a computed value. The figure script already
self-checks the demo ranks against `d_k = 8` (qkv-multihead-sum.py:236) and the
additivity identity to machine epsilon (line 68), so the underlying numbers are
guarded; only the caption wording changed.

## Refs

- File: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.10,
  Figure A.10 caption (paragraph `a10-multiple-heads-a-sum-of-low-rank-circuits-4`)
- Figure script: `surveys/llms-for-coding/figures/qkv-multihead-sum.py`
- Rule: `.claude/rules/figure-operating-conditions.md` (numeric demo-dim
  disclosure)
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 22
