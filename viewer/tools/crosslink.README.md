# `crosslink.py` — cheap, pre-filtered cross-link proposer

A token-frugal replacement for the all-agent cross-link sweep. The
2026-06-23 corpus sweep spent **~11.5M tokens / 217 sonnet agents** to land
131 links (~87k tokens/link) because it handed *discovery*, *judgment*, and
*application* all to agents — and the apply agents silently failed to persist
(`field-notes/2026-06-23-workflow-apply-persistence.md`). Three of those four
jobs are deterministic. This tool does them in code and reserves the model for
the irreducible semantic judgment, on a **pre-filtered shortlist**, **in
batches**.

Estimated cost for the same corpus: **~4–6 sonnet agents** over ~60 candidates
instead of 217 — a **20–40× reduction** — with no apply-persistence failure to
recover from (application is deterministic and filesystem-verified).

## The four stages

| # | Stage | Who | Cost |
|---|---|---|---|
| 1 | `extract` | code | ~0 |
| 2 | `candidates` (TF-IDF cosine pre-filter) | code | ~0 |
| 3 | **decide** — `review` sheet, checked by a **human** (default); batched **agent** judge only for a shortlist > ~200 | human / agent | ~0 (human) or the only token spend (agent) |
| 4 | `apply` (human-attributed, idempotent, filesystem-verified) | code | ~0 |

**Detect, do not auto-apply** (`docs/harness-roadmap.md` § 1.5): at the deployed
operating point the corpus yields ~81 candidates, a human list. `apply` refuses an
unattributed decision file (upstream bug 2026-07-10-19). Link **syntax** and **dedup**
live in stage 2/4, never in whoever decides; the agent (when used) returns only
`{id → keep, anchor_phrase, confidence}`.

## Run it

```bash
# 0. GROUPS — `.claude/crosslink-scope` defines named corpus groups; each is an
#    independent TF-IDF corpus, so a candidate never spans two groups. Pick the
#    group that owns the doc you are cross-linking. NEVER hand-expand the scope
#    file with grep — the `[group]` headers would become bogus paths.
python viewer/tools/crosslink.py groups
#   fec-decoding     20 path(s)
#   receiver-chain   14 path(s)
#   sync-acquisition 12 path(s)
#   spatial-sensing   6 path(s)
#   noise-asic        1 path(s)

# 1. EXTRACT — parse every section (heading, body, existing links).
#    `--strict` fails if any scoped file yields 0 sections (invisible to the
#    index: it can neither propose nor receive a link). Without it you still get
#    a `WARNING: 0 sections from …` line — never ignore one, a "no gaps" result
#    is meaningless for that file (upstream bug 2026-07-09-13).
SCOPE=$(python viewer/tools/crosslink.py groups --group fec-decoding)
python viewer/tools/crosslink.py extract $SCOPE --out temp/xlink-index.json --strict

# 2. CANDIDATES — TF-IDF cosine pre-filter -> ranked shortlist, grouped into
#    agent batches. Symmetric pairs collapse to the assertion->derivation
#    direction by default. Link syntax + dedup key are precomputed here.
python viewer/tools/crosslink.py candidates \
    --index temp/xlink-index.json --out temp/xlink-cands.json \
    --per-source 1 --max-candidates 60 --min-score 0.20 --batch 15

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

## Stage 4b — record the rejections (mandatory)

On the human path, `apply --from-review` records rejects and merges for you. Only
on the agent-judge escape hatch must you persist rejections by hand, or `check`
re-reports the same dismissed pairs forever and `--severity=error` becomes
unreachable:

```bash
python viewer/tools/crosslink.py reject --candidates temp/xlink-cands.json \
    --decisions temp/xlink-dec.json --note "judged YYYY-MM-DD (<group>)"
```

Appends `pair_key`s to `.claude/crosslink-rejected.json` (idempotent, committed).
`check` skips them and always prints how many it suppressed. The ledger keys on
the pair, not on section content — after a large rewrite, re-examine with
`check --ignore-rejections`.

## Stage 3 (escape hatch) — the batched judge, for a shortlist too large to read

Each batch is ≤ `--batch` candidates. One agent call per batch. The agent sees
only the **blinded** `judge_view` (source + target snippets) and returns a few
tokens per candidate.

**The prompt and schema live in `crosslink.py`, not here** — restating them in
prose is what let the prompt drift to "an LLM inference survey" for a five-group
corpus, and let the workflow hand the judge the cosine score it exists to check
(upstream bugs 2026-07-10-16, -06). Get them from the tool:

```bash
python viewer/tools/crosslink.py judge-prompt            # the corpus-neutral prompt
python viewer/tools/crosslink.py judge-prompt --schema   # + JUDGE_SCHEMA
```

The prompt (for reference; the tool is the source of truth):

> You are judging proposed cross-links for a technical survey corpus. For each
> candidate you get a SOURCE section snippet and a TARGET section snippet.
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
// Index the BLINDED view, never the full candidate — the judge must not see `score`
// (upstream bug 2026-07-10-17). `judge_view` is emitted by `candidates` and asserted score-free.
const byId = Object.fromEntries(data.judge_view.map(c => [c.id, c]))
const decisions = (await parallel(data.batches.map((ids, k) => () =>
  agent(
    JUDGE_PROMPT + `\n\n` +                 // from `crosslink.py judge-prompt`
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
  (`boxplus`, `girth`, `density_evolution`, `kurkoski`) dominate the IDF, so the
  cosine ranks genuine topical kinship, not boilerplate. No external deps.
- **Cross-file only.** Same-file links are the `secref` system's job; this tool
  finds the cross-corpus and cross-appendix links.
- **Symmetric-pair dedup** (default on) collapses each unordered pair to its
  assertion→derivation direction via a tier (`survey body 1 < appendix 2 <
  wiki 3`). `--keep-symmetric` keeps both directions.
- **Syntax is keyed on the TARGET's corpus** — matching the existing 131 links:
  target in a survey → `secxref` + `§` glyph; target in a wiki → plain relative
  link with descriptive text, no `§`. The script writes the form; the agent
  never does.
- **Two-level dedup.** Candidate generation drops targets the *source section*
  already links. `apply` additionally skips any link whose `relpath#anchor`
  already appears anywhere in the source *file* — so re-runs are idempotent and
  a target is linked at most once per file (link-spam guard). This is why a
  re-run over an already-swept corpus is a near-no-op.
- **`apply` is filesystem-verified by construction** — it edits bytes and you
  diff the tree; there is no agent self-report to over-trust (the failure mode
  in the field note). `--dry-run` plans without writing.
- **normalize-with-map matcher** locates `anchor_phrase` even when the file has
  emphasis/markers/anchors the agent's quote dropped (strip comments/`<a>`/`**`/
  `==`/`*`/`` ` `` and collapse whitespace on both sides, map the match back to
  the original offset), with a final-sentence prefix fallback.

## Tuning

| Flag | Default | Effect |
|---|---|---|
| `--min-score` | **0.20** | cosine floor. Measured: tokens per accepted link are minimised here (12.2K, vs 19.9K at 0.12). upstream decision 2026-07-10-03 |
| `review --out` | — | write the human decision sheet (the default Stage 3) |
| `apply --reviewed-by` | — | who reviewed; required (or a `reviewed_by` field) — the provenance guard |
| `--per-source` | **1** | max targets per source section. Measured: top-1 dominates top-3 at every deployment budget — more recall, less budget. upstream decision 2026-07-10-06 |
| `--max-candidates` | 60 | global cap after ranking (caps agent batches) |
| `--batch` | 15 | candidates per agent call |
| `--keep-symmetric` | off | keep both directions of a pair |

Lowering `--min-score` buys recall at a steeply rising cost per link, and precision
saturates at 0.417 [0.301, 0.543] regardless, so extra volume buys rejects. At the
defaults the whole corpus yields ~81 candidate pairs — a list a person reads in an
hour. The deterministic stages are free; iterate on the shortlist before spending
any agent tokens, and consider not spending them at all (see `docs/harness-roadmap.md`).
