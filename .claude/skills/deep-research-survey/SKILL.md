---
name: deep-research-survey
description: >
  Use when the user asks for a deep research survey, literature review,
  technical landscape, or state-of-the-art review of an LLM / AI topic —
  e.g. transformer & attention architectures, pretraining & scaling laws,
  fine-tuning and alignment (SFT/RLHF/DPO/RLAIF/PEFT/LoRA), retrieval-augmented
  generation, LLM agents & tool use, inference & serving (KV-cache,
  quantization, speculative decoding, batching), evaluation & benchmarks,
  long-context methods, multimodal models, or safety & interpretability — and
  expects first-principles explanation, broad method coverage, tradeoff
  analysis, current practice, cited references, or a reusable research prompt.
---

# Deep Research Survey

Translate broad LLM / AI research requests into a concrete research brief, then execute with phased control, evidence discipline, and a consistent final deliverable. The workflow is domain-general; the defaults (outline, method taxonomy, source rubric) are tuned for LLM and LLM-adjacent surveys.

## Modes and flags

Selected from the skill arguments (`$ARGUMENTS`):

- **`original`** (default) — baseline workflow only. Do NOT read any `addenda/` file. Current behavior, unchanged.
- **`proposed`** — apply ALL improvements (P0-1 … P2-5).
- **`flags: <ids>`** — apply ONLY the named items, e.g. `flags: P1-2,P0-2` (per-item lattice for item-by-item A/B ablation).

**Lazy loading (token discipline).** The improvement addenda are NOT inlined — they live in `addenda/` and cost zero tokens unless a non-`original` mode is active. When `proposed` or `flags:` is set: read `addenda/global.md` once (P2-4, P2-5), then read `addenda/phase-N.md` just-in-time as you begin phase N — and only if `proposed` is set or one of that phase's item ids (named in each phase file's one-line pointer) is in the active `flags` set. Apply a block iff `proposed` is set OR its id is in `flags`. Record the active mode/flags in the final report (one line). Item registry + how each is tested: `bench/deep-research-survey/items.json`. Default stays `original` — no `addenda/` file is ever read.

## Phases

Run in order. Read each phase file just-in-time when starting that phase.

| Phase | File | Goal |
|-------|------|------|
| 1. Scope | `phases/phase-1-scope.md` | Pin down subject, audience, depth, output shape |
| 2. Outline | `phases/phase-2-outline.md` | Section outline with research questions |
| 3. Evidence | `phases/phase-3-evidence.md` | Collect section-level evidence with source quality discipline |
| 4. Synthesis | `phases/phase-4-synthesis.md` | Write section drafts from evidence ledger |
| 5. Report | `phases/phase-5-report.md` | Produce final deliverable |

**Citation gate.** Before Phase 5 sign-off, run the `citation-audit` skill on the deliverable: every external citation must trace to an acquired source per `.claude/rules/citation-integrity.md`. Author to that rule from Phase 3 onward — the audit is the final gate, not a substitute for citing correctly the first time.

**Cross-link & rendering gate.** Surveys land under `./surveys/`, so the cross-link and display-math discipline in `.claude/rules/math-authoring.md` is load-bearing for every deliverable, and is hook-enforced (`lint-math.py` PostToolUse + pre-push) exactly like the citation rule. Read that rule before writing any survey prose, and author with its marker systems — equation (`eq` + `ref`), section (`sec` + `secref`/`secxref`), paragraph (`para`), and reference (`bib` + `cite`) cross-links — from Phase 4 onward, not as a cleanup pass. Before Phase 5 sign-off, run `/check-survey`: the full mechanical gate (lint-math, every renumber/link/validate `--check`, the bare-ref prohibition at `--severity=error`, and reference source-tag verification) — the same checks CI and pre-push run. Authoring to this discipline inline is nearly free; retrofitting it is not — a large transformer-architectures survey needed a 152-ref `secxref` migration after the fact.

## Response Modes

Choose based on user intent:
- **Survey**: broad, comparative, source-backed coverage
- **Proposal**: recommend a plan for one target problem
- **Implementation**: convert research into code, experiments, or design steps
- **Prompt**: produce a reusable prompt for later use
- **Report**: publication-style deliverable with stricter evidence discipline

## Execution Defaults

- Start with definitions, assumptions, scope boundaries.
- Organize: fundamentals → architecture → method inventory → tradeoffs → current practice → roadmap.
- Treat omission risk as a quality problem.
- Prefer primary sources. Browse and cite when current, standards-driven, high-stakes, or niche.
- Say explicitly when a conclusion is inference vs sourced fact.
- When drafts disagree, preserve supported unique findings and resolve conflicts explicitly.

## Templates

- `templates/agent-brief.md` — fill-in template for narrow agent briefs
- `templates/preflight-checklist.md` — pre-flight workload estimation and launch checklist

## Gotchas

- Phase 3 agents with >15 estimated searches tend to die silently. Stay under the limit.
- Agents with >7 questions are borderline — prefer 5 or fewer.
- Always instruct agents to checkpoint-write to `survey/_scratch/`. Without this, dead agents produce zero results.
- The synthesis merge in Phase 4 collides cross-link IDs across sections — not just duplicate equation IDs but clashing section numbers and stale paragraph anchors too. After any merge run the full sequence (`renumber-equations`, `renumber-sections`, `renumber-paragraphs`, `link-references`, then `validate-refs`), or just `/check-survey` — `renumber-equations` alone is not enough.
- If a survey file exceeds 100 KB, switch to multi-file architecture before enriching further.
- Don't delegate synthesis to agents — only raw evidence collection. The main thread owns all writing.
- Vague agent briefs ("research X broadly") produce low-quality results. Use concrete questions with expected output formats and stop conditions.
