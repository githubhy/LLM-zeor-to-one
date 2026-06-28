---
slug: icl-as-online-learning-intuition
date_filed: 2026-06-28
status: open
---

# Add the in-context-learning-as-online-optimization intuition to Appendix A

## Context

§A.6 / §A.16 establish that a single head's score→softmax→combine is a **fixed
matched-filter detector** (Bayes-exact, eq 14–17), and departure (i) sharpens that
"adaptive" there means only *input-dependent*, **not** an LMS/RLS recursive coefficient
update — attention runs no such loop in the forward pass. The user asked whether an
*adaptive-filter* reading fits; the honest answer is that the genuine
adaptive / online-learning reading is a **different, deeper** claim than the per-head
score: the line of work showing a transformer **forward pass** can *implement* a step of
gradient descent / ridge regression over the in-context examples (an across-the-sequence,
multi-layer statement). That is a legitimate "attention as an online learner" intuition,
but it is out of scope for the per-head matched-filter sections and — crucially — its
sources are **not yet in `references.md`**, so writing it now would violate the
citation-integrity rule (no external citation from memory).

## What is left

- `source-fetch` the in-context-learning-as-gradient-descent papers, e.g. von Oswald et al.
  2023 ("Transformers learn in-context by gradient descent"), Akyürek et al. 2023 ("What
  learning algorithm is in-context learning?"), Dai et al. 2023 (GPT as meta-optimizers /
  implicit gradient descent), Garg et al. 2022 ("What can transformers learn in-context?").
  Acquire into `download/`, add `references.md` entries with `local:` source tags.
- Verify each claim against the acquired source (which architecture, which assumptions —
  linear-attention vs softmax, single- vs multi-layer); do not overstate (much of the exact
  result is for linear attention / constructed weights, not trained softmax heads).
- Write a short intuition subsection (e.g. A.17) framing the forward pass as an
  online-optimization / ridge-regression step over in-context examples — the legitimate
  "adaptive / online learner" reading — explicitly contrasted with the per-head matched-filter
  *detection* of §A.6 (the two are different levels: one head's detection vs a stack's
  in-context optimization).

## Acceptance

New intuition subsection added under the survey-explainer-fold / `/enrich` conventions; every
external claim cited to an acquired `download/` source (strong `local:` tags); validation
sweep green; cross-link sign-off cleared.

## Refs

- `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.6 departure (i), §A.16
- `.claude/rules/citation-integrity.md`; `.claude/skills/source-fetch/SKILL.md`
- Conversation log: `prompts/2026-06-28-qkv-index-notation-fold.md` (Conversation 17)
