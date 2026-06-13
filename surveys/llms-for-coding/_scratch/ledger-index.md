# Evidence Ledger — Index & Section→Reference Map

Phase-3 deliverable of record. Detailed evidence (findings, locators, confidence, gaps) lives in
`clusterA..F.md`. This index maps each survey section to its primary references (numbering = `references.md`)
and records gap-resolution status. All 45 refs are `local:` full-text (check-citation-sources: 45/45 strong, 0 err).

## Section → primary refs (evidence cluster)

| § | Section | Primary refs | Cluster |
|---|---|---|---|
| 2 | Scope & Code Modality | 1,2,3,4,5,6,44 | A |
| 3 | Historical Evolution | 2,1,3,4,6,8,10,11,43,25 | A,B,F |
| 4 | Fundamentals (FIM, pass@k) | 1,5,4,6,3 | A |
| 5 | Code-Model Pipeline | 11,10,8,9,6 | B |
| 6 | Pretraining Data | 7,9,8,10,11,12,13 | B |
| 7 | Pretraining Objectives/Scaling | 5,8,9,10,11,6,12 | B |
| 8 | Instruction Tuning & Alignment | 15,16,17,18,19,20 | C |
| 9 | Reasoning & Test-Time Compute | 21,22,23,24,25,26,19,20 | C |
| 10 | Inference/Decoding/Serving | 5,27,28,29 | D |
| 11 | Retrieval & Repo Context | 30,14,2,6 | D |
| 12 | Agentic Coding Systems | 31,32,33,34 | D |
| 13 | Evaluation & Benchmarks | 1,35,36,37,38,39,40 | E |
| 14 | Compute/Cost/Latency Tradeoffs | 43,27,26,40 | D,F |
| 15 | State of the Art & Practice | 43,25,38,39 (+web, dated, caveated) | F |
| 16 | Safety/Security/Licensing | 41,42,7,8,9 (+web litigation) | F |
| 17 | Design Guidance | synthesis across all | — |
| 18 | Open Problems & Roadmap | 44,45,38,40,12 | F |

## Gap resolution (flagged by agents → status)

- Semantic dedup (§6): **resolved** — acquired SemDeDup [13] as the embedding-dedup contrast (corpora use exact+MinHash; [13] is the semantic technique).
- Tokenizer fertility (§7): **partial** — byte-level BPE + cross-whitespace merge (45% reduction, InCoder [4]) and vocab sizes ([8,9,10,11]) are primary; no per-model fertility table exists in sources → state qualitatively, no fabricated number.
- DPO primary (§8): **resolved** — [18] acquired (loss equation read from source).
- Self-Instruct / Code Alpaca / CoT / Self-Consistency (§8,§9): **resolved** — [15,21,22] acquired.
- RLEF full text (§8): **resolved** — [20] acquired.
- o-series exact figures (§9): **resolved** — [26] acquired (o3 figures from primary).
- Speculative decoding primary (§10): **resolved** — [27] acquired.
- General grammar-constrained decoding (§10): **resolved** — [29] (Outlines) acquired; [28] PICARD for SQL.
- Dense code retrieval (§11): **resolved** — [14] UniXcoder acquired; [30] RepoCoder (sparse).
- Long-context-vs-RAG head-to-head (§11): **unresolved** — no single primary; treat as qualitative tradeoff, cite [30] framing only.
- ClassEval exact numbers (§13): **unresolved** — abstract-only; cite qualitatively ("class-level << method-level"), no fabricated pass@1. (add ref 47 abstract-only if used)
- LLM-as-judge-for-code (§13): **unresolved** — web synthesis; state as "documented, task-dependent, not reliable without execution," no precise stat.
- Secure-code-gen benchmark (§16): **resolved** — [42] SVEN acquired.
- Verbatim code memorization measurement (§16): **unresolved** — no primary; use the Doe v. GitHub court characterization (web) + license-clean-by-construction counter-pattern ([7,8,9]).
- Second SE roadmap (§18): **resolved** — [45] Fan et al. acquired.
- SOTA frontier numbers >81% SWE-bench (§15): **DO NOT CITE** — web leaderboards surfaced unverifiable/fabricated model names. Use primary 2024 anchor [43] (SWE-bench 12.7) + credible dated band ~80% as web-caveated estimate w/ contamination asterisk.

## Web/abstract refs to append (46+) as used
46 OpenAI "Introducing SWE-bench Verified" (web) · 47 ClassEval (abstract-only) · 48 Aider leaderboard (web) ·
49 SWE-bench Verified late-2025 frontier snapshot (web, dated, caveated) · 50 GitHub Copilot custom-model latency (web) ·
51 Cursor/Fireworks speculative-edits (web) · 52 OWASP agentic prompt-injection (web 2026) · 53 Doe v. GitHub litigation (web 2024).
