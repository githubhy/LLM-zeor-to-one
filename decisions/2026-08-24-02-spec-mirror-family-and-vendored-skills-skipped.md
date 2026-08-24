---
id: 2026-08-24-02
title: The spec-mirror gate family and the three vendored third-party skills are SKIP-domain, not deferred work
status: accepted
date: 2026-08-24
plan: .claude/commands/sync-upstream.md (inbound, step 1 classification)
---

## Context

Two clusters in the `cedfccb2..24cfca29` delta look like harness additions and are not.

**The spec-mirror family** (~3,240 lines): `check-spec-constants.py`,
`check-spec-mirrors.py`, and five test modules covering MathType/OLE equation extraction,
WMF metafile parsing, and CP936 mojibake adjudication over a standards-document mirror.
Every one resolves against `docs/specs/3gpp/`, `tools/fetch_3gpp_specs.py`, a `specparse`
package borrowed from a sibling repo, and a channel-model simulation module. None of those
four exists here, and the sync command already declares top-level `tools/` out of scope.
Their three new `requirements.txt` deps (`openpyxl`, `olefile`, `python-docx`) exist to
read a calibration spreadsheet and Word-format standards documents.

**Three vendored skills**: `grilling`, `grill-with-docs`, `domain-modeling`, plus a
`GRILL-PROVENANCE.md` note. Upstream installed them from a third-party repository, and its
own note says they "will be DELETED at the next config sync" because a weekly job wipes and
re-copies `.claude/skills/`. This repo already has all three — installed properly as the
`mattpocock-skills` plugin, with its configuration in `docs/agents/`, which upstream has no
counterpart for.

## Decision

Classify both clusters SKIP-domain and do not port them. Likewise skip
`check-idealized-binding.py` (defaults to upstream's conformance register, dense with
receiver/TRP/SNR vocabulary), the `.gitignore` additions (all upstream artifact paths), the
`.claude/crosslink-scope` additions (upstream survey groups), and the three
`requirements.txt` deps above.

## Alternatives considered

- **Port the spec-mirror gates as scaffolding for a future `docs/specs/` mirror here.**
  Rejected: they would be dead code whose gates cannot run, and a gate that cannot run is
  indistinguishable from one that runs and passes — the exact confusion `Scope`/REFUSE
  exists to prevent. The citation-integrity concern they serve is real here, but its LLM
  form is a *paper* mirror under `download/`, already covered by
  `check-citation-sources.py --index`. A different mechanism, not a port.
- **Port the vendored skills anyway, for parity with upstream.** Rejected: it would give
  this repo two copies of each skill — one from the plugin, one vendored — with no rule
  saying which wins, and would import a note announcing its own deletion. Parity with
  upstream is not the goal; the goal is the same capability, which this repo already has by
  a better route.
- **Port `check-idealized-binding.py` re-domained.** Rejected for the same reason as the
  campaign instance drivers (`decisions/2026-08-24-01`): the register it grades does not
  exist here, so re-domaining means inventing one.

## Consequences

- ~3,900 lines of the 15,734-line delta are deliberately not here, and this record is what
  distinguishes that from an oversight — the distinction the next sync's `--back`
  classification depends on (`SKIP-domain`, not `SYNC-BACK`, not "upstream-newer").
- If a formal-spec mirror ever lands here (`docs/specs/`, e.g. the Model Context Protocol
  spec the citation-integrity rule's `spec:` tag already anticipates), the UTF-8/greppability
  gate is the one piece worth revisiting — a non-UTF-8 mirror makes `grep` return empty with
  exit 1, indistinguishable from a genuine no-match, which silently pushes an author back to
  citing from memory. Tracked in `todos/2026-08-24-upstream-sync-followups.md`.
- `viewer/tools/tests/test_campaign_gates_subprocess.py` shipped with a `SpecConstantsGate`
  class testing the unported gate. It was removed rather than left to skip forever, with a
  comment naming what it was and where to recover it.

## Refs

- `.claude/commands/sync-upstream.md` § "Exclude as content", § "out of scope"
- `.claude/skills/` (plugin-provided `grilling` / `grill-with-docs` / `domain-modeling`)
- `docs/agents/domain.md`, `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`
- `prompts/2026-08-24-upstream-sync.md`
