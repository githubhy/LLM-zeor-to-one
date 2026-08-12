---
slug: sync-back-generic-tool-fixes
date_filed: 2026-08-12
status: open
---

# Sync back three generic fixes made HERE that upstream lacks

## Context

The 2026-08-12 inbound sync (`9b118d3..cedfccb2`) and the `/cross-link` pass that
followed produced three fixes that are **domain-agnostic bug fixes, not
genericization** — the `SYNC-BACK` bucket in `/sync-upstream --back` § R0, not
`SKIP-genericization` or `SKIP-domain`. Each was verified against `origin/main` on
2026-08-12 as still absent upstream.

They are *not* the re-domained skills from the same sync (`spec-provenance`,
`kernel-bringup`, `accelerator-cost-study`) — those diverge from upstream **by
design** and are `SKIP-domain`. See `decisions/2026-08-12-01`.

## What is left

Run `/sync-upstream --back`, scoped to these three. In R0 terms all three are
**end-to-end-generic** (a tool fix plus its tests, no domain refs), so they copy
wholesale rather than needing a surgical seam edit — but confirm that against
upstream's actual text before copying, since upstream may have moved.

### 1. `viewer/tools/check-record-ids.py` — scan git's tracked set, not `rglob`

**Highest value of the three: this one breaks upstream's own push.** The gate scans
with `ROOT.rglob("*.md")` (upstream `check-record-ids.py:180`), which sweeps in
gitignored build output. Playwright writes `test-results/<case>/error-context.md`
containing a copy of the failing test's **source comment** — bug IDs included — so
merely **running the viewer suite** makes the gate report dangling refs and fail the
push, on a path that is gitignored and varies per machine and per run.

Here it scans git's tracked set (inheriting `.gitignore`) with a filtered-`rglob`
fallback for a non-git root. Carry both regression tests: generated output is not
scanned, **and** an authored dangling ref still fails — the second is what proves the
exclusion did not blunt the gate.

Upstream is more exposed than this repo, not less: it has a larger viewer suite and
its `bugs/` corpus is bigger, so more source comments carry resolvable-looking IDs.

### 2. `viewer/tools/crosslink.py::short_text` — do not truncate mid-phrase

Upstream cuts link text at 6 words with no ellipsis, so a `Name: Subtitle` heading
loses its tail: "A Discovered Circuit: Reverse-Engineering a Real Model" renders as
link text ending "…a Real", which reads as a dropped word rather than an
abbreviation.

Here it truncates at the subtitle **colon** when the head is a usable label
(>= 2 words), else falls back to the word cap **with** an ellipsis. Four regression
tests. `Name: Subtitle` is a common heading shape in both corpora, so upstream hits
this too.

**Carry the operational note with it** (it cost a revert-and-redo cycle here):
`link_markdown` is frozen into the candidates JSON at Stage 2 and replayed by
`apply`, so fixing `short_text` changes nothing until Stage 2 is re-run. Worth a
comment at the `short_text` definition upstream.

### 3. `viewer/viewer.js` — resolve relative asset links against the doc's directory

Upstream has **0** occurrences of this guard; this repo has 2 (the main content
renderer and the split-pane renderer). Without it a link to `figures/*.svg` or a
`.pdf` resolves against the SPA root and 404s, while images beside it resolve
correctly — an asymmetry a reader hits as a broken link.

This one has history: it survived the 2026-08-12 inbound sync only because it was
**deliberately re-applied** after taking upstream's `viewer.js` wholesale. Left
unsynced it will need re-applying by hand on every future inbound viewer sync, which
is exactly the drift the `--back` direction exists to stop.

## Deliberately NOT in scope

- **`check-citation-sources.py`'s added `\bRFC\s?\d`** — that widened `_SPECNUM_RE`
  toward the identifiers *this* corpus cites (RFC / MCP specs). Additive and harmless
  upstream, but it is domain-ward, not a bug fix. `SKIP-domain`.
- **`test_corpus_scope.py`'s corpus-derived floor** — replaced a magic `n > 100` that
  is correct for upstream's 811-file corpus and wrong for this 78-file one. Arguably a
  robustness improvement for any repo, but upstream's assertion passes today, so it is
  a judgment call rather than a fix. Offer it in the PR body as optional; do not
  bundle it silently.
- **`check-basis-declarations.py`'s registry** — fully re-domained to LLM bases.
  `SKIP-domain`.

## Acceptance

- A `sync-from-llm-zero-to-one` branch on `FenLinger/data-channel-receiver` carries
  the three fixes with HERE provenance stripped (no local bug/decision IDs, no LLM
  paths in fixtures), and the PR body names what was excluded and why.
- Upstream's own suites pass on that branch — `python3 -m pytest viewer/tools` plus
  the viewer tests touching `viewer.js`.
- Test-completeness checked per R2: `grep -rl 'short_text\|_scan_files' viewer/tools`
  here, and each corresponding test file confirmed present upstream.
- On merge, advance `last_synced_commit` in `.claude/upstream-sync.json` to the
  post-merge upstream HEAD (R4), or the next INBOUND run re-detects the round-trip.
  The `from llm-zero-to-one` subject filter is the backstop, not the plan.

## Refs

- `decisions/2026-08-12-01-inbound-upstream-sync-scope-calls.md` — the sync's scope
  calls, including why the re-domained skills are `SKIP-domain`.
- Commits `cbd01c7` (record-ids scan fix + its two tests) and `3af5c8c` (short_text
  fix + its four tests, and the Stage-2/Stage-4 note).
- `prompts/2026-08-12-upstream-sync.md` Conversations 2 and 3.
- `.claude/commands/sync-upstream.md` — the `--back` procedure (R0–R4).
- Supersedes the follow-on half of the now-closed
  `todos/2026-07-05-land-viewer-fixes-upstream-via-back-sync.md` (its own PR #36 is
  merged).
