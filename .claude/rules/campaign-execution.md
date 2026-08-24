# Campaign-Execution Rule

Loaded on demand by `CLAUDE.md`. Read this file before starting, resuming, or
signing off any **campaign** — and before adding a gate to one.

**Domain-agnostic.** No campaign has run in this repo yet; the harness landed ahead of its
first instance. A long benchmark-evaluation sweep, a multi-model reproduction, or a
method-search over a large candidate set is the shape it is for.

## What counts as a campaign

Work is a campaign when all three hold:

1. **Multi-session** — it will outlive the context that authored it.
2. **Multi-task** — a task list, with dependencies, not a single deliverable.
3. **Accumulating** — each task changes the baseline the next one is measured
   against, so results compound (and errors compound too).

A survey, a single experiment, a bug fix, a review: **not** campaigns. A multi-model
benchmark sweep, a long migration, a multi-phase study: campaigns.

## The rule

**A plan that depends on being remembered is not a plan.** Only a gate that blocks
sticks; everything else is vigilance, and vigilance decays across sessions,
compactions, and subagents.

The repo has already paid for this: the pre-push hook was **copied** into
`.git/hooks`, silently drifted, and ran **5 of 9 checks for months** with nothing
reporting it (measured upstream). The fix was not diligence — it was
`core.hooksPath`. **A copy drifts; a pointer cannot.** Design so the failure mode
is impossible, not so that it is merely detected.

So a campaign MUST carry three things on disk:

| Artifact | Why |
|---|---|
| `campaigns/<slug>/campaign.json` | **The plan as data.** Prose cannot gate. The markdown README is rendered *from* it. |
| `tasks/<TID>/pre-registration.md` | For any task that will **assert a claim**. Committed **before** the result. |
| `ledger/` | The **result-of-record**. `measured.json` is generated from artifacts; `attributions/` is one file per record. |

**Directory existence is the registration.** There is no opt-in registry file —
registries drift (measured upstream: 8 of 14 declared documents were structurally
invisible to their gate). Create `campaigns/<slug>/` and the gates apply.

## Pre-registration (the universal mechanism)

**The pre-registration commit must PRECEDE the first result commit.** Git is a
tamper-evident clock, so this is mechanically checkable —
`viewer/tools/lib/prereg.py` does it.

- **Same-commit is a FAILURE.** If the registration and the result land together
  their order is unverifiable, which is exactly how the discipline gets bypassed
  (including by an innocent `git add -A`). Costs one extra commit; closes the only
  hole.
- **Silent post-hoc edits to the thresholds block are a FAILURE.** An amendment is
  allowed but must be a visible `## Amendment` section — never a quiet rewrite.
- **Every hypothesis carries a numeric threshold AND a falsifier.** A
  pre-registration you cannot fail is not a pre-registration.

This is a **library, not a campaign feature.** It exists because the repo already
promises pre-registration in two places and enforces it in neither:

- `.claude/rules/sim-report-completeness.md` Section 1 — *"pre-registered hypotheses
  with numeric thresholds"*;
- `.claude/skills/asic-synthesis-cost-study/SKILL.md` — *"a pre-registered
  CONFIRM/REFUTE window"*.

Any gate may call `lib/prereg.py`. Nothing has to become a "campaign" to use it.

## The ledger

- **`measured.json` is GENERATED from artifacts, never hand-written.** A
  hand-maintained ledger becomes prose within three sessions — and a generated file
  has **no merge-conflict surface**: a collision between concurrent sessions is
  resolved by re-running the builder.
- **`attributions/` is one file per record**, like `bugs/` and `decisions/` — the
  pattern the repo adopted precisely *because* a shared index collides.
- Every row carries the **envelope** (the spread of the external reference, where it
  is an aggregate) and the **basis** (what is averaged, over what population, with
  what normalization). A residual inside the envelope **is not a defect**; a
  disagreement that dissolves under basis reconciliation was never a finding.

## Tier is derived from the OUTPUT, not declared

**A task that writes an `attribution` IS the top tier, whatever it calls itself.**
Rigor cannot be downgraded by relabelling a task as "simple". `check-campaign.py`
infers the tier from what the task produced.

## The retraction path

Accumulation without reconciliation is not compounding — it is **accretion of stale
claims**. When a later task falsifies an earlier attribution:

1. Append to `history[]` (never edit the old entry away).
2. Move `status` back (`ATTRIBUTED → LEAD` / `OPEN`).
3. Run **`results-reconciliation`** — the prose goes stale silently while the data
   blocks stay correct.
4. File a `bugs/` entry if the wrong attribution ever shipped.

This is not hypothetical upstream: a finding measured in ONE configuration became the
framing of an entire report and was **provably false for its sibling configuration**. The
LLM shape is identical -- a regression attributed to a quantization scheme after testing
one model size, then asserted for the family
(`.claude/rules/calibration-residuals.md` check 2).

## Gates

| Tool | Scope | Blocks on |
|---|---|---|
| `viewer/tools/check-campaign.py` | `campaigns/*/` | manifest, dep order, tier-from-output, gate records, pre-registration order, claimed ⊆ measured, the measure-first dependency |
| `viewer/tools/check-ledger.py` | `campaigns/*/` | ledger staleness, missing envelope / basis / CI, attribution without a bucket or a quantified closure |
| `viewer/tools/check-forbidden-phrasing.py` | **repo-wide** | the forbidden attribution phrasings of `.claude/rules/calibration-residuals.md` |
| `viewer/tools/campaign-status.py` | — | not a gate: the session-resume renderer |

Severity: `campaign.json` `gates.severity` and `.claude/campaign-phrasing-severity`
(`off | warn | error`). Roll out `warn → error`, as bare-refs and crosslink did.

## What gates cannot do

They catch **structure, not insight**. A checker can verify an adversarial panel
*ran*; not that it was adversarial. It can confirm a candidate list exists; not that
it is complete. It can confirm a basis was *recorded*; not that it was *understood*.
What they buy is that the judgment is **forced to happen at the right moment and
leaves an auditable trail** — precisely what was missing when the
single-configuration attribution shipped.

## Cross-references

- `.claude/rules/calibration-residuals.md` — the honesty standard the phrasing gate enforces.
- `.claude/rules/sim-report-completeness.md` — promises pre-registration; `lib/prereg.py` enforces it.
- `.claude/skills/harness-harvest/SKILL.md` — run at every phase boundary; this is the compounding mechanism.
- `.claude/skills/results-reconciliation/SKILL.md` — the retraction path.
- No worked instance in this repo yet — the first campaign to register under
  `.claude/campaigns` becomes it.
