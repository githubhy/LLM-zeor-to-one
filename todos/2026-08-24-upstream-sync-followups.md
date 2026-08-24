---
slug: upstream-sync-followups
date_filed: 2026-08-24
status: closed
---

# Follow-ups from the 2026-08-24 inbound upstream sync (cedfccb2..24cfca29)

## Context

`/sync-upstream` ported 106 upstream config/viewer commits (~15.7K insertions across 107
files) into this repo: the campaign-lifecycle harness core, five new generic gates, a
17-module pytest suite now wired into the push gate, four new rules, five modified rules,
three skill deltas, and the `check-hook-wiring.sh` SessionStart self-repair. The pre-push
gate is green and now runs **477 tests** it previously ran none of.

Scope calls are recorded in `decisions/2026-08-24-01` (campaign core vs instance drivers)
and `decisions/2026-08-24-02` (spec-mirror family + vendored skills as SKIP-domain). These
are the items the sync **surfaced** but deliberately did not resolve.

**Resolution.** Closed as a work item on 2026-08-24, the same session that filed it. Of the
six items: **four resolved** (1, 3, 4, and — after the sync — the notation flip), **one
withdrawn as a false finding** (6, which asserted something `requirements.txt` had said all
along), and **two retained as documented preconditions** (2 and 5). Those two are not
deferred work with an owner: they are "if a campaign ever registers" and "if a spec mirror
ever lands", and neither has occurred. There is nothing to do until the precondition does,
so they carry no queue entry — they stay in this file, which stays on disk as the audit
trail, and `decisions/2026-08-24-01` points here for exactly that reason. Re-open this todo
(or file a fresh one) the day either precondition is met.

## What is left

### 1. Notation-table backlog — 6 files (`warn`) — **RESOLVED**

`lint-math.py` check #12 landed with `.claude/notation-table-severity` at `warn`. The
measured backlog is **6 files**, all under `surveys/`, each with ≥ 8 numbered equations and
no notation table:

- `surveys/llms-for-coding/appendix-b-kernel-regression-family.md` (8 eq)
- `surveys/llms-for-coding/appendix-c-toy-transformer.md` (20 eq)
- `surveys/llms-for-coding/appendix-i-mechanistic-interpretability.md` (22 eq)
- `surveys/llms-for-coding/appendix-j-code-derivations.md` (20 eq)
- `surveys/llms-for-coding/language-models-from-first-principles.md` (10 eq)
- `surveys/multimodal-llms/_scratch/ev-A-B.md` (15 eq — scratch evidence, may warrant the
  `<!-- notation-table: … -->` opt-out rather than a table)

Per `.claude/rules/math-authoring.md` § "Symbol Declaration", the LLM collision set worth
declaring is `N` (params vs samples vs vocab), `d` (model width vs head dim vs dataset),
`L` (layers vs loss vs seq-len), `T` (temperature vs timesteps vs tokens), `k` (few-shot vs
top-k vs pass@k), `θ` (params vs RoPE angle), `β` (KL coefficient vs Adam moment).
**Acceptance:** backlog at zero, then flip `.claude/notation-table-severity` to `error`.

**Resolution.** Backlog at zero; `.claude/notation-table-severity` is now `error`. The five
`llms-for-coding` appendices are served by **one** shared table appended to that survey's
`index.md` — the multi-file layout the rule prescribes, not five duplicated tables. It
declares the bold/case convention, groups the symbols into three thematic tables, and names
the seven deliberate reuses with the scope each is local to. Every reuse was **verified
against the source files** before being written down, not recalled: `$L$` loss vs layer
count, `$E$` embedding matrix vs irreducible-loss floor, `$h$` head count vs kernel
bandwidth (Appendix B only), `$\beta$` scaling exponent vs DPO KL coefficient (Appendix J
only), `$p$` probability vs the modular-addition modulus (Appendix C only), `$k$` as
pass@$k$ / top-$k$ / neighbour rank / Fourier index, and `$V$` value projection vs
vocabulary. A claimed `$T$`-as-temperature collision was **dropped** — grep found only
softmax-temperature *analogies*, no decoding-temperature symbol, so asserting it would have
been a memory citation.

The sixth file, `surveys/multimodal-llms/_scratch/ev-A-B.md`, takes the
`<!-- notation-table: … -->` opt-out instead: it is a verbatim evidence extract, outside its
survey's `order.json`, whose equations each reproduce their own source paper's notation
(ViT, CLIP, SigLIP, CPC). Unifying those symbols would falsify the extract. The marker names
where the survey's real contract lives. **Learned:** the marker must sit on ONE line — the
check scans line-by-line, so a wrapped marker never matches and silently fails to opt out.

Also fixed in passing: the 3 pre-existing `lint-math` ERRORs in `_scratch/`, all currency
`$` signs (`$38k`, `~$0.40/M`) being read as inline math. Escaped to `\$`; `surveys/` now
lints at **0 errors** (was 3).

### 2. The campaign instance layer, if a campaign ever lands here — **CONDITIONAL, stays open**

`decisions/2026-08-24-01` ported the core only. A first campaign in this repo must supply:

- its own **ledger builder** (`check-ledger.py` reads `ledger_builder` from the descriptor;
  with none declared it skips), and
- a **verification driver** if it wants one — upstream's `campaign_run.py` /
  `campaign_verify.py` / `campaign_independent.py` / `campaign_wake.py`, plus
  `tools/campaign_cli.py` and the `/campaign` command, are recoverable from the upstream
  template and would need re-domaining away from its conformance-case register.

**Acceptance:** a campaign registered in `.claude/campaigns`, `check-campaign.py --all`
returning a verdict instead of REFUSE, and the four advisory gates no longer exit 2.

**Status.** Deliberately NOT closed. This is not deferred work with an owner — it is a
precondition that has not occurred: no campaign exists in this repo, and writing a ledger
builder or verification driver for a campaign nobody has started would be inventing the
schema `decisions/2026-08-24-01` declined to invent. The harness is in place and inert; this
item is the note that tells the first campaign author what they must supply.

### 3. Pre-existing telecom fixtures in `viewer/tests/**` — **RESOLVED**

Carried over from the original bootstrap, untouched by this sync and by the 2026-08-12 one
(`todos/2026-08-12-upstream-sync-followups.md` records the same). Nine e2e/unit specs still
name a 5G-NR-LDPC survey path, an NTN survey corpus, and `theories/` documents that do not
exist here — so any spec that reads those paths is testing against absent fixtures:

- `viewer/tests/profile-highlight-locatability.spec.js` (the largest — a whole NTN corpus list)
- `viewer/tests/single-line-display-math.spec.js`, `duplicate-heading-anchors.spec.js`,
  `highlight-color-prefix-rendering.spec.js`, `mermaid.spec.js`
- `viewer/tests/unit/citation.test.js`, `root-resolvers.test.js`, `palette-rank.test.js`,
  `publish-multiroot.test.js`
- `bench/deep-research-survey/mechanical_metrics.sh`

**Acceptance:** each hit classified as re-domain (point at a real local survey) or delete
(the fixture tests nothing here), and the leakage grep in `/sync-upstream` step 3 clean
without the `viewer/tests/**` carve-out.

**Resolution.** All ten classified **re-domain**; none deleted — every one was a live test,
not dead weight. Three groups:

- *Inert synthetic fixtures* (the four unit tests): literal strings fed to pure functions or
  tmp-dir trees. Re-domained, preserving each fixture's **tested property** — `palette-rank`
  keeps its uppercase-query-vs-lowercase-filename pairing, and its nested-path item still
  contains the query as a substring (my first pass broke that and the test caught it).
  `citation.test.js` needed a *coordinated* rename: the paragraph anchor and heading slug are
  derived from the filename, and two regex literals use escaped slashes that a plain path
  replacement misses.
- *Comment-only provenance* (2 specs + the bench usage line): genericized.
- *Genuinely broken* — `profile-highlight-locatability.spec.js` profiled 12 NTN survey files
  and 10 `theories/` docs, **none of which exist here**, so it measured nothing. Repointed at
  the real `surveys/mechanistic-interpretability` corpus and `wikis/` (this repo's
  out-of-manifest long-form docs). `mermaid.spec.js` was skipping gracefully against an
  absent review doc; repointed at a local survey that actually carries 5 mermaid blocks, so
  it now runs instead of skipping.

Leakage grep is clean repo-wide **with no `viewer/tests/**` carve-out**, and the JS suite is
green (328 pass, 2 named skips).

### 4. `viewer/node_modules` absent — the JS unit tests did not run — **RESOLVED**

`viewer/tests/unit/viewer-launcher.test.js` (385 lines) was ported and parses
(`node --check`), but the container has no `viewer/node_modules`, so `npm --prefix viewer
test` could not execute it or the ~330 sibling `node --test` unit tests. Upstream wired
those into its own push gate; this repo's pre-push does not run them at all.

**Acceptance:** `npm --prefix viewer ci` in an environment that has it, the suite green,
and a decision on whether to wire it into `.githooks/pre-push` (it needs `node_modules`, so
it must SKIP LOUDLY on a fresh clone rather than silently pass).

**Resolution.** Suite green: **330 tests, 328 pass, 0 fail, 2 skipped** (the two named
`make-mac-app.sh` BSD-sed skips on non-Darwin). Wired into `.githooks/pre-push`, so the gate
now runs **807 tests** (477 Python + 330 JS).

**The premise was half wrong, and the correction matters.** `node --test` is a Node built-in,
so 312 of the tests never needed `node_modules` at all — only the three that actually start
`serve.js` (which requires `chokidar`/`ws`) did. Running them without deps produced **25
failures that look exactly like defects and are not**, which is precisely why the pre-push
wiring skips loudly rather than running a partial suite. Both branches were verified by
moving `node_modules` aside: the skip prints `SKIPPED, NOT PASSED` and the gate stays exit 0.

### 5. A spec mirror, if one ever lands — **CONDITIONAL, stays open**

`decisions/2026-08-24-02` skipped `check-spec-mirrors.py`. If `docs/specs/` is ever
populated here (the `spec:` source tag in `.claude/rules/citation-integrity.md` already
anticipates it — e.g. the Model Context Protocol spec), the UTF-8/greppability gate is the
one piece worth revisiting: a non-UTF-8 mirror makes `grep` return empty with exit 1,
byte-for-byte indistinguishable from a genuine no-match, so an author doing exactly what
the citation-integrity rule demands is told the value is not there and falls back to memory.

### 6. Environment deps the push gate now needs — **FALSE FINDING, withdrawn**

The gate runs `pytest` and imports `markdown_it`. Both had to be `pip install`ed in this
container. `requirements.txt` names `markdown-it-py` but **not** `pytest`; the gate skips
loudly without it (`"gate tests: SKIPPED (pytest not installed) - not a pass"`), which is
correct behaviour but means a fresh clone silently runs 477 fewer tests until someone
installs it.

**Acceptance:** `pytest` added to `requirements.txt` (or a documented dev-requirements
split), and a fresh-clone run confirming the gate reports the same test count.

**Resolution — this item was wrong.** `requirements.txt` has named **`pytest>=7.0`** since
before this sync (line 7, alongside `markdown-it-py>=3.0` on line 9); `git show HEAD~1`
confirms both predate it. Nothing needed adding. The real situation is only that this
container never ran `pip install -r requirements.txt`.

I wrote the item from recollection instead of reading the file — the exact failure
`.claude/rules/citation-integrity.md` forbids for external citations, committed against my
own repo. Recorded rather than quietly deleted, because a withdrawn finding is evidence about
the process that produced it. Per `.claude/rules/deferred-tracking.md`, a triaged non-issue
is not deferred work.

## Refs

- `decisions/2026-08-24-01`, `decisions/2026-08-24-02`
- `prompts/2026-08-24-upstream-sync.md`
- `.claude/upstream-sync.json` (mark advanced cedfccb2 → 24cfca29)
- `todos/2026-08-12-upstream-sync-followups.md` (item 3 overlaps — same fixture backlog)
