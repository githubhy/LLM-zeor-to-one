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

## Conversation 2
- **Request**: `/goal finish all todos spawned in this session`.
- **Actions**: Worked `todos/2026-08-24-upstream-sync-followups.md` end to end. Cleared the
  6-file notation-table backlog — five `llms-for-coding` appendices served by **one** shared
  table appended to that survey's `index.md`, the sixth (`_scratch/ev-A-B.md`) taking the
  one-line `<!-- notation-table: … -->` opt-out — then flipped
  `.claude/notation-table-severity` to `error`. Re-domained all ten `viewer/tests` telecom
  fixtures. Installed the viewer's runtime deps, got the JS suite green, and wired it into
  `.githooks/pre-push` with a verified loud-skip path. Updated `CLAUDE.md` and
  `math-authoring.md` to match, and closed the todo.
- **Result**: gate green, now **807 tests** (477 Python + 330 JS). `surveys/` lints at **0
  errors** (was 3). Leakage grep clean with **no `viewer/tests` carve-out**. Four items
  resolved, one withdrawn, two retained as preconditions.
- **Findings**:
  - **One of my own todo items was a false finding.** Item 6 claimed `pytest` was missing
    from `requirements.txt`. It has been there since before the sync — `git show HEAD~1`
    confirms it. I had written the item from recollection instead of reading the file, which
    is exactly what `citation-integrity.md` forbids for external sources, committed against
    my own repo. Recorded as withdrawn rather than deleted: a withdrawn finding is evidence
    about the process that produced it.
  - **Item 4's premise was half wrong too, and the correction is load-bearing.**
    `node --test` is a Node built-in, so 312 of the 330 JS tests never needed
    `node_modules` — only the three that actually start `serve.js` did. Running the suite
    without deps produced **25 failures that look exactly like defects and are not**. That
    is the argument for the pre-push block skipping *loudly* instead of running a partial
    suite, and I verified both branches by moving `node_modules` aside.
  - **Diagnosing "pre-existing vs mine" needs a clean worktree, not a guess.** 22 of those
    25 failures also fail at `HEAD~1`; a `git worktree add` of the prior commit separated
    them in one command. The same technique settled the same question in Conversation 1.
  - **Re-domaining a fixture can silently destroy the property it tests.** Renaming
    `palette-rank`'s nested path from `5g-nr-ldpc/intro.md` to `peft-methods/intro.md` broke
    the test, because the original *contained the query as a substring* and the replacement
    did not. The test caught it. `citation.test.js` needed a coordinated rename — its
    paragraph anchor and heading slug derive from the filename — and two regex literals with
    escaped slashes that a plain path replacement misses.
  - **`profile-highlight-locatability.spec.js` was measuring nothing**: it profiled 12 NTN
    survey files and 10 `theories/` docs, none of which exist here. Repointed at the real
    interpretability corpus and `wikis/`. `mermaid.spec.js` was skipping gracefully against
    an absent doc; it now targets a local survey with 5 real mermaid blocks.
  - **The opt-out marker must be on ONE line.** `check_notation_table` scans line-by-line, so
    my first (wrapped) marker never matched and read as a silent non-opt-out. Documented in
    `math-authoring.md` so the next author does not lose the same ten minutes.
  - **Before writing the notation table I verified every collision against the source.**
    Seven confirmed ($L$, $E$, $h$, $\beta$, $p$, $k$, $V$). A claimed
    $T$-as-decoding-temperature collision was **dropped** — grep found only softmax-temperature
    *analogies*, so asserting it would have been the very memory citation the table exists to
    prevent.
  - **The 3 standing `lint-math` errors were never math**: `$38k` and `~$0.40/M` currency
    signs read as inline math. Escaped; only a backslash changed, values untouched.

<!-- LOG-END -->
