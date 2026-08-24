# Campaign Lifecycle Rule

Loaded on demand by `CLAUDE.md`. Read before starting, extending, or signing off a
**campaign** — a long, multi-wave programme validating a population of things against an
external authority (a benchmark's task set, a published reference-score set).

Ported from the upstream template harness (`/sync-upstream`). This rule is the durable
layer; the tools it names live under `viewer/tools/`.

## The rule

**A campaign is executed against a machine-readable descriptor, and every stage predicate is
re-derived rather than read.** A `status: done` is an assertion; the predicate is the evidence.

Register the descriptor in `.claude/campaigns` (opt-in, one path per line). An unregistered
campaign is never gated.

## The four things a descriptor must carry

| Field | Why it is load-bearing |
|---|---|
| `population` with `unit`, `total`, `partition` | The partition must SUM. A partition that does not sum is how 32 scope-call cases went missing from a coverage figure, undetected, until an audit re-derived it from the spec. A coverage claim with no named unit is un-interpretable — several counts are simultaneously correct. |
| a `disposition` on every unit | 100% attributed is not 100% implemented. Every non-covered unit names a scope call and a `todos/` ref, so deferred work cannot hide in a data field. |
| a declared `basis` on every published result | A margin is not a number until it names what it is measured against. Against a *requirement* it is mostly the margin stack, NOT receiver headroom. |
| `produced_by` on every artifact | Configuration is not lineage. A tool that must know which driver made a file will otherwise infer it from a config field, and a resolving identifier proves nothing about the producer. |

## The basis enum has one definition

`viewer/tools/campaign_common.py::BASES`. Every gate imports it. Three copies drifted apart
inside a single build session before this was consolidated — the same mechanism as
measured upstream, where a register and its gate disagreed and 32 margins sat in the
disagreement.

The published-side members are not interchangeable: **reference performance** reproduced
under your own harness (the only basis that is capability headroom), the **published value**
from a model card / paper / leaderboard (reference + a configuration stack: prompt template,
few-shot $k$, decoding params, harness version, answer-extraction rule), and a
**harness-baseline** re-scored under a third party's harness (published value + that
harness's scoring conventions). See `.claude/rules/sim-report-completeness.md`
`[opt:SIM-REQBASIS]`.

## Every gate reports its own denominator

Use `campaign_common.Scope`. A gate prints what it read of what it was named, and **REFUSES**
(exit 2) when it has no denominator. `REFUSE` is deliberately distinct from `FAIL`: a gate that
found problems is working; a gate that could not establish a denominator has no verdict to give.
Conflating them is how `check-value-ledger` read 12 of 811 files and `validate-refs` read 1, both
exiting 0.

## Autonomy stops at a decision

Scope calls and wave go/no-go are `decisions` entries with a `blocks: <stage>` edge. An `open`
decision BLOCKS its stage. The campaign surfaces it; it never infers an answer. Autonomous within
a wave, hard block at a scope call.

## A gate ships at `warn` with a ratchet when its baseline is zero

`check-lineage.py` measures 0/247 attributable at introduction. A gate introduced at `error`
against 0% coverage blocks every push and gets disabled, which is worse than not having it. Ship
at `warn`, add a `--min-coverage` floor, raise the floor as the population is stamped.

## Never backfill an anchor you cannot audit

Existing artifacts are not retro-stamped with a synthesized `builder_version`: their producing
code is exactly what is unknown, and synthesizing it launders the unknown into the anchor. Same
error as regenerating a checksum manifest without first auditing each file for completeness
(measured upstream, on a checksum manifest regenerated without auditing each file first).

## The tools

| Tool | Owns |
|---|---|
| `viewer/tools/check-campaign.py` | descriptor shape, partition sum, basis enum |
| `viewer/tools/check-lineage.py` | artifact attributability + the coverage ratchet |
| `viewer/tools/check-coverage.py` | register dispositions, basis validity, headroom claims, pooled conditions |
| `viewer/tools/campaign.py` | the 8-stage lifecycle + the decision queue |
| `viewer/tools/check-plan-progress.py` | wave/subset anti-drift (pre-existing, unchanged) |
| `viewer/tools/campaign_common.py` | `Scope`, `BASES`, `NOT_HEADROOM` — one definition each |

## Cross-references

- `.claude/rules/sim-report-completeness.md` — `[opt:SIM-REQBASIS]`, the
  `published = reference + configuration delta` decomposition the basis enum mechanises.
- `.claude/rules/calibration-residuals.md` — check 4 (declare the basis) is what the basis
  enum mechanises.
- `.claude/rules/deferred-tracking.md` — the `todos/` ref every deferred unit must name.
- `.claude/rules/campaign-execution.md` — the sibling rule: the manifest, the
  pre-registration commit-order mechanism, and the retraction path.
