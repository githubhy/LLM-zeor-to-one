# Conversation Log — 2026-07-02 — session: branch-cleanup

## Conversation 1
- **Request**: "clean up the local branches"
- **Actions**: Surveyed local branches (`main`, `survey/mechanistic-interpretability`). `git fetch --prune` showed `origin/survey/mechanistic-interpretability` **deleted** on the remote and `origin/main` advanced `76c61a7..1dd786b` (14 commits). Verified the survey branch was **squash-merged** into `origin/main` (tips `bc823b0`/`02ad061`/`c7beedd`/`82cf6cb`); the only lines "unique" to the branch were stale versions of content `origin/main` carries in newer form (appendix-c expanded +182, todos/INDEX rows updated) — nothing lost. Switched to `main` (carrying an uncommitted Conversation-19 log edit in `prompts/2026-06-28-qkv-index-notation-fold.md`, which is identical on both branches and untouched by the incoming commits → no conflict), fast-forwarded `main` to `origin/main` (1dd786b), then `git branch -D survey/mechanistic-interpretability` (was 7b94007).
- **Result**: Only `main` remains, in sync with `origin/main`. Deleted branch's tip `7b94007` stays in reflog ~90 days if ever needed. The prior session's uncommitted log edit is preserved untouched in the working tree.
- **Findings**: `git branch --merged main` did **not** flag the survey branch (squash-merge produces no merge-base ancestry), so `-d` would have refused it; the correct evidence that it was safe to delete was "remote branch deleted + content present in origin/main," not the `--merged` list.

## Conversation 2
- **Request**: "commit the log edit, then what's the next RIS?"
- **Actions**: Committed the pending Conv-19 log edit + this session log on branch `docs/session-logs-2026-07-02` (not main, to keep local main == origin/main). Surveyed RIS handoffs.
- **Result**: Next RIS = **EAP-IG faithfulness** (mechinterp candidate 2), the only laptop-runnable one (GPT-2-small = its actual substrate); A3/B1/B2 GPU-gated.

## Conversation 3
- **Request**: "what are the options of RIS?" then "what are the options of the RIS itself such as proposed mode?"
- **Actions**: Enumerated the 5 candidate studies (mechinterp A2/A3 + multimodal B1/B2 + SAE-followons C), and the RIS skill's 3 modes (`original`/`proposed`/`flags:`) + the 13-item lattice.
- **Result**: Menu delivered; recommended `proposed` for EAP-IG.

## Conversation 4 — RIS program (A2,A3,B1,B2,C) in proposed mode
- **Request**: `/goal` — run `reference-implementation-study` proposed on A2,A3,B1,B2,C autonomously, commit each step, push→PR→merge. (ultracode / xhigh.)
- **Actions**: Probed host: **offline except a local proxy** (127.0.0.1:10086; HF reachable ~214 KB/s), MPS-only/16 GB, GPT-2+wikitext cached, no Gemma/VLM. AskUserQuestion → user chose GPT-2-small for A3 and "fix the network" for B1/B2 → downloaded **SmolVLM-256M** (real VLM) via the proxy. Decision `2026-07-02-04` records per-track substrate scope. Then executed 5 genuine studies:
  - **A2 EAP-IG** (GPT-2-small, faithful): built + *verified* residual-node attribution harness (faith(full)=1/empty=0 exact); G1-G4+REPORT all PASS. EAP-IG > EAP +0.224 (p=3.6e-34), ρ=0.92 vs 0.46. Node-vs-edge divergence from Hanna Fig3 root-caused (§7). Bug `2026-07-02-04` (handoff memory-drift on IOI) filed+fixed.
  - **C SAE-ext**: BatchTopK/Matryoshka/AdaptiveJumpReLU on the verified sae_frontier base; red-team REFUTED (TopK stays best); orthonormal shrinkage curve; bug `2026-07-02-01` closed w/ regression test.
  - **A3 steering** (GPT-2): diff-in-means > prompting > SAE-clamp; SAE-clamp-worst reproduces AxBench (verified vs PDF), prompting/diffmean flip root-caused; G1 PASS.
  - **B1 FastV** (real SmolVLM-256M): H1 attention-collapse confirmed (68×), H4 Eq-5 FLOP confirmed, **H3 refuted** (attn-rank < random on redundant task) root-caused; G1 PASS.
  - **B2 connector** (real-but-tiny, frozen SigLIP + MLP vs Q-Former): in progress at log time.
  - Per-study followup todos filed; both survey→RIS handoffs closed.
- **Result**: 4 studies committed (8 commits on `study/ris-program-2026-07-02`); B2 + finalize (push/PR/merge) pending.
- **Findings**: Citation-integrity caught its own precedent — the mechinterp handoff's "EAP-IG lifts IOI from ~0%" was a memory drift (paper: IOI EAP≈EAP-IG≈0.6; the ~0% catastrophe is SVA). Reading the acquired PDFs (Hanna, AxBench, FastV) before each study prevented propagating drift into hypotheses.

<!-- LOG-END -->
