---
id: 2026-06-29-01
title: §A.19 worked example used the row/data-matrix convention, clashing with §A.1's column convention
severity: med
status: fixed
date: 2026-06-29
component: surveys/llms-for-coding/appendix-a
plan: n/a
---

## Symptom

§A.19 "One Attention Layer, Written Out in Full" presented its worked example in
the row / data-matrix convention — $X\in\mathbb{R}^{T\times d}$ (tokens as rows),
$W_Q\in\mathbb{R}^{d\times d_k}$, $W_O\in\mathbb{R}^{d_k\times d}$, $Q=XW_Q$,
$\text{out}=OW_O$ — while §A.1 (and the whole of Appendix A) defines the **column**
convention: $\mathbf{x}_i$ a column, $X\in\mathbb{R}^{d\times T}$,
$W_Q,W_K\in\mathbb{R}^{d_k\times d}$, $W_V\in\mathbb{R}^{d_v\times d}$,
$W_O\in\mathbb{R}^{d\times d_v}$, with $\mathbf{q}_i=W_Q\mathbf{x}_i$ and
$\Delta\mathbf{x}_i=W_O\mathbf{o}_i$. The numbers were internally self-consistent,
so no gate caught it; the user flagged the dimension convention.

## Root cause

The worked-example matrices were authored in the PyTorch-style data-matrix
(row-token) convention out of habit, without reconciling against the appendix's
established column convention. The mismatch was **not merely cosmetic**: §A.19's
own sentence "the content map $W_{OV}=W_OW_V$ of §A.3" is dimensionally *false*
in the as-written shapes: the product $W_O\,(d_k\times d)\cdot W_V\,(d\times d_v)=d_k\times d_v$,
not the $d\times d$ OV circuit — whereas in §A.1's convention
$W_O\,(d\times d_v)\cdot W_V\,(d_v\times d)=d\times d$. So the row convention
silently contradicted a load-bearing cross-reference. §A.19 was in fact
internally **mixed**: the surrounding $h$-head sum and $\Delta\mathbf{x}_i=W_O\mathbf{o}_i$
references were already written in column form.

## Fix

Rewrote §A.19 to §A.1's column convention — **same computed values, transposed
layout**: $X\in\mathbb{R}^{d\times T}$ (4×3), $W_Q,W_K\in\mathbb{R}^{d_k\times d}$
(2×4), $W_V\in\mathbb{R}^{d_v\times d}$ (2×4), $W_O\in\mathbb{R}^{d\times d_v}$
(4×2); $Q=W_QX$, $S=Q^\top K/\sqrt{d_k}$, $O=VA^\top$, $H=X+W_OO$; equations
(21)–(25), the step prose (each step now cites Equation (2)), and Figure A.12
(script + caption) all updated. Figure recomputed and re-verified via PNG; the
attention matrix $A$ and all numeric values are unchanged. All gates green
(validate-refs 0/0, 28 eq tags sequential, bare-refs clean). §A.20 needed no
change (it uses the convention-neutral bilinear form $\mathbf{x}_i^\top M\mathbf{x}_j$
and component-listed feature vectors). Commit: pending.

## Regression test

none — survey content; the convention is now consistent with §A.1 and the
$W_{OV}=W_OW_V$ product is dimensionally valid. No mechanical gate checks
cross-section convention consistency; this relies on author/reader review (the
user's catch here). A lightweight future guard could grep §A.19/§A.20 for the
$d\times T$ vs $T\times d$ orientation, but it is not worth a dedicated checker.

## Refs

- Files: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.19;
  `figures/qkv-one-layer-forward.{py,svg,json}`
- Found by: user question — "The dimension convention of those matrices are correct?"
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 9
- Related: decision `2026-06-29-05` (the §A.19/§A.20 authoring)
