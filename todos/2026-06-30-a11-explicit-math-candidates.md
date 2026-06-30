---
slug: a11-explicit-math-candidates
date_filed: 2026-06-30
status: closed
---

# §A.11 (and appendix-a) — remaining prose-only quantities that could be explicit math

## Context

After turning the §A.11 definition of the loss $L$ into an explicit numbered
equation (Eq 11, commit `4d22a50`), the user asked to "check other similar
needs for explicit math." A grep+read audit of `appendix-a-qkv-first-principles.md`
(softmax / logit / gradient-descent / update / learning-rate patterns) found the
remaining prose-only quantities below. The rest of the appendix's foundational
quantities (softmax, posterior, $1/\sqrt{d_k}$ scaling, the induction circuits,
the one-/two-layer traces) already carry explicit equations.

## What is left

1. **Gradient-descent update rule — §A.11 final paragraph (`a11-…-7`).**
   The co-adaptation conclusion ("gradient descent *raises* the score $s_{im}$
   exactly when $\boldsymbol{\delta}_i^\top(\mathbf{v}_m-\mathbf{o}_i)<0$") rests
   on the unstated update $s_{im}\leftarrow s_{im}-\eta\,\partial L/\partial s_{im}$
   (more generally $\theta\leftarrow\theta-\eta\,\nabla_\theta L$) together with
   $a_{im}>0$ (from Eq 14) making the sign of $\partial L/\partial s_{im}$ equal the
   sign of $\boldsymbol{\delta}_i^\top(\mathbf{v}_m-\mathbf{o}_i)$.
   The update rule is the missing explicit step behind "raises/lowers." **(Primary —
   most directly the "no step escapes" gap, parallel to the $L$ request.)**
2. **Output logits $\mathbf{z}_t$ — §A.11 Eq 11.** $\mathbf{z}_t$ is used in
   Eq 11 but defined only as "the model's output logits." Its production is the
   unembedding $\mathbf{z}_t = W_U\,\mathbf{x}^{(\text{final})}_t$ (the map $W_U$
   is already named in the §A.9 logit-position Note). A half-clause linking Eq 11's
   $\mathbf{z}_t$ to $W_U$ would close it. **(Secondary — slightly outside the
   head's scope.)**
3. **(Optional) survey-wide sweep.** Appendices B–H were not audited; a
   parallel sweep for prose-only foundational quantities (esp. the optimizer /
   backward-pass appendices) could surface analogous gaps.

## Acceptance

Each item above is either rendered as an explicit equation/relation (inline or
numbered, cascade-aware) or explicitly ruled out with a one-line reason; the
renumber/validate sweep stays clean; KaTeX-checked if a new display equation.

## Refs

- File: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.11
- Prior work: commit `4d22a50` (explicit $L$ Eq 11); decision `2026-06-30-02`
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversations 28 (filed), 29 (resolved)

## Resolution

**Resolved 2026-06-30 (Conversation 29) — all three applied/closed, inline (no equation cascade).** (1) **Update rule** added to §A.11's co-adaptation paragraph: $\theta\leftarrow\theta-\eta\,\partial L/\partial\theta$, and for a score $s_{im}\leftarrow s_{im}-\eta\,\partial L/\partial s_{im}$, with the $a_{im}>0$ sign link making the descent direction explicit; cross-linked to §C.4 (the Adam variant). (2) **Output logits** made explicit in Eq 11's prose: $\mathbf{z}_t = W_U\,\mathbf{x}_t^{\text{(out)}}$ (the unembedding of §A.9 on the final residual stream). (3) **B–H sweep:** the loss / cross-entropy, the softmax-CE gradient, and the optimizer update are *already* explicit equations in appendix-c — §C.2 (cross-entropy output), §C.3 (softmax+CE gradient), §C.4 (Adam, with the SGD baseline $\theta\leftarrow\theta-\eta\,\mathrm{d}\theta$) — so there was no analogous prose-only gap to fill; §A.11 now cross-links §C.4 instead. validate-refs 0/0 (118 .md links); 32 eq tags unchanged.
