---
name: cross-link
description: Add high-value cross-links across the survey corpus cheaply — a deterministic TF-IDF pre-filter proposes candidates, a small batched agent judges only keep/where, and a deterministic idempotent applier inserts them with the correct directional syntax. Use to clear the gaps the crosslink gate reports, or as the sign-off step after authoring/expanding a survey. Replaces the all-agent sweep (which cost ~11.5M tokens for 131 links) at ~20-40x lower cost. File: .claude/skills/cross-link/SKILL.md
---

# Cross-Link (on-demand insertion pass)

## Overview

This is **Tier 2** of the cross-linking rule (`.claude/rules/cross-linking.md`):
the on-demand, batched judgment + apply pass — the **only** place agents spend
tokens on cross-linking. Tier 1 (the `crosslink.py check` gap detector in the
gates) only *reports* gaps; this skill *clears* them.

The split is the whole point: link **discovery, syntax, dedup, and application**
are deterministic (the script); only the **keep/where** judgment is an agent,
and it runs on a pre-filtered shortlist in batches. Never hand the whole job to
agents — that is the anti-pattern a prior all-agent sweep demonstrated
(~11.5M tokens / 217 agents, with a silent apply-persistence failure).

## When to use

- The crosslink gate (Stop-hook or pre-push) reported unlinked candidates.
- You created or substantially expanded a survey and are at sign-off.
- The user asks to cross-link a doc or the corpus.

## Inputs

- **Scope**: the corpus group in `.claude/crosslink-scope` (default). For an
  authoring sign-off, you may also pass `--changed` to focus on what you touched.

## Workflow

The tool is `viewer/tools/crosslink.py`; its full driver (flags, the judge
prompt, the structured schema) is `viewer/tools/crosslink.README.md`. Read that
README, then run the four stages. Use `temp/` for the intermediate JSON.

### Stage 1 — extract (code)

Parse the scope into a section/anchor/existing-link index:

```bash
SCOPE=$(grep -vE '^[[:space:]]*#|^[[:space:]]*$' .claude/crosslink-scope | tr '\n' ' ')
python viewer/tools/crosslink.py extract $SCOPE --out temp/xlink-index.json
```

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
agent bill before spending any tokens; the deterministic stages are free.

### Stage 3 — judge (agent, batched — the only token spend)

Run ONE agent per batch (use the Workflow tool — concurrent, structured output).
The agent sees only short snippets and returns only
`{id -> keep, anchor_phrase, confidence}`. It does **not** choose link syntax or
paths. Use the prompt and `JUDGE_SCHEMA` documented in `crosslink.README.md`:

- `keep`: true only if the TARGET genuinely derives / grounds / proves /
  materially extends the SOURCE claim (assertion → derivation), non-redundant.
- `anchor_phrase`: a **verbatim** substring (≤ 12 words) from the SOURCE snippet,
  ending where the link should attach.

Concatenate the per-batch `decisions` into `temp/xlink-dec.json` as
`{"decisions":[ ... ]}`.

For a tiny shortlist (≤ ~10 candidates) you may judge inline without a workflow.

### Stage 4 — apply (code, idempotent, filesystem-verified)

Dry-run first, then apply:

```bash
python viewer/tools/crosslink.py apply --candidates temp/xlink-cands.json \
    --decisions temp/xlink-dec.json --dry-run
python viewer/tools/crosslink.py apply --candidates temp/xlink-cands.json \
    --decisions temp/xlink-dec.json
```

`apply` skips any link already present in the source file (idempotent) and uses
the normalize-with-map matcher to locate `anchor_phrase` through emphasis /
markers. **Verify persistence against the filesystem** (`git diff`) — never the
agent's report (the prior all-agent sweep's failure mode).

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
