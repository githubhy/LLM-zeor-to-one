# Field Notes — 2026-07-02 — RIS program (A2/C/A3/B1/B2) execution

## Context
Ran five `reference-implementation-study` tracks in proposed mode, autonomously, on an offline
Apple-Silicon host reached only via a local HTTPS proxy. Several infra/execution hazards were found
and resolved inline; none warranted a bug (env-specific, not code defects), but they share a theme —
**offline / scaled-substrate execution hazards** — worth retrospecting.

## Issues found and resolved
- **Handoff citation drift → caught by reading the source.** The MI-RIS handoff said "EAP-IG lifts
  IOI faithfulness from ~0%"; the acquired PDF (Hanna §4.3) shows IOI is EAP≈EAP-IG≈0.6 and the ~0%
  catastrophe is *SVA*. Reading the PDF before pre-registering hypotheses caught it (filed bug
  `2026-07-02-04`). Lesson: the citation-integrity "read before you cite" rule catches drift in the
  repo's *own* prior artifacts, not just external memory.
- **SSH push auth broken → HTTPS-via-proxy workaround.** `git push` over the SSH remote hung twice
  (3 min, 6 min); root cause was `Permission denied (publickey)` (SSH key/agent not loaded), not the
  network. HTTPS to github via the proxy worked (200/1.4 s); `gh auth setup-git` + push to the
  explicit HTTPS URL succeeded. **origin remote left unchanged (still SSH)** — the SSH-key issue is
  the user's to fix; don't silently rewrite their remote.
- **1.4 GB `features.npz` committed → caught by GitHub's 100 MB limit.** The B2 SigLIP feature cache
  (432×1024×768 f32 = 1.4 GB) got swept into `git add artifacts/connector-ablation/`. GitHub's
  pre-receive rejected the push; removed from the tip commit (`--amend`), gitignored the cache path.
  Lesson: `git add <dir>/` over an artifacts dir can grab regenerable caches — gitignore cache files
  at creation, not after the push bounces.
- **B1 attention OOM (42 GB) → resolution tuning.** `output_attentions=True` on 1088 image tokens
  materialises all 30 layers of (T,T) attention ≈ 42 GB on a 16 GB box (silent thrash, 12 min no
  progress). Fixed by `do_image_splitting` + `size={"longest_edge":768}` → 320 tokens / 0.1 GB.
  Lesson: VLM attention memory is quadratic in the (large) image-token count × layers × heads —
  budget it before enabling `output_attentions`.
- **B2 synthetic task too easy → 3 task redesigns.** Color, then quadrant, then left/right binding —
  each was aced at q=1 because SigLIP features are position-rich and the label space tiny. Settled
  on an honest null result rather than engineer a task to force a positive. Lesson: on a
  high-capacity frozen encoder, toy tasks won't stress a connector's token budget; the survey's
  detail-vs-budget claim genuinely needs DocVQA/TextVQA-scale detail (deferred).

## Patterns / lessons
- **Read the acquired source before pre-registering any hypothesis** — it caught a drift in our own
  handoff, exactly the failure the citation-integrity rule guards.
- **Diagnose "slow/hung" by its actual cause**, not the seductive one: the push wasn't "network", it
  was SSH auth; the B1 hang wasn't "slow CPU", it was a 42 GB allocation.
- **Gitignore regenerable caches at write time.** A single `git add <dir>/` can smuggle a multi-GB
  cache past local commit and only fail at the remote.
- **Prefer an honest null result over a rigged positive** (B2) — and root-cause every divergence from
  the paper (A2 §7, A3 §7, B1 §7) into named modelling gaps, never hand-wave.
