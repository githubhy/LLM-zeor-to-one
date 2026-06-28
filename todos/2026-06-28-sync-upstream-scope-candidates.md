---
slug: sync-upstream-scope-candidates
date_filed: 2026-06-28
status: closed
---

**Resolution (2026-06-28).** User went with the recommendations: **added** `bench/`,
`.gitignore`, `.viewerignore` to the `/sync-upstream` inbound §1 pathspec + path list (with
handling notes: bench scenarios re-adapted & context-isolated; `.gitignore`/`.viewerignore`
surgical merges) and the §3 leakage scan (`bench/`). **Held** (decided against for now,
revisit on request): `.github/workflows` + `.claude-sync.yml` (separate `FenLinger/claude-config`
sync lineage), `viewer.content.json`/`viewer.manifest.json` (domain root list), top-level `tools/`
(telecom-specific). The HOLDs are recorded inline in the command file's §1 "Still out of scope"
note. Committed in the `/sync-upstream` scope-expansion commit.

# Decide which additional infrastructure paths to add to /sync-upstream inbound scope

## Context

`decisions/2026-06-28-06` broadened `/sync-upstream` inbound scope to include the whole viewer
app (`viewer/**`). The user asked to also be shown the *other* currently-out-of-scope items so
they can decide which to fold in. This todo holds that pending decision so it is not lost if the
conversation moves on. Grounded against real files (here vs `../data-channel-receiver`).

## What is left

User to decide, per candidate, whether to add it to the inbound `git diff` pathspec in
`.claude/commands/sync-upstream.md` §1 (and the §3 leakage/verify handling). Candidates:

| Candidate | Here? | Upstream? | Nature | Suggested |
|---|---|---|---|---|
| `bench/` (skill pressure-test harness) | yes (deep-research-survey) | yes (+reference-implementation-study) | harness=infra; RED scenarios=domain | ADD (re-adapt scenarios) |
| `.gitignore` | yes | yes | infra; local divergence (viewer-highlights) | ADD (surgical merge) |
| `.viewerignore` | yes | yes | viewer content-root prune (mostly generic here) | ADD (viewer-related) |
| `.github/workflows/` (CI) | no | yes (`sync-claude-config.yml`) | CI automation, but pulls in the claude-config consumer mechanism | HOLD (separate sync lineage) |
| `.claude-sync.yml` | no | yes | makes repo a consumer of external `FenLinger/claude-config` | HOLD (adopts a 2nd sync system) |
| `viewer.content.json` / `viewer.manifest.json` | no | yes | viewer multi-root config; root list is domain-specific | HOLD (domain root list) |
| top-level `tools/` | no | yes (`fetch_3gpp_specs.py`, `mtef_decode.py`) | mostly telecom-specific (3gpp fetcher) | HOLD / cherry-pick `mtef_decode.py` only |

Keep excluded (domain content + audit trail — not candidates): `surveys/ docs/ reports/ sim/
octave/ download/ theories/ wikis/ proposals/ archives/ artifacts/ dist/ implementation/
simulations/ QA-sessions/ temp/`; `decisions/ bugs/ todos/ field-notes/ prompts/ plans/`.

## Acceptance

For each chosen candidate: added to the §1 pathspec + §1 path list, with handling notes (re-adapt
/ surgical / keep-local) and a verify step; `/sync-upstream --dry-run` reports it; this todo closed
with the final set recorded.

## Refs

- `decisions/2026-06-28-06-sync-upstream-include-viewer.md`
- `.claude/commands/sync-upstream.md` §1
- Conversation log: `prompts/2026-06-28-qkv-index-notation-fold.md` (Conversation 8)
