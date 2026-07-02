# Implementation Report — Appendix I: Mechanistic Interpretability

- **Date:** 2026-07-01
- **Survey:** `surveys/llms-for-coding/`
- **Plan:** `plans/2026-07-01-mi-clusters-survey-buildout.md`
- **Gap analysis:** `wikis/mechanistic-interpretability-coverage-gaps.md`
- **Tracks:** `todos/2026-07-01-mi-coverage-gaps.md`

## Summary

Authored a new **Appendix I — Mechanistic Interpretability** (`appendix-i-mechanistic-interpretability.md`, registered in `order.json` after Appendix H), covering all five MI gap clusters identified earlier from first principles, math-rich, intuition-forward, and fully cited to acquired sources. Nine sections, **22 numbered equations**, **24 newly-acquired references** (all strong `local:` tags). Every validation gate is green.

## What was built

| Cluster | Sections | Core content |
|---|---|---|
| Framing | I.1 | Circuit vs feature level; linear-representation hypothesis; privileged vs non-privileged basis |
| A — representational | I.2, I.3 | Superposition (interference Eq (2), sparsity Eq (3), JL capacity Eq (4)); SAEs (encoder/decoder Eq (5), objective Eq (6), L1-shrinkage soft-threshold Eq (7), gated/top-$k$/JumpReLU, loss-recovered Eq (8)) |
| B — intervention | I.4 | Ablation; activation patching Eq (9); attribution patching Eq (10); logit lens Eq (11) / tuned lens Eq (12); ACDC; DAS |
| C — circuits + heads | I.5, I.6 | IOI discovered circuit (logit-diff Eq (13), faithfulness Eq (14)); head zoo — prev-token, duplicate, induction, name-mover, successor Eq (15), copy-suppression Eq (16) |
| D — code-specific | I.7 | Probing Eq (17) + selectivity Eq (18); syntax/identifiers; execution-state world models, intervention Eq (19); code circuits |
| E — payoff + epistemics | I.8, I.9 | Steering Eq (20); ROME Eq (21) / MEMIT Eq (22); auditing; illusions, self-repair, attention-isn't-explanation, streetlight caveat |

Each section follows the §A/§C register: intro → derivation → "what it buys" → "intuition". A forward-link from §C.10 (superposition line) into §I.2 closes the loop the wiki flagged.

## Source acquisition (Phase 3)

24 papers fetched via `source-fetch/oa_fetch.py` (arXiv-direct, keyless) into `download/`, added as `references.md` entries **[70]–[93]** with `local:` tags. P1 (SAE + code): Cunningham 2309.08600, Gao 2406.04093, gated 2404.16014, JumpReLU 2407.14435, Li 2210.13382, Nanda 2309.00941, Jin 2305.11169, Troshin 2202.08975. P2/P3 (intervention/circuits/payoff/epistemics): Wang-IOI 2211.00593, Olsson 2209.11895, Meng-ROME 2202.05262, Belrose 2303.08112, Conmy-ACDC 2304.14997, Geiger-DAS 2303.02536, Hanna 2305.00586, Gould 2312.09230, McDougall 2310.04625, Wan 2202.06840, Turner 2308.10248, Zou 2310.01405, Meng-MEMIT 2210.07229, Bolukbasi 2104.07143, Jain 1902.10186, Wiegreffe 1908.04626.

Reference metadata (title/authors/venue) was read from each PDF's first page, not from memory.

## Verification (citation integrity)

Every citation was verified against the acquired source (pdftotext cache, grep). Signature claims confirmed for all 24; specific phrasings spot-checked (Nanda's "MINE vs. YOURS" frame, Gould's ordinal-increment OV, Turner's ActAdd steering vector, Zou's LAT reading vector, IOI's "26 heads / 7 classes / faithfulness-completeness-minimality"). **Two attribution errors were caught and fixed before delivery** (see `field-notes/2026-07-01-mi-appendix-authoring.md`):

1. Li Othello [83] was described as a *linearly*-decodable board state; Li's probe was **nonlinear** (linear probes failed) — the linear finding is Nanda [84]. Reworded so [83] = emergent (causal, intervenable) representation, [84] = linear in the mine/theirs frame.
2. The superposition *phase-transition / tegum-geometry* claim was cited to Cunningham [70], which contains no such content (that is Elhage's Toy Models of Superposition, not acquired). Removed the unsourced specifics; kept the sparsity-enables-superposition point, which [70] does support.

Derivations are self-contained (interference, JL capacity, L1 soft-threshold shrinkage, ROME rank-one, MEMIT least-squares all derived inline); citations credit empirical findings, and no load-bearing derivation rests on a weak source. No `web`/`abstract-only` citations were introduced — all 24 are strong `local:`.

## Gates (all green)

- `renumber-sections/paragraphs/equations --check`: clean — **22 equation tags sequential, zero cascade** (new file has its own `eq:I-*` namespace); 91 paragraph anchors.
- `link-references --check`: up to date.
- `validate-refs`: 0 errors — 10 files, 114 equation markers, 150 `.md` links valid, 0 orphaned refs.
- bare-refs `--severity=error`: clean.
- `check-citation-sources`: 93 entries, **83 strong local / 0 errors**.
- `crosslink check --changed`: **no cross-link gaps** (appendix is densely self-linked; ~30 `secxref`/`secref` to §A/§C).

This is the full `/check-survey` component set — the survey passes its delivery gate.

## Bugs / decisions / field notes

- Field note: `field-notes/2026-07-01-mi-appendix-authoring.md` (the two caught-and-fixed citation attributions).
- No `bugs/` entry — both citation errors were caught by the authoring-time verification pass and never shipped.
- No new `decisions/` — placement (new Appendix I) and derive-now/cite-findings were pre-decided in the plan.

## Recommended follow-ups (tracked)

- **Formal `citation-audit` pass** as the independent final gate. Authoring-time in-source verification was done (and caught 2 errors), but the standalone skill was not separately run. Tracked in `todos/2026-07-01-mi-appendix-followups.md`.
- **Optional backlinks** §A.9 / §A.22 → §I.4/§I.6 (the crosslink gate is already green without them; appendix-i links *to* those sections). Tracked in the same follow-up todo.
- P2/P3 canonical web-only sources (Elhage TMS, Bricken/Templeton monosemanticity) were intentionally not cited — the math is self-derived and the local SAE papers carry the load-bearing claims. Fetch + add as `web` only if a future pass wants origin credit.
