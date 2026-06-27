Add an evaluation benchmark / dataset to `download/datasets/`: $ARGUMENTS

Expected `$ARGUMENTS` form: `<benchmark-name> [<subset/version>]`
Examples:
- `mmlu` — the full MMLU 57-subject multiple-choice benchmark (the default whole-dataset case)
- `swe-bench Verified` — the human-validated `Verified` subset of SWE-bench
- `humaneval` — the 164-problem HumanEval code-generation set
- `gpqa main` — the `main` split of GPQA (a gated, contamination-controlled set)

Workflow:

1. **Parse arguments**: extract the benchmark name and optional subset / version from `$ARGUMENTS`. Normalise the name against the registry table below (case-insensitive; `mmlu`, `MMLU`, `mmlu-test` resolve to the same row). If the user gave a dataset-hub URL (HuggingFace `datasets`, a GitHub release) or an archive filename instead, derive the benchmark + subset from it. If anything is ambiguous — or the name is not in the registry — ask the user before proceeding.
2. **Acquire**. LLM eval sets split into two acquisition classes; pick the branch from the registry table's **Acquisition** column.
   - **Openly fetchable** (e.g. MMLU, GSM8K, HumanEval, MBPP, HellaSwag, MMLU-Pro, BBH): download the archive into the gitignored dataset cache and record its sha256:
     ```bash
     mkdir -p download/datasets/_cache
     # HuggingFace datasets snapshot, a GitHub release tarball, or a direct file:
     curl -L -o download/datasets/_cache/<benchmark>-<subset>.zip "<source-url>"
     shasum -a 256 download/datasets/_cache/<benchmark>-<subset>.zip
     ```
     When the dataset tool is present (see Tooling below), prefer it over raw `curl`:
     ```bash
     python viewer/tools/fetch_dataset.py --add <benchmark> [<subset>]   # once ported
     ```
   - **Gated / contamination-controlled** (e.g. GPQA — request access + canary; a benchmark's hidden/blind test split; a leaderboard-only eval): the archive **cannot** be auto-downloaded. Print the registry row's **Acquisition** note (the access-request / gated-repo URL), then **guide the user to place the archive** at the known cache path and continue from there:
     ```
     Place the GPQA archive at:  download/datasets/_cache/gpqa-main.zip
     (request access on the gated HuggingFace repo; this command will register it, not fetch it.)
     ```
     Once the file is at that path, compute its sha256 with `shasum -a 256 download/datasets/_cache/<benchmark>-<subset>.zip` and proceed to step 3. Never invent a download URL for a gated set, and never fabricate a sha256.
3. **Record the MANIFEST row** in `download/datasets/MANIFEST.md`. The table columns are:
   `benchmark | subset | items | format | license | local-path | sha256 | citation`
   - `benchmark` / `subset` — the normalised name and subset (or `—` for whole-dataset).
   - `items` — count of scored units (e.g. `14042 questions`, `164 problems`, `1319 test`, `80 prompts`); from the registry or counted after extraction.
   - `format` — ground-truth format(s): `MC (Q + 4 choices + answer)`, `code (prompt + tests, pass@k)`, `gen + reference (LLM-judge)`, `CoT + numeric answer`, etc.
   - `license` — the exact licence string (`MIT`, `Apache-2.0`, `CC BY 4.0`, `CC BY-SA`, `gated / request-access`); never `unknown` — if you cannot determine it, stop and ask.
   - `local-path` — the gitignored cache path (`download/datasets/_cache/<benchmark>-<subset>.zip`). The archive itself is **not** tracked (see Conventions); the MANIFEST row is the tracked anchor.
   - `sha256` — the digest from step 2. This anchors the exact bytes acquired.
   - `citation` — the canonical citation tag (see Citation form below) plus the primary reference, e.g. `[MMLU] Hendrycks et al. (2021)`.

   Three cases mirror the source-acquisition workflow:
   - **New benchmark entirely**: append a new row at the end of the main table.
   - **New subset / version of a benchmark already present**: insert directly below the existing row(s) for that benchmark (keeps a benchmark's subsets grouped). Note in the README's "Notes" section if multi-subset tracking for this benchmark is new.
   - **Replacing an old version** (the user said "bump SWE-bench → SWE-bench Verified", "MMLU → MMLU-Pro"): keep the old row only if backward citations still point at it; otherwise delete the old row + recompute, then add the new row, and update inline citations across the repo (`grep -rn "SWE-bench (full)"` etc.).
4. **Add the benchmark to the registry note** if it is not already one of the common eval sets documented in `download/datasets/README.md` — append a one-line description of what it provides (task coverage + metric) so the next author does not re-derive it.
5. **Contamination hygiene**. LLM eval sets carry a concern audio corpora do not: **train/test contamination**. If the benchmark ships a canary GUID or a "do not train on this" clause, record it in the README, and never fold a benchmark's test answers into a training/few-shot corpus that a model under evaluation has seen. A held-out / blind split must never be committed in the clear.
6. **Verify**:
   ```bash
   python viewer/tools/check-citation-sources.py download/datasets/MANIFEST.md   # validates the source-tag invariant
   ```
   Also verify by hand: re-run `shasum -a 256` on the cache path and confirm it matches the MANIFEST row's `sha256`, and confirm the `license` and `citation` cells are both non-empty. The verification contract is: **every benchmark row carries a present-on-disk archive whose sha256 matches, plus a non-empty licence and citation** — the strong `(local: download/datasets/<path>)` form of the `references.md` ↔ `download/` invariant from `citation-integrity.md`.
7. **Stage and report**:
   ```bash
   git add download/datasets/MANIFEST.md download/datasets/README.md
   ```
   (The archive under `_cache/` is gitignored and is **not** staged — only the MANIFEST + README are tracked.) Report the item count, archive size, sha256, the licence, and the source URL (or the access-request URL for gated sets). Suggest a commit message of the form:
   `data(datasets): add <Benchmark> [<subset>] (<task coverage>)`
   or, when bumping:
   `data(datasets): bump <Benchmark> <old-version> → <new-version>`

Conventions to follow (from `download/datasets/README.md` and `.claude/rules/citation-integrity.md`):

- **Only the MANIFEST + README are tracked**; the archive (and any extracted data) live in the gitignored `download/datasets/_cache/`, re-fetchable (openly) or re-obtainable (gated) on any clone. Large data files are gitignored repo-wide — force-add only a tiny unit-test fixture with `git add -f tests/fixtures/<sample>.jsonl` when one is genuinely needed.
- **sha256 anchors everything** — re-running the verify step after any re-fetch catches a corrupted or silently-updated archive (benchmarks do get re-released under the same name — split fixes, decontamination passes, answer-key corrections).
- **Licence is mandatory and load-bearing** — a benchmark row with no licence is a citation-integrity violation, not a TODO. Gated sets must never be committed in the clear; only their MANIFEST row (which contains no gated bytes) is tracked.
- **Citation form** in surveys / plans / reports: `[MMLU]` for the whole benchmark, or `[SWE-bench Verified]` / `[MMLU-Pro]` when the cited content is subset- or version-specific (a leaderboard number that changed between releases, or a curated subset). The bracket tag resolves to the MANIFEST row, which carries the full provenance.
- **Provenance per `citation-integrity.md`** — a benchmark held in the repo is a `local`-class source: its reference-list entry ends with the strong tag `(local: download/datasets/<path>)`, and any value attributed to it (a reported baseline accuracy, a pass@k, an item count, the canonical metric) must be read from the dataset or its paper, never recalled from memory.

Registry of common eval sets (resolve the user's name against this; extend `download/datasets/README.md` when the user requests one not yet listed):

| Benchmark | Provides | Task | Metric | Acquisition |
|---|---|---|---|---|
| **MMLU** | 57 subjects, ~14k four-way multiple-choice | knowledge / reasoning | accuracy (few-shot) | openly fetchable (HF `cais/mmlu`; MIT) |
| **MMLU-Pro** | harder 10-option MMLU successor, ~12k | knowledge / reasoning | accuracy (CoT) | openly fetchable (HF `TIGER-Lab/MMLU-Pro`; MIT) |
| **GSM8K** | 8.5k grade-school math word problems | arithmetic reasoning | exact-match (CoT) | openly fetchable (HF `gsm8k`; MIT) |
| **HumanEval** | 164 hand-written Python problems + unit tests | code generation | pass@k | openly fetchable (GitHub `openai/human-eval`; MIT) |
| **MBPP** | ~1k crowd-sourced Python problems + tests | code generation | pass@k | openly fetchable (HF `mbpp`; CC BY 4.0) |
| **MT-Bench** | 80 multi-turn prompts, 8 categories | instruction-following | LLM-judge score (1–10) | openly fetchable (FastChat repo; Apache-2.0) |
| **AlpacaEval 2.0** | 805 instructions vs a reference model | instruction-following | length-controlled win-rate (LLM-judge) | openly fetchable (GitHub `tatsu-lab/alpaca_eval`; Apache-2.0) |
| **HellaSwag** | ~10k commonsense sentence completions | commonsense NLI | accuracy | openly fetchable (HF `hellaswag`; MIT) |
| **ARC** (Easy / Challenge) | grade-school science multiple-choice | reasoning | accuracy | openly fetchable (HF `ai2_arc`; CC BY-SA) |
| **WinoGrande** | ~44k pronoun-resolution problems | commonsense | accuracy | openly fetchable (HF `winogrande`; CC BY) |
| **TruthfulQA** | 817 questions probing imitative falsehoods | truthfulness | MC / gen (judge) | openly fetchable (HF `truthful_qa`; Apache-2.0) |
| **BBH** | 23 challenging BIG-Bench tasks | reasoning | accuracy (CoT) | openly fetchable (GitHub `suzgunmirac/BIG-Bench-Hard`; MIT) |
| **SWE-bench** (Lite / Verified) | real GitHub issue→PR tasks + repo snapshots | agentic code repair | % resolved | openly fetchable (HF `princeton-nlp/SWE-bench`; subset-versioned) |
| **GPQA** | 448 graduate-level expert-written Q&A | hard reasoning | accuracy | **gated** (request access; canary / contamination-controlled) |

Annotation / interchange standards an eval set may ship its data in: **JSONL**, the **HuggingFace `datasets`** Arrow/parquet format, **CSV**, or a benchmark-bespoke harness (e.g. HumanEval's execution-based test runner). Record the actual format in the MANIFEST `format` column; when a set ships a non-standard format or an execution harness, note the loader / harness entry-point alongside it in the README so the next reader does not reverse-engineer it.

If the user gives a benchmark by name only (no subset) for a set that *has* meaningful subsets (SWE-bench Lite/Verified/full, MMLU per-subject splits, ARC Easy/Challenge), report the available subsets from the registry / dataset card and ask whether to register the whole set or a specific subset before fetching.

If the user requests a benchmark that is **gated**, do not attempt a download — surface the access-request / gated-repo URL, explain that this command **registers** the archive but cannot fetch it, and pause for the user to place the file at the cache path before continuing.

Tooling: the openly-fetchable download helper `viewer/tools/fetch_dataset.py` lands on demand; the MANIFEST/reference verifier `viewer/tools/check-citation-sources.py` is already present and validates the source-tag invariant. **Until `fetch_dataset.py` is ported into `viewer/tools/`, run the documented `curl` + `shasum` steps by hand** — the contract above (download to gitignored cache, sha256 anchor, MANIFEST row with mandatory licence + citation, by-hand verify) holds either way; the tool only automates it. A full dataset-acquisition spec is authored on demand under `proposals/`.
