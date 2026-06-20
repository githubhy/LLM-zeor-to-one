# Citation Audit — Appendices C–H (`surveys/llms-for-coding`)

Date: 2026-06-20. Scope: the LLM-anatomy appendix series C–H. Appendix C
(`appendix-c-toy-transformer.md`) carries **no external citations** (a
self-contained toy), so the audit covers D–H. All cited sources are `local:`
PDFs present in `download/`, acquired and page-1-verified during authoring.

## Phase 1 — Citation ledger (10 distinct references)

Materiality: **N** = numeric-load-bearing, **C** = claim-load-bearing, **D** = decorative.

| Ref | Source PDF | Cited claims (locus) | Mat. |
|---|---|---|---|
| [61] GPT-2 | gpt2-2019.pdf | params 117/345/762/1542M; L 12/24/36/48; d 768/1024/1280/1600; V=50257; ctx 1024; "largely follows OpenAI GPT" quote; XL=1.5B (D, H) | N |
| [62] GPT-3 | gpt3-2020.pdf | 175B params; hundreds of billions of tokens (D) | N |
| [65] Llama-1 | llama1-2023.pdf | Table 2 d 4096–8192 / H 32–64 / L 32–80; FFN=(2/3)·4d=(8/3)d; RMSNorm+SwiGLU+RoPE; SentencePiece BPE; d_head=128 (E, F, H) | N |
| [66] RoFormer | su-rope-2021.pdf | RoPE = rotate Q,K by angle ∝ position; relative-position property (E) | C |
| [63] Llama-2 | llama2-2023.pdf | GQA at 34B/70B, MHA at 7B/13B; 70B H=64 G=8; ctx 4096; 70B dims 8192/80/64 (E, F, H) | N |
| [6] Code Llama | code-llama-2023.pdf | sizes 7/13/34/70B; 16k train / 100k serve; FIM infilling (F, H) | C |
| [10] DeepSeek-Coder | deepseek-coder-2024.pdf | sizes 1.3B–33B; 16k window; FIM; ~2T tokens (F, H) | N |
| [56] Chinchilla | hoffmann-chinchilla-2022.pdf | compute-optimal: fixed-budget loss min trades N vs D (F) | C |
| [64] DeepSeek-V3 | deepseek-v3-2024.pdf | 671B/37B; 1 shared+256 routed, top-8, expert 2048, MoE except first 3 layers; sigmoid+topk gating Eqs 12–15; aux-loss-free bias; MLA latent d_c+RoPE d_h^R; d_c=512 d_h^R=64 n_h=128 d_head=128 L=61 d=7168; V=128k ctx=128k (G, H) | N |
| [43] DeepSeek-Coder-V2 | deepseek-coder-v2-2024.pdf | 236B/21B and 16B/2.4B active; MoE on DeepSeek-V2 framework (G, H) | N |

## Phases 2–4 — Verification and classification

Method: a per-source verifier fan-out (workflow `wf_1ce7741b-b4d`, 11 agents,
384k tokens) — each agent opened its PDF, ran a page-1 identity probe, then
locus-targeted every attributed claim with `pdftotext | grep` + tight reads and
reproduced each number; any non-`correct` claim was re-checked by an independent
skeptical second reader. All 10 source identities verified ✓.

**Per-tag counts: 24 `correct`, 1 `wrong-value`, 1 `unverifiable` (= clean against [65]).**

| Ref | Claims | Result |
|---|---|---|
| [61] GPT-2 | 5 | all `correct` — params 117/345/762/1542M, L 12/24/36/48, d 768/1024/1280/1600, V=50257, ctx 512→1024, "largely follows OpenAI GPT", XL=1.5B all reproduced from Table 2 / [§2.3] |
| [62] GPT-3 | 2 | all `correct` — 175B params; "All models were trained for a total of 300 billion tokens" |
| [65] Llama-1 | 5 | all `correct` — Table 2 d/H/L; FFN "(2/3)4d"; RMSNorm+SwiGLU+RoPE; BPE/SentencePiece; d_head=128 derived from confirmed inputs |
| [66] RoFormer | 2 | all `correct` — rotation by angle ∝ position (Eq 12-13); inner product depends on m−n (Eq 11) |
| [63] Llama-2 | 4 | 2 `correct` (GQA at 34B/70B vs MHA at 7B/13B; ctx 4096); **1 `wrong-value`** (70B "H=64": the paper has no head-count column, H=64 not in text); 1 `unverifiable` against [63] (70B dims 8192/80/64 — **but verifiable against [65]**, the 65B config Llama-2-70B reuses; that column cites [65]) |
| [6] Code Llama | 3 | all `correct` — 7/13/34/70B; "16k tokens ... up to 100k"; infilling |
| [10] DeepSeek-Coder | 3 | all `correct` — 1.3B–33B; FIM 16K; **"2 trillion tokens"** confirmed |
| [56] Chinchilla | 1 | `correct` — fixed-budget loss-min trades N vs D; "scaled equally" |
| [64] DeepSeek-V3 | 7 | all `correct` — 671B/37B; 1+256 experts, top-8, expert 2048, MoE except first 3 layers; sigmoid+topk gating (Eqs 12-15); aux-loss-free bias (Eq 16); MLA latent c_KV; d_c=512, d_h^R=64, n_h=128, d_head=128, L=61, d=7168; V=128K, ctx→128K — every number reproduced exactly |
| [43] DeepSeek-Coder-V2 | 2 | all `correct` — Table 2: 236B/21B and 16B/2.4B; MoE on DeepSeek-V2 framework |

## Phase 5 — Citation-impact audit

The single `wrong-value` finding is **[63] in Appendix E.5**: the parenthetical
"(with $H=64$, $G=8$)" attributed the Llama-2-70B head count to [63], but the
Llama-2 paper states neither a 64-head count nor per-model dimensions (its Table 1
columns are only Params / Context / GQA / Tokens / LR). The "8 KV projections"
*is* in [63] (the GQA design), but the 64-head figure is derivable, not stated.

**Impact: decorative / non-load-bearing — no result is corrupted.** The values
themselves are correct (Llama-2-70B genuinely is 64 heads / 8 KV groups). The one
derivation that consumes them — F.3's 70B KV-cache arithmetic ($262$ GB MHA vs
$33$ GB GQA at 100k context) — derives $H=64$ from the 70B dimensions
($d=8192$, $d_{\text{head}}=128 \Rightarrow H=64$, sourced to [65]) and uses
$G=8$, **not** from the [63] citation. So the $8\times$ cache reduction and every
downstream number stand independently. This is a citation-precision defect, not a
math error.

The `unverifiable`-against-[63] row (H master-table 70B dims) is **not a defect**:
those dimensions trace cleanly to [65] (Llama-1 65B = d8192/L80/H64, the config
Llama-2-70B inherits), and the master-table column cites [65]. No change needed.

## Phase 6 — Fix and record

- **Fixed** Appendix E.5: replaced "(with $H=64$, $G=8$)" with "grouped-query
  attention — $8$ key/value groups —", attributing to [63] only what its text
  states. Re-validated: lint-math, validate-refs (0/0), bare-refs, citation-sources
  all clean. (commit appended below)
- **Bug filed**: `bugs/2026-06-20-01-llama2-70b-headcount-overattribution.md`
  (severity low — value correct, non-load-bearing).
- **No other changes.** The remaining 24 claims, including every load-bearing
  DeepSeek-V3 and Llama-1 number, are faithful to their sources.

**Sign-off: the C–H appendix series passes the citation gate.** One non-load-bearing
attribution imprecision found and fixed; no fabricated citations, no wrong values
in any derivation, all 10 sources are the works cited and are held locally.
