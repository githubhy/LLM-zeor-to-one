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
- **`proposed`** — apply ALL improvements: the Part-1 P-items (P0-1 … P3-1) AND the Part-2 richness/depth items (R-GOV, R-CARD, R-SURVEY, R-DEPTH, R-MATHREV, R-COVER, R-RUBRIC).
- **`richness`** — apply ONLY the Part-2 richness/depth layer (all `R-*` items); leaves the Part-1 P-items off. Makes the produced survey deeper/broader/more rigorous. **Read `R-GOV` (the depth-tier governor) first — it bounds how much depth every other R item spends, so the gates raise depth-per-load-bearing-concept rather than words per method.**
- **`flags: <ids>`** — apply ONLY the named items, e.g. `flags: R-CARD,R-DEPTH` or `flags: P1-2,P0-2` (per-item lattice for item-by-item A/B ablation).

**Lazy loading (token discipline).** The improvement addenda are NOT inlined — they live in `addenda/` and cost zero tokens unless a non-`original` mode is active. When `proposed`, `richness`, or `flags:` is set: read `addenda/global.md` once (P2-4, P2-5), then read `addenda/phase-N.md` just-in-time as you begin phase N — and only if `proposed`/`richness` is set or one of that phase's item ids (named in each phase file's one-line pointer) is in the active `flags` set. Apply a block iff `proposed`/`richness` is set OR its id is in `flags`. The Part-2 richness items live in `addenda/phase-2.md` (R-GOV / R-CARD / R-SURVEY), `addenda/phase-4.md` (R-DEPTH), and `addenda/phase-5.md` (R-MATHREV / R-COVER / R-RUBRIC); `richness` activates all of them and `R-GOV` (the depth-tier governor) must be read first. Record the active mode/flags in the final report (one line). Item registry + how each is tested: `bench/deep-research-survey/items.json`. Default stays `original` — no `addenda/` file is ever read.

### Operational scale (orthogonal throughput axis)

`scale` is a **separate axis** from the mode lattice above: it sets *numeric operational knobs* (per-agent search/question budget, verify fan-out, download budget, file-split threshold) and composes **alongside** any mode (`original`/`proposed`/`richness`/`flags:`). The values are configurable in `config/operational-scale.json` — edit that file to retune; the calibration sweep updates it, not this skill.

- **`scale: standard`** (DEFAULT) — the caps used today. No behavior change; no need to pass it.
- **`scale: wide`** — apply the `wide` profile from the config (operator-set, provisional pending calibration: searches ≤40, questions ≤7, verify fan-out ≤12, downloads ≤200/day, file-split ≤200 KB).
- **`scale: <knobs>`** — per-run override, e.g. `scale: searches=40,verify_fanout=12`.

At Phase-3 launch, read `config/operational-scale.json` and size agents to the active profile's `searches_per_agent` / `questions_per_agent` / `downloads_per_day`; at Phase 5 use its `verify_fanout`; apply `file_split_kb` when deciding to split. **Wide mode raises throughput; it never removes a safety net** — `scale: wide` is INVALID unless every `safety_net_invariant` in the config stays ON (checkpoint-writes, event-driven death detection + 15-min poll fallback, structured-output schemas, main-thread synthesis, the citation-integrity gate, and the restart-intensity ceiling that emits a visible coverage-gap marker on fallback). Record the active scale in the Phase-5 report footer next to mode/flags.

⚠️ **`searches=40` (wide) is above the only measured death boundary (~28, 2026-03)** and is provisional pending the calibration sweep (see the wide-mode operational-scaling proposal + its calibration-sweep todo). Until then, wide mode leans on the safety nets to make any overrun recoverable, and the residual it does not close is an "alive but byzantine" shallow return — surfaced by the coverage gate, not eliminated.

### Audience / register (orthogonal exposition axis)

`audience` is a **third axis**, orthogonal to both the mode lattice and `scale`: it sets the *exposition register* — how prose is written for a given reader — without changing *which* concepts get deep treatment (that is R-GOV's depth tier) or evidence throughput (`scale`). Values live in `config/audience-register.json`; pass `audience: <value>` to override per run.

- **`audience: practitioner`** (DEFAULT) — the current Staff-level register. No behavior change; no need to pass it.
- **`audience: learner`** — pedagogical: derive prerequisites from first principles, expand every routine step, intuition + analogy around each result, worked examples lead, define terms on first use, fundamentals at full depth.
- **`audience: expert`** — terse: assume fluency, compress routine algebra, one-line intuition, glossary-only definitions, fundamentals at recap depth — spend the depth budget on the advanced material.

Phase-1 scope resolves the register (precedence: invocation arg → explicit request language → ask → default `practitioner`) and records it in the brief; R-GOV (Phase 2) consumes it for the fundamentals floor, R-DEPTH (Phase 4) for derivation granularity / intuition / examples / definitions. **The register changes exposition, never correctness** — every `register_invariant` in the config (boxed results, worked-oracle numbers, epistemic tags, the no-load-bearing-step-dropped floor, the citation + mechanical gates) holds identically across registers; `expert` compresses only ROUTINE algebra, never a load-bearing step. Record the active register in the Phase-5 report footer next to mode/flags/scale.

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

- **Evidence-agent "silent death" is a per-agent ITERATION/STEP cap (~36-40 tool calls), not context size and not model tier** (2026-06-25, transcript-measured: a dead agent used only ~58K of a 200K window; the final message was `stop_reason=tool_use` with empty text — cut off mid-loop before writing). The default-ON `agent_hardening` policy (`config/operational-scale.json` `evidence_agent_policy`) is the fix: file-first `_scratch` deliverable, **exact paths / no Glob** (18 wasted Glob calls were the largest step sink), **WebFetch ≤ 2**, **~3-4 questions/agent** with tool-call headroom, and **empty-return-as-death** in the orchestrator (`try/catch` schema agents — a missing `StructuredOutput` THROWS). Disable with `agent_hardening: off` (restores the broken legacy path). See the evidence-agent hardening bug + its decision record. Fewer questions/agent does NOT narrow or shallow the research — it raises per-question budget; coverage is gated by R-COVER, not agent size.
- Phase 3 agents beyond the active scale's search budget (`config/operational-scale.json`: standard 15 / wide 40) tend to die silently — more searches = more steps = closer to the step cap above. Stay under the active limit — and note wide=40 is above the 2026-03 death boundary and provisional pending calibration.
- Questions per agent: standard ≤5 (≤7 borderline) / wide ≤7 (`config/operational-scale.json`).
- Always instruct agents to checkpoint-write to `survey/_scratch/`. Without this, dead agents produce zero results.
- The synthesis merge in Phase 4 collides cross-link IDs across sections — not just duplicate equation IDs but clashing section numbers and stale paragraph anchors too. After any merge run the full sequence (`renumber-equations`, `renumber-sections`, `renumber-paragraphs`, `link-references`, then `validate-refs`), or just `/check-survey` — `renumber-equations` alone is not enough.
- If a survey file exceeds the active scale's file-split threshold (`config/operational-scale.json`: standard 100 KB / wide 200 KB), switch to multi-file architecture before enriching further.
- Don't delegate synthesis to agents — only raw evidence collection. The main thread owns all writing.
- Vague agent briefs ("research X broadly") produce low-quality results. Use concrete questions with expected output formats and stop conditions.
- **Phase-4 authoring: write each prose paragraph as a single unwrapped line** (or at least never break a line immediately before a `<!-- ref:/secref:/secxref:/cite: -->` comment or inside a `$...$` span). The PostToolUse `lint-math` hook rejects a ref-comment or split inline-math at line start — the #1 synthesis round-trip sink, since hard-wrapping at ~100 cols repeatedly lands a marker or math at a continuation line's start. A deterministic joiner (read each line; if it starts with a ref-comment, append it to the previous line) clears a whole file in bulk. Mark every same-file `§` as `secref`, every cross-file `§` as `secxref`, and bracket-wrap external-spec / cross-document `§` (e.g. `[MCP spec §6.2]`, `[§14.6]`) — bare `§X.Y` is ERROR-blocking when `.claude/bare-refs-severity` is `error`, and `--init` cannot run mid-hook to fix it.
- **`references.md` must be numbered `[N] … (source-tag)` entries with the paragraph anchor on the line ABOVE each `[N]`, not inline.** `renumber-paragraphs --init` injects the para anchor inline at the block start, pushing `[N]` off column 0 — and `check-citation-sources` then matches **0 entries and silently validates nothing** (it keys on `^\[N\]`). Split the anchor onto its own line (the model-card / arXiv reference format) so each entry is detected. Verify the gate by running the lint scripts directly via Bash, not only via the PostToolUse block: `lint-math` errors mask the bare-ref and citation-source checks until they pass.

## Cross-link sign-off

Before sign-off, cross-link the new/expanded survey into the corpus (per `.claude/rules/cross-linking.md`): run the `cross-link` skill (or `crosslink.py check $SCOPE --changed`) and clear the reported high-value gaps, or file a `todos/` entry for any left out of scope. A freshly authored document has no links and the gap detector will fire — clearing it is part of done.
