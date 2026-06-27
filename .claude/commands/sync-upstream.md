Sync harness config between this repo and the upstream template repo (`../data-channel-receiver`). **Default = inbound** (upstream → here), re-adapting each change from the wireless/5G-NR / telecom-3GPP domain to this project's LLM/AI deep-research-survey domain. **`--back` = outbound sync-back** (here → upstream); see the Reverse section. The two directions are **asymmetric** — this is not a symmetric mirror. $ARGUMENTS

`$ARGUMENTS` (all optional):
- *(empty)* — INBOUND: sync every upstream config delta since the last high-water mark.
- `--dry-run` — do steps 0–1 only; report the deltas + classification, change nothing.
- `<commitish>..<commitish>` — sync a specific upstream range instead of `<baseline>..HEAD`.
- `--back` — OUTBOUND (reverse): prepare generic improvements from THIS repo onto an upstream branch. Runs the Reverse procedure below, not steps 0–4. Never pushes to the upstream remote without explicit go-ahead.

## What this is

This project's Claude harness was bootstrapped by adapting a **shared research harness** from the upstream template repo (`../data-channel-receiver`, a wireless/5G-NR / telecom-3GPP survey project) and retargeting it telecom → LLM/AI surveys. This command is the manual, idempotent re-sync. It ports *harness config* (rules/skills/commands/agents/settings/hooks/tools, `CLAUDE.md`/`AGENTS.md`), **never research content** (the upstream's own surveys/reports/decisions are wireless deliverables, not shared config). See the `claude-infra-ported-from-data-channel-receiver` memory.

## 0. Resolve upstream + baseline

Read `.claude/upstream-sync.json`:
- `upstream_path` — the upstream working copy (default `../data-channel-receiver`).
- `last_synced_commit` — the upstream SHA this repo was last synced through (the high-water mark).

If the upstream working copy may be stale, `git -C <upstream_path> fetch` first (or note that the local clone is the source of truth).

## 1. Find config deltas (not content)

```bash
UP="$(python3 -c "import json;print(json.load(open('.claude/upstream-sync.json'))['upstream_path'])")"
BASE="$(python3 -c "import json;print(json.load(open('.claude/upstream-sync.json'))['last_synced_commit'])")"
git -C "$UP" log --oneline "$BASE"..HEAD                      # every upstream commit since the mark
git -C "$UP" diff --name-status "$BASE"..HEAD -- \
    CLAUDE.md AGENTS.md .claude viewer/tools .githooks scripts requirements.txt
```

- **Skip round-tripped sync-back commits.** A commit whose subject contains `from llm-zero-to-one` (the reverse-sync template, R3 below) is a change that originated HERE and was pushed out — do **not** re-adapt it back in (it already lives here, ungenericized). Filter it: `git -C "$UP" log --oneline "$BASE"..HEAD | grep -vi 'from llm-zero-to-one'`. If the range is *only* sync-back commits, there is nothing to import — advance the mark (step 4) to skip past them and stop. (A *sibling* repo's sync-back — e.g. a subject saying `from pitch-perfector` — is a **legitimate** inbound delta for this repo, since it did not originate here; do not skip those.)
- **Config paths to consider:** `CLAUDE.md`, `AGENTS.md`, `.claude/**` (rules, skills, commands, agents, settings, hooks, scripts), `viewer/tools/**`, `.githooks/**`, `scripts/**`, `requirements.txt`.
- **Exclude as content** (the upstream's domain work — do NOT sync): `surveys/`, `docs/`, `reports/`, `decisions/`, `bugs/`, `todos/`, `field-notes/`, `prompts/`, `plans/`, `proposals/`, `sim/`, `octave/`, `download/`, `theories/`, `wikis/`, `archives/`, and any wireless-specific tooling under those.
- For each changed config file, read the actual diff: `git -C "$UP" show "$BASE"..HEAD -- <file>` (or per-commit). Classify each: **modified**, **added** (new skill/rule/command), or **deleted**.

If `--dry-run`: stop here and report the deltas + classification.

## 2. Port deltas — re-adapt, never overwrite

Each existing config file is already an **adapted, LLM-domain** version carrying local fixes. **Do not copy the upstream file wholesale** — that reintroduces wireless examples and clobbers local adaptations.

- **Modified file:** apply the *equivalent* change to the local file, re-adapting per the mapping below. Genericize upstream provenance (bug IDs like `2026-05-25-01`, plan filenames, worked-instance report paths) that does not exist here. Preserve local adaptations and graceful-degradation notes.
- **Added file** (a brand-new upstream skill/rule/command/agent): adapt the whole file (read source + mapping → write adapted target), as in the original bootstrap. Add it to the relevant catalog in `CLAUDE.md`. For a large multi-file addition, consider a Workflow fan-out (one agent per file, adversarial verify) like the bootstrap used.
- **Deleted file:** confirm intent, then remove the local counterpart only if it is a pure mirror with no local-only value.

### Domain mapping (wireless/5G-NR / telecom-3GPP → LLM/AI surveys)

| Upstream | This repo |
|---|---|
| Staff Wireless Algorithm Designer | Staff LLM/AI Research Engineer |
| LDPC / IRC / channel-coding methods & studies | LLM methods: transformer & attention architectures, pretraining & scaling laws, SFT/RLHF/DPO/RLAIF/PEFT/LoRA, RAG, agents & tool use, inference & serving (KV-cache, quantization, speculative decoding, batching), evaluation & benchmarks, long-context, multimodal, safety & interpretability |
| 3GPP specs (TS/TR), `docs/specs/3gpp/` | papers + model cards + technical reports (arXiv, vendor cards, eval harnesses); formal specs (e.g. Model Context Protocol) under `docs/specs/`; source-tags `local: download/` for papers, `spec: docs/specs/` for specs |
| BLER/FER; Wilson/Clopper–Pearson rate CIs | benchmark metrics (accuracy, pass@k, perplexity, win-rate; MMLU/GSM8K/HumanEval/MT-Bench); bootstrap + binomial/Wilson CIs |
| FLL/PLL/KF tracker params (K_f, ρ, lag D, channel) | model/training hyperparams: $d_{\text{model}}$, layers $L$, heads $h$, context length, token/compute budget $N$/$D$, LR schedule, batch size, temperature, top-p |
| spec-vs-sim conformance matrix | benchmark-and-eval-protocol conformance matrix (harness/version, few-shot $k$, decoding params) |
| octave / `.m` simulation | Python (numpy/pytorch/transformers) experiment; `.jsonl` eval traces; `.npz`/`.csv` results |
| LDPC `tanh(L/2)=∏tanh(L_j/2)` worked equation | an LLM equation (scaled dot-product attention / softmax / a scaling-law power law) |

Full provenance: the `claude-infra-ported-from-data-channel-receiver` memory and `decisions/2026-06-17-01-viewer-wholesale-sync-from-upstream.md`.

### Tooling reality (graceful degradation)

This repo ported the full math/cross-link toolchain into `viewer/tools/`: `lint-math.py`, `validate-refs.py`, `renumber-equations.py`, `renumber-sections.py`, `renumber-paragraphs.py`, `link-references.py`, `check-citation-sources.py`, `check-report-completeness.py`, `check-footnote-refs.py`, `crosslink.py` (+ `test_crosslink.py`), `build-index.py`, `init-doc.py`, `split-markdown.py`, `verify.py`. The toolchain is **complete** — there is no longer a "not yet ported" backlog. If a delta changes an already-ported tool, re-apply the change directly (these are domain-agnostic Python — no remap needed beyond docstring examples). If a delta adds a brand-new self-contained (stdlib-only) tool, port it verbatim.

## 3. Verify

```bash
# Leakage: no wireless/telecom terms may survive in ported config.
# Expected self-hits (NOT leakage): this command file's own mapping table + grep,
# and upstream-sync.json's provenance note — exclude them and read the rest.
grep -rniE 'ldpc|3gpp|\birc\b|harq|\bofdm\b|otfs|\bntn\b|\b5g\b|wireless|\bfll\b|\bpll\b|beamform|zadoff|\bisac\b|\bbler\b' \
    CLAUDE.md AGENTS.md .claude/ viewer/tools/ \
    | grep -vE '\.claude/commands/sync-upstream\.md|\.claude/upstream-sync\.json'
python3 -m py_compile <any changed .py>        # Python still compiles
python3 -m json.tool <any changed .json> >/dev/null   # JSON still valid
```

Confirm rule/skill/dir names still match `CLAUDE.md`'s canonical catalogs. If a `viewer/tools/*.py` changed, run the relevant `viewer/tools/test_*.py` (or `/check-survey surveys/attention-demo` as the end-to-end gate).

## 4. Record + advance the mark

- Update `.claude/upstream-sync.json`: set `last_synced_commit` to the upstream HEAD SHA just synced and `last_synced_date` to today.
- Append a `prompts/` conversation-log entry citing the upstream SHAs ported.
- Per Todo Capture, file a `todos/` entry for any delta you could **not** fully port this pass.
- Commit (`chore: sync upstream config deltas from data-channel-receiver`) listing the upstream SHAs; push only if the user asks.

## Reverse — sync-back (here → upstream) [`--back`]

The OUTBOUND direction: push generic harness improvements developed HERE back to the upstream template. **Asymmetric** to the inbound flow — different discovery, transform, and safety profile. The inbound flow *re-adapts domain in*; this *strips provenance out*. Run this only on `--back`.

### R0. Discover candidates (no mark — a classification sweep)

There is no high-water mark for this direction. Diff the **generic surface** and classify each differing / here-only file (a fan-out classifier agent is worth it for a large surface — keep it read-only):

```bash
UP="$(python3 -c "import json;print(json.load(open('.claude/upstream-sync.json'))['upstream_path'])")"
for d in viewer/tools viewer/lib viewer/serve.js viewer/viewer.js viewer/index.html viewer/style.css \
         .claude/rules .claude/skills .claude/hooks .claude/commands .claude/agents scripts .githooks .gitignore CLAUDE.md; do
  diff -rq "$d" "$UP/$d" 2>/dev/null | grep -vE 'node_modules|__pycache__|\.pyc|test-results|\.DS_Store'
done
```

Bucket each delta — only the first is a candidate:

- **SYNC-BACK** — a net-new generic capability or bug fix made HERE that upstream lacks, **not** domain-specific and **not** mere provenance genericization.
- **SKIP-not-ours** — a generic capability that reached HERE by importing it from a *sibling* repo (e.g. a `/sync-upstream from ../pitch-perfector` catch-up). It did not originate here; it should travel to upstream via its origin repo's own `--back` (or already did). Do not re-export it.
- **SKIP-genericization** — the only diff is that HERE re-domained upstream's wording (telecom → LLM). Re-syncing would re-domain upstream's *own* files. The dominant bucket; skip.
- **SKIP-domain** — LLM-specific content (figure-operating-conditions table, add-dataset / eval-benchmark vocab, crosslink-scope, agent descriptions, test fixtures). Skip.
- **SKIP-upstream-newer** — upstream has more; that's an inbound import, not a sync-back.

### R1. Port — strip provenance; surgical on diverged files

Inverse of the inbound re-adaptation:

- **End-to-end-generic file** (no domain refs — a brand-new tool + its tests, a shell hook) → copy wholesale.
- **Diverged file** (a tool or doc that differs only by genericization) → apply the change as a **surgical seam edit** against upstream's actual text. Do **not** overwrite the file (that would re-domain it to LLM and clobber upstream's adaptations).
- **Strip HERE provenance** from anything copied: local bug/decision IDs, dated worked-instances, LLM paths in test fixtures. Rewrite test fixtures with neutral data rather than importing LLM labels (e.g. augment upstream's own test, don't replace it).

### R2. Verify against upstream's own suites

From `<upstream>`: run the affected `viewer/tools/test_*.py` (`python3 -m pytest viewer/tools` or the per-tool runner) and any viewer test suite the change touches. **Test-completeness:** grep the source repo's test surface for the moved symbols and confirm each related test landed upstream — `grep -rl '<MovedSymbol>' viewer/tools` here, then verify each file exists upstream.

### R3. Branch + confirm-before-push + open the PR (with provenance)

Prepare on upstream branch `sync-from-llm-zero-to-one`; stage **only** the generic sync files; leave upstream's own WIP untouched. Commit there with the subject template below (the inbound skip-guard keys on the `from llm-zero-to-one` phrase):

```
feat: sync generic harness improvements from llm-zero-to-one
```

**Never stage this repo's audit trail** (`decisions/`, `bugs/`, `todos/`, `field-notes/`, `reports/`, `plans/`, `prompts/`) into the sync-back — it is domain/provenance content (the same category the inbound flow excludes), it would clash with upstream's own decision numbering, and the *why* belongs in the PR description + code comments (which travel with the code), not in upstream's tree.

**Do not push** without explicit user go-ahead (separate `FenLinger/data-channel-receiver` remote). On go-ahead: `git -C "$UP" push -u origin sync-from-llm-zero-to-one`, then **open the PR** with `gh pr create -R FenLinger/data-channel-receiver --base <default-branch> --head sync-from-llm-zero-to-one` (don't just surface the `pull/new/…` link — create it). The PR **body must include**:

- the ported items (what + why each is generic), the verification (tool tests), and what was deliberately excluded; **and**
- a **Provenance** section that links back to THIS repo's source records **by reference** — `decisions/<feature-id>` + `decisions/<this-sync-back-id>` + any `bugs/<id>` — stating the audit-trail docs were intentionally *not* copied, and that upstream may author its own decision on merge.

Surface the created PR URL.

### R4. Close the loop — round-trip hygiene

- File a `decisions/` entry HERE listing what was synced + the branch.
- **After the user merges the PR**, advance `last_synced_commit` in `.claude/upstream-sync.json` to the post-merge upstream HEAD — otherwise the next INBOUND run diffs `BASE..HEAD` and re-detects the round-tripped commit as a "new upstream delta." The step-1 `from llm-zero-to-one` filter is the backstop if the mark wasn't advanced in time.
