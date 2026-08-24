# Conversation Log — 2026-08-24 — session: upstream-sync

## Conversation 1
- **Request**: sync the harness from `data-channel-receiver` to `LLM-zeor-to-one`.
- **Actions**: Ran `/sync-upstream` inbound end-to-end. Resolved the mark
  (`cedfccb2`), fetched upstream and diffed against `origin/main` (**not** HEAD — the
  working copy sat on a differently-named branch, and the mark's own scope note warns
  about this): 106 config/viewer commits, 107 files, ~15.7K insertions. No round-trip
  (`from llm-zero-to-one`) commits in range.
  Classified the delta, then ported in six passes:
  (1) the campaign-lifecycle **core** — 12 tools incl. `campaign_common.py`
  (`Scope`/`BASES`/`assert_persisted`) and `lib/prereg.py`, plus rules
  `campaign-execution.md` + `campaign-lifecycle.md` and an **empty** `.claude/campaigns`;
  (2) 5 new generic gates + `job_status.py` (relocated from upstream's top-level `tools/`
  into `viewer/tools/`, which is this repo's tool home) + the 17-module test suite;
  (3) 10 modified tools via `git merge-file` 3-way against the locally-adapted copies
  (7 clean, 1 conflict in `test_check_record_ids.py` resolved by keeping BOTH sides —
  both were pure additions);
  (4) 2 new + 5 modified rules, re-domained;
  (5) `check-hook-wiring.sh` on SessionStart, the pgrep-self-match detector, the pre-push
  wiring, and 9 skill-options registry entries;
  (6) 3 skill deltas + `viewer/GUIDE.md` + the `CLAUDE.md` catalogs.
- **Result**: pre-push gate **green** (exit 0). It now runs **477 tests** it previously ran
  none of. Mark advanced to `24cfca29`. Two decisions and one todo filed. Zero telecom
  leakage across every file the sync touched.
- **Findings**:
  - **The delta is not uniform, and the split is structural, not stylistic.** The campaign
    subsystem divides cleanly into a stdlib-only parameterized core and four drivers welded
    to `artifacts/nr-pdsch-demod`'s conformance register. Porting the second half would
    have meant inventing an LLM register schema nobody uses — authoring, not porting
    (`decisions/2026-08-24-01`). Same shape for the spec-mirror family, which resolves
    against four things absent here (`decisions/2026-08-24-02`).
  - **The newly-wired test runner is what made the sync honest.** Upstream's own note says
    those 20 `viewer/tools/test_*.py` files "were executed by NOTHING"; wiring them
    surfaced 10 failures. Diagnosing them against a clean `git worktree` of HEAD showed
    **7 were pre-existing and environment-caused** (`markdown-it-py` absent, not a code
    defect — they fail identically upstream) and 3 were in the file I had just ported. The
    worktree comparison is what separated "I broke this" from "this was already red", and
    it took one command.
  - **A ported test can be domain-specific in a way the tool is not.**
    `test_check_basis_declarations.py` exercises a `file_context` guard through
    *time-interleaved-converter* vocabulary. The ported fix (`prose_only`) is generic and
    landed; but **no rule in this repo's re-domained registry declares a `file_context` at
    all**, so the guard is dormant here. Rewrote it to test `prose_only()` directly and
    skipped the file-level cases with that named reason, rather than inventing a
    `file_context` rule to have something to test.
  - **My own edits tripped the gate I was porting.** `check-skill-options.py` caught 8
    `[opt:…]` site markers I had added with no registry entry. It also caught two
    pre-existing drifts — and revealed that upstream passes `DRS-HARDEN` only *accidentally*
    (the string appears in its `plans/`/`todos/`, not as a real site marker). Fixed here by
    putting a real marker at the point of use.
  - **`| tail` ate an exit code mid-session** — the exact trap
    `.claude/rules/reported-vs-persisted.md`, which this same sync ported, warns about in
    its check 4. Re-ran unpiped; `check-record-ids.py` was exiting **1**, not 0, on a
    dangling `decisions/` ref left in `reset-durability.md` by the *previous* sync. Fixed.
  - **Two gates landed at `error` rather than `warn` because their backlog was measured at
    zero**, following the repo's own bare-refs/crosslink rollout rule:
    `campaign-phrasing-severity` (0 findings over 108 files) and `check-skill-options`.
    `notation-table-severity` landed at `warn` with a measured 6-file backlog.
  - **Three launcher scripts were already byte-identical** to upstream's — the same change
    landed in both repos independently (local PR #4 / upstream PR #176). Only the *test*
    was missing, so that is all that was ported.

<!-- LOG-END -->
