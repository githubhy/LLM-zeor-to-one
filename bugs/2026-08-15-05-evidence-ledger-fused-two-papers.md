---
id: 2026-08-15-05
title: An evidence ledger attributed one paper's headline statistic to a different paper, with a matching-sounding title
severity: med
status: fixed
date: 2026-08-15
component: surveys/multimodal-llms/_scratch (frontier evidence sweep, Q2)
---

## Symptom

`surveys/multimodal-llms/_scratch/ev-frontier-eval.md` line 32 records:

> At least 68.8% of items across 18 widely-used multimodal benchmarks are affected by at
> least one of three systematic distortions: weak visual dependence, item saturation, and
> pseudo-hardness — *source:* arXiv:2602.16763, "When AI Benchmarks Plateau: A Systematic
> Study of Benchmark Saturation"

and the ledger's own Q2 verdict repeats it as one of the sweep's two clearest quantified
findings. `todos/2026-08-15-multimodal-residual-gaps.md` item 1 then directed a future pass
to "fetch the primary PDFs, verify, and then either state the numbers or record that they
did not survive verification" — i.e. to cite it.

The paper does not contain the figure. Fetching `arXiv:2602.16763`
(`download/akhtar-benchmark-saturation-2026.pdf`) shows it studies **60 language-model
benchmarks** using 14 properties, defining saturation as loss of discriminative power
derived from leaderboard uncertainty. It is not multimodal, not 18 benchmarks, not an
item-level audit, and contains no 68.8%.

## Root cause

**Two papers fused into one ledger row.** The 68.8% is real, and belongs to **MMGist**
(arXiv:2606.22437, `download/yuan-mmgist-2026.pdf`) — the other paper the same sweep
section cites, two rows above. It is not a directly-printed number there either: MMGist
states "7,262 items from 18 source benchmarks, representing **31.2%** of the original
23,250 items," and $1 - 0.312 = 0.688$. The three named distortions are MMGist's own three
filter stages, verbatim from its abstract.

So the row's *content* came from MMGist and only the *source line* came from the Akhtar
paper. Every individual element is real; the join is fabricated.

Why it was not caught in-sweep: the wrong attribution is **plausible on every check short
of opening the PDF**. The arXiv ID resolves, the title is real and reads exactly like a
paper that would carry such a statistic, the venue framing is right, and the claim is
thematically adjacent to a paper the sweep genuinely did read. The ledger's own quality
grading (`silver — abstract/summary read via search snippet, not full text`) was *accurate
about its own provenance* and still did not prevent the error: knowing you read a snippet
does not tell you the snippet belonged to a different paper.

This is the same failure class as this session's three wrong `cite:N` numbers
(`field-notes/2026-08-15-multimodal-expansion.md`): a **reference identity** recalled or
inferred rather than read, where the wrong answer is well-formed and therefore survives
every mechanical gate. `check-citation-sources.py` would have passed this entry the moment
a PDF was placed at the tagged path, because it verifies that the file exists, not that the
file says what the citation claims.

## Fix

Nothing shipped in the survey — `decisions/2026-08-15-02` had kept every number in this
class out of the deliverable pending exactly this verification, so the containment held and
no reader ever saw it. That is why this is `med` and not `critical`.

Concretely:

- A **post-hoc verification block** appended to `_scratch/ev-frontier-eval.md` stating that
  line 32's attribution is wrong, what the number actually is, and that nothing may be cited
  to arXiv:2602.16763. The original row is left in place (it is a preserved artifact) with
  the correction reading against it.
- The 68.8% is now stated in § 9.3 of the survey, correctly attributed to MMGist
  `[54]`, derived as the complement of the retention rate rather than quoted as "≥68.8%",
  and tagged *[reported]* with the caveat that it is one pipeline's removal rate at one set
  of thresholds, self-reported by the paper proposing the benchmark that survives it.
- Both PDFs are retained in `download/`. The Akhtar paper is kept deliberately: it is the
  evidence that the mis-attribution *is* one.

## Regression test

none as an automated check, and the reason is worth recording rather than hand-waving: no
mechanical gate in this repo can catch it. The failure is a true statement joined to a real
source that does not make it, and every checkable property — ID resolves, file exists, tag
well-formed, title plausible — holds. The countermeasure is procedural and already in the
rules (`.claude/rules/citation-integrity.md`: a citation is verified only when the cited
section has been read and the number reproduced from it), plus the one cheap habit this
session confirmed twice: **before citing, open the abs page and compare the title to the
claim** — an arXiv ID that resolves to a paper about a different modality and a different
benchmark count is a two-second catch.

## Refs

- `surveys/multimodal-llms/_scratch/ev-frontier-eval.md` — the ledger, with the correction
  block appended at the end.
- `decisions/2026-08-15-02` — the decision that quarantined this number class; the reason
  the survey was never wrong.
- `todos/2026-08-15-multimodal-residual-gaps.md` item 1 — the todo that forced the check.
- `field-notes/2026-08-15-multimodal-expansion.md` — the "the index is memory too" pattern
  this is another instance of, at paper granularity rather than reference-number granularity.
