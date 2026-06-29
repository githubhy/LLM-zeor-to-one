---
id: 2026-06-29-06
title: Make §A.20's X "closer to practice" via residual accumulation + a caveat note, not a fully dense embedding
status: accepted
date: 2026-06-29
plan: n/a (direct request)
---

## Context

After clarifying that real models have $|\mathcal{V}| \gg d$ with dense (superposed)
embeddings — not the toy's $d=2|\mathcal{V}|$ one-hot blocks — the user asked to
(a) rename the vocabulary symbol to $|\mathcal{V}|$ (so it no longer collides with the
§A.19 value matrix $V=XW_V$) and (b) "make the X in A.20 more close to what's in
practice." A fully realistic $X$ — dense embeddings, $|\mathcal{V}| \gg d$ — would
destroy the legible, written-out-in-full arithmetic that is the whole point of
§A.19/§A.20.

## Decision

Rename vocab size $V \to |\mathcal{V}|$ throughout §A.20 and Figure A.13. Make $X$
"closer to practice" by (1) showing $X^{(2)}$ as the residual **accumulation**
$X^{(2)} = X^{(1)} + \Delta X^{(1)}$ (token embedding + previous-token-head write —
the recurrence Eq (26) applied, the structurally faithful part), and (2) adding a
"How this differs from a real residual stream" Note: the one-hot blocks and
$d=2|\mathcal{V}|$ are a legible basis, while in practice embeddings are dense,
$|\mathcal{V}| \gg d$, and own/prev/positional features are superposed directions in
one width-$d$ stream. The worked numbers stay one-hot (legible).

## Alternatives considered

- **Fully dense embedding (genuinely realistic $X$).** Rejected: $M$ and $W_{OV}$
  become dense, the score/softmax arithmetic becomes opaque, and the section loses
  the "written out in full" legibility that motivated it. Offered to the user as a
  follow-up if they want it.
- **Decouple $d > 2|\mathcal{V}|$ with inert "other content" dimensions.** Rejected:
  zero-padding extra dims is no more realistic than $d=2|\mathcal{V}|$ (real features
  are superposed, not zero-padded subspaces) and adds clutter; the caveat Note makes
  the point honestly without fake dimensions.
- **Caveat note only (no structural change).** Rejected as too little: the
  accumulation $X^{(2)}=X^{(1)}+\Delta X^{(1)}$ is a genuine, legible realism gain —
  it shows the stream as a running sum and that layer 1 *produced* the prev block.

## Consequences

- §A.20 equations are now (27) accumulation, (28) circuits $M$/$W_{OV}$, (29) $S$,
  (30) $A$, (31) copy. The new circuits equation got a fresh ID (`A-20-1b`) so the
  marker system auto-cascaded the downstream tags and refs (3 tag + 3 ref updates)
  without renaming the existing eq IDs. 31 eq tags, validate-refs 0/0.
- A "How this differs from a real residual stream" Note (dense, $|\mathcal{V}|\gg d$,
  superposition) cross-links §A.13 / §A.1 / §A.15.
- Vocabulary size is $|\mathcal{V}|$ in §A.20, disambiguated from the §A.19 value
  matrix $V$.
- The legible one-hot worked numbers are retained; full dense realism remains an
  open option (a `todos/` candidate only if the user requests it — not filed, since
  it is offered, not deferred).

## Refs

- File: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.20;
  `figures/qkv-two-layer-trace.{py,svg,json}`
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 13
- Related: bug `2026-06-29-01` (the column-convention fix); decision `2026-06-29-05`
  (the §A.19/§A.20 worked examples)
