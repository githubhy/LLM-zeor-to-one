---
id: 2026-06-30-01
title: Formalize survey-explainer-fold output as three modes (full / note-only / prose), not just add the requested prose mode
status: accepted
date: 2026-06-30
plan: n/a (direct request)
---

## Context

The user asked to "add an option for the fold skill for the plain-prose
folding" — a mode where a just-answered Q&A is folded as plain main-flow
paragraphs at the host (no `> **Note —**` blockquote, no dedicated section),
which had already been done by hand three times this session (§A.20 of
`surveys/llms-for-coding/appendix-a-qkv-first-principles.md`: "Reading the two
ones", the full "what the 1's encode" expansion, and "Where the two values come
from" / "Why this query–key pair"). The `survey-explainer-fold` skill's
contract was a *rigid two-artifact* output (inline Note + dedicated anchored
section). A second, lighter shape — inline Note only — already existed as an
*ad-hoc deviation* recorded in decision `2026-06-29-03` and the
`inline-notation-folds-preference` memory, but was not part of the skill's
documented contract.

## Decision

Document the skill's output as **three first-class modes** — `full` (default,
the existing two-artifact fold), `note-only` (the inline Note alone), and
`prose` (plain main-flow paragraphs, no box, no section) — selected per request,
default `full`, overridden by the user's phrasing. Add a `## Modes` table
(artifacts × use-when × which workflow steps apply), a Step-2′ for the prose
insert, mode tags on Steps 3–5 (full-only) and the Step-2 note-only carve-out,
a mode-aware checklist, and a no-cascade reminder hoisted into the Modes
section. The mechanics (placement rules, no-cascade discipline, the Step-6
renumber/validate sweep, citation integrity) are explicitly *identical* across
modes — only which artifacts ship changes.

## Alternatives considered

- **Add only the `prose` mode the user named.** Rejected: `note-only` was
  already an undocumented deviation living only in a decision + memory, so the
  skill's stated contract (always two artifacts) was already false. Formalizing
  all three at once makes the contract honest and gives one selection rule
  instead of one documented mode plus two folklore exceptions.
- **A separate skill for plain-prose folds.** Rejected: same host-location,
  same no-cascade discipline, same sweep — only the artifact shape differs. A
  mode flag on the existing skill avoids duplicating the entire mechanics
  section and keeps the selection decision in one place.
- **Make `prose` the new default.** Rejected: the full fold is still correct for
  substantial, link-targetable answers; the user picks the lighter shapes
  situationally ("fold this directly / without the note"). Default stays `full`;
  the caller overrides.

## Consequences

- `survey-explainer-fold/SKILL.md` now carries a `## Modes` section, Step 2′,
  mode-tagged Steps 3–5, a no-cascade line, an updated frontmatter description,
  Inputs `mode` field, and a mode-aware checklist + cross-link sign-off note.
- **Aliases added (same-day follow-up):** the two lighter modes carry
  user-vocabulary aliases — `inline` → `note-only`, `direct` → `prose` — shown
  as "(aka …)" in the Modes table and pinned in the selection paragraph on the
  **box vs. no box** axis. `direct` is unambiguous (the user's actual trigger
  word for prose); `inline` is overloaded (prose is the *more* inline mode), so
  the doc fixes the mapping explicitly (`inline` = the boxed Note) to stop a
  future reader routing it to `prose`. Rejected `note`/`gloss` as the
  note-only alias in favor of the user's established word "inline".
- The `inline-notation-folds-preference` memory is updated to record the
  plain-prose tendency as a third shape and to point at the skill's modes and
  this decision.
- Supersedes nothing; complements `2026-06-29-03` (note-only fold) and
  `2026-06-29-04` (full fold) by lifting both ad-hoc shapes plus the new one
  into the documented contract.
- No `todos/` (request completed this turn). No new external citations (a skill
  doc edit; citation-integrity not engaged).

## Refs

- File: `.claude/skills/survey-explainer-fold/SKILL.md`
- Worked prose-mode instances: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md`
  §A.20; session log `prompts/2026-06-29-viewer-serve-launcher.md` Conversations
  15, 16, 18
- Memory: `inline-notation-folds-preference` (updated this turn)
- Related: `decisions/2026-06-29-03-logit-position-inline-fold.md`,
  `decisions/2026-06-29-04-kcomposition-dedicated-section.md`
