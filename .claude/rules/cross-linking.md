# Cross-Linking Rule

Loaded on demand by `CLAUDE.md`. Read this file before authoring or
substantially expanding any survey document or section, before signing off such
a task, or before changing the cross-link tooling or gates.

## The rule

Cross-linking the corpus is **two operations with opposite natures**, and they
live in different places:

| Operation | Nature | Where it runs |
|---|---|---|
| **Detect** a missing high-value link | deterministic, cheap | the lint / generate **gates** (Tier 1) |
| **Insert** the right link at the right place | semantic judgment (agent) | **on-demand**, batched (Tier 2) |

**Never put an agent in a per-edit hook.** An agent judging links on every
`Edit`/`Write` re-creates the exact cost and nondeterminism the `crosslink.py`
pre-filter exists to remove (a prior all-agent sweep spent ~11.5M tokens / 217
agents for 131 links, with a silent apply-persistence failure to recover from).
The gates only **detect and report** gaps; a deliberate on-demand pass
**inserts** them.

This also governs **generation**: a freshly generated document has no
cross-links, so the gap detector fires heavily — by design. The generating
task clears those gaps as its sign-off step (below), or files a `todos/` entry.

## Tier 1 — deterministic detection (in the gates)

`crosslink.py check` runs the deterministic stages, reports unlinked
high-cosine candidates, and **never writes**. It is wired into:

- **Stop-gate** (`.claude/hooks/validate-refs-on-dirty.sh`): once per turn-end
  on the turn's changed files (`--changed`), advisory, **never blocks**.
- **pre-push** (`.githooks/pre-push`): full corpus group; advisory at `warn`,
  **blocks only at `error`** severity when a gap is at/above the block-score.

Two config files govern it:

- **`.claude/crosslink-severity`** — `off | warn | error` (default `warn`),
  mirroring `.claude/bare-refs-severity`. `off` silences the check everywhere;
  `error` lets the pre-push gate block on an obvious missing link.
- **`.claude/crosslink-scope`** — the paths (files/dirs) forming **one corpus
  group**. Cross-linking is **opt-in per corpus**: to extend coverage to
  another survey, add its directory (and any related out-of-manifest docs)
  here. Keeping unrelated surveys out avoids cross-survey false-positive
  candidates.

## Tier 2 — on-demand judgment + apply (the only agent spend)

The `/cross-link` skill (`.claude/skills/cross-link/SKILL.md`) runs the full
pipeline — `extract` → `candidates` → batched judge agent → `apply` → verify —
scoped to the changed documents. This is the supported way to clear the gaps
the gates report. It is always author-initiated and batched. The judge agent
returns only `{id -> keep, anchor_phrase, confidence}`; link **syntax and
dedup are owned by the script**, never the agent.

## Authoring sign-off step (mandatory)

When a task **creates or substantially expands** a survey document or section,
before sign-off either:

1. run `/cross-link` (or `crosslink.py check`) over the new content and clear
   the reported high-value gaps, **or**
2. if cross-linking is out of scope for the task, file a `todos/` entry naming
   the gaps (per the Todo Capture convention in `CLAUDE.md`).

A "documented but not linked" survey is not signed off. This applies to the
authoring skills: `deep-research-survey` and `survey-explainer-fold`.

## Directional syntax convention (keyed on the TARGET's corpus)

This is encoded in `crosslink.py::make_link` — the script writes the form, the
author/agent never hand-writes it:

- **Target is a survey section** (a heading that lives in the survey's
  `order.json`) → `secxref` marker + section glyph:
  `<!-- secxref:A.13 -->[§A.13](appendix-a-qkv-first-principles.md#sec-A.13)`.
  The `secxref` resolver uses the survey's `order.json` to find the owning file.
- **Target is an out-of-manifest doc** (a standalone explainer / wiki page that
  is *not* in `order.json`) → plain relative link, descriptive text, **no**
  section glyph: `[softmax derivation](path/to/explainer.md#sec-4)`. Such docs
  are not in `order.json`, so a `secxref` would orphan; a plain link is correct.
  (This corpus currently holds only in-manifest survey files, but the convention
  is part of the tool's contract.)

Both conventions use the canonical `sec-<num>` anchor scheme. The relative path
is computed from the source file's directory.

## Dedup and idempotency

- **Candidate generation** drops a target the source *section* already links
  (the on-demand pass over-proposes deliberately; the agent + apply filter).
- **`check`** and **`apply`** dedup file-scoped: a target already linked
  anywhere in the source *file* is skipped. So `apply` is idempotent (a target
  is linked at most once per file — a link-spam guard) and a re-run over an
  already-linked corpus is a near-no-op. This is why `check`'s gap report
  matches what `apply` would actually add.

## Rollout (mirrors bare-refs)

`off` (land, gates are no-ops) → `warn` (observe gap reports, tune
`--min-score` / `--block-score`) → `error` (block a push only on an obvious
missing link). Currently `warn`, scoped to the `surveys/llms-for-coding` corpus
group.

## Cross-references

- `viewer/tools/crosslink.py`, `viewer/tools/crosslink.README.md` — the tool
  and its four-stage driver.
- The cross-link subsystem design (detection in the gates, on-demand insertion
  via `/cross-link`).
- `CLAUDE.md` Todo Capture — the `todos/` fallback for out-of-scope gaps.
- `.claude/rules/math-authoring.md` — the `secref`/`secxref` marker system the
  survey-target form participates in.
