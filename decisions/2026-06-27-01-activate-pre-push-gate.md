---
id: 2026-06-27-01
title: Activate the .githooks/pre-push gate via core.hooksPath; adapt it to the multi-survey layout
status: accepted
date: 2026-06-27
plan: .claude/commands/sync-upstream.md
---

## Context

Final batch of the 2026-06-27 upstream sync. The upstream delta modifies
`.githooks/pre-push` (a tracked survey-wide validation hook). This repo had **no**
git pre-push hook — `CLAUDE.md` previously stated `/check-survey` was the sole
authoritative gate and called the repo "not git-initialized" (stale: it is a live
git repo). The user was asked how to handle the hook and chose **"Port and
activate."**

Two reality gaps surfaced on porting:

1. **Activation mechanism.** Upstream installs the hook by *copying* it into
   `.git/hooks/` via `scripts/install-git-hooks.sh` (not ported). Git's
   `core.hooksPath` lets the tracked `.githooks/` directory serve hooks directly
   — no copy, no install script, and the hook stays version-controlled.
2. **Layout mismatch.** The upstream hook runs the validators on `surveys/`
   (a flat layout). This repo is **multi-survey**: `surveys/llms-for-coding/` and
   `surveys/attention-demo/`, each with its own `order.json`. `renumber-equations`
   and `renumber-paragraphs` exit 1 when handed the `surveys/` parent (no `.md` /
   `order.json` directly there), so the ported-verbatim hook blocked every push.

## Decision

Port `.githooks/pre-push`, **activate** it with `git config core.hooksPath
.githooks`, and **adapt its body** to iterate over each `surveys/*/order.json`
directory (the same per-survey target `/check-survey` resolves), running
`validate-refs` + the three renumber `--check` passes + bare-refs-at-error per
survey, then the corpus-level `crosslink.py check` (advisory at `warn`). Also
adapt `python` → `python3` (macOS has no `python`).

## Alternatives considered

- **Port file but don't activate** (the recommended-in-question option). Rejected:
  the user explicitly chose to activate.
- **Copy-install into `.git/hooks/` (upstream mechanism).** Rejected: needs the
  un-ported install script and de-syncs the live hook from the tracked source;
  `core.hooksPath` is simpler and keeps the hook under version control.
- **Run validators on `surveys/` verbatim.** Rejected: blocks every push in this
  repo's layout (proven — exit 1 from two renumber checks). The per-survey loop is
  the faithful equivalent of the local gate.

## Consequences

- `git push` now runs the full survey-wide gate; verified green on the current
  corpus (both surveys clean; 5 advisory cross-link gaps listed, non-blocking).
- `core.hooksPath` is **local git config** (`.git/config`), not committed — a
  fresh clone must re-run `git config core.hooksPath .githooks` to activate.
  Documented in `CLAUDE.md` Validation Hooks.
- Bypass remains `git push --no-verify`.
- The hook will block a push only on a real validation error or (if
  `.claude/crosslink-severity` is raised to `error`) an at-threshold cross-link
  gap. Cross-link severity stays `warn` (advisory) for now.

## Refs

- `.claude/commands/sync-upstream.md`; decisions `2026-06-26-01`, `2026-06-26-02`.
- Branch `sync/upstream-2026-06-26`, batch 5 (final).
- `.claude/rules/cross-linking.md` (the pre-push cross-link gate it references).
- Conversation log: `prompts/2026-06-26-adapt-sync-upstream-skill.md` (Conversation 7).
