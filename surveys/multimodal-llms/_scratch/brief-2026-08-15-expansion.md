# Research Brief (north star) — Multimodal LLMs, max-mode EXPANSION pass

**Status:** ✅ CONFIRMED 2026-08-15 (P0-3 gate cleared) — scope = **full expansion** (tiers + frontier
sweep + all six appendices to `headline` + §7 parity + figures).
**Mode:** `max` → proposed (all P- + R-items) · **scale:** wide · **audience:** learner · **response mode:** Survey.
**Supersedes nothing** — extends `_scratch/brief.md` (confirmed 2026-06-28), whose scope decision
(*full omni-modal parity*, *learner* register) is carried forward unchanged.

## What this pass is

Not a new survey. `surveys/multimodal-llms/` already exists (30,351 words, 23 files, authored
2026-06-28 → 07-05 in this same mode) and its `index.md` still reads **"under construction (Phase 4
synthesis)"**. This pass finishes it to the depth its own confirmed brief promised.

## Measured delivered-vs-promised state (2026-08-15)

Baseline gates are **green**: validate-refs 0 errors, 0 bare refs, 172/172 links valid, 49 references
0 errors. The structure is sound and the marker discipline is excellent. The gap is **depth**, and it
is measurable against the survey's own commitments:

| Artifact | Promised by | Delivered | Peer (MI survey, same mode) |
|---|---|---|---|
| `Depth tier:` labels | R-GOV, declared in this survey's own `index.md` legend | **0** — gate reports *"out of scope, no checks run"* | 22 |
| `figures/` | R-SURVEY (≥1 block diagram per architecture family) | **absent** | present |
| Appendices A–F | R-GOV `headline` = derivation + worked example + figure | 627–843 words each — all six at MI's *pre-deepening* size | 2,351–3,886 after deepening |
| References | citation-integrity | 49 (41 local / 8 weak) | 102 (85 strong) |
| Equations | — | 32 | 60 |
| §7 modality breadth | brief: *"§6 and §7 promoted to **[M]** at full depth"* | 1,294 words — among the thinnest body sections | — |

**The sharpest instance.** `appendix-f-audio-video.md` (627 w) backs §7, the section the 2026-06-28
brief explicitly confirmed as promoted to full depth for omni-modal parity. It contains one trivial
equation ($N_{\text{video}} = F \cdot N_v^{\text{frame}}$, a multiplication), no derivation, no worked
example, no figure. The confirmed parity commitment is the one promise the survey most visibly did not keep.

**Staleness.** Content is frozen at 2026-06-28; today is 2026-08-15. In the fastest-moving subfield
covered by this repo, ~7 weeks is a real gap — §11 (SOTA) and §13 (open problems) are the exposed
sections. The MI survey took a "2026 frontier sweep" for exactly this reason.

## Defect found during Phase-1 measurement (fix in this pass)

`viewer/tools/validate-refs.py` check #12 uses `BARE_SEC_RE = §([A-Z]?\d+(?:\.\d+)+|...)` — the digit
must **immediately** follow `§`. A reference written `§ 2.3` (with a space) is therefore invisible to
the bare-ref gate. Corpus-wide there are **90** such dead, non-clickable cross-references — 57 here,
33 in `mechanistic-interpretability` — while the gate reports clean at `--severity=error`.
Filed as a bug; the fix is a `\s*` in the pattern plus a corpus-wide promotion pass.

## Work plan (phases 2–5)

- **Phase 2 — tier the survey.** Assign + deliver the R-GOV `Depth tier:` labels (table below), so the
  depth gate stops silently skipping and the Phase-5 drift-diff has a baseline.
- **Phase 3 — evidence.** 2026 frontier sweep (Jun→Aug 2026) for §11/§13, plus derivation-grade sources
  for the six appendices. Sized by `sizing_rule`: `min(searches_per_agent, (200 − holdback)/n_agents)`,
  holdback 25 reserved for main-thread Phase-4/5 verification.
- **Phase 4 — synthesis.** Deepen appendices A–F to the `headline` contract; close the §7 parity gap;
  add the R-SURVEY figures; body updates from the sweep.
- **Phase 5 — sign-off.** `[opt:MATH-REDERIVE]` independent re-derivation per materially-changed
  appendix (on Opus, deriving before reading); R-COVER / R-RUBRIC coverage; `citation-audit`;
  `/check-survey`; `/cross-link`.

<!-- depth-tier-allocation -->

| Section | Tier | Justification |
|---|---|---|
| sec-0 | supporting | Executive summary — 60-second verdict + claims→evidence spine; carries no method of its own |
| sec-1 | load-bearing | The three-axis taxonomy (where modalities enter / how they fuse / what is generated) is the survey's organizing analysis |
| sec-2 | headline | Fundamentals — `learner` register pins the fundamentals floor at headline (continuous→token, ViT, InfoNCE, projection) |
| sec-3 | headline | Architecture building blocks — connector + fusion families are the survey's core method axis |
| sec-4 | load-bearing | Method inventory — R-CARD cards; breadth is the job, the headline derivations live in the appendices |
| sec-5 | load-bearing | Training and alignment — objectives derived + complexity, without a full worked example per recipe |
| sec-6 | headline | Multimodal generation — the 2026-06-28 brief confirmed *full omni-modal parity*, promoting this to full depth |
| sec-7 | headline | Modality breadth (audio/video/omni) — same confirmed parity commitment; currently the least-kept promise |
| sec-8 | load-bearing | Inference and serving — the vision-token cost model is quantitative; derivation + complexity |
| sec-9 | load-bearing | Evaluation and benchmarks — metric definitions + validity threats |
| sec-10 | load-bearing | Comparison and tradeoffs — the R-SURVEY master comparison matrix |
| sec-11 | load-bearing | SOTA and practice — R-SURVEY quantitative SOTA table + deployment-gap thesis |
| sec-12 | supporting | Design guidance — decision guidance synthesized from §10/§11; introduces no new method |
| sec-13 | supporting | Open problems and roadmap — gap register + reference-implementation handoff; not a method card |
| sec-A | headline | ViT / encoder internals — backs §2 |
| sec-B | headline | InfoNCE from first principles — backs §2 |
| sec-C | headline | Connector derivations (Q-Former, gated cross-attention, resampler) — backs §3 |
| sec-D | headline | Visual tokenization (VQ, straight-through, EMA) — backs §6 |
| sec-E | headline | Unified generation: the three likelihoods — backs §6 |
| sec-F | headline | Audio/video front-ends — backs §7, the confirmed parity commitment |
| sec-Q | supporting | Reader's-questions Q&A appendix |

**Four `supporting` rows surfaced explicitly** (P0-3 requires this, so they are confirmed as genuine
non-method context rather than a depth-dodge): sec-0, sec-12, sec-13, sec-Q. Each is synthesis or
front/back matter over methods derived elsewhere — none is a method card in disguise.

## Exclusions (carried forward from the confirmed brief, unchanged)

Pure text-only LLMs; pure diffusion image generators except where fused into an LLM; contrastive
embedders beyond their encoder role; Vision-Language-Action / embodied robotics (adjacent, not covered);
pre-transformer classical multimodal ML; domain-specific vertical MLLMs beyond a mention.

## MAST coverage checkpoint (P2-5)

Outline coverage-gap check: every section of the confirmed outline has a delivered file and a tier row
above; no taxonomy axis is unhoused. The residual risk this pass carries is **depth**, not coverage —
which is exactly what R-COVER / R-RUBRIC score at Phase 5.
