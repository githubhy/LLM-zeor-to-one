---
id: 2026-08-14-04
title: Six medium/low citation errors surfaced by the §§1-11/14-18 audit (values, scope, and one unsupported attribution)
severity: med
status: fixed
date: 2026-08-14
component: surveys/llms-for-coding (§§5, 3, 8, 14)
---

## Symptom

The citation-audit pass over sections 1–11 and 14–18 checked 196 claims against their
source PDFs and alleged 10 errors; an adversarial pass upheld 7 and refuted 3. One upheld
finding is `high` and filed separately (`bugs/2026-08-14-03`). The remaining six are
recorded here.

| # | Location | Class | Was | Is |
|---|---|---|---|---|
| 1 | `language-models-from-first-principles.md` | WRONG_VALUE | CodeRL RL over "$\approx 10^4$" APPS problems | **5,000** — the training half of APPS's 50-50 split (2639 + 2000 + 361) |
| 2 | `language-models-from-first-principles.md` | WRONG_VALUE | "Chinchilla reports $a=b=0.50$ from two methods" | only **one** method gives 0.50/0.50; IsoFLOP gives **0.49/0.51**, parametric 0.46/0.54 |
| 3 | `compute-cost-and-latency-tradeoffs.md` | WRONG_VALUE | AlphaCode "requires sampling thousands of candidates" | up to **a million** samples per problem, ~99% filtered, clustered to ≤10 submissions |
| 4 | `compute-cost-and-latency-tradeoffs.md` | NOT_IN_SOURCE | the 1.4 s → 0.7 s vendor latency figure cited to Leviathan et al. | that paper measures T5-XXL, not vendor completion latency; citation removed, the vendor source retained |
| 5 | `instruction-tuning-and-alignment.md` | OVERSTATED | "Qwen2.5-Coder's DPO preferences come from a code sandbox rather than human labels" | sandbox only for **self-contained** snippets; complex ones fall back to an **LLM judge** |
| 6 | `the-code-model-pipeline.md` | UNSUPPORTED | "all three reports tie FIM specifically to the completion deployment" | StarCoder frames FIM as enabling tasks *beyond* completion |

## Root cause

No single mechanism; three distinct ones, which is itself informative:

- **1 and 2 are aggregation errors** — a total quoted where a split was meant (10,000
  problems where only the 5,000-problem train half is used), and three table rows collapsed
  into "two methods and a third" when the middle row differs from both.
- **3 is a directional understatement** that inverts the point being made. The section is
  *about* the cost of test-time compute; "thousands" instead of "a million" understates the
  argument by three orders of magnitude, so the error weakens the survey's own case.
- **4, 5 and 6 are scope errors** — a citation carried past what its source supports.
  Finding 5 is the most consequential of the three: the sentence was making an argument that
  execution-derived rewards cannot be gamed, and the LLM-judge branch it omitted is
  precisely a learned, gameable reward model. The correction now says so.

## Fix

All six corrected in place as targeted edits. Finding 1 additionally required fixing the
**result-of-record artifacts** behind a figure — `figures/training-and-serving-economics.py`
(four occurrences, including the plot annotation) and its `.json` sidecar — and re-rendering
the SVG, since a prose-only fix would have left the wrong value live in the data the figure
regenerates from.

Three alleged errors were **refuted** and deliberately not "fixed": DeepSeek-Coder's
87/10/3 data mixture (verbatim in the source), an efficiency claim the accuser scoped to the
wrong section of a survey, and a license-detection sentence carrying *two* citations where
the accuser audited only one. Recording refutations matters — acting on them would have
introduced errors into correct prose.

## Regression test

none — prose citation content. The audit itself is the control, and it is now a repeatable
one: the per-source verification packets are preserved under
`surveys/llms-for-coding/_scratch/audit/`.

## Refs

- `bugs/2026-08-14-03` — the `high` finding from the same pass.
- `bugs/2026-08-14-01` — the RLEF error that motivated running this audit at all.
- Sources of record: `download/coderl-2022.pdf` (§4.2), `download/hoffmann-chinchilla-2022.pdf`
  (Table 2), `download/alphacode-2022.pdf` (§4.4, Tables 5/9),
  `download/leviathan-speculative-decoding-2023.pdf`, `download/qwen25-coder-2024.pdf` (§4.2),
  `download/starcoder-2023.pdf` (§6.2.3).
- `todos/2026-08-14-llms-for-coding-followups.md` item 1 — the todo this closes.
