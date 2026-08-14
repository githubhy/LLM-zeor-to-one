# Max-mode expansion — research brief and depth-tier allocation

**Date:** 2026-08-14
**Skill:** `deep-research-survey`
**Mode resolution:** `max` -> `proposed` + `scale: wide` + `audience: learner`
**Target:** `surveys/llms-for-coding/` (expand in place; NOT a new survey)

This file is the Phase-1 north star. Phase 5 reads the tier table below back as the
left-hand side of the drift-diff (`viewer/tools/depth-tier-coverage.py`); a delivered
`Depth tier:` label that diverges from its approved row here is a `TIER-DRIFT` finding.

---

## 1. Research brief

**Subject.** Large Language Models for Code, end to end: the code modality, the training
pipeline (data, objectives, alignment), test-time compute, retrieval and repository
context, agentic systems, evaluation, serving economics, and the safety/licensing layer.

**Output contract.** Multi-file survey under `surveys/llms-for-coding/`, expanded in
place. The existing 18-section body and 9-appendix stack are preserved and deepened; a
new Appendix J carries the code-specific derivations.

**Audience register.** `learner` (`config/audience-register.json`). Derive prerequisites
from first principles; expand routine algebra with a one-line justification per step;
intuition and analogy before AND after each non-obvious result; the worked example LEADS
rather than follows; define every non-trivial term on first use; fundamentals pinned to
`headline` tier. Register changes exposition only — every boxed result, worked-oracle
number, and epistemic tag is register-invariant.

**Operational scale.** `wide`, sized against the binding constraint:
`searches_per_session` = 200, shared across the main thread and every subagent.
Effective per-agent budget = `min(40, (200 - 25) / 8)` = **21 searches**, 8 agents,
~4 questions each, 25-call holdback reserved for main-thread Phase-4/5 verification.
Agents hardened per DRS-HARDEN (exact paths, no Glob, WebFetch <= 2, file-first
`_scratch` deliverable written after each question, empty-return-as-death).

**Exclusions.** No new survey directory. No re-derivation of the general transformer
substrate — Appendices A through I already own it. Multimodal code (screenshot-to-code),
formal verification/synthesis, and non-LLM program synthesis are out of scope; the
survey is about LLMs for code, not program synthesis generally.

**Source preferences.** Primary sources first: original papers with a pinned arXiv id and
version, official model and system cards, reference implementations. A vendor-published
benchmark number is Tier-1 evidence for *what the lab claims* and is not neutral evidence
of capability — corroborate or tag it. Every cited source must be acquired to `download/`
per `.claude/rules/citation-integrity.md`; the `references.md` <-> `download/` invariant
is a delivery gate.

---

## 2. The measured gap this expansion closes

Baseline measured 2026-08-14 at commit `1d8f017`:

| Layer | Words | Equations | Assessment |
|---|---|---|---|
| Body, 16 sections excluding section 3 | ~11,900 | **0** | Well-cited prose; no mathematics at all |
| Section 3 (LMs from first principles) | ~7,000 | many | Already deep |
| Appendices A-I | 379 KB | hundreds | Deep, but derives the GENERAL transformer, not code |

Two consequences:

1. Against the Survey Rules in `.claude/rules/workflow.md` — *"a rigorous first-principles
   mathematical derivation for every method, architecture, or implementation variant that
   is included"* — the body fails. Fill-in-the-middle, the pass@k estimator,
   execution-feedback RL, and verifier-guided search are all asserted in prose and never
   derived.
2. The title's destination is the thinnest part of the document. `agentic-coding-systems.md`
   is 795 words, and its frontier evidence is 2024-era.

**Structural defects found during Phase 1** (fix in this pass):

- `appendix-i-mechanistic-interpretability.md` is in `order.json` but absent from
  `index.md`'s Contents list.
- No top-level section carries a `sec-N` anchor. All 18 body headings are `## N Title`
  with a flat number and no marking, and `heading_grammar.match_heading` deliberately
  refuses to treat an unmarked flat number as a section (otherwise `## 2020 in review`
  becomes section 2020). Consequence: top-level sections are not link targets, and only
  `N.M` subsections can be cross-referenced. **FIXED in this pass.** The initial plan was to
  defer it, on the assumption that the fix required the dash marking (`## 12 — Title`), which
  changes heading text and cascades every paragraph anchor. That assumption was wrong: the
  two healthy surveys in this corpus use the *anchor* marking instead
  (`## <a id="sec-9"></a>9 Circuits across models`), which leaves the visible text untouched
  and cascades nothing — confirmed by `renumber-paragraphs --check` reporting `Updates: 0`.
  Applied `sec-1`..`sec-18` plus `sec-A`..`sec-I` across 27 files. Closed as
  `todos/2026-08-14-top-level-section-anchors.md`.

---

## 3. Depth-tier allocation (R-GOV)

Tiers are a fixed, mechanically-gated vocabulary (`viewer/tools/check-depth-tiers.py`):
`headline` / `load-bearing` / `catalog`, plus the ratified off-ladder `supporting` for
non-method context sections.

Depth is scored as a **coverage fraction over load-bearing items**, never as prose volume.
A tight survey that fully treats its headline methods and catalogs the rest must score
higher than a bloated one that half-treats everything.

<!-- depth-tier-allocation -->

| Section | Tier | Justification |
|---|---|---|
| 1 | supporting | Executive summary. Non-method context; owns no method of its own. |
| 2 | headline | The executable-verifiability thesis is the survey's spine — the one property that explains the whole trajectory from autocomplete to agents. |
| 3 | headline | Language-model fundamentals. Pinned to headline by the `learner` register's fundamentals floor; already deep, so incremental spend is low. |
| 4 | supporting | Historical evolution. A provenance trace from Codex forward, not a method inventory. |
| 5 | supporting | Pipeline map. Structural orientation; every method it names is owned by a later section. |
| 6 | load-bearing | Pretraining data. Real methods with derivable content: near-dup detection, semantic dedup, decontamination, license filtering. |
| 7 | headline | Pretraining objectives. Fill-in-the-middle is THE code-specific pretraining objective and is currently underived. |
| 8 | headline | Alignment. Execution feedback and RLVR are the code-specific alignment story; tests are the reward function. |
| 9 | headline | Test-time compute. best-of-n, execution-based selection, verifier-guided search — all derivable, all code-specific because tests are the verifier. |
| 10 | load-bearing | Inference and serving. Largely general machinery, but prefix-cache economics in an agent loop is code-specific and quantitative. |
| 11 | load-bearing | Retrieval and repository context. Currently the thinnest section (591 words); agentic search vs embedding retrieval is a live architectural dispute. |
| 12 | headline | Agentic coding systems. The title's destination, the field's centre of gravity, and the thinnest section relative to its importance. |
| 13 | headline | Evaluation. The measurement spine: the pass@k estimator, contamination, and whether the field reports uncertainty at all. |
| 14 | load-bearing | Compute, cost, latency. Token economics of an agent trajectory versus a single completion. |
| 15 | load-bearing | State of the art and practice. Hosts the R-SURVEY quantitative SOTA table and the published-vs-deployed gap thesis. |
| 16 | load-bearing | Safety, security, licensing. Vulnerability rates, prompt injection against agents, and the licensing status. |
| 17 | supporting | Design guidance. A decision table synthesized from the sections above; contributes no method of its own. |
| 18 | supporting | Open problems and roadmap. The R-SURVEY handoff register. |
| J | headline | NEW. Appendix J, code-specific derivations: the full first-principles work the body cross-references. |

**Every `supporting` row is surfaced deliberately** (P0-3 requires it, so the reader can
confirm each is genuine non-method context rather than a depth-dodge): sections 1, 4, 5,
17, and 18 are respectively a summary, a provenance trace, a structural map, a decision
table, and a handoff register. None of them owns a method. Every method they mention is
derived in a `headline` or `load-bearing` section.

Tally: 7 headline (incl. Appendix J), 6 load-bearing, 5 supporting.

---

## 4. Research questions by evidence cluster (Phase 3)

Must-have questions block their section; nice-to-have enrich it. All 8 clusters are
must-have — each maps to a `headline` or `load-bearing` section.

| Cluster | File | Feeds sections | Priority |
|---|---|---|---|
| C1 Agent loop, protocols, context management | `max-c1.md` | 12 | must-have |
| C2 Frontier results and deployed systems | `max-c2.md` | 12, 15, 14 | must-have |
| C3 Evaluation, benchmarks, reporting statistics | `max-c3.md` | 13, J | must-have |
| C4 Pretraining objectives (FIM) and data | `max-c4.md` | 6, 7, J | must-have |
| C5 Execution feedback and RLVR | `max-c5.md` | 8, J | must-have |
| C6 Reasoning and test-time compute | `max-c6.md` | 9, J | must-have |
| C7 Retrieval and repository context | `max-c7.md` | 11 | must-have |
| C8 Serving economics, security, licensing | `max-c8.md` | 10, 14, 16 | must-have |

Four clusters carry a designated highest-value extraction, because each is the input to a
derivation in Appendix J and prose cannot substitute for the exact printed form:

- C3 Q1 — the pass@k unbiased estimator, verbatim from the Codex paper.
- C4 Q1 — the FIM document transformation, verbatim, both SPM and PSM orderings.
- C5 Q1 — the GRPO objective, verbatim, with the group-relative advantage.
- C6 Q1 — AlphaCode's sampling-budget-versus-solve-rate points, as printed.

---

## 5. R-SURVEY artifacts (reserved slots)

- **Notation contract** — front matter table: symbol, meaning, units and convention
  (bits vs nats, per-token vs per-sequence, non-embedding vs total parameters), and the
  defining-section link. Satisfies `[opt:MATH-BASIS]` at authoring time.
- **Master comparison matrix** — rows = every inventory method, columns = the declared
  evaluation axes plus an explicit "assumptions and cost" column, so a higher-scoring
  method that did not ship has a visible reason.
- **Quantitative SOTA table** — one row per published result with its full eval
  conditions (benchmark variant, split, model, scaffold, date, self-reported flag) and a
  normalization note where conditions are incomparable.
- **Figures** — a conceptual block diagram per method family, each caption carrying the
  numeric operating-conditions disclosure required by
  `.claude/rules/figure-operating-conditions.md`.
- **Open problems and handoff** — each gap as {question, known, unknown, why it matters,
  state of attack, candidate next step}, with study-ready candidates carrying a
  baseline-to-beat and a predicted margin.
- **Appendix J** — code-specific derivations, cross-linked from the body.

---

## 6. Guardrails carried into Phase 4

- **Citation integrity.** No citation from memory. Every new reference entry carries a
  source tag and its `local:` file must exist. Agent-collected claims are treated as
  unverified until the source is in `download/`.
- **Calibration residuals.** A "+N point" margin against a vendor-published number is
  mostly harness and prompt difference, not capability. Any margin states which basis it
  is measured on. Forbidden phrasings: "brackets", "agrees with", "qualitative match".
- **Scaffold-versus-model attribution.** A resolve-rate comparison across systems and
  dates conflates a better scaffold with a better base model. Every agentic number is
  reported as a (model x scaffold x date) triple, never as a property of either alone.
- **Metric basis.** pass@1 versus pass@k, non-embedding versus total parameters, unique
  versus seen tokens, bits versus nats — declared at the point of use.
- **Cross-link sign-off.** Mandatory before delivery, at subsection granularity.
