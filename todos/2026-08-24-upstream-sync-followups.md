---
slug: upstream-sync-followups
date_filed: 2026-08-24
status: open
---

# Follow-ups from the 2026-08-24 inbound upstream sync (cedfccb2..24cfca29)

## Context

`/sync-upstream` ported 106 upstream config/viewer commits (~15.7K insertions across 107
files) into this repo: the campaign-lifecycle harness core, five new generic gates, a
17-module pytest suite now wired into the push gate, four new rules, five modified rules,
three skill deltas, and the `check-hook-wiring.sh` SessionStart self-repair. The pre-push
gate is green and now runs **477 tests** it previously ran none of.

Scope calls are recorded in `decisions/2026-08-24-01` (campaign core vs instance drivers)
and `decisions/2026-08-24-02` (spec-mirror family + vendored skills as SKIP-domain). These
are the items the sync **surfaced** but deliberately did not resolve.

## What is left

### 1. Notation-table backlog — 6 files (`warn`)

`lint-math.py` check #12 landed with `.claude/notation-table-severity` at `warn`. The
measured backlog is **6 files**, all under `surveys/`, each with ≥ 8 numbered equations and
no notation table:

- `surveys/llms-for-coding/appendix-b-kernel-regression-family.md` (8 eq)
- `surveys/llms-for-coding/appendix-c-toy-transformer.md` (20 eq)
- `surveys/llms-for-coding/appendix-i-mechanistic-interpretability.md` (22 eq)
- `surveys/llms-for-coding/appendix-j-code-derivations.md` (20 eq)
- `surveys/llms-for-coding/language-models-from-first-principles.md` (10 eq)
- `surveys/multimodal-llms/_scratch/ev-A-B.md` (15 eq — scratch evidence, may warrant the
  `<!-- notation-table: … -->` opt-out rather than a table)

Per `.claude/rules/math-authoring.md` § "Symbol Declaration", the LLM collision set worth
declaring is `N` (params vs samples vs vocab), `d` (model width vs head dim vs dataset),
`L` (layers vs loss vs seq-len), `T` (temperature vs timesteps vs tokens), `k` (few-shot vs
top-k vs pass@k), `θ` (params vs RoPE angle), `β` (KL coefficient vs Adam moment).
**Acceptance:** backlog at zero, then flip `.claude/notation-table-severity` to `error`.

### 2. The campaign instance layer, if a campaign ever lands here

`decisions/2026-08-24-01` ported the core only. A first campaign in this repo must supply:

- its own **ledger builder** (`check-ledger.py` reads `ledger_builder` from the descriptor;
  with none declared it skips), and
- a **verification driver** if it wants one — upstream's `campaign_run.py` /
  `campaign_verify.py` / `campaign_independent.py` / `campaign_wake.py`, plus
  `tools/campaign_cli.py` and the `/campaign` command, are recoverable from the upstream
  template and would need re-domaining away from its conformance-case register.

**Acceptance:** a campaign registered in `.claude/campaigns`, `check-campaign.py --all`
returning a verdict instead of REFUSE, and the four advisory gates no longer exit 2.

### 3. Pre-existing telecom fixtures in `viewer/tests/**`

Carried over from the original bootstrap, untouched by this sync and by the 2026-08-12 one
(`todos/2026-08-12-upstream-sync-followups.md` records the same). Nine e2e/unit specs still
name a 5G-NR-LDPC survey path, an NTN survey corpus, and `theories/` documents that do not
exist here — so any spec that reads those paths is testing against absent fixtures:

- `viewer/tests/profile-highlight-locatability.spec.js` (the largest — a whole NTN corpus list)
- `viewer/tests/single-line-display-math.spec.js`, `duplicate-heading-anchors.spec.js`,
  `highlight-color-prefix-rendering.spec.js`, `mermaid.spec.js`
- `viewer/tests/unit/citation.test.js`, `root-resolvers.test.js`, `palette-rank.test.js`,
  `publish-multiroot.test.js`
- `bench/deep-research-survey/mechanical_metrics.sh`

**Acceptance:** each hit classified as re-domain (point at a real local survey) or delete
(the fixture tests nothing here), and the leakage grep in `/sync-upstream` step 3 clean
without the `viewer/tests/**` carve-out.

### 4. `viewer/node_modules` absent — the JS unit tests did not run

`viewer/tests/unit/viewer-launcher.test.js` (385 lines) was ported and parses
(`node --check`), but the container has no `viewer/node_modules`, so `npm --prefix viewer
test` could not execute it or the ~330 sibling `node --test` unit tests. Upstream wired
those into its own push gate; this repo's pre-push does not run them at all.

**Acceptance:** `npm --prefix viewer ci` in an environment that has it, the suite green,
and a decision on whether to wire it into `.githooks/pre-push` (it needs `node_modules`, so
it must SKIP LOUDLY on a fresh clone rather than silently pass).

### 5. A spec mirror, if one ever lands

`decisions/2026-08-24-02` skipped `check-spec-mirrors.py`. If `docs/specs/` is ever
populated here (the `spec:` source tag in `.claude/rules/citation-integrity.md` already
anticipates it — e.g. the Model Context Protocol spec), the UTF-8/greppability gate is the
one piece worth revisiting: a non-UTF-8 mirror makes `grep` return empty with exit 1,
byte-for-byte indistinguishable from a genuine no-match, so an author doing exactly what
the citation-integrity rule demands is told the value is not there and falls back to memory.

### 6. Environment deps the push gate now needs

The gate runs `pytest` and imports `markdown_it`. Both had to be `pip install`ed in this
container. `requirements.txt` names `markdown-it-py` but **not** `pytest`; the gate skips
loudly without it (`"gate tests: SKIPPED (pytest not installed) - not a pass"`), which is
correct behaviour but means a fresh clone silently runs 477 fewer tests until someone
installs it.

**Acceptance:** `pytest` added to `requirements.txt` (or a documented dev-requirements
split), and a fresh-clone run confirming the gate reports the same test count.

## Refs

- `decisions/2026-08-24-01`, `decisions/2026-08-24-02`
- `prompts/2026-08-24-upstream-sync.md`
- `.claude/upstream-sync.json` (mark advanced cedfccb2 → 24cfca29)
- `todos/2026-08-12-upstream-sync-followups.md` (item 3 overlaps — same fixture backlog)
