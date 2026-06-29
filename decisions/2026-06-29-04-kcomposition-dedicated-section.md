---
id: 2026-06-29-04
title: Fold the K-composition elaboration as a full survey-explainer-fold (inline Note + new §A.18)
status: accepted
date: 2026-06-29
plan: n/a (direct request — "fold this into the survey as a fuller dedicated subsection this time")
---

## Context

After answering "elaborate 'the cross-layer K-composition'" for §A.9, the user
asked to fold it in "as a fuller dedicated subsection this time" — explicitly
overriding the session's established inline-only default (decision `2026-06-29-03`
and the saved `inline-notation-folds-preference` memory, both of which carve out
"unless the user asks for a section"). The K-composition answer is richer than the
prior notation glosses: a Q/K/V taxonomy plus a two-equation derivation of the
composed virtual circuit — genuinely section-worthy.

## Decision

Run the full `survey-explainer-fold`: a compact inline `> **Note —**` at §A.9
(forward-linked) PLUS a new dedicated section **§A.18 "Composition Across Layers:
Q-, K-, and V-Composition"** appended at the END of appendix-a, carrying two new
numbered equations (the key's residual decomposition; the virtual two-layer QK
circuit $M\,W_{OV}^{\text{prev}}$).

## Alternatives considered

- **Inline-only (the session default).** Rejected here: the user explicitly asked
  for a dedicated subsection, and the taxonomy + derivation exceed what a single
  blockquote should carry.
- **Co-located 3-level subsection A.9.x.** Rejected: appendix-a uses only 2-level
  headings (A.1–A.17); a lone A.9.x would break the style, and the skill permits
  3-level only "if the appendix already uses them."
- **Mid-appendix insert (a new A.10, shifting A.10–A.17 → A.11–A.18).** Rejected:
  renumber-sections does not rewrite printed heading numbers, so this forces a
  manual renumber of every later heading and every secref/secxref corpus-wide.
- **Append at the appendix end as the new highest section A.18 (chosen).**
  Cascade-free for sections (no later sibling) and for equations (new tags are
  highest, so (1)–(18) are untouched); the §A.9 → §A.18 forward link bridges the
  distance, exactly as A.13 "Concrete Dimensions" already does for its hosts.

## Consequences

- A.18 is a new link target (composition / virtual heads) for future cross-links
  from §A.9, §A.10 (multi-head), and the induction discussion.
- Two new equations (19), (20); 20 eq tags total in appendix-a, sequential, no
  cascade. New paragraph anchors under the A.18 slug.
- Citations: reused [59] (Elhage 2021) for the Q/K/V taxonomy + "virtual attention
  heads" and [60] (Olsson 2022) for the ICL-coincidence — both verified against
  their live pages via WebFetch at authoring time (citation-integrity); the
  induction = K-composition claim is derived inline, not rested on the web refs.

## Refs

- File: `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` §A.9 (Note), §A.18 (section)
- Conversation log: `prompts/2026-06-29-viewer-serve-launcher.md` Conversation 6
- Related: decision `2026-06-29-03` (the inline-only logit-position fold this
  contrasts); decision `2026-06-17-02` ([59]/[60] non-load-bearing web-cite
  posture); the `inline-notation-folds-preference` memory's "unless the user asks
  for a section" carve-out
