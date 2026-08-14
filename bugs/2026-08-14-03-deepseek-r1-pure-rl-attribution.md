---
id: 2026-08-14-03
title: §4 attributes DeepSeek-R1's 96.3rd-percentile Codeforces result to the pure-RL recipe, contradicting §9 of the same survey
severity: high
status: fixed
date: 2026-08-14
component: surveys/llms-for-coding (historical-evolution.md §4)
---

## Symptom

`historical-evolution.md` stated:

> DeepSeek-R1 (2025) showed that competitive-programming-level ability can *emerge from
> reinforcement learning with verifiable, rule-based rewards alone* — no supervised
> reasoning traces required — **reaching the 96.3rd percentile on Codeforces**.

Both halves of the characterisation fail for the model that scores 96.3.

The value 96.3 is transcribed correctly, and the paper does contain it — which is why no
value-checking pass would flag this. What is wrong is **which model it belongs to**.

## Root cause

DeepSeek-R1's Table 3 reports a five-column progression across training stages:

| | R1-Zero | Dev1 | Dev2 | Dev3 | R1 |
|---|---|---|---|---|---|
| Codeforces (percentile) | **80.4** | 84.5 | 90.5 | 92.1 | **96.3** |
| Codeforces (rating) | 1444 | 1534 | 1687 | 1746 | 2029 |

- **R1-Zero** is the SFT-free model — "we bypass the conventional supervised fine-tuning
  (SFT) phase before RL training" — trained with rule-based accuracy and format rewards
  only. It reaches the **80.4th** percentile.
- **R1** (the 96.3 figure) is a multi-stage pipeline: cold-start SFT on human-aligned
  reasoning traces, RL, rejection-sampling SFT over reasoning *and* non-reasoning data,
  then a second RL stage whose reward is
  `Reward_reasoning + Reward_general + Reward_language` with
  `Reward_general = Reward_reward_model + Reward_format` — i.e. **a model-based preference
  reward is mixed in**.

So the sentence is wrong twice over: supervised reasoning traces *are* used for the 96.3
model, and its rewards are *not* rule-based alone.

**The decisive evidence that this is an error rather than deliberate shorthand:** the
survey's own §9 states the decomposition correctly, distinguishing R1-Zero's pure-RL recipe
from the production R1's cold start. The offending sentence cross-references §9 while
contradicting it.

## Fix

Rewrote the §4 sentence to carry both models and both numbers: R1-Zero at the 80.4th
percentile (rating 1444) as the pure-RL result, and the production R1 at the 96.3rd
(rating 2029) with its actual recipe named. The survey's thesis is unharmed — pure RL
reaching the 80.4th percentile with no supervised traces is still the striking claim — it is
now attributed to the model that earned it.

Deliberately **not** changed: `executive-summary.md` carries a looser version of the same
sentence that asserts neither "alone" nor "no supervised traces", and is defensible as
written. Sweeping it into this fix would have been overcorrection.

## Regression test

none — prose citation content. The systemic control is the `citation-audit` pass that found
it; this instance was surfaced by the automated audit's verify stage and then independently
upheld by an adversarial reviewer that attempted to refute it and could not.

## Refs

- Source of record: `download/deepseek-r1-2025.pdf`, Table 3 and §§1–3.
- Found by the citation-audit workflow over §§1–11/14–18 (196 claims checked); the finding
  survived adversarial refutation.
- Same class as `bugs/2026-08-14-01` — a **multi-column table read along the wrong axis**,
  where every digit is present in the source and only the row/column assignment is wrong.
  Two instances of one failure mode in one survey is a pattern, not a coincidence: see the
  *Patterns* note in `field-notes/2026-08-14-citation-audit-and-followups.md`.
- `.claude/rules/citation-integrity.md` — plausible-but-wrong attribution is the named
  failure this rule exists to prevent.
