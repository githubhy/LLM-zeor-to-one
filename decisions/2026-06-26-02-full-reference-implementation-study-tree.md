---
id: 2026-06-26-02
title: Port the full reference-implementation-study tree (16 files), not just the 4 in-range deltas
status: accepted
date: 2026-06-26
plan: .claude/commands/sync-upstream.md
---

## Context

The full upstream sync (branch `sync/upstream-2026-06-26`, batch 4) ports the
net-new skills/rules/commands from `../data-channel-receiver`. The `--dry-run`
classification (Conversation 2) was built from `git diff --name-status 7c3a3bf..HEAD`,
which for `.claude/skills/reference-implementation-study/` reports only **4**
changed files: `SKILL.md` (M), `phases/phase-6-report.md` (M), `signoff.py` (A),
`validate_gate.py` (M).

Reality on inspection: the skill is **16 files** in upstream HEAD (README, SKILL,
6 `addenda/`, 6 `phases/`, `signoff.py`, `validate_gate.py`). The other 12 predate
the high-water mark (created at/ before the 2026-06-13 bootstrap) and so do not
appear in the `BASE..HEAD` window. Critically, the skill is **entirely absent
locally** — the 2026-06-13 bootstrap never ported it. `SKILL.md` references
`phases/phase-1..5`, `addenda/`, and `README` by path, so porting only the 4
in-range files would land a **non-functional skill** (a SKILL.md whose lazy-loaded
phases and addenda do not exist).

## Decision

Port the **full 16-file `reference-implementation-study` tree**, re-adapted
telecom→LLM, rather than the 4-file `BASE..HEAD` slice. The user's explicit scope
choice ("everything incl. new skills", which named this skill) is honoured by
delivering a *working* skill; the 16-vs-4 gap is a mechanical artifact of the
diff window, not a scope expansion.

## Alternatives considered

- **Port only the 4 in-range files.** Rejected: yields a broken skill (dangling
  internal `phases/`/`addenda/`/`README` references); violates the spirit of
  "add the skill."
- **Defer the skill entirely (todo) as pre-mark content.** Rejected: the user
  named it explicitly, and the sibling sim/eval cluster being ported this same
  batch (`sim-audit`, `study-signoff`, `sim-report-completeness`) cross-references
  it — deferring would fragment a coherent cluster and create dangles.
- **Ask the user again.** Rejected per the decisive-recommendation preference:
  the skill was already in the agreed scope; the file count is an implementation
  detail, not a new fork.

## Consequences

- Advances local coverage of `reference-implementation-study` beyond the strict
  high-water mark for this one skill (the 12 pre-mark files). The sync mark still
  advances to upstream HEAD `5d485d7` (final batch), which correctly subsumes
  these files going forward.
- The skill is the heaviest sim/DSP→LLM conceptual remap in the sync (signal
  model → task/data distribution; BLER-vs-SNR waterfall → quality-vs-budget curve;
  finite-precision → quantization). Low-confidence mappings flagged by the adapter
  were reviewed; one spec-flavored grade token (`SPEC-SILENT`) is retained verbatim
  because `viewer/tools/check-report-completeness.py` matches it literally.
- Graceful degradation: the skill's `proposed`/`flags` enhancement modes reference
  `bench/reference-implementation-study/items.json`, which is **not** ported (bench
  content is excluded by the sync). The default `original` mode needs no registry;
  the absent registry is noted inline, not fabricated.
- No follow-up todo: the full tree is functional as landed.

## Refs

- `.claude/commands/sync-upstream.md` (the sync workflow); decision `2026-06-26-01`.
- Branch `sync/upstream-2026-06-26`, batch 4.
- Conversation log: `prompts/2026-06-26-adapt-sync-upstream-skill.md` (Conversation 6).
