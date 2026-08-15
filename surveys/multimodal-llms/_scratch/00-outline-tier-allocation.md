# Depth-tier allocation (R-GOV Layer-2 north star) — Multimodal LLMs

Approved at the P0-3 gate on **2026-08-15** as part of the max-mode expansion pass
(`_scratch/brief-2026-08-15-expansion.md`). This table is the **authoritative depth-budget
allocation**: every later phase reads it back, and it is the left-hand side of the Phase-5
drift-diff (`viewer/tools/depth-tier-coverage.py`). A delivered `Depth tier:` label that
diverges from its row here is a `TIER-DRIFT` finding.

Register is `learner`, which pins the fundamentals floor at `headline`
(`config/audience-register.json`). Scope is *full omni-modal parity*, carried forward from the
2026-06-28 brief — that decision is why §6 and §7 are `headline` rather than `load-bearing`.

<!-- depth-tier-allocation -->

| Section | Tier | Justification |
|---|---|---|
| 0 | supporting | Executive summary — 60-second verdict + claims→evidence spine; carries no method of its own |
| 1 | load-bearing | The three-axis taxonomy (where modalities enter / how they fuse / what is generated) is the survey's organizing analysis |
| 2 | headline | Fundamentals — the `learner` register pins the fundamentals floor at headline (continuous→token, ViT, InfoNCE, projection) |
| 3 | headline | Architecture building blocks — connector + fusion families are the survey's core method axis |
| 4 | load-bearing | Method inventory — R-CARD cards; breadth is the job, the headline derivations live in the appendices |
| 5 | load-bearing | Training and alignment — objectives derived + complexity, without a full worked example per recipe |
| 6 | headline | Multimodal generation — the confirmed *full omni-modal parity* scope promotes this to full depth |
| 7 | headline | Modality breadth (audio/video/omni) — same confirmed parity commitment; the survey's least-kept promise before this pass |
| 8 | load-bearing | Inference and serving — the vision-token cost model is quantitative; derivation + complexity |
| 9 | load-bearing | Evaluation and benchmarks — metric definitions + validity threats |
| 10 | load-bearing | Comparison and tradeoffs — the R-SURVEY master comparison matrix |
| 11 | load-bearing | SOTA and practice — R-SURVEY quantitative SOTA table + deployment-gap thesis |
| 12 | supporting | Design guidance — decision guidance synthesized from §10/§11; introduces no new method |
| 13 | supporting | Open problems and roadmap — gap register + reference-implementation handoff; not a method card |
| A | headline | ViT / encoder internals — backs §2 |
| B | headline | InfoNCE from first principles — backs §2 |
| C | headline | Connector derivations (Q-Former, gated cross-attention, perceiver resampler) — backs §3 |
| D | headline | Visual tokenization (VQ, straight-through, EMA, VQGAN) — backs §6 |
| E | headline | Unified generation: the three likelihoods — backs §6 |
| F | headline | Audio/video front-ends — backs §7, the confirmed parity commitment |
| Q | supporting | Reader's-questions Q&A appendix |

**The four `supporting` rows, surfaced explicitly** (P0-3 requires this so they are confirmed as
genuine non-method context rather than a depth-dodge): `sec-0`, `sec-12`, `sec-13`, `sec-Q`. Each is
synthesis or front/back matter over methods that are derived elsewhere in the survey — none is a
method card in disguise. `supporting` is the ratified off-ladder context label (decision
2026-07-08-02), so these four are outside the depth-budget ladder by construction, not by omission.
