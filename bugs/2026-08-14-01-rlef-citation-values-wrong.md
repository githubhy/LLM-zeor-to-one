---
id: 2026-08-14-01
title: RLEF citation in §8.3 misreads a valid/test pair as a before/after pair, and reports two values that do not exist in the source
severity: high
status: fixed
date: 2026-08-14
component: surveys/llms-for-coding (instruction-tuning-and-alignment.md §8.3)
---

## Symptom

`surveys/llms-for-coding/instruction-tuning-and-alignment.md` §8.3 stated, citing
reference [20] (RLEF, arXiv:2410.02089, `download/rlef-2024.pdf`):

> the 70B model improves from 37.5 to 40.4 on validation and reaches 41.2 on test
> (versus 38.0 with feedback limited to public tests)

Four distinct errors in one sentence:

1. **37.5 and 40.4 are not a before/after pair.** In the source's Table 1, `37.5` is the
   RLEF-trained 70B model's **validation** score and the adjacent cell is its **test**
   score. The survey read one row's *valid/test* pair as a *pre/post-RLEF* pair on
   validation alone.
2. **40.4 is not in the source.** The adjacent cell reads **40.1**.
3. **41.2 does not appear in Table 1 at all.**
4. **"versus 38.0 with feedback limited to public tests" describes an ablation the paper
   does not report.** No public-tests-only ablation row exists in Table 1.

Net effect: the *direction* of the claim (RLEF improves CodeContests performance) survived,
while the effect size was materially understated and two of the four numbers were
unsourceable. The real improvement is roughly **11.6 points** on validation, not the ~2.9
the sentence implied.

## Root cause

A two-column results table (`Valid Set` | `Test Set`) read as a one-dimensional
before/after sequence. This is the failure mode a values-checking pass catches only if it
re-reads the *table structure* rather than grepping for the numbers: every individual digit
string in the sentence except `41.2` and `40.4` does appear somewhere in the paper, so a
substring check would pass. What is wrong is the **row-and-column assignment**, i.e. the
semantics of the citation rather than its tokens.

The verified Table 1 rows (CodeContests, `n@k` = 1@3):

| Model | Valid | Test |
|---|---|---|
| Llama 3.1 70B Instruct | 25.9 | 27.5 |
| + RLEF | **37.5** | **40.1** |

with `AlphaCodium gpt-4-0613` at 5@100 scoring 44 valid / 29 test.

## Fix

Rewrote the §8.3 sentence to state the actual before/after pair on each split, the sample
budget those numbers are measured at (1@3 — load-bearing, since the same table reports very
different values at 10@100), and the correct AlphaCodium comparison. Commit: see the
max-mode expansion commit for `surveys/llms-for-coding`.

## Regression test

none — this is a prose-content citation error, not code. The systemic control is the
`citation-audit` skill, which is the pass that would catch the class; this instance was
surfaced by an evidence agent reading the primary PDF while collecting for a different
question, and then verified independently against `download/rlef-2024.pdf` Table 1 before
the fix was applied.

## Refs

- Source of record: `download/rlef-2024.pdf`, Table 1.
- Surfaced by: cluster C5 of the max-mode evidence round
  (`surveys/llms-for-coding/_scratch/max-c5.md`), which flagged the discrepancy and
  recommended a citation-audit follow-up rather than asserting the correction itself.
- `.claude/rules/citation-integrity.md` — the rule this violates ("every cited number has
  been reproduced from the source").
- Related todo: `todos/2026-08-14-llms-for-coding-followups.md` (a full `citation-audit`
  pass over the pre-existing body sections is now warranted — this error was found by
  accident, which means the population has not been audited).
