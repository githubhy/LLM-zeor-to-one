---
slug: source-fetch-grokking-citations
date_filed: 2026-07-01
status: open
---

# Source-fetch + cite the grokking literature for appendix-c §C.8

## Context

§C.8 ("Grokking: Why Generalization Can Lag Memorization") was written as a self-contained first-principles derivation with **no external citations** (decision `2026-07-01-02`), because `references.md` held no grokking paper and acquiring them was a detour the derivation did not need. The section's "Provenance" note flags that the empirical attributions are deferred to this pass. §C.8 is derivation-complete but **citation-incomplete** — do not treat it as delivery-signed-off until this closes.

## What is left

- `source-fetch` the load-bearing sources: Power et al. 2022 (grokking, the phenomenon); Nanda et al. 2023 (progress measures / the Fourier-multiplication circuit); Varma et al. 2023 (circuit efficiency — the norm/efficiency account of the delay). Secondary: Liu et al. 2022 (Omnigrok / effective theory — grokking beyond algorithmic data, the "toward SOTA" bridge); Wei et al. 2022 (emergent abilities); Schaeffer et al. 2023 (emergence-as-mirage).
- Add `references.md` entries with strong `local:` source tags (PDFs in `download/`).
- Add `<!-- cite:N -->` markers in §C.8 at the Provenance note and at each attributed empirical claim (the phenomenon, the Fourier circuit, the efficiency argument, the beyond-toy evidence, the emergent-abilities analogy + mirage caveat).
- Run `link-references.py` + `check-citation-sources.py`; verify every cited value against the acquired source.

## Acceptance

- Every empirical claim in §C.8 carries a citation traceable to an acquired source; the derivation stays self-contained (no claim *rests* on the weak citations).
- `references.md` ↔ `download/` invariant holds; `check-citation-sources.py` clean; `/check-survey llms-for-coding` green.

## Refs

- Survey: `surveys/llms-for-coding/appendix-c-toy-transformer.md` §C.8.
- Decision: `decisions/2026-07-01-02-grokking-first-principles-derive-now-cite-later.md`.
- Skill: `.claude/skills/source-fetch/SKILL.md`; rule: `.claude/rules/citation-integrity.md`.
