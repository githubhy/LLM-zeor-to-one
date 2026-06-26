Sync harness-config updates from the upstream template repo into this repo, re-adapting each change from the wireless/5G-NR / telecom-3GPP domain to this project's LLM/AI deep-research-survey domain: $ARGUMENTS

`$ARGUMENTS` (all optional):
- *(empty)* — sync every config delta since the last high-water mark.
- `--dry-run` — do steps 0–1 only; report the deltas + classification, change nothing.
- `<commitish>..<commitish>` — sync a specific upstream range instead of `<baseline>..HEAD`.

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

This repo ported the full math/cross-link toolchain into `viewer/tools/`: `lint-math.py`, `validate-refs.py`, `renumber-equations.py`, `renumber-sections.py`, `renumber-paragraphs.py`, `link-references.py`, `check-citation-sources.py`, `check-report-completeness.py`, `build-index.py`, `init-doc.py`, `split-markdown.py`, `verify.py`. **Not yet ported** from upstream (mark "once ported / lands with the toolchain" if a delta touches them): `check-footnote-refs.py`, `crosslink.py` (+ `test_crosslink.py`). If a delta adds/changes one of these and it is self-contained (stdlib-only), port it verbatim. If a delta changes an already-ported tool, re-apply the change directly (these are domain-agnostic Python — no remap needed beyond docstring examples).

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
