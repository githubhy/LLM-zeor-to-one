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
- **`.claude/crosslink-scope`** — **named corpus groups**. A `[group-name]` header
  opens a group; the following path lines (files/dirs) belong to it. A file with
  no header parses as a single `default` group (the legacy flat form). Each group
  is an **independent TF-IDF corpus** — a candidate never spans two groups, which
  is what keeps unrelated surveys from proposing links at each other.

  Consumers must **never hand-expand this file with `grep`** — the `[group]`
  headers would be passed as bogus paths. Use `--scope-file` (gates) or ask the
  tool:

  ```bash
  python viewer/tools/crosslink.py groups                      # list groups
  python viewer/tools/crosslink.py groups --group llm-methods  # that group's paths
  ```

  Membership is derived, not guessed: `viewer/tools/crosslink-cluster.py propose`
  clusters the corpus (section-level TF-IDF + complete linkage; out-of-manifest
  docs assigned by nearest-survey), and `… validate` prints per-group cohesion
  plus the inter-group edges a partition deliberately forgoes. Re-run both after
  adding a survey.

## Tier 2 — on-demand judgment + human insertion

The `/cross-link` skill (`.claude/skills/cross-link/SKILL.md`) runs the full
pipeline — `extract` → `candidates` → **decide** → `apply` → verify — scoped to
the changed documents. This is the supported way to clear the gaps the gates
report. It is always author-initiated.

**Detect, do not auto-apply.** At the deployed operating point the corpus yields a
shortlist small enough that the **decide** step is a human reading a
`crosslink.py review` sheet and checking `link` / `merge` / `reject` per pair.
`crosslink.py apply` **refuses an unattributed decision file** — a link it writes
becomes ground truth for the recall measurement, so a person takes responsibility,
via the review sheet or `--reviewed-by`. The batched **judge agent** is an escape
hatch for a shortlist too large to read (> ~200), not the default. Whichever
decides, link **syntax and dedup are owned by the script**, never the agent; the
judge returns only `{id -> keep, anchor_phrase, confidence}`.

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
- **Target is a section in a DIFFERENT survey** (not in *this* survey's
  `order.json`) → plain relative link, descriptive text, **no** `§` glyph:
  `[interpretability survey, circuits section](../mechanistic-interpretability/circuits-across-models.md#sec-9.2)`.
  A `secxref` cannot resolve it (it keys on *this* survey's `order.json`), and a
  bare `§X.Y` is worse — `renumber-sections --init` would auto-link it to a
  same-numbered section of the *current* survey (the wrong target). The `§` glyph
  in visible link text also trips the bare-ref gate. Treat exactly like an
  out-of-manifest target: plain link, no glyph.
  `[opt:SX-DEGLYPH · default ON · toggle .claude/skill-options.json]`

Both conventions use the canonical `sec-<num>` anchor scheme. The relative path
is computed from the source file's directory.

## `secxref` is legal ONLY inside a multi-file survey directory

A `secxref` asks: *resolve this section number against the other files of **this
survey***. The resolver (`renumber-sections.py::build_survey_heading_index`) walks
the **source document's own directory**, keyed on its `order.json`.

So a `secxref` is meaningful only where an `order.json` exists. It is **illegal**:

- in `wikis/` — the neighbours are unrelated documents that merely share a
  numbering scheme;
- in a flat directory of single-file surveys — likewise.

`build_survey_heading_index` returns an **empty index** for a directory with no
`order.json`, so such a marker is reported as an orphan and never resolved.
Orphaning a cross-corpus reference is correct; resolving it against a bag of
unrelated files is strictly worse than doing nothing. Upstream's older code
globbed the directory anyway, and a flat-anchor migration then created a
`sec-5.4.1` anchor inside an unrelated wiki and re-pointed three wikis'
*survey-targeted* `secxref`s at it — links that render, resolve, and cite a
document their own prose contradicts.

**Corollary — the `§` glyph is not a style choice.** A `§X.Y` in visible link text
*requires* a `secref`/`secxref` marker (`validate-refs` check #12), and a marker
outside a survey directory is illegal. The two constraints leave exactly one form
for a cross-corpus link: **plain relative link, descriptive text, no glyph, no
marker**. `crosslink.py::make_link` emits it; never hand-write one.

`.githooks/pre-push` runs `renumber-sections --check surveys/ wikis/`, so a
reintroduced marker blocks a push.

## Dedup and idempotency

- **Candidate generation** drops a target the source *section* already links
  (the on-demand pass over-proposes deliberately; the agent + apply filter).
- **`check`** and **`apply`** dedup file-scoped: a target already linked
  anywhere in the source *file* is skipped. So `apply` is idempotent (a target
  is linked at most once per file — a link-spam guard) and a re-run over an
  already-linked corpus is a near-no-op. This is why `check`'s gap report
  matches what `apply` would actually add.

Dedup is **symmetric**: once `a -> b` is linked, `b -> a` is not a gap. (One-way
dedup made every applied link re-appear backwards at an identical cosine.)

## Coverage is not silent

`crosslink.py` reports every scoped file it cannot see:

- `WARNING: 0 sections from <path>` — the file matched no heading, so it is absent
  from the index and can neither propose nor receive a link. **A "no gaps" result
  is meaningless for such a file.** `extract --strict` turns this into exit 1.
- `note: <path> … usable as a link source, never as a link target` — it has
  sections but no `sec-` anchor.
- `group 'G': showing top N of M gaps` — the `--max-candidates` cap never reads as
  "that is all there is".

`check` refuses (exit 2) rather than printing "no cross-link gaps" when it is given
no corpus, or when the corpus parses to zero sections. A green gate must mean
"looked and found nothing", never "did not look".

`crosslink.py coverage` is the companion: it reports every survey/wiki that is
neither in a group (`.claude/crosslink-scope`) nor declared in
`.claude/crosslink-keepout`, so a newly-added document is never silently unscanned.
Severity: `.claude/crosslink-coverage-severity`.

## Reachability is a different question from coverage — and from gaps

`crosslink.py reach` asks the one question none of the other gates ask: **can a
reader get here at all?**

- `check` asks *"is this pair linked?"* — and scores **pairs**, with **symmetric
  dedup**: once `a -> b` exists, `b -> a` is not a gap. So a one-way-linked pair is
  **closed** to the detector and a **dead end** to the reader. Making that dedup
  directional would re-introduce the reverse-duplicate spam it was built to fix —
  the fix is a *different check*, not a tuning change.
- `coverage` asks *"is this doc scanned?"* — group membership, not linkage.
- `reach` asks *"can a reader arrive?"* — transitive reachability from `surveys/`
  through **reader-facing** links. Mentions inside `<!-- HTML comments -->` do
  **not** count, because they are invisible in the rendered page.

**The cause of an unreachable doc is structural, not sloppiness.** The
`reference-implementation-study` G0 gate requires a derivation ledger to cite the
**survey** (provenance). Nothing requires the survey to cite the **ledger**. The
obligation has **no owner** in the survey→wiki direction, so it fails identically
for every such wiki. The prevention is `[opt:RIS-BACKLINK]` (add the back-link in
the same turn); this gate is the detection.

Config: `.claude/reachability-severity` (`off | warn | error`, currently **`warn`**
— there is a measured backlog). Deliberately-standalone process/harness wikis are
declared in `.claude/reachability-keepout` — **do not park a derivation wiki there
to silence the gate**: a G0 ledger has a survey host *by definition*, so an
unreachable one is a defect in the survey, not an exemption.

## A rejected pair is not a gap

The pre-filter over-proposes on purpose so the judge can be strict — most
candidates are rejected. Every rejection is persisted to
**`.claude/crosslink-rejected.json`** (keyed on `pair_key`, direction-independent,
committed and reviewable) by

```bash
python viewer/tools/crosslink.py reject --candidates <cands> --decisions <dec> --note "..."
```

`check` skips ledger entries and reports how many it suppressed. Recording
rejections is a **mandatory** step of `/cross-link`: skip it and the gate
re-reports the same dismissed pairs forever, which is what keeps `error` severity
unreachable. The ledger keys on the pair, not on section content — after a large
rewrite, re-examine with `check --ignore-rejections`.

## Rollout (mirrors bare-refs)

`off` (land, gates are no-ops) → `warn` (observe gap reports, tune
`--min-score` / `--block-score`) → `error` (block a push only on an obvious
missing link). Currently `warn`, over the `llm-methods` corpus group; promote to
`error` once the residual gap count reaches zero and stays there.

## Cross-references

- `viewer/tools/crosslink.py`, `viewer/tools/crosslink.README.md` — the tool
  and its four-stage driver.
- The cross-link subsystem design (detection in the gates, on-demand insertion
  via `/cross-link`).
- `CLAUDE.md` Todo Capture — the `todos/` fallback for out-of-scope gaps.
- `.claude/rules/math-authoring.md` — the `secref`/`secxref` marker system the
  survey-target form participates in.
