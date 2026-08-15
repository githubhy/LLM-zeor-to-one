---
id: 2026-08-15-02
title: MEMIT's batched update was written in Appendix E.3 with its factors in an order that does not multiply
severity: med
status: fixed
date: 2026-08-15
component: surveys/mechanistic-interpretability (Appendix E — steering and editing mathematics)
---

## Symptom

`appendix-e-steering-and-editing-math.md` §E.3 stated MEMIT's batched, rank-$u$ generalization of the
ROME update as

```
Delta = R (C + K_1 K_1^T)^{-1} K_1
```

With the shapes the surrounding prose defines — $R \in \mathbb{R}^{H\times u}$ the residuals of the $u$ new associations, $K_1 \in \mathbb{R}^{D\times u}$ the new keys, and $(C + K_1K_1^{\top}) \in \mathbb{R}^{D\times D}$ — the first product requires $u = D$. **The expression is not conformable** for any batch size other than the residual-stream width, and the intended result $\Delta \in \mathbb{R}^{H\times D}$ does not come out.

The source (Meng et al., MEMIT, Eq. 14) prints the factors in the other order:

```
Delta = R K_1^T (C_0 + K_1 K_1^T)^{-1},    C_0 = K_0 K_0^T
```

which checks: $(H\times u)(u\times D)(D\times D) \to H\times D$.

The error was live on `main` — §E.3 predates this session and was not introduced by the current
expansion.

## Root cause

The appendix compressed MEMIT's derivation into a single prose sentence ("whose weighted
least-squares solution is a rank-$u$ update $\Delta = \ldots$") rather than deriving it, and the
factor order was reconstructed from the *shape of the ROME solution* rather than read off the
source. ROME's own closed form is $\hat W = W + \Lambda (C^{-1}\mathbf{k}_*)^{\top}$ — a
residual-like term on the left, an inverse-covariance term on the right — and transposing that
pattern onto the batched case puts the inverse in the middle, which is where it does not belong.

The deeper cause is that **§E.3 was the one equation in the appendix with no derivation attached**.
Every other numbered result in E.2 is developed step by step, and a conformability slip in a derived
line would have been caught when the next line failed to follow. A result stated as a fait accompli
has no next line.

Nothing downstream consumed the wrong form: the survey body's §7.5 describes MEMIT qualitatively and
quotes no formula, so the error was confined to the appendix. It would have misled a reader
transcribing it, which is exactly the population an appendix titled "mathematics" serves.

## Fix

§E.3 now states the update as a numbered equation in the source's factor order, with an explicit
shape annotation naming why the order matters:

> **Note the shapes**, because the factor order is easy to get wrong and a transposed version does
> not even multiply: $R \in \mathbb{R}^{H\times u}$, $K_1 \in \mathbb{R}^{D\times u}$, so
> $R K_1^{\top}\in\mathbb{R}^{H\times D}$ meets a $D\times D$ inverse.

Two further things were added in the same pass, both of which the source states and the appendix had
dropped: that $C_0 \triangleq K_0K_0^{\top}$ is the pre-existing keys' outer product specifically,
and that the batched form **drops ROME's exact equality constraint**, so per-fact exact insertion is
no longer guaranteed.

Commit: see the appendix-deepening commit for 2026-08-15.

## Regression test

none — this is survey prose, not repo code, and no mechanical gate checks matrix conformability in
LaTeX. The durable control is the one the root cause names: **an appendix result stated without a
derivation has nothing to catch it.** The `[opt:MATH-REDERIVE]` independent re-derivation pass is the
process-level backstop, and it is what was run over this appendix in the same session.

Worth noting for the harness: a conformability linter over display math is *conceivable* (parse
`\in \mathbb{R}^{a\times b}` declarations, check products) but the declarations are usually in prose
rather than in the math, so the precision would be poor. Not proposed.

## Refs

- Source: `download/meng-memit-2023.pdf`, §4.2 Eq. (14) — read directly to confirm the factor order,
  not inferred.
- `.claude/rules/workflow.md` `[opt:MATH-REDERIVE]` — the re-derivation pass that covers this class.
- `decisions/2026-08-15-01` — the same session's other citation-integrity finding.
- `field-notes/2026-08-15-mi-appendix-deepening.md`.
