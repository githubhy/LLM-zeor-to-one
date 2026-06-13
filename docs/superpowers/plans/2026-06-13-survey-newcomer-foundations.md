# Newcomer Foundations Enrichment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) to implement this plan task-by-task. The deep-research-survey skill requires the main thread to own all survey prose — do NOT delegate prose synthesis to subagents; subagents may be used only for evidence/verification. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add a first-principles, newcomer-friendly Section 3 primer ("Language Models from First Principles") to the LLMs-for-Code survey — calibrated for a signal-processing reader (strong math, no DL) — plus distributed intuition/diagrams, with the existing FIM/pass@k fundamentals folded in.

**Architecture:** New Section 3 file; fold + delete the old fundamentals file; History shifts 3->4; Sections 5-18 unchanged. Diagrams in mermaid (+ ASCII for function plots). New citations acquired full-text and audited. All survey cross-link/lint gates stay green.

**Tech Stack:** Markdown + the `viewer/tools/` Python toolchain (lint-math, renumber-equations/sections/paragraphs, link-references, validate-refs, check-citation-sources); `source-fetch` (`oa_fetch.py`); Git LFS for PDFs; mermaid (CDN, client-rendered).

**Authoring conventions (apply in every prose step):**
- Cross-refs to other sections: plain prose "Section N" (single number — NOT `§N.M`, which trips the bare-ref hook). Same-file equation refs: `<!-- ref:3-K -->[(K)](#eq-K)` with `<a id="eq-K"></a><a id="eq-1"></a><!-- eq:3-K -->` on the line above the `$$`. Citations: bare `[N]` (promoted by `link-references --init` later).
- Inline math `$...$`: opening `$` not preceded by a digit, closing `$` not followed by a digit (keep numerals inside the span). Money as `USD x`, never `$x`.
- Display `$$...$$`: blank line after the close; in tight lists no blank line between math-bearing items.
- Diagrams: ```mermaid fences (skipped by lint-math). Function plots (scaling curves): ASCII inside a plain ``` fence.
- After editing any file, the PostToolUse hook runs lint-math + bare-refs (error severity); fix before moving on.

---

### Task 0: Acquire + verify new source PDFs; extend references.md

**Files:**
- Modify: `surveys/llms-for-coding/references.md` (append [54]+)
- Create (download, LFS): `download/*.pdf`

- [ ] **Step 1: Acquire the four mandatory primaries + optional MoE.**

```bash
cd /Users/claire/GitRepos/llm-zero-to-one
for kv in \
 "1706.03762|vaswani-attention-is-all-you-need-2017" \
 "2001.08361|kaplan-scaling-laws-2020" \
 "2203.15556|hoffmann-chinchilla-2022" \
 "2104.09864|su-rope-2021" \
 "2101.03961|fedus-switch-transformer-2021"; do
  id="${kv%%|*}"; name="${kv##*|}"
  python .claude/skills/source-fetch/oa_fetch.py "arxiv:$id" --download "download/$name.pdf"
done
```

- [ ] **Step 2: Content-verify each (title/first page match).**

```bash
for n in vaswani-attention-is-all-you-need-2017 kaplan-scaling-laws-2020 hoffmann-chinchilla-2022 su-rope-2021 fedus-switch-transformer-2021; do
  python -c "import fitz;d=fitz.open('download/$n.pdf');print('$n',d.page_count,d[0].get_text()[:80].replace(chr(10),' '));d.close()"
done
```
Expected: titles match (Attention Is All You Need; Scaling Laws for Neural LMs; Training Compute-Optimal LLMs; RoFormer/RoPE; Switch Transformers). If a title mismatches, delete and re-resolve by title query.

- [ ] **Step 3: Extract load-bearing scaling-law numbers (for subsection 3.6).** Read the loci and record, verbatim, into a scratch note `surveys/llms-for-coding/_scratch/scaling-evidence.md`:
  - Kaplan: the power-law exponents for loss vs N (params, non-embedding), D (data), C (compute) — e.g. alpha_N, alpha_D, alpha_C — with the equation forms and the page/section.
  - Chinchilla: the parametric loss `L(N,D) = E + A/N^alpha + B/D^beta` constants (E, A, B, alpha, beta), the compute relation `C ~= 6ND`, the compute-optimal exponents (a,b in N_opt~C^a, D_opt~C^b), and the "~20 tokens per parameter" result. Locator each.
  Do NOT write any number into the survey that is not copied from these PDFs.

- [ ] **Step 4: Append references [54]-[58] to references.md** (only those actually cited), each with a `local:` tag, e.g.:

```markdown
<a id="ref-54"></a><!-- bib:54 -->
[54] A. Vaswani, N. Shazeer, N. Parmar, et al., "Attention Is All You Need." *NeurIPS 2017.* arXiv:1706.03762. (local: download/vaswani-attention-is-all-you-need-2017.pdf)
```
(Repeat for Kaplan [55], Chinchilla [56], RoPE [57], Switch Transformer [58] if used.)

- [ ] **Step 5: Verify reference invariant.**

Run: `python viewer/tools/check-citation-sources.py surveys/llms-for-coding/references.md`
Expected: `0 error(s)`, strong count increased to 49-50.

- [ ] **Step 6: LFS-track + commit the new PDFs.**

```bash
git add download/*.pdf surveys/llms-for-coding/references.md
git lfs ls-files | grep -E 'vaswani|kaplan|chinchilla|rope|switch'   # confirm LFS pointers
git commit -m "Acquire foundations primaries (Transformer, Kaplan, Chinchilla, RoPE, MoE) via LFS"
```

---

### Task 1: Pre-flight cross-reference inventory

**Files:** none modified (read-only).

- [ ] **Step 1: Confirm no linked section-refs exist (the swap assumption).**

Run: `grep -rnE "secref:|secxref:" surveys/llms-for-coding/*.md`
Expected: no matches. If any exist, switch those to the marker+link rewrite path instead of the plain-prose swap.

- [ ] **Step 2: Inventory every section cross-reference to build the swap map.**

Run: `grep -rnoE "Sections? [0-9]+(\\b|–[0-9]+)" surveys/llms-for-coding/*.md | sort`
Record which mention "Section 3" (History -> becomes 4), "Section 4" (old fundamentals/FIM/pass@k -> becomes 3), and any ranges like "Sections 2–4" / "Sections 5–9" (rewrite by hand in Task 5). Save to `_scratch/xref-map.md`.

---

### Task 2: Write the new Section 3 primer (general subsections 3.1-3.6)

**Files:**
- Create: `surveys/llms-for-coding/language-models-from-first-principles.md`

- [ ] **Step 1: Author the section header + subsections 3.1-3.5.** Write `## 3 Language Models from First Principles` + a short orientation paragraph stating the SP-calibrated contract (math assumed; DL built from scratch; analogies). Then:
  - **3.1 A language model is an autoregressive predictor.** Define the next-token model p(x_t | x_<t); the training objective as cross-entropy = negative log-likelihood (tie to KL). Analogy box: "Intuition. An LM is an AR(p) model with the linear predictor replaced by a learned nonlinear map and a categorical (softmax) output over a token alphabet." Worked example: next-token over a short code line. One numbered display equation for the NLL objective (`<a id="eq-2"></a><!-- eq:3-1 -->`).
  - **3.2 Tokens and embeddings.** Tokenization as discretization/symbol-mapping; embedding matrix as a learned lookup into R^d. Tiny example tokenizing `def add(a, b):`. Mermaid: text -> tokens -> embedding vectors.
  - **3.3 Attention and the Transformer.** Self-attention as data-dependent weighted averaging; `Attention(Q,K,V)=softmax(QK^T/sqrt(d_k))V` as a numbered eq (`<a id="eq-3"></a><!-- eq:3-2 -->`); weights = normalized correlations (matched-filter analogy); contrast fixed-kernel convolution. Multi-head; the block (attention + MLP + residual + LayerNorm). Cite Vaswani [54]. Mermaid: Transformer block. Worked example: a 3-token attention weight computation (small numbers).
  - **3.4 Architectural structures.** Encoder-only / decoder-only / encoder-decoder; causal vs bidirectional masking; why code LLMs are decoder-only (reuse CodeBERT [2] encoder vs Codex [1] decoder). Variants: MHA/MQA/GQA (KV-cache cost intuition), MoE (sparse routing; cite [58] if used), positional encodings — sinusoidal and RoPE [57] as Fourier-basis/phase-rotation. Mermaid: architecture family tree; mermaid: causal vs bidirectional mask.
  - **3.5 How a model is trained.** The arc pretrain -> fine-tune -> align: what each stage optimizes and changes (no RL/DPO detail — forward-point to Sections 8 and 9). Mermaid: training pipeline. Mermaid: autoregressive generation / KV-cache loop. Forward-pointers: data (Section 6), objectives (Section 7), alignment (Section 8), reasoning (Section 9), serving (Section 10).

- [ ] **Step 2: Author subsection 3.6 (scaling laws — full math), using only the verified numbers from `_scratch/scaling-evidence.md`.** Content:
  - Power-law scaling (Kaplan [55]): loss as a power law in N, D, C; give the forms and the measured exponents (from the PDF). Numbered eqs.
  - Chinchilla [56] parametric loss `L(N,D) = E + A/N^alpha + B/D^beta` (numbered eq) with the fitted constants from the PDF.
  - Compute budget `C ~= 6ND` (numbered eq) and the constrained-optimization derivation: minimize L(N,D) subject to fixed C via a Lagrange multiplier, yielding `N_opt ~ C^a`, `D_opt ~ C^b` (a,b from PDF, ~0.5 each) and the "~20 tokens per parameter" rule. Show the Lagrangian setup (the SP reader's wheelhouse).
  - ASCII figure: log-log loss-vs-compute line + an IsoFLOP/compute-optimal frontier sketch (plain ``` fence).
  - Tie forward: this is why the pretraining sections over-train small models and why data mixture matters (Sections 6, 7); SP analogy to a capacity-vs-data (bias-variance) tradeoff.

- [ ] **Step 3: Lint the new file.**

Run: `python viewer/tools/lint-math.py surveys/llms-for-coding/language-models-from-first-principles.md --errors-only`
Expected: `0 error(s)`. Fix any `$`-abutting-digit or display-spacing issues.

- [ ] **Step 4: Verify equations renumber cleanly.**

Run: `python viewer/tools/renumber-equations.py surveys/llms-for-coding/language-models-from-first-principles.md --check`
Expected: tags sequential, no orphans.

- [ ] **Step 5: Commit.**

```bash
git add surveys/llms-for-coding/language-models-from-first-principles.md surveys/llms-for-coding/_scratch/scaling-evidence.md
git commit -m "Add Section 3 primer: LMs from first principles (3.1-3.6) with diagrams + scaling-law math"
```

---

### Task 3: Fold FIM/pass@k into the primer (3.7-3.9); delete the old file; fix order.json

**Files:**
- Modify: `surveys/llms-for-coding/language-models-from-first-principles.md` (append 3.7-3.9)
- Delete: `surveys/llms-for-coding/conceptual-and-mathematical-fundamentals.md`
- Modify: `surveys/llms-for-coding/order.json`

- [ ] **Step 1: Move content from the old fundamentals file into the primer as subsections 3.7-3.9.** Cut:
  - old "Tokenization for Code" -> **3.7 Tokenization for code**
  - old FIM subsection -> **3.8 Fill-in-the-middle** (keep the FIM display eq; relabel its marker `eq:4-2` -> `eq:3-8a` style within the 3-x space; the new doc-order tag is assigned by renumber-equations)
  - old pass@k subsection -> **3.9 Measuring correctness: pass@k** (keep the pass@k estimator + stable-form eqs; relabel markers into the 3-x space)
  Drop the old "3.1 autoregressive objective on code" / general AR text that is now subsumed by 3.1; keep only code-specific content. Preserve all citations [1],[3],[4],[5],[6],[8],[9],[10],[11].

- [ ] **Step 2: Delete the old file and update order.json.**

```bash
git rm surveys/llms-for-coding/conceptual-and-mathematical-fundamentals.md
```
Edit `order.json`: insert `"language-models-from-first-principles.md"` immediately before `"historical-evolution.md"`, and delete the `"conceptual-and-mathematical-fundamentals.md"` entry. Resulting order: index, executive-summary, scope-and-the-code-modality, language-models-from-first-principles, historical-evolution, the-code-model-pipeline, ... references.

- [ ] **Step 3: Lint + equation check the merged primer.**

Run: `python viewer/tools/lint-math.py surveys/llms-for-coding/language-models-from-first-principles.md --errors-only` (expect 0)
Run: `python viewer/tools/renumber-equations.py surveys/llms-for-coding/language-models-from-first-principles.md --check` (expect sequential)

- [ ] **Step 4: Commit.**

```bash
git add surveys/llms-for-coding/language-models-from-first-principles.md surveys/llms-for-coding/order.json
git commit -m "Fold FIM/pass@k into primer (3.7-3.9); remove standalone fundamentals; fix order.json"
```

---

### Task 4: Renumber History (Section 3 -> Section 4)

**Files:**
- Modify: `surveys/llms-for-coding/historical-evolution.md`

- [ ] **Step 1: Update the heading and subsection numbers.** `## 3 Historical Evolution` -> `## 4 Historical Evolution`; each `### 3.x ...` -> `### 4.x ...`. Update any in-file prose that says "Section 3" referring to itself (rare). Add a one-line "Intuition." opener if helpful (optional, keep terse).

- [ ] **Step 2: Lint + bare-ref check.**

Run: `python viewer/tools/lint-math.py surveys/llms-for-coding/historical-evolution.md --errors-only` (expect 0)
Run: `python viewer/tools/validate-refs.py --bare-refs-only --severity=error surveys/llms-for-coding/historical-evolution.md` (expect clean)

- [ ] **Step 3: Commit.**

```bash
git add surveys/llms-for-coding/historical-evolution.md
git commit -m "Renumber History to Section 4 (primer takes Section 3)"
```

---

### Task 5: Cross-reference swap across all files

**Files:**
- Modify: every `surveys/llms-for-coding/*.md` that references Section 3 or Section 4 (per `_scratch/xref-map.md`).

- [ ] **Step 1: Apply the mapping from the inventory.** For each occurrence:
  - "Section 3" that meant History -> "Section 4".
  - "Section 4" that meant fundamentals/FIM/pass@k -> "Section 3".
  - Ranges: "Sections 2–4 build the foundations (the modality, the history, the math)" in the executive summary -> rewrite to reflect the new structure (e.g., "Sections 2–4 set up the foundations: the code modality (Section 2), the first-principles primer (Section 3), and the historical arc (Section 4)"). Rewrite "the math" pointer to Section 3.
  - Any "Sections 5–9" etc. that did not include 3/4 stay unchanged.
  Do this per-file with explicit Edits (do NOT blind-sed; History vs fundamentals disambiguation is semantic). The executive summary needs the most care (it enumerates the structure).

- [ ] **Step 2: Re-verify nothing references a now-nonexistent "Conceptual and Mathematical Fundamentals" title.**

Run: `grep -rn "Conceptual and Mathematical Fundamentals\|the math)" surveys/llms-for-coding/*.md`
Expected: no stale references; fix any.

- [ ] **Step 3: Lint all + bare-refs.**

Run: `python viewer/tools/lint-math.py surveys/llms-for-coding --errors-only` (expect 0)
Run: `python viewer/tools/validate-refs.py --bare-refs-only --severity=error surveys/llms-for-coding` (expect exit 0)

- [ ] **Step 4: Commit.**

```bash
git add surveys/llms-for-coding/*.md
git commit -m "Swap Section 3<->4 cross-references after primer insertion"
```

---

### Task 6: Distributed intuition + diagrams (option 3)

**Files:**
- Modify: `surveys/llms-for-coding/pretraining-data.md` (or `pretraining-objectives-and-scaling.md`), `instruction-tuning-and-alignment.md`, `reasoning-and-test-time-compute.md`

- [ ] **Step 1: Add a bold "Intuition." opener + one diagram to each, non-duplicating the primer.**
  - Pretraining: a data -> dedup/filter -> tokens -> next-token+FIM objective mermaid flow; 2-3 sentences linking to the scaling-law tradeoff (Section 3).
  - Alignment (Section 8): "Intuition." — RLHF/RL as optimizing the policy against a (here, executable) reward; DPO as a single classification loss; pointer to Section 3's training arc. Optional small mermaid (preference-pair -> loss).
  - Reasoning (Section 9): "Intuition." — test-time compute trades inference cost for accuracy (sampling and self-repair); link to the pass@1-vs-pass@k gap in Section 3.

- [ ] **Step 2: Lint + bare-refs on the three files** (expect 0 / clean), then commit.

```bash
git add surveys/llms-for-coding/pretraining-data.md surveys/llms-for-coding/instruction-tuning-and-alignment.md surveys/llms-for-coding/reasoning-and-test-time-compute.md
git commit -m "Distributed newcomer intuition + diagrams in pretraining/alignment/reasoning"
```

---

### Task 7: Update index.md TOC

**Files:**
- Modify: `surveys/llms-for-coding/index.md`

- [ ] **Step 1: Rewrite the numbered TOC.** Insert `3. [Language Models from First Principles](language-models-from-first-principles.md)`; renumber History to `4.`; remove the standalone `Conceptual and Mathematical Fundamentals` line; keep 5-18 as-is; References stays 19. Update the abstract paragraph if it mentions the section structure.

- [ ] **Step 2: Commit.**

```bash
git add surveys/llms-for-coding/index.md
git commit -m "TOC: add Section 3 primer; History -> 4; drop standalone fundamentals"
```

---

### Task 8: Cross-link init pass + full /check-survey gate

**Files:** all survey files (anchors/citations regenerated in place).

- [ ] **Step 1: Run the init pass.**

```bash
python viewer/tools/renumber-sections.py   surveys/llms-for-coding --init
python viewer/tools/renumber-paragraphs.py surveys/llms-for-coding --init
python viewer/tools/link-references.py      surveys/llms-for-coding --init
```

- [ ] **Step 2: Run the full gate (the 8 /check-survey steps).**

```bash
F=surveys/llms-for-coding
python viewer/tools/lint-math.py $F --errors-only
for f in $F/*.md; do python viewer/tools/renumber-equations.py "$f" --check; done
python viewer/tools/link-references.py $F --check
python viewer/tools/renumber-paragraphs.py $F --check
python viewer/tools/renumber-sections.py $F --check
python viewer/tools/validate-refs.py $F
python viewer/tools/validate-refs.py --bare-refs-only --severity=error $F
python viewer/tools/check-citation-sources.py $F/references.md
```
Expected: lint-math 0 errors; equations sequential; links up to date; paragraphs clean; sections clean; validate-refs 0/0; bare-refs exit 0; citation-sources 0 errors.

- [ ] **Step 3: Commit any anchor/citation churn.**

```bash
git add surveys/llms-for-coding
git commit -m "Cross-link sync after primer insertion (sections/paragraphs/citations)"
```

---

### Task 9: Verify cross-refs resolve + citation-audit the new refs

**Files:** none modified unless a fix is needed; report to `reports/`.

- [ ] **Step 1: Verify every "Section N" mention points to a real section.**

Run: `grep -rnoE "Section [0-9]+" surveys/llms-for-coding/*.md | sort -u`
Check the max N <= 19 and each refers to the intended section (spot-check History=4, primer=3, pass@k inside 3). Fix any stragglers.

- [ ] **Step 2: Citation-audit the new references [54]+** (adversarial, against the acquired PDFs): verify the Transformer attention equation, the Kaplan exponents, the Chinchilla parametric-loss constants + compute-optimal rule, and RoPE's claim are each reproduced exactly from their source loci. Under ultracode, run this as a small fan-out verification workflow grouped by source file. Record results in `reports/citation-audit-foundations-2026-06-13.md`. Any mismatch -> fix the survey number + file a `bugs/` entry.

- [ ] **Step 3: (Optional) visual smoke check** — start the viewer and confirm the primer renders, mermaid diagrams draw, and KaTeX shows the scaling-law equations.

```bash
node viewer/serve.js surveys/llms-for-coding -p 4500   # then open the primer in a browser
```

---

### Task 10: Final commit + push

- [ ] **Step 1: Confirm clean gate + push.**

```bash
git status -sb
git push origin main
```
Expected: working tree clean; push succeeds (retry once if an LFS lock-verify EOF blip occurs).

- [ ] **Step 2: Update the session log** `prompts/2026-06-13-llms-for-coding-survey.md` with a Conversation entry summarizing the enrichment, and commit/push.

---

## Self-Review (run after writing)

- **Spec coverage:** 3.1-3.5 (basics/structures/training) = Tasks 2; 3.6 scaling math = Task 2 Step 2; folded 3.7-3.9 = Task 3; distributed = Task 6; diagrams = Tasks 2/6; citations = Task 0; renumber (History 3->4 only) = Tasks 3-5,7; verification = Tasks 8-9. All spec sections covered.
- **Placeholder scan:** scaling-law exponents are intentionally deferred to Task 0 Step 3 extraction (citation-integrity), not placeholders — the plan forbids writing any unverified number.
- **Consistency:** new file slug `language-models-from-first-principles.md` used identically in Tasks 2,3,7,8; eq-id 3-x space used consistently; "Section 3 = primer, Section 4 = History" mapping consistent across Tasks 4,5,9.
