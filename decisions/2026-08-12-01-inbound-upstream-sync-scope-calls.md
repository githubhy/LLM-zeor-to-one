---
id: 2026-08-12-01
title: Scope and re-adaptation calls for the 9b118d3..cedfccb2 inbound upstream sync
status: accepted
date: 2026-08-12
---

## Context

`/sync-upstream from the main branch of ../data-channel-receiver`. The high-water mark in
`.claude/upstream-sync.json` was `9b118d3` (2026-06-28). Two facts reshaped the run before
any porting started:

1. **The upstream working copy is live and was mid-branch.** A first read of `HEAD` landed
   on `plan/tr38901-calibration-campaign` (a concurrent session moved it). Diffing against
   that branch would have imported a campaign-execution harness that is **not on `main`**.
2. **Upstream's local `main` was 1647 commits behind `origin/main`.** The user's phrasing
   ("from the main branch") resolves to the branch's true tip, so the sync was scoped to
   `origin/main` = `cedfccb2` after an explicit `git fetch`.

Final range: `9b118d3..cedfccb2`, **162 files / ~20,287 insertions** across 245
config+viewer commits. Two commits were skipped by the round-trip guard
(`444aeb0d`, `710afc6f` — this repo's own sync-backs, PRs #15 and #36, both now merged
upstream).

## Decision

Port the whole delta, with six judgment calls:

1. **The ASIC hardware-realization family → re-domained to GPU/accelerator, not skipped
   and not copied.** Upstream added `asic-rtl-bringup` (bit-exact Verilog vs an integer
   golden) and `asic-synthesis-cost-study` (Yosys + OpenROAD on sky130hd/Nangate45). Both
   were rewritten as `kernel-bringup` and `accelerator-cost-study`. The transferable
   mechanism is *"remove the ambiguity from the reference, then gate against it"*: the
   integer-golden trick becomes a **deterministic** float reference (fixed reduction order,
   float64 accumulation, TF32 off) compared against a **derived** tolerance (`n·u` in the
   accumulator dtype), which is the honest replacement for a default `allclose`. The
   synthesis flow becomes a profiler + roofline + power-sampling flow producing latency
   distribution, achieved FLOP/s vs dense peak *for the dtype used*, HBM utilization,
   memory footprint as a closed form, and joules per token.
   *User-selected among {skip+todo, re-domain, port verbatim}.*

2. **`spec-provenance` → re-domained, 3GPP fetcher dropped.** The skill's value is the
   *draft-vs-published gate*, and LLM work has an unusually thick draft layer: arXiv v1
   vs vN, model cards edited in place with no version bump, blog-post numbers preceding
   the paper, harness defaults drifting between releases. The provenance ladder was
   rewritten around those rungs, `tools/fetch_3gpp_tdoc.py` was not imported (explicitly
   out of `/sync-upstream` scope), and every `[opt:SP-*]` marker the toggle registry
   references was preserved with a re-domained meaning.
   *User-selected among {re-domain, skip+todo, port verbatim}.*

3. **Gate severities start at `warn` where the gate is new here, even when upstream runs
   `error`.** The repo's documented rollout is `off → warn → error`, and these gates have
   never run against this corpus. Exceptions kept at `error` because they are
   deterministic and the corpus is provably clean: `record-ids`, `duplicate-anchor`,
   `foreground-bg`, `math-oracle` and `ris-derivation` (the last two are no-ops with an
   empty registry). `crosslink-severity` stays `warn` — upstream is at `error`, but this
   corpus has 3 open gaps.

4. **Registries that encode upstream's corpus ship empty, with the reason in the file.**
   `.claude/rollup-pages`, `.claude/program-manifests`, `.claude/math-basis-strict`,
   `.claude/math-rederive-strict`, `.claude/internal-eq-refs-rejected.json`, and
   `check-math-oracles.py`'s `ORACLE_DIRS` (which hardcoded `surveys/adc-calibration`).
   An empty registry makes its gate a no-op, which is correct; importing upstream's rows
   would make every one of them fail on a path that does not exist here.

5. **Corpus-calibrated tests are recalibrated from the corpus, not from a new magic
   number.** `test_corpus_scope.py` asserted `n > 100` against upstream's 811-file corpus;
   a literal port fails here at 78 files for reasons that have nothing to do with the tool.
   The floor is now derived (`max(flat_root_md, nested_md // 2)`), which preserves the
   property actually under test — *does the scan get past the corpus root* — at any corpus
   size. `test_check_value_ledger.py`'s `n_decl > 0` was scoped down with a comment: the
   `val:` ledger is opt-in and unadopted here.

6. **A measurement record is not genericized.**
   `bench/deep-research-survey/scenarios/RESULTS-2026-05-30.md` names the topics its
   experiments actually ran on (Kalman, OFDM, LMS, Viterbi, PLL). Rewriting those to LLM
   topics would falsify a record rather than re-domain a fixture. Its *dangling record
   refs* were repaired (they pointed at upstream `bugs/` files that do not exist here);
   the measured topics stay, and the leakage grep is documented as legitimately hitting it.

## Alternatives considered

- **Sync from the working copy's `HEAD`** — rejected: it was a feature branch, and its
  campaign-execution harness is not on `main`. It would have imported unmerged upstream
  WIP under the label of a main-branch sync.
- **Sync from the stale local `main` (`5ff43873`)** — rejected: 1647 commits behind
  `origin/main`, so it would have silently delivered ~⅓ of the delta and advanced the
  high-water mark past the rest.
- **Copy the ASIC skills near-verbatim** — rejected by the user: silicon-flow skills in an
  LLM repo would fail the leakage grep and mislead about what the repo can actually do.
- **Overwrite diverged files wholesale** — rejected: `viewer/viewer.js` carries a
  local-only relative-asset-link fix upstream lacks. The port was a 3-way merge
  (`git merge-file --diff3`) for all 30 skill files: 12 merged clean, 8 conflicted and
  were resolved by hand, keeping local adaptations and adopting upstream's corrections.
  The most consequential correction adopted: `survey-explainer-fold` now requires math
  exhibits as **untagged `$$` KaTeX**, reversing this repo's inherited "ASCII art in a
  fence" guidance, whose stated cascade rationale upstream proved false.

## Consequences

**Enables.** ~30 new gates now run on every push, several of which immediately paid for
themselves against this corpus (see below). `/normalize-survey` gives the write-mode twin
of `/check-survey`. The cross-link corpus is now group-structured with coverage and
reachability gates. The shared hooks moved from the machine-local settings file into the
tracked one, so a fresh clone gets them.

**Defects the new gates found in this repo's own corpus, fixed in this sync:**

- **10 cross-file equation references** in `surveys/mechanistic-interpretability` marked
  `<!-- ref: -->` (same-file) while pointing at a sibling file — a silent-staleness blind
  spot: not an orphan, so `renumber-equations` said nothing; not an `xref`, so it would
  never be propagated. Rewritten to the `xref:` form.
- **Two wikis with no `sec-` anchors**, usable as link sources but never as link targets.
- **11 unresolvable record references** to upstream `bugs/`/`decisions/` IDs, 5 of them
  pre-existing since the original bootstrap.

**A defect found in an imported tool, fixed here:** `check-record-ids.py` scanned the repo
with `rglob("*.md")`, which swept in gitignored generated output — Playwright's
`test-results/**/error-context.md` copies a failing test's *source comment* (bug IDs
included) into a generated file, so merely **running the viewer suite** made the gate fail
the push. It now scans git's tracked set (inheriting `.gitignore`) with a filtered-rglob
fallback outside a checkout.

**Forecloses.** Nothing irreversibly. The re-domained ASIC pair diverges from upstream by
design, so a future inbound sync will show those two paths as here-only rather than as
modified — they are `SKIP-domain` for `--back`, not sync-back candidates.

**Follow-up.** `todos/2026-08-12-upstream-sync-followups.md` — the `[opt:MATH-BASIS]`
42-item backlog, 3 cross-link gaps + 2 unreachable wikis, 10 pre-existing telecom test
fixtures, and the two branch-only upstream subsystems (hook-wiring self-heal,
campaign-execution harness) to revisit when they reach upstream `main`.

## Refs

- Upstream range: `9b118d3940d54307a76ebee350c10b2fe4cf22bf..cedfccb2` (`origin/main`).
- Skipped round-trips: `444aeb0d`, `710afc6f` (this repo's own sync-backs).
- `.claude/upstream-sync.json` — high-water mark advanced to `cedfccb2`.
- `prompts/2026-08-12-upstream-sync.md`
- Supersedes the `pending_sync_back` block: PRs #15 and #36 are both merged upstream.
