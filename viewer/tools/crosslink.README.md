# `crosslink.py` — cheap, pre-filtered cross-link proposer

A token-frugal replacement for the all-agent cross-link sweep. A prior
all-agent sweep spent **~11.5M tokens / 217 sonnet agents** to land 131 links
(~87k tokens/link) because it handed *discovery*, *judgment*, and *application*
all to agents — and the apply agents silently failed to persist their edits.
Three of those four jobs are deterministic. This tool does them in code and
reserves the model for the irreducible semantic judgment, on a **pre-filtered
shortlist**, **in batches**.

Estimated cost for the same corpus: **~4–6 sonnet agents** over ~60 candidates
instead of 217 — a **20–40× reduction** — with no apply-persistence failure to
recover from (application is deterministic and filesystem-verified).

## The four stages

| # | Stage | Who | Cost |
|---|---|---|---|
| 1 | `extract` | code | ~0 |
| 2 | `candidates` (TF-IDF cosine pre-filter) | code | ~0 |
| 3 | **judge** (batched) | **agent** | the only token spend |
| 4 | `apply` (idempotent, filesystem-verified) | code | ~0 |

Link **syntax** and **dedup** live in stage 2/4, never in the agent. The agent
returns only `{id → keep, anchor_phrase, confidence}`.

## Run it

```bash
# 1. EXTRACT — parse every section (heading, body, existing links).
#    Pass dirs (expanded to *.md, minus index/references) and/or files.
python viewer/tools/crosslink.py extract surveys/llms-for-coding \
    --out temp/xlink-index.json

# 2. CANDIDATES — TF-IDF cosine pre-filter -> ranked shortlist, grouped into
#    agent batches. Symmetric pairs collapse to the assertion->derivation
#    direction by default. Link syntax + dedup key are precomputed here.
python viewer/tools/crosslink.py candidates \
    --index temp/xlink-index.json --out temp/xlink-cands.json \
    --per-source 3 --max-candidates 60 --min-score 0.10 --batch 15

# 3. JUDGE — run the batched agent (see below) over temp/xlink-cands.json,
#    writing temp/xlink-dec.json.

# 4. APPLY — idempotent, normalize-with-map insertion; --dry-run first.
python viewer/tools/crosslink.py apply \
    --candidates temp/xlink-cands.json --decisions temp/xlink-dec.json --dry-run
python viewer/tools/crosslink.py apply \
    --candidates temp/xlink-cands.json --decisions temp/xlink-dec.json

# 5. VERIFY (always — persistence is not the agent's word):
python viewer/tools/renumber-sections.py surveys/llms-for-coding/<edited>.md
python viewer/tools/validate-refs.py surveys/llms-for-coding   # 0 errors expected
# lint-math runs automatically on each Edit via the PostToolUse hook.
```

## Stage 3 — the batched judge (the only token spend)

Each batch is ≤ `--batch` candidates. One agent call per batch. The agent sees
only short snippets and returns a few tokens per candidate. Suggested prompt:

> You are judging proposed cross-links for an LLM/AI deep-research survey. For
> each candidate you get a SOURCE section snippet and a TARGET section snippet.
> Keep a link only if the TARGET genuinely **derives, grounds, proves, or
> materially extends** the specific claim in the SOURCE (assertion → derivation),
> and the link is non-redundant and high-value. Reject vague topical overlap.
> For each kept candidate, return `anchor_phrase`: a **verbatim** substring
> (≤ 12 words) copied from the SOURCE snippet, ending at the exact assertion the
> link should attach to. Do NOT choose link syntax or paths — that is handled
> downstream. Return one object per candidate id.

Structured-output schema (force it):

```json
{
  "type": "object",
  "properties": {
    "decisions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id":            {"type": "string"},
          "keep":          {"type": "boolean"},
          "confidence":    {"type": "number"},
          "anchor_phrase": {"type": "string"}
        },
        "required": ["id", "keep", "anchor_phrase"]
      }
    }
  },
  "required": ["decisions"]
}
```

Workflow form (one agent per batch, runs concurrently):

```js
export const meta = {
  name: 'crosslink-judge',
  description: 'Judge pre-filtered cross-link candidates in batches',
  phases: [{ title: 'Judge' }],
}
const data = JSON.parse(/* read temp/xlink-cands.json via args */ args.cands)
const byId = Object.fromEntries(data.candidates.map(c => [c.id, c]))
const decisions = (await parallel(data.batches.map((ids, k) => () =>
  agent(
    `Judge these ${ids.length} cross-link candidates. Keep only genuine ` +
    `assertion->derivation links; return a verbatim anchor_phrase (<=12 words) ` +
    `from each kept SOURCE snippet.\n\n` +
    JSON.stringify(ids.map(id => byId[id]), null, 2),
    { label: `judge:batch-${k}`, phase: 'Judge', schema: JUDGE_SCHEMA }
  ).then(r => r.decisions)
))).filter(Boolean).flat()
return { decisions }
```

Concatenate the returned `decisions` into `temp/xlink-dec.json` and run stage 4.

## Design choices (why it is cheap *and* safe)

- **TF-IDF cosine** over render-normalized section text (math/code/comments/tags
  stripped, emphasis removed, unigrams + adjacent bigrams). Rare technical terms
  (`softmax`, `rotary`, `kv_cache`, `chinchilla`) dominate the IDF, so the
  cosine ranks genuine topical kinship, not boilerplate. No external deps.
- **Cross-file only.** Same-file links are the `secref` system's job; this tool
  finds the cross-corpus and cross-appendix links.
- **Symmetric-pair dedup** (default on) collapses each unordered pair to its
  assertion→derivation direction via a tier (`survey body 1 < appendix 2 <
  out-of-manifest doc 3`). `--keep-symmetric` keeps both directions.
- **Syntax is keyed on the TARGET's corpus** — matching the convention of the
  landed cross-links: target in a survey section (in `order.json`) → `secxref`
  + `§` glyph; target in an out-of-manifest doc (a standalone explainer/wiki not
  in `order.json`) → plain relative link with descriptive text, no `§`. The
  script writes the form; the agent never does.
- **Two-level dedup.** Candidate generation drops targets the *source section*
  already links. `apply` additionally skips any link whose `relpath#anchor`
  already appears anywhere in the source *file* — so re-runs are idempotent and
  a target is linked at most once per file (link-spam guard). This is why a
  re-run over an already-swept corpus is a near-no-op.
- **`apply` is filesystem-verified by construction** — it edits bytes and you
  diff the tree; there is no agent self-report to over-trust (the failure mode
  in the prior all-agent sweep). `--dry-run` plans without writing.
- **normalize-with-map matcher** locates `anchor_phrase` even when the file has
  emphasis/markers/anchors the agent's quote dropped (strip comments/`<a>`/`**`/
  `==`/`*`/`` ` `` and collapse whitespace on both sides, map the match back to
  the original offset), with a final-sentence prefix fallback.

## Tuning

| Flag | Default | Effect |
|---|---|---|
| `--min-score` | 0.10 | cosine floor; raise to cut weak candidates (fewer agent tokens) |
| `--per-source` | 3 | max targets proposed per source section |
| `--max-candidates` | 60 | global cap after ranking (caps agent batches) |
| `--batch` | 15 | candidates per agent call |
| `--keep-symmetric` | off | keep both directions of a pair |

Raising `--min-score` to ~0.15 and lowering `--max-candidates` shrinks the agent
bill further at the cost of recall; the deterministic stages are free, so iterate
on the shortlist before spending any agent tokens.
