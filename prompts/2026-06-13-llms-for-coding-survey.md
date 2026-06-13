# Conversation Log — 2026-06-13 — session: llms-for-coding-survey

## Conversation 1
- **Request**: `/deep-research-survey LLMs for coding` (mode: `original`, default — no flags).
- **Actions**: Ran Phase 1 (Scope) — asked 3 scoping questions. User chose: Focus = Comprehensive landscape; Audience = newcomer→staff depth ramp (option 4 then 1); Emphasis = historical evolution then current SOTA (option 3 then 1). Ran Phase 2 (Outline) — drafted an 18-section comprehensive outline with per-section research questions + must/nice tags, checked against the LLM method taxonomy. User chose "Proceed with full 18-section".
- **Result**: Scope + outline locked. Scaffolded `surveys/llms-for-coding/` via `init-doc.py` (18 section files + index + references + order.json). Created 13-item task list (Phase 3 evidence ×6 clusters, consolidate, Phase 4 writing ×4, Phase 5 validate + audit). Verified source-fetch works end-to-end (Codex 2107.03374 → download/, 35pp validated).

## Conversation 2
- **Request**: (continuation) Execute Phase 3 evidence collection.
- **Actions**: Launched 6 parallel background evidence agents (clusters A–F), each: ≤5 questions, ≤6 PDF downloads, ≤~12 searches, citation-integrity rule embedded, checkpoint-writes to `surveys/llms-for-coding/_scratch/cluster{A..F}.md`. Acquisition targets seeded with arXiv IDs (content-verified by agents).
- **Result**: Agents running in background. Awaiting completion notifications to consolidate the evidence ledger (Task #7), then Phase 4 synthesis on main thread.

## Conversation 3
- **Request**: (continuation, effort raised to `ultracode`) Consolidate evidence, write the survey, validate, audit.
- **Actions**: All 6 evidence agents returned (clusters A–F; ~36 PDFs acquired). Main thread acquired 12 gap-fill primaries (DPO, Self-Instruct, CoT, Self-Consistency, RLEF, o-series 2502.06807, SemDeDup, speculative decoding, Outlines, SVEN, UniXcoder, Fan SE survey) → 45 local: PDFs total. Built `references.md` (45 strong local + 8 weak web/abstract, check-citation-sources clean) and `_scratch/ledger-index.md`. Wrote all 18 sections + executive summary on the main thread (synthesis not delegated, per skill), authoring inline with cross-link markers; verified RLEF/DPO/o-series/SVEN/CodeRL load-bearing numbers directly against PDFs before writing (caught + corrected an o1-vs-o1-ioi rating drift: o1=1673/89th, o3=2724/99.8th). Ran the cross-link init pass (renumber-sections/paragraphs --init, link-references --init) and the full `/check-survey` gate.
- **Result**: `/check-survey` GREEN — lint-math 0 errors, equations sequential (5), 19 cross-file citation links valid, bare-refs clean (exit 0), references 53 entries/0 errors. Launched adversarial citation-audit workflow (32 source verifiers, `wf_0a879215-105`) — awaiting completion before sign-off.
- **Findings**: Cluster-F flagged that 2026 web SWE-bench leaderboards surface unverifiable/fabricated model names above ~81%; §15 SOTA therefore uses only the primary mid-2024 anchor (DeepSeek-Coder-V2 SWE-bench 12.7) plus a dated, contamination-caveated frontier band — no fabricated numbers propagated.

## Conversation 4
- **Request**: (continuation) Citation audit + sign-off.
- **Actions**: Adversarial citation-audit workflow `wf_0a879215-105` completed — 32 source verifiers, 84 load-bearing claims, 83 correct, 1 `wrong-value`. Verified the flagged item against the PDF and fixed it: §8 had Code Llama-Python-7B base as 48.2% (that is WizardCoder-CL's figure); corrected to 37.8% per Magicoder Table 1. Filed bug `2026-06-13-01` (med, fixed) + `bugs/INDEX.md`; wrote `reports/citation-audit-llms-for-coding-2026-06-13.md`. Re-ran the full gate.
- **Result**: SIGN-OFF. `/check-survey` green after fix (lint-math 0, equations sequential, links up-to-date, paragraphs/sections clean, validate-refs 0/0, bare-refs exit 0, references 53/0). Survey ≈15.7k words, 19 files, 45 local + 8 weak refs. All 13 tasks complete.
- **Findings**: The audit caught one subagent-introduced base-figure misattribution (48.2↔37.8 across adjacent Table-1 rows) that survived authoring; two other drifts (o1 vs o1-ioi rating; o3 2724 vs 2706; RLEF abstract→full-text) were caught earlier during authoring-time verification. Net: the fan-out audit is the gate that catches exactly the cross-row numeric drift parametric/secondary evidence introduces.

## Conversation 5
- **Request**: commit and push; then merge to main and clean up.
- **Actions**: Branched `survey/llms-for-coding` off main (per default-branch rule), committed 36 files as `bbb1f29` (survey + `_scratch` evidence + reports/bugs/prompts; `download/*` PDFs gitignored), pushed to origin. Then fast-forwarded `main` to `bbb1f29`, pushed `main` (8ebd7de..bbb1f29), and deleted the feature branch local + remote.
- **Result**: Delivered on `main` (origin `githubhy/LLM-zeor-to-one`). Working tree clean; only `main` remains. All 13 survey tasks complete.

<!-- LOG-END -->
