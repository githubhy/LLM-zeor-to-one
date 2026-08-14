# Max-mode expansion — research brief and depth-tier allocation

**Date:** 2026-08-15
**Skill:** `deep-research-survey`
**Mode resolution:** `max` -> `proposed` + `scale: wide` + `audience: learner`
**Target:** `surveys/mechanistic-interpretability/` (expand in place; NOT a new survey)

Phase-1 north star. Phase 5 reads the tier table below back as the left-hand side of the
drift-diff (`viewer/tools/depth-tier-coverage.py`). The `Section` cell is the **bare token**
that appears inside the heading anchor (`4`, `A`), not the `sec-` prefixed form — an earlier
run in this corpus wrote `sec-4` and the diff silently bound nothing while reporting
`0 TIER-DRIFT`.

---

## 1. Research brief

**Subject.** Mechanistic interpretability of neural networks, end to end: fundamentals and
the linear-representation/superposition substrate, the method inventory (observational,
causal, dictionary-learning, steering/editing, automation), circuits across models,
evaluation, tradeoffs, current practice, applications, and open problems.

**Output contract.** Multi-file survey under `surveys/mechanistic-interpretability/`,
expanded in place. The 16-section body keeps its structure; appendices A–E are deepened;
new evidence closes a one-year frontier gap.

**Audience register.** `learner`. Derive prerequisites from first principles, expand routine
algebra with a one-line reason per step, intuition before and after each non-obvious result,
worked examples lead, define terms on first use, fundamentals pinned to `headline`.

**Operational scale.** `wide`. Binding constraint is `searches_per_session` (~200, shared
across the main thread and every subagent), **not** the per-agent knob. This run additionally
front-loads acquisition through the **arXiv API and direct PDF fetch**, neither of which
consumes the WebSearch pool — 19 sources acquired before any agent launched.

**Exclusions.** No new survey directory. Interpretability of non-transformer architectures
(CNN vision circuits beyond the historical anchor, RL policies, biological networks) stays
out of charter. Prompt-level explainability, saliency-map XAI, and post-hoc rationalization
are named as *adjacent and excluded* rather than covered — this is a mechanistic survey.

**Source preferences.** Primary papers with pinned arXiv id and version; the Transformer
Circuits Thread posts are primary for the work they report but carry no arXiv version and are
therefore `(web)` — a weak form this pass is explicitly trying to reduce.

---

## 2. The measured gap this expansion closes

Baseline measured 2026-08-15 at commit `b0893eb`:

| Layer | Words | Equations | Assessment |
|---|---|---|---|
| Body, 16 sections | 18,119 | 15 | Solid; unlike the sibling coding survey, the body carries math |
| Appendices A–E (math) | 3,335 | 21 | **~670 words / ~4 equations each** |
| Appendix Q (reader questions) | 891 | 0 | The R-SURVEY Q&A artifact already exists |
| References | 81 entries | — | 64 `local:` / **19 `(web)` = 23% weak-form** |

Two holes, both specific.

1. **The frontier is missing a year.** Citation years run 2004–2025 with **zero 2026
   entries**. An arXiv sweep for this brief returned 60 mechanistic-interpretability and 50
   sparse-autoencoder papers from 2026 alone. Three themes are structurally absent from the
   survey: **weight-space / parameter interpretability**, which §4.4 catalogs but does not derive; a
   **circuit-discovery methodology-critique** cluster (variance, mediator interaction,
   self-repair, certified fidelity); and the **continuation of the SAE re-evaluation** past
   the 2025 papers the survey already cites.
2. **The title promises first principles and the appendices are the thinnest layer relative
   to that promise.** Five math appendices at ~670 words each. For scale, a single appendix
   written for the sibling survey the previous day is 4,300 words and 20 equations.

Also absent: **any figures** (the only survey in this corpus with none) and **any
`Depth tier:` labels**, so no R-GOV allocation exists to gate against.

---

## 3. Depth-tier allocation (R-GOV)

<!-- depth-tier-allocation -->

| Section | Tier | Justification |
|---|---|---|
| 0 | supporting | Executive summary. Non-method context. |
| 1 | supporting | Introduction and scope. Charter boundaries, not methods. |
| 2 | headline | Fundamentals. Pinned by the `learner` register's fundamentals floor; hosts the linear-representation and superposition substrate everything else rests on. |
| 3 | supporting | Methodology and taxonomy. An organizing map; every method it names is owned elsewhere. |
| 4 | load-bearing | Observational methods (probing, logit lens, attention analysis). Real methods with derivable content and a known confound literature. |
| 5 | headline | Causal / interventional methods. The methodological core of the field, and the target of the 2026 critique cluster. |
| 6 | headline | Dictionary learning / SAEs. The field's central and most contested method family. |
| 7 | load-bearing | Steering and model editing. Where the SAE debate becomes an applied question. |
| 8 | load-bearing | Automation and the current frontier. Attribution graphs and circuit tracing live here. |
| 9 | load-bearing | Circuits across models. The empirical catalogue of found circuits. |
| 10 | headline | Evaluation and metrics. The live story is the field re-evaluating its own instruments; 2026 sharpened it. |
| 11 | load-bearing | Comparison and tradeoffs. Hosts the R-SURVEY master matrix (35 table rows already present). |
| 12 | load-bearing | State of the art and practice. Hosts the quantitative SOTA table. |
| 13 | supporting | Applications. Downstream uses; contributes no method. |
| 14 | supporting | Design guidance. A decision table synthesized from the sections above. |
| 15 | supporting | Open problems and roadmap. The handoff register. |
| A | headline | Transformer-circuits mathematics. The QK/OV substrate; deepen from 747 words. |
| B | headline | Superposition. The capacity argument the whole feature program rests on; deepen from 649 words. |
| C | headline | Causal interventions. The formal semantics of patching, and where the 2026 critiques bite; deepen from 680 words. |
| D | headline | SAE derivations. The objectives, the frontier, and what the evaluation critique implies; deepen from 656 words. |
| E | load-bearing | Steering and editing mathematics. Deepen from 603 words. |
| Q | supporting | Reader's questions. Pre-answers "why is it built this way"; grows as folds land. |

**Every `supporting` row surfaced deliberately** (P0-3): 0, 1, 3, 13, 14, 15 and Q are a
summary, a charter, an organizing map, a downstream-use catalogue, a decision table, a
handoff register, and a Q&A appendix. None owns a method.

Tally: **8 headline, 7 load-bearing, 7 supporting** (22 tiered sections).

---

## 4. Evidence clusters (Phase 3)

Acquisition ran **before** the fan-out, via the arXiv API and direct PDF fetch, so agents read
local files rather than spending the shared search pool. 19 sources acquired
(`download/mi26-*.pdf`).

| Cluster | Feeds | Why it is must-have |
|---|---|---|
| E1 Circuit-discovery methodology critique | 5, C, 10 | The strongest 2026 thread: the field auditing its own core method. Variance, mediator interaction, self-repair backups, certified fidelity. |
| E2 SAE re-evaluation, 2026 | 6, D, 10 | Continues the 2025 debate the survey already carries (AxBench, SAEBench, sparse probing) into its next year. |
| E3 Weight-space interpretability | 4.4, 8, 15 | **CORRECTED after the Phase-3 critique.** This brief originally called it "a new axis the survey does not have". That was wrong: `method-inventory-observational.md` **§4.4 already covers direct weight/SVD analysis**, tagged `[catalog-only]`. The 2026 work is an **upgrade to that entry** — promoting the direct-weight half out of catalog-only on quantitative backing — plus one genuinely new placement (per-weight auto-interp belongs in §8, whose novelty is a unit swap inside an existing pipeline). Recorded rather than silently fixed, because the error was a negative asserted without checking the file that would have refuted it. |
| E4 Theory and foundations | 2, A, B | Spectral identifiability, induction heads as n-gram interpolation, sparsity/superposition loss — direct appendix inputs. |
| E5 Steering, control, and reasoning models | 7, E, 13 | The knowing-vs-steering gap, and interpretability of reasoning-mode models. |
| E6 Frontier framing and model diffing | 8, 12, 15 | A 2026 survey anchor plus model-diffing as a method family. |

Derivation inputs for appendices A–E come from the **existing** local corpus (64 papers),
extracted separately so the appendix build-out does not depend on the frontier sweep.

---

## 5. R-SURVEY artifacts

- **Notation contract** — front matter symbol/meaning/units table. Partially present in
  `index.md`; to be made explicit.
- **Master comparison matrix** — section 11 already carries 35 table rows; gate the row count
  against the section-4–8 inventory and add the assumptions-and-cost column.
- **Quantitative SOTA table** — section 12 has 11 rows; normalize conditions per row.
- **Figures — NEW, and the largest structural addition.** The survey has none. The reader
  chose the **full rendered pipeline** (matplotlib generator + persisted `.json` sidecar +
  numeric operating-conditions caption), matching `surveys/llms-for-coding/figures/`.
- **Open problems + handoff** — section 15, with study-ready candidates.

---

## 6. Guardrails

- **Citation integrity.** No citation from memory; every new entry carries a source tag and
  its `local:` file must exist in git's index.
- **The weak-form reduction is an explicit goal**, not a side effect: 19 of 81 entries are
  `(web)`, and several are load-bearing 2025 circuit-tracing posts.
- **Calibration residuals.** The SAE debate is a residual-attribution minefield — "SAEs
  underperform baselines" is a claim about a *comparison*, and the baseline is under test too.
  Every margin states its basis; forbidden phrasings apply.
- **Figures** obey `.claude/rules/figure-operating-conditions.md`: numeric disclosure in
  caption section 1, deterministic generation, persisted data.
- **R-MATHREV** on every new or materially changed numbered derivation, on Opus, deriving
  before reading.
