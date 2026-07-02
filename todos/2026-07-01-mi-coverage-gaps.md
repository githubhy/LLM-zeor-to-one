---
slug: mi-coverage-gaps
date_filed: 2026-07-01
status: closed
---

# Mechanistic-interpretability coverage gaps in the llms-for-coding survey

## Context

Asked, from a mechanistic-interpretability (MI) perspective, what the
`surveys/llms-for-coding` survey is still missing. The survey has strong
**circuit/weight-level** attention MI in the anatomy appendices — QK/OV collapse
(§A.2–A.3), gauge freedom (§A.4), reading a head by SVD (§A.8), hand-built
induction head (§A.9), multi-head as a sum of low-rank circuits (§A.10),
Q/K/V-composition (§A.18), direct path to the logits (§A.21), induction-as-ICL
with an ablation table (§A.22), and a fully-solved circuit in §C.8 (grokking).
The **feature/activation** side, the **interventional methodology**, the
**code-specific** representational findings, and the **payoff/limitations** are
thin or absent. This todo is the durable backlog of those gaps (a survey
roadmap-gap batch, per CLAUDE.md Todo Capture).

## Progress (2026-07-01)

- Gap analysis folded to `wikis/mechanistic-interpretability-coverage-gaps.md`.
- Buildout plan authored: `plans/2026-07-01-mi-clusters-survey-buildout.md` (new
  Appendix I, sections I.1–I.9, per-section equation inventory + source list,
  P1→P3 sequencing). **Awaiting review before the survey edits.**
- Phase-3 acquisition (P1 set) done → `download/`: SAE cluster
  (cunningham-2309.08600, gao-2406.04093, gated-2404.16014, jumprelu-2407.14435),
  code cluster (li-othello-2210.13382, nanda-linear-2309.00941,
  jin-evidence-2305.11169, troshin-2202.08975), anchors (wang-ioi-2211.00593,
  olsson-induction-2209.11895). Not yet added to `references.md` (added at cite time).
- Remaining: P2/P3 acquisition (intervention, head-zoo, payoff/epistemics), then
  Phase-4 authoring cluster-by-cluster, then citation-audit + /cross-link + /check-survey.

## What is left

Prioritized (P1 highest). Each fold is citation-heavy → run a `source-fetch`
round first, then author under the math-authoring + citation-integrity rules.

- **P1 — Representational MI (features, not just circuits).** Superposition & the
  linear-representation hypothesis (capacity/sparsity/interference/phase change);
  **sparse autoencoders / dictionary learning** (gated / top-k / JumpReLU;
  monosemanticity) — the single biggest omission; features ≠ neurons /
  polysemanticity. In-charter: extends §C.10 / a new §C or Appendix I.
- **P1 — Code-specific MI.** What code models represent (AST/syntax, variable
  binding & scope, types, control-flow, **execution-state / world-model
  probing**); code-relevant circuits (bracket/indentation matching, variable
  tracking, copy-from-context specialized from §A.22 to code completion / repo
  context). Highest domain-differentiating value.
- **P2 — Intervention toolkit + a discovered real-model circuit.** Activation
  patching / causal tracing, path patching, attribution patching, causal
  scrubbing, DAS; logit lens / tuned lens as *named* tools (the math is latent in
  §A.21). Plus one *reverse-engineered* real-model circuit capstone (IOI /
  greater-than / docstring) — the survey only hand-builds (§A.9) and derives
  (§C.8), never discovers.
- **P2 — Head taxonomy beyond induction.** Duplicate-token, name-mover /
  negative-name-mover, copy-suppression, successor heads.
- **P3 — Payoff & epistemics (bridges to existing chapters).** MI→control
  (activation steering, representation engineering, weight editing ROME/MEMIT;
  ties to design-guidance); MI→safety (circuit auditing, backdoor / sleeper-agent
  detection, deception probes; bridge to `safety-security-and-licensing.md`);
  scalable/automated interp (neuron/feature auto-labeling, ACDC, attribution
  graphs / circuit tracing); limitations & faithfulness (interpretability
  illusions, ablation ≠ necessity, attention-weights-aren't-explanations,
  evaluating MI).

## Acceptance

Each gap is either (a) folded into the survey — with sources acquired to
`download/` first and cited to `references.md` under the citation-integrity
invariant, `/check-survey llms-for-coding` green — or (b) explicitly scoped out
with a one-line reason (e.g. "out of charter for an architecture anatomy"). At
minimum the P1 items land or are consciously deferred with rationale.

## Refs

- Survey: `surveys/llms-for-coding/` — anatomy appendices A (§A.2–A.22), C (§C.8, §C.10).
- Conversation log: `prompts/2026-07-01-tiny-transformer-progressive-build.md` (Conversation 13).
- Rules: `.claude/rules/citation-integrity.md`, `.claude/rules/math-authoring.md`; skill: `.claude/skills/source-fetch/SKILL.md`.

**Resolution.** (2026-07-01) All five clusters authored into a new **Appendix I — Mechanistic Interpretability** (I.1–I.9, 22 equations, references [70]–[93], all strong `local:` tags), from first principles with every citation verified in-source (two attribution errors caught + fixed pre-delivery, see `field-notes/2026-07-01-mi-appendix-authoring.md`). All gates green — sections/paragraphs/equations `--check` clean (zero cascade), `validate-refs` 0 err (150 links), `check-citation-sources` 93 entries / 83 strong local / 0 err, `crosslink --changed` 0 gaps. Report: `reports/2026-07-01-mi-appendix-buildout.md`. Residual polish (formal `citation-audit` pass, optional §A→§I backlinks) tracked in `todos/2026-07-01-mi-appendix-followups.md`.
