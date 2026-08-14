---
slug: llms-for-coding-followups
date_filed: 2026-08-14
status: closed
---

**Resolution.** All six items closed 2026-08-14, in the same session that filed them.

1. **Citation audit — DONE.** 196 claims checked against source PDFs across §§1–11/14–18 by
   16 source-grouped verifiers, then every alleged error adversarially tested. 186 correct,
   10 alleged, **7 upheld / 3 refuted**. Fixed: `bugs/2026-08-14-03` (high — the DeepSeek-R1
   pure-RL attribution, a second wrong-axis table read) and `bugs/2026-08-14-04` (six med/low).
   The 30% false-alarm rate is why the refute stage existed; acting on those three would have
   damaged correct prose.
2. **Unexpanded sections — DONE.** §11 retrieval (602 → ~1,900 words), §14 cost, §15 SOTA,
   §16 safety all rewritten from the collected evidence plus 19 newly acquired sources. The
   `_scratch/max-c*.md` ledgers are now consumed rather than orphaned.
3. **2026 SOTA table — DONE, and better than planned.** Rather than a leaderboard screenshot,
   §15 is built from the SWE-bench team's own per-submission `results.json` files: 134
   submissions, a 4.4% → 79.2% progression on a fixed 500-instance denominator, and two
   near-controlled pairs. The blocker recorded here ("needs a headless browser") was wrong —
   the primary source publishes structured data.
4. **Code→reasoning transfer — DONE, and it is measured.** New §7.5 written as a deflation:
   exactly one controlled ablation exists, its headline +8.2% is a pre-cooldown comparison at
   470M only, and the paper's own post-cooldown table shows +1.5% with world knowledge going
   to the *text-only* arm.
5. **Source acquisition — DONE.** 19 sources acquired and identity-verified; references
   97 → 130 entries, 0 errors index-mode, 97 → 117 strong-`local:`.
6. **Multi-agent replication gap — DONE, and sharpened.** §12.7 now reports the significance
   tests the papers omit, computed from their own integer counts: two of three flagship
   effects do not clear p<0.05 (p=0.17, p=0.44), the surviving one is budget-confounded, and
   one control's cost columns are byte-identical to the baseline's self-disclosure, proving it
   was never re-measured. Consolidated into a new §18.6 replication register alongside four
   other claims in the same position.

**Follow-on filed:** `todos/2026-08-14-survey-residual-gaps.md`.


# Follow-ups from the max-mode expansion of `surveys/llms-for-coding`

## Context

The `deep-research-survey` skill was run in `max` mode (`proposed` + `scale: wide` +
`audience: learner`) over the existing survey on 2026-08-14. It delivered Appendix J (four
code-specific derivations), rewrote sections 12 and 13 against 2025–26 evidence, corrected a
high-severity citation error (`bugs/2026-08-14-01`), and added 13 references with 10 newly
acquired sources. The items below were deliberately not completed and are not tracked
anywhere else.

## What is left

### 1. A `citation-audit` pass over the pre-existing body sections — highest priority

`bugs/2026-08-14-01` was found **by accident**: an evidence agent collecting for a different
question happened to read the RLEF paper and noticed the survey's numbers disagreed with
Table 1. The error was a two-column table read as a before/after pair, which a substring
check cannot catch because every digit string involved except two appears somewhere in the
paper.

That means **the population has not been audited**. One error found by chance in a body
written before the citation-integrity rule was in force is evidence about the rate, not
about that one sentence. Sections 1–11 and 14–18 carry roughly 180 citation markers that
have never been checked against their sources. Run the `citation-audit` skill over them.

### 2. Sections not expanded in this pass

The depth-tier allocation approved seven headline sections. Two were rewritten (12, 13),
three were wired to Appendix J and left otherwise intact (7, 8, 9), and two were not touched
(2 scope/modality, 3 language-model fundamentals — the latter already deep). The
`load-bearing` sections were labelled but not expanded:

- **11 Retrieval and repository context** — still the thinnest section in the survey (~590
  words). Evidence is collected and unused in `_scratch/max-c7.md`, including the agentic-
  search-vs-vector-retrieval dispute, RepoGraph and LocAgent results, and a counter-finding
  that repository instruction files can *reduce* success while raising cost.
- **15 State of the art and practice** — the R-SURVEY quantitative SOTA table was not built.
  See item 3 for why.
- **16 Safety, security, licensing** — `_scratch/max-c8.md` holds unused evidence on prompt
  injection against coding agents (the most under-covered threat class in the current text)
  and on the litigation posture as of 2026.
- **14 Compute, cost, latency** — `_scratch/max-c2.md` Q3 and the acquired HAL paper
  (`download/hal-holistic-agent-leaderboard-2025.pdf`) are unused.

### 3. The 2026 frontier leaderboard numbers are deliberately absent

The survey states no current SWE-bench Verified top-of-leaderboard figure. This is a
decision, not an omission: two independent search passes returned figures that disagreed
with each other for the *same* leaderboard, and the authoritative pages render their tables
in JavaScript, which a plain-text fetch does not capture. Recording a number that could not
be reproduced twice would have been worse than recording none.

To close it: acquire vendor system cards via `source-fetch`, or fetch the leaderboard with a
headless browser, and record each figure with its **denominator** — at least three instance
counts circulate for "SWE-bench Verified" (the original 500, plus smaller counts used by
particular evaluators), so a cross-vendor percentage comparison is not a like-for-like
comparison unless each N is stated.

### 4. Evidence-cluster coverage gap: does code training improve general reasoning?

`_scratch/max-c4.md` Q4(c) carries an explicit coverage-gap marker. The claim is widely
repeated and **no source opened in this pass measures it**. Two agents died on the step cap
before reaching the question and the restart-intensity ceiling stopped a third attempt.
Acquire a primary source that measures code-to-reasoning transfer, or state in section 7
that the claim is unverified. Do not resolve it in favour of the popular answer.

### 5. Sources named but not acquired

Each `_scratch/max-c*.md` ends with a `## Sources worth acquiring` list. Ten sources were
acquired during this pass; the lists still name others whose numbers are consequently
reported as unverified or omitted — notably the OpenAI post retiring SWE-bench Verified, the
multi-agent coding papers (see item 6), and the UTBoost test-augmentation audit.

### 6. Multi-agent coding: no independent replication exists

Section 12.7 states the question is open rather than reporting the available numbers,
because every ablation located was produced by the team proposing the method, and one system
reports two mutually inconsistent figures for its own resolve rate. Closing this needs a
third party running both arms with a shared base model, a shared token budget, and a control
tuned as carefully as the treatment. This is a genuine research gap, not a literature-search
failure — it is worth stating as such in section 18.

## Acceptance

- `citation-audit` report exists for sections 1–11 and 14–18, with every finding either
  fixed or filed under `bugs/`.
- Sections 11, 14, 15 and 16 either expanded from the collected evidence or explicitly
  re-scoped, with the `_scratch` evidence consumed rather than orphaned.
- Either a sourced 2026 SOTA table with per-row denominators, or a stated decision that the
  survey does not track leaderboard positions.
- Section 7 either cites a measurement of code-to-reasoning transfer or says it is unverified.

## Refs

- `surveys/llms-for-coding/_scratch/00-max-mode-outline.md` — the approved brief and
  depth-tier allocation this pass was measured against.
- `surveys/llms-for-coding/_scratch/max-c1.md` … `max-c8.md` — the evidence ledgers, each
  with its own `## Gaps` and `## Sources worth acquiring` sections.
- `bugs/2026-08-14-01-rlef-citation-values-wrong.md` — the found-by-accident citation error
  motivating item 1.
- `reports/2026-08-14-llms-for-coding-max-mode-expansion.md` — the Phase-5 report.
