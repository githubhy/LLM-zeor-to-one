---
name: cross-link
description: Add high-value cross-links across the survey corpus cheaply — a deterministic TF-IDF pre-filter proposes candidates, a small batched agent judges only keep/where, and a deterministic idempotent applier inserts them with the correct directional syntax. Use to clear the gaps the crosslink gate reports, or as the sign-off step after authoring/expanding a survey. Replaces the all-agent sweep (which cost ~11.5M tokens for 131 links) at ~20-40x lower cost. File: .claude/skills/cross-link/SKILL.md
---

# Cross-Link (on-demand insertion pass)

## Overview

This is **Tier 2** of the cross-linking rule (`.claude/rules/cross-linking.md`):
the on-demand judgment + apply pass. Tier 1 (the `crosslink.py check` gap detector
in the gates) only *reports* gaps; this skill *clears* them.

The split is the whole point: link **discovery, syntax, dedup, and application**
are deterministic (the script); only the **keep/where** judgment needs a mind.
At the deployed operating point (`per_source = 1`, `min_score = 0.20`) that
judgment is a **human reading the shortlist** — the default. The agent judge is
an escape hatch for a shortlist too large to read (> ~200), not the norm.

Two anti-patterns this avoids. Handing the *whole* job to agents is the pattern a
prior all-agent sweep demonstrated (~11.5M tokens / 217 agents, with a silent
apply-persistence failure). And letting the tool *auto-apply* is a closed loop:
at the deployed threshold the great majority of what the pre-filter "recalled"
was link it had written itself, which then corrupted the recall measurement.
`apply` therefore refuses an unattributed decision file — a human takes
responsibility, by review sheet or by naming themselves.

## When to use

- The crosslink gate (Stop-hook or pre-push) reported unlinked candidates.
- You created or substantially expanded a survey and are at sign-off.
- The user asks to cross-link a doc or the corpus.

## Inputs

- **Scope**: ONE named corpus group from `.claude/crosslink-scope`. The file
  defines several `[group]` blocks; each is an independent TF-IDF corpus, so a
  cross-link never spans two groups. Always pick the group that owns the doc you
  are cross-linking — `python viewer/tools/crosslink.py groups` lists them. For an
  authoring sign-off, you may also pass `--changed` to focus on what you touched.

## Workflow

The tool is `viewer/tools/crosslink.py`; its full driver (flags, the judge
prompt, the structured schema) is `viewer/tools/crosslink.README.md`. Read that
README, then run the four stages. Use `temp/` for the intermediate JSON.

### Stage 1 — extract (code)

Parse ONE group into a section/anchor/existing-link index. Never hand-expand the
scope file with `grep` — it now carries `[group]` headers, which would be passed
as bogus paths. Ask the tool for the group's paths:

```bash
python viewer/tools/crosslink.py groups                       # list group names
GROUP=fec-decoding                                            # pick the owning group
SCOPE=$(python viewer/tools/crosslink.py groups --group "$GROUP")
python viewer/tools/crosslink.py extract $SCOPE --out temp/xlink-index.json
```

`extract` warns on any scoped file that yields 0 sections (invisible to the
index — it can neither propose nor receive a link). Investigate such a warning
before trusting a "no gaps" result; `--strict` turns it into a failure.

### Stage 2 — candidates (code)

TF-IDF cosine pre-filter → ranked shortlist, grouped into agent batches, with
link syntax + dedup key precomputed:

```bash
python viewer/tools/crosslink.py candidates --index temp/xlink-index.json \
    --out temp/xlink-cands.json --per-source 3 --max-candidates 60 \
    --min-score 0.12 --batch 15
```

Inspect `temp/xlink-cands.json` — `n_candidates`, `n_batches`, and the
`candidates[]` (each has `source`/`target` snippets, `score`, `link_markdown`,
`dedup_target`). Tune `--min-score` UP and `--max-candidates` DOWN to shrink the
agent bill before spending any tokens; the deterministic stages are free. At the
defaults the corpus yields ~81 pairs, so **check whether the judge is worth running at
all** — a human reads 81 pairs in an hour, and the judge costs ~0.45M tokens, rejects
58%, and is 12.5% irreproducible on re-ask.

### Stage 3 — decide (HUMAN by default; agent judge only for a large shortlist)

**Detect, do not auto-apply** (`plans/2026-07-10-crosslink-detector-only.md`,
`docs/harness-roadmap.md` § 1.5). At the deployed operating point
(`per_source = 1`, `min_score = 0.20`) the whole corpus yields **~81 candidate
pairs**, and a per-group shortlist is a handful. A person reads that in minutes;
the agent judge costs ~0.45M tokens, rejects 58%, and is 12.5% irreproducible on
re-ask. **The judge is the large-shortlist escape hatch, not the default.**

**Default path — human review sheet.** Emit the shortlist as a checkable sheet:

```bash
python viewer/tools/crosslink.py review --candidates temp/xlink-cands.json \
    --out temp/xlink-review.md
```

Each block has three boxes — `[ ] link  [ ] merge  [ ] reject`. Check exactly one:

- **link** — a genuine cross-reference; `apply` inserts it at the (editable) Anchor.
- **merge** — the two sections say the same thing. A structural twin is a
  *duplication to fix* (survey § 9.4), not a link; it is recorded to the merge
  ledger and nothing is written. This outcome does not exist on the judge path,
  which can only record it as a lossy `reject`.
- **reject** — neither; recorded to the rejection ledger so the gate stops
  reporting it.

**Escape hatch — the agent judge.** ONLY when `n_candidates` in the candidates
JSON is large enough that a human will not read it (rule of thumb: **> 200**).
Either raise `--min-score` until the shortlist is human-sized, or run one agent
per batch (Workflow tool, structured output) with the prompt + `JUDGE_SCHEMA` in
`crosslink.README.md`. The agent returns only `{id -> keep, anchor_phrase,
confidence}` and never chooses link syntax. Concatenate the per-batch decisions
into `temp/xlink-dec.json`. A judge run is a deliberate choice you record — note
in the sign-off that you judged rather than reviewed, and why.

### Stage 4 — apply (code, human-attributed, filesystem-verified)

`apply` **refuses an unattributed decision file** — a link it writes becomes
ground truth for the recall measurement (`upstream bug 2026-07-10-19`), so a human must
take responsibility. From the review sheet (the normal path):

```bash
python viewer/tools/crosslink.py apply --candidates temp/xlink-cands.json \
    --from-review temp/xlink-review.md --reviewed-by "<you>" --dry-run
python viewer/tools/crosslink.py apply --candidates temp/xlink-cands.json \
    --from-review temp/xlink-review.md --reviewed-by "<you>"
```

`--from-review` routes all three outcomes: links applied, merges to the merge
ledger, rejects to the rejection ledger — Stage 4b happens automatically. If you
took the judge escape hatch, apply its decisions **only** by taking responsibility
for them explicitly:

```bash
python viewer/tools/crosslink.py apply --candidates temp/xlink-cands.json \
    --decisions temp/xlink-dec.json --reviewed-by "<you> (via judge on N candidates)"
```

`apply` skips any link already present in the source file (idempotent) and uses
the normalize-with-map matcher to locate `anchor_phrase` through emphasis /
markers. **Verify persistence against the filesystem** (`git diff`) — never the
agent's report (the prior all-agent sweep's failure mode).

### Stage 4b — rejections and merges (automatic from `--from-review`)

The review path records both ledgers for you. Only when applying a **judge**
decision file (the escape hatch) must you record rejections by hand, or `check`
re-reports them forever and `--severity=error` becomes unreachable:

```bash
python viewer/tools/crosslink.py reject --candidates temp/xlink-cands.json \
    --decisions temp/xlink-dec.json --note "judged YYYY-MM-DD (<group>)"
```

Both ledgers key on `pair_key` (idempotent, committed, reviewable). `check` skips
rejected pairs and prints how many it suppressed; `check --ignore-rejections`
re-examines them after a large rewrite. **Merge candidates
(`.claude/crosslink-merge-candidates.json`) are a documentation backlog, not link
work** — they are sections that should be consolidated, tracked separately.

### Stage 5 — verify the corpus is clean

```bash
python viewer/tools/renumber-sections.py surveys/llms-for-coding/<edited>.md
python viewer/tools/validate-refs.py surveys/llms-for-coding   # 0 errors expected
python viewer/tools/crosslink.py check $SCOPE --severity warn   # residual gaps
```

`lint-math` runs automatically on each Edit via the PostToolUse hook. Then clean
`temp/xlink-*.json`.

## Directional syntax (the script owns this — do not hand-write)

- Target in a **survey** section (in `order.json`) → `secxref` marker + section
  glyph:
  `<!-- secxref:A.13 -->[§A.13](appendix-a-qkv-first-principles.md#sec-A.13)`.
- Target in an **out-of-manifest doc** (a standalone explainer / wiki not in
  `order.json`) → plain relative link, descriptive text, no glyph:
  `[softmax derivation](path/to/explainer.md#sec-4)`.

## Anything left undone

If you judge some reported gaps out of scope for this pass, file a `todos/` entry
naming them (per the Todo Capture convention in `CLAUDE.md`) before sign-off.
