---
id: 2026-06-29-03
title: Fold the logit-position answer as an inline-only §A.9 Note (no dedicated section)
status: accepted
date: 2026-06-29
plan: n/a (direct request — "fold this answer to the survey")
---

## Context

After answering "What is the logit position?" (about $\mathbf{e}^{\text{logit}}$ /
$W_{OV}$ in Equation (9) of §A.9), the user said "fold this answer to the survey."
The named match is the `survey-explainer-fold` skill, whose default ships TWO
artifacts: a compact inline `> **Note —**` AND a dedicated, link-targetable
numbered subsection. The preceding companion fold this session (the
e^own/e^prev notation, Conversation 4) was explicitly narrowed by the user —
mid-skill — to "integrate this to the survey inline," i.e. Note-only.

## Decision

Fold the logit-position answer as a SINGLE inline `> **Note —**` blockquote
placed immediately after the existing e^own-notation Note (right after Equation
(9)), with no dedicated section — deviating from the skill's two-artifact
default.

## Alternatives considered

- **Full fold (Note + dedicated numbered subsection).** Rejected: (a) the user's
  immediately-prior fold of the *paired* notation Q&A was explicitly scoped to
  inline-only, a strong same-session preference signal; (b) structurally awkward
  here — a dedicated subsection appended adjacent to §A.9 cascades every later
  `A.x` heading (renumber-sections does not rewrite printed numbers, so every
  shifted heading + secref needs a manual edit), and appended at the appendix
  end it sits ~9 sections from its §A.9 host with only a long forward link
  tying it back.
- **Extend the existing e^own Note in place.** Rejected: that Note is titled and
  self-contained about the input side (own/prev/$M$); a separate Note titled
  about the logit position directly answers the user's question and keeps each
  gloss focused.

## Consequences

- Equation (9)'s notation is now glossed by two adjacent Notes — input side
  (own/prev, $M$) and output side (logit, $W_{OV}$) — co-located at the host, no
  new section, zero equation/section cascade (only paragraph anchors renumbered:
  9 updates).
- The answer is permanent and paragraph-anchored (citation-toolbar targetable)
  but not section-link-targetable; acceptable for a notation gloss.
- Establishes the working pattern for this session's notation Q&A folds:
  inline-only Note, not the full two-artifact fold.

## Refs

- File: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.9 (Note after Eq (9))
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 5
- Related: decision `2026-06-29-02` (the §A.9 diagrams the Note cross-ties to);
  the `survey-explainer-fold` skill, whose two-artifact default this deviates from
