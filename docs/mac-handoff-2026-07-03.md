# Mac handoff — 2026-07-03

Everything is committed and pushed to `origin/main` (`01f7e66`); all **191 LFS files**
(PDFs in `download/` + trained `.pt` weights in `artifacts/`) are on origin. A Mac
gets the complete state with a clone + `git lfs pull`. This note is the setup +
"what's next" so the work continues cleanly on the Mac (which, unlike this
Windows/CPU box, has MPS and is the intended compute host — decision `2026-07-02-04`).

## Setup on the Mac

```bash
git clone <origin-url> LLM-zeor-to-one && cd LLM-zeor-to-one
git lfs pull                                  # materialize the 191 LFS blobs (weights + PDFs)

# Re-wire the pre-push gate — core.hooksPath is LOCAL git config, NOT committed,
# so it does not transfer with the clone. The hook auto-detects python (python3
# works natively on macOS — no Store-stub issue).
git config core.hooksPath .githooks           # or: bash scripts/install-git-hooks.sh

# Deps (a venv is fine). macOS torch ships with MPS.
python3 -m pip install torch transformer_lens transformers datasets einops scikit-learn pymupdf

# Verify the reproduction (G1 gate) + the reproduce recipe in the report §12:
PYTHONPATH=implementation python3 -m pytest tests/tiny_transformer -q
```

**MPS speedup:** the toy configs hardcode `device="cpu"`
(`implementation/tiny_transformer/config.py` `ModelConfig`/`TrainConfig`, and
`run_phase*.py`). On the Mac set `device="mps"` for training/analysis; GPT-2 loads
via `HookedTransformer.from_pretrained("gpt2", device="mps")`.

## What's here (the completed induction study)

- `implementation/tiny_transformer/` — model builder + first-party train loop +
  circuit extraction + the Phase-4 MI-observable suite; `run_phase{3,4,4b,5}.py`.
- `tests/tiny_transformer/test_core.py` — the G1 gate (9 tests).
- `artifacts/induction-tiny/` — trained weights + per-phase JSON summaries + manifest.
- `docs/tiny-transformer-induction-study.md` — the 14-section report (all gates
  PASS; §10 red-team; §11 roadmap; §12 reproduce recipe).

## What's next (the backlog)

Single index: **`todos/2026-07-03-blocked-backlog-consolidated.md`** (the umbrella).
The Mac unblocks most of it:

1. **Deferred hypotheses (the study's §11 roadmap), now MPS-feasible at scale:**
   - Cheap anywhere: **H19** illusion (cross-corpus head-role census), **H17** +MLP
     privileged basis.
   - Want scale (the report defers these precisely because the toy's distributed
     circuit gives weak localization): **H15** automated discovery (ACDC/EAP/EAP-IG;
     the concurrent session's `implementation/eap_ig/` is a head start), **H16**
     DAS/IIA, **H18** IOI — all on GPT-2-small, feasible on MPS.
   - **H9** in-context-regression sub-study — its source gate is **cleared** (the 4
     papers `vonoswald-…`, `akyurek-…`, `dai-…`, `garg-…` are in `download/`).
2. **`todos/2026-07-02-tiny-transformer-gpu-host-rungs.md`** — Rung 2 mini-GPT-2
   (~10M from scratch), full-scale Rung 1 (`n_ctx=256`/20k/≥5 seeds), auto-interp.
3. **`todos/2026-07-01-gpt2-training-reproduction.md`** — GPT-2 124M from scratch
   (still wants a multi-GPU host; MPS is likely too slow for 124M from scratch).
4. **The RIS-program follow-ups** (`eap-ig-`/`steering-`/`fastv-`/`sae-frontier-followups`,
   `connector-ablation`) — the *other* session's studies, whose intended host is the
   Mac (Gemma-2 / GemmaScope / real-VQA); pick up per their own todos.

## Housekeeping

- Local-only safety branches `backup/pre-reconcile-2026-07-02` / `-03` do **not**
  transfer (they're fully subsumed by `origin/main`); safe to delete.
- Infra fixed this session: the pre-push validation gate (bug `2026-07-02-03`) now
  chains git-lfs + auto-detects python and is active via `core.hooksPath`.
