---
id: 2026-06-30-02
title: Present §A.11's four parameter gradients as a cascade-free markdown table, not a new numbered equation
status: accepted
date: 2026-06-30
plan: n/a (direct request — "make §A.11 explicit about every parameter, no step escaping")
---

## Context

The user asked to articulate $L$ and make §A.11 explicit about every parameter
(e.g. $W_O$), "not letting any intermediate step escape." The section derived
the score gradient $\partial L/\partial s_{im}$ (Eq 13) and the weight gradient
$\partial L/\partial a_{ij}$ (Eq 12) but never connected them to the four
learnable matrices' gradients ($\partial L/\partial W_O$, $\partial L/\partial W_V$, $\partial L/\partial W_Q$, $\partial L/\partial W_K$) — the missing "last step."
Presenting those four gradients needed a form.

## Decision

Add the four parameter gradients as a **cascade-free markdown table** (one row
per matrix, with the one-line chain-rule derivation stated in the surrounding
prose), not as a new numbered `$$…$$` equation. Also: define $L$ explicitly in
a new setup, name all four matrices + the forward pass, and make $W_O$ explicit
inside $\boldsymbol{\delta}_i = W_O^\top\mathbf{g}_i$.

## Alternatives considered

- **A new numbered display equation** for the four gradients. Rejected: it would
  mint a `\tag` immediately after Eq (13) and cascade every later equation in
  the appendix (Eqs 14–31 → 15–32, ~18 tag renumbers plus their `[(N)]` ref and
  cross-file xref updates) for a single added equation — a large, noisy diff
  disturbing the whole appendix, with no benefit over a table for four parallel
  results. (The marker system *can* do this safely; the cost is reviewability.)
- **Dense inline prose.** Rejected: four heavy `\frac`/`\sum`/`\top` expressions
  inline in running text are unreadable.
- **Cascade-free table (chosen).** Localized diff (no equation renumber — 31
  tags unchanged), clean parallel presentation of the four gradients, the
  explicitly-endorsed cascade-free device for tabular results; the two heaviest
  cells were parse-checked against KaTeX 0.16.21.

## Consequences

- §A.11 now: (1) a setup naming $W_Q,W_K,W_V,W_O$, the full forward pass, and
  $L$ (the scalar next-token cross-entropy); (2) $W_O$ made explicit in
  $\boldsymbol{\delta}_i=W_O^\top\mathbf{g}_i$; (3) the parameter-gradient table
  closing the loop to all four matrices; (4) "six raw matrices" → "four" (bug
  `2026-06-30-02`), incl. the regenerated Figure A.11.
- The parameter-gradient *table* itself adds no equation cascade (+2 paragraphs
  anchored; validate-refs 0/0; KaTeX-checked). **Follow-up (same session):** a
  separately-requested explicit $L$ definition — the autoregressive
  cross-entropy — was then added as a *numbered display* (now Eq 11), which does
  cascade (31 → 32 tags; Eqs 11–31 → 12–32, refs/anchors auto-updated). This is
  consistent, not contradictory: a single foundational definition earns a
  numbered equation, whereas four parallel derived gradients are clearer as a
  table.
- The four gradients were re-derived and verified by shape and by the
  column-convention chain rule before writing.

## Refs

- File: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.11;
  `figures/qkv-coadaptation.{py,svg}`
- Related bug: `2026-06-30-02` (six→four count)
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 26
