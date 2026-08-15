---
id: 2026-08-15-03
title: Figure SVGs were not byte-reproducible, so re-running an unchanged generator produced a 363-line diff
severity: low
status: fixed
date: 2026-08-15
component: surveys/mechanistic-interpretability/figures (matplotlib SVG pipeline)
---

## Symptom

Re-running the three figure generators produced modified SVGs for **all three**, including the two
whose `.py` had not been touched at all:

```
 M figures/appendix-b-superposition-capacity.svg   (363 insertions, 363 deletions)
 M figures/appendix-c-patching-approximation.svg
 M figures/appendix-d-sae-shrinkage.svg
```

This reads as nondeterministic computation, which would be serious — the repo's diagram rule
requires figure-backing code to be deterministic and the generators disclose seeds on that basis.

## Root cause

**Not** nondeterministic computation. The plotted coordinates are bit-identical across runs
(`M 75.400419 265.715312` is unchanged in every path). Two matplotlib output artifacts account for
the entire diff:

1. **A wall-clock timestamp in the SVG metadata** — `<dc:date>2026-08-15T00:16:11.817074</dc:date>`.
2. **Randomized element identifiers.** matplotlib derives `clipPath` and `defs` ids from a per-process
   salt, so every run renames every one of them: `p13abf0a3f4` → `p5f3dd4607c`,
   `mb11a0fa6e7` → `m20392c723f`. This is what generates the hundreds of lines; each renamed id
   appears at both its definition and every `xlink:href` use.

The numeric determinism the generators were written for (seeded `default_rng`, closed forms, no
wall-clock in the *computation*) was real and is intact. What was missing is that **the persisted
artifact was not reproducible even though the computation was** — a distinction the diagram rule
does not currently draw, and the reason this went unnoticed when the figures landed.

The consequence is auditability rather than correctness: in a 363-line diff of renamed identifiers,
a genuine change to a plotted value is invisible. A reviewer either reads every line or trusts the
commit message, and both defeat the point of persisting the artifact next to its generator.

## Fix

Two lines per generator, with the reason stated in a comment at the point of use:

```python
matplotlib.rcParams["svg.hashsalt"] = "<figure-stem>"      # deterministic element ids
fig.savefig(HERE / f"{STEM}.svg", metadata={"Date": None}) # no wall-clock in metadata
```

The salt is set to the figure's own stem, so ids stay stable per figure and cannot collide across
figures if two SVGs are ever inlined into one document.

Verified by generating twice and comparing: all three are **byte-identical across runs** (`cmp`
clean). The committed SVGs were regenerated once under the new settings, so the next re-run produces
an empty diff.

## Regression test

none as an automated check — but the fix is *self-testing in the diff*: from now on, re-running an
unchanged generator produces no change at all, so any diff in a figure SVG is a real diff. That is a
stronger and cheaper signal than a test would be.

Worth considering for the harness if a fourth figure appears: a `--check` mode for the figure
pipeline (regenerate to a temp dir, `cmp` against the committed artifact) would make the property a
gate rather than a convention. Not proposed on three figures.

## Refs

- `.claude/rules/workflow.md` § Diagram Rules — "Persistent data: save the underlying experiment or
  computation results so the figure can be regenerated later" and the determinism requirement. This
  bug is the gap between *deterministic computation* and *reproducible artifact*; the rule currently
  states only the former.
- `field-notes/2026-08-15-mi-appendix-deepening.md`.
