# Clean residual wireless example-strings in viewer/tools/ docstrings

status: closed

## Context

While adapting the `/sync-upstream` command (2026-06-26), its step-3 leakage grep
(`ldpc|3gpp|ntn|...` over `CLAUDE.md .claude/ viewer/tools/`) surfaced four
wireless/telecom example strings that leaked through the original 2026-06-13
bootstrap port from `../data-channel-receiver` and were never retargeted. They are
docstring / `--help` usage examples and one code comment — cosmetic, no logic,
no citations, tools run identically. Deferred because they are unrelated to the
sync-command deliverable and are better batched into a real cleanup pass.

## What is left

Replace the upstream domain examples with LLM-survey equivalents:

- `viewer/tools/lint-math.py:81` — usage example `surveys/ntn-initial-sync-tracking/` → an LLM survey slug (e.g. `surveys/attention-demo/`).
- `viewer/tools/build-index.py:8` and `:11` — `surveys/ntn-survey.md` → an LLM example path.
- `viewer/tools/test_lint_math.py:96` — comment referencing `wikis/ldpc-signed-minsum-...md:8`; genericize or point at a local fixture (keep the bug-`2026-06-01-03` reference if the test logic depends on that shape).

## Acceptance

`grep -rniE 'ldpc|3gpp|\birc\b|harq|\bofdm\b|otfs|\bntn\b|\b5g\b|wireless|\bfll\b|\bpll\b|beamform|zadoff|\bisac\b|\bbler\b' CLAUDE.md .claude/ viewer/tools/`
returns only the two by-design provenance files (`.claude/commands/sync-upstream.md`,
`.claude/upstream-sync.json`). The four `viewer/tools/` hits are gone. `viewer/tools/test_*.py` still pass.

**Resolution.** Fixed during the upstream-sync batch 2 (viewer/tools port): `lint-math.py:81` `ntn-initial-sync-tracking/` → `attention-demo/`; `build-index.py` `ntn-survey.md` → `attention-survey.md` (×2); `test_lint_math.py:96` comment genericized (dropped `wikis/ldpc-signed-minsum` + bug ID). Full-harness leakage grep now CLEAN (only the two by-design provenance files remain). Tests 17/17 pass.

## Refs

- Command: `.claude/commands/sync-upstream.md` (step 3 verify).
- Decision: `decisions/2026-06-26-01-adapt-sync-upstream-command.md`.
- Conversation log: `prompts/2026-06-26-adapt-sync-upstream-skill.md`.
