---
slug: upstream-sync-followups
date_filed: 2026-08-12
status: open
---

# Follow-ups from the 2026-08-12 inbound upstream sync (9b118d3..cedfccb2)

## Context

`/sync-upstream from the main branch of ../data-channel-receiver` ported ~2 months of
upstream harness work (162 files, ~20K insertions) into this repo: ~30 new `viewer/tools`
gates, the viewer app deltas, ~20 gate-severity toggles, 4 new rules, 6 new/re-domained
skills, and the rebuilt `.githooks/pre-push`. Everything in the delta landed, and the
pre-push gate is green. These are the items the sync **surfaced** but deliberately did not
resolve, because each is corpus work rather than harness porting.

## What is left

### 1. `[opt:MATH-BASIS]` backlog — 42 undeclared basis uses (`warn`)

`viewer/tools/check-basis-declarations.py` was re-domained to LLM bases (parameter count
`N` non-embedding-vs-total; token budget `D` unique-vs-seen; batch `B` sequences-vs-tokens;
`pass@k` sampling basis; loss in bits-vs-nats). Against the live corpus it reports **42
undeclared uses**, concentrated in `surveys/multimodal-llms` (`N` in scaling-law contexts,
`D` in token-budget contexts).

- Declare the basis once per section, or once survey-wide in the notation contract.
- When a survey reaches zero findings, add its path to `.claude/math-basis-strict` to hold
  it at `error`.
- Severity stays `warn` (`.claude/math-basis-severity`) until then.

### 2. Cross-link gaps ✅ CLEARED — reachability + coverage still open (`warn`)

**The 3 cross-link gaps are closed** (2026-08-12, `/cross-link` pass on the
`llm-methods` group; `crosslink.py check` now reports *no cross-link gaps*). All three
were genuine links, not rejections, so the rejection ledger stayed empty:

| Pair | Link |
|---|---|
| mech-interp §2.2 → §A.3 | the composition derivation §2.2's prose already gestured at; A.2 and A.4 were linked, A.3 was the hole |
| llms-for-coding §10.3 → §14.3 | §10.3 already ended "quantified in Section 14" — an unlinked prose pointer |
| mech-interp §9.2 → coding §I.5 | cross-survey, so a plain relative link with no glyph (correct per the directional convention) |

Still open, and these are what hold the two companion gates at `warn`:

`crosslink.py reach` reports **2 UNREACHABLE wikis**
(`wikis/laptop-scale-training-feasibility.md`,
`wikis/mechanistic-interpretability-coverage-gaps.md`) — no survey links to either by a
reader-facing link.
- For the two wikis: link each from the survey section it supports, or — only if it is
  genuinely a process/methodology doc with no survey host — declare it in
  `.claude/reachability-keepout`. Do **not** park a derivation wiki there.
- `surveys/llms-for-coding/executive-summary.md` reports INVISIBLE to the index (its
  headings carry no section number, by design for a preamble). It is currently neither
  numbered nor kept out, because a file-level keep-out inside a grouped directory is a
  CONFLICT to the coverage gate. Either accept the standing warning, number the summary's
  headings, or add file-level keep-out support to `crosslink.py`.

### 3. Pre-existing telecom leakage in viewer test fixtures

Ten `viewer/tests/**` files carry telecom fixture content from the original bootstrap
(FLL/PLL block diagrams in `mermaid.spec.js`, an NTN-survey corpus list in
`profile-highlight-locatability.spec.js`, `5g-nr-ldpc` paths in `root-resolvers.test.js`,
`palette-rank.test.js`, `publish-multiroot.test.js`, `citation.test.js`,
`duplicate-heading-anchors.spec.js`, `single-line-display-math.spec.js`,
`highlight-color-prefix-rendering.spec.js`). These are **untouched by this sync** — they
predate it — so they were left alone rather than rewritten blind. Two fixtures that this
sync *did* touch (`citation.spec.js`, `highlights-resolve-inline-math.spec.js`) were
re-domained.

Rewriting the rest is safe but must be done with the suite green after each file, since
several assert on exact fixture strings. Supersedes/extends
`todos/2026-06-26-clean-residual-wireless-leakage-in-viewer-tools.md`.

**Deliberately excluded from that cleanup:**
`bench/deep-research-survey/scenarios/RESULTS-2026-05-30.md` names the topics its
experiments were actually run on (Kalman, OFDM, LMS, Viterbi, PLL). Rewriting them would
falsify a measurement record, not genericize it. Its dangling `bugs/` refs were repaired
to non-resolving prose form; the measured topics stay.

### 4. Imported e2e specs run close to the 30 s per-test cap

`viewer/playwright.config.js` sets `timeout: 30_000`. Measured on this host with a
raised cap, the newly-imported / touched specs run at:

| Test | Time |
|---|---|
| `highlight-span-boundary` — *em* case | **29.0 s** |
| `highlight-span-boundary` — **strong** case | 18.5 s |
| `highlights-resolve-inline-math:41` (7-math-span) | **50.2 s** |
| `highlights-resolve-inline-math:140` | 26.7 s |
| `multiroot-serve:165` (outline "All") | 35.0 s |

At the default cap those five **fail**; at `--timeout=120000` all pass (12/12 and
2/2). So this is a timing envelope, not a port defect — the same environmental class
as the closed `todos/2026-06-28-citation-t12-e2e-timeout.md`. Each test does a full
page load with KaTeX render plus a selection/toolbar interaction, and two exceed 30 s
outright.

Options, in order of preference:

1. Give these specs a per-file `test.setTimeout()` (surgical; leaves the rest of the
   suite's 30 s cap intact, so a genuine hang elsewhere still fails fast).
2. Speed up the fixtures — the 7-math-span paragraph at 50 s is the outlier and may
   be doing more KaTeX work than the assertion needs.
3. Raise the global `timeout` (last resort — it masks real hangs everywhere).

Do **not** simply mark them skipped: they guard the `snapOutOfInlineSpans()` splice
fix and the inline-math highlight resolution, both of which this sync imported and
both of which pass on their merits.

### 5. Severity promotions already applied (do not re-litigate)

A post-sync re-check measured each gate at `error` rather than guessing. Three were
promoted `warn` -> `error` because they are provably non-blocking here and match
upstream: `crosslink-severity` (it gates the **block-score** 0.30, and the group's open
candidates are 0.275/0.220/0.208), `derivation-dag-severity`, `reproduce-block-severity`.

Still at `warn` because they DO block today — these are the ones items 1-2 above are
about, and each flips to `error` when its backlog clears:

| Toggle | Blocks because |
|---|---|
| `math-basis-severity` | the 42 undeclared basis uses (item 1) |
| `crosslink-coverage-severity` | the one INVISIBLE file (item 2) |
| `reachability-severity` | the two unreachable wikis (item 2) |

### 6. Opt-in registries left empty on purpose

`.claude/rollup-pages`, `.claude/program-manifests`, `.claude/math-basis-strict`,
`.claude/math-rederive-strict`, and `check-math-oracles.py`'s `ORACLE_DIRS` are all empty
here. Their gates are no-ops until a first entry is added. Nothing is broken; this is the
note so a future session knows the emptiness is deliberate, not an omission.

### 7. `check-value-ledger` declaration assertion relaxed

`viewer/tools/test_check_value_ledger.py::test_the_real_corpus_is_actually_in_scope`
upstream asserts `n_decl > 0`. The `<!-- val:ID = V -->` ledger is opt-in and this corpus
has not adopted it, so that assertion would test the corpus's conventions rather than the
tool's scope. It is scoped down with a comment; re-enable it once the ledger is in use.

### 8. Not imported from upstream `main`

- `.claude/hooks/check-hook-wiring.sh` (SessionStart auto-repair of the hook pointer +
  exec bit) lives on an upstream **branch**, not `main`, so it was out of scope for a
  main-branch sync. The `SessionStart` `core.hooksPath` install *was* imported via
  `.claude/settings.json`; the exec-bit assertion and stale-copy detection were not.
- The campaign-execution harness (`campaign.json` manifests, pre-registration gate,
  generated ledger, `viewer/tools/lib/prereg.py`, `check-campaign.py`,
  `build-ledger.py`, `campaign-status.py`, `.claude/rules/campaign-execution.md`) is also
  branch-only upstream. Worth revisiting when it reaches upstream `main`.

## Acceptance

- `check-basis-declarations.py surveys/*/` reports 0 findings, and the cleared surveys are
  listed in `.claude/math-basis-strict`.
- `crosslink.py check` and `crosslink.py reach` report 0 at `warn`, and the severities are
  promoted to `error`.
- The leakage grep in `.claude/commands/sync-upstream.md` § 3 returns only the documented
  self-hits across `viewer/tests/**`.
- `npm --prefix viewer test` green after each fixture rewrite.

## Refs

- Upstream range `9b118d3940d54307a76ebee350c10b2fe4cf22bf..cedfccb2` (origin/main).
- `decisions/2026-08-12-01-inbound-upstream-sync-scope-calls.md`
- `prompts/2026-08-12-upstream-sync.md`
- `.claude/upstream-sync.json` (high-water mark)
