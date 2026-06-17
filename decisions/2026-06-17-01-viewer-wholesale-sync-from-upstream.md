---
id: 2026-06-17-01
title: "Wholesale viewer sync from ../data-channel-receiver, preserving LLM-retargeted tool docstrings"
status: accepted
date: 2026-06-17
plan: (ad-hoc request — "update the whole viewer from ../data-channel-receiver")
---

## Context

The viewer toolchain was originally ported telecom→LLM from
`../data-channel-receiver`; per memory, "upstream fixes live in
../data-channel-receiver." The user asked to update the whole viewer from
that upstream. Survey of the two trees: 29 files byte-identical; client/server
(`viewer.js` 220→298KB, `style.css` 50→75KB, `serve.js`, `index.html`) and 4
`lib/` files were upstream-newer; upstream additionally carries deploy/test
infra (`vendor/`, `tests/`, `cloudflare/`, `publish.js`, `pull-annotations.js`,
`GUIDE.md`, `playwright.config.js`, new tools, `lib/reading-position.js`) and a
new runtime dep `ignore@^7` (used by serve.js's `.viewerignore` matcher).

Two ambiguities the request did not pre-decide: (a) 4 Python tools
(`init-doc`, `renumber-sections`, `validate-refs`, `split-markdown`) are
*larger here* than upstream; (b) how much of the deploy/test stack and its
heavy devDeps to pull/install.

## Decision

Sync the entire upstream viewer into `viewer/` via `rsync`, **excluding**
`node_modules/`, `test-results/`, `playwright-report/`, viewer-local
`.claude/`, and the 4 locally-larger tools. Diffing those 4 showed their only
delta is cosmetic LLM-flavored docstrings/examples (`Vaswani et al.` vs
`3GPP`, `transformer-attention` vs `5g-nr-ldpc`) plus this repo's nicer
`-p 4500`/`npm install` hint in `init-doc.py` — functional logic is already at
parity — so they are **kept** (copying upstream would regress telecom strings
into an LLM repo). Adapt `package.json` to keep repo identity
(`llm-zero-to-one-viewer`, `private`) while adopting upstream scripts + deps
(`+ignore`) + playwright/wrangler devDeps. Install **runtime deps only**
(`npm install --omit=dev`) — lean `node_modules`, complete lockfile — leaving
the e2e/deploy devDeps declared-but-uninstalled. Add `.viewerignore` at repo
root and `viewer/test-results/`, `viewer/playwright-report/`, `viewer/dist/`
to `.gitignore`. Retarget `GUIDE.md`'s telecom example slugs to this repo's
surveys (consistent with the kept tool docstrings).

**Convergence policy:** treat upstream as canonical for viewer *code*. Bugs
found in synced code (e.g. `2026-06-17-01`) are fixed upstream first and
re-synced, not patched locally, to keep the copies convergent. Cosmetic
LLM-retargeting (tool docstrings, GUIDE examples) is the one accepted,
deliberate local divergence.

## Alternatives considered

- **Copy the 4 tools from upstream too (pure byte-parity).** Rejected:
  reintroduces telecom example strings into an LLM repo and loses the local
  `-p 4500` hint, with zero functional gain (logic identical).
- **Copy only client/server, skip deploy/test infra.** Rejected: user said
  "the whole viewer"; the infra is inert until invoked and rounds out parity.
- **Full `npm install` incl. devDeps + `playwright install` browsers.**
  Rejected as the default: pulls hundreds of MB of browser binaries the user
  did not ask for; e2e isn't needed to validate this sync. Manifest still
  declares them, so `npm install` + `npx playwright install` enables e2e later.
- **Fix the EISDIR crash locally as part of the sync.** Deferred to the user:
  it is an outward action on a second repo (upstream) and a real scope
  question; see bug `2026-06-17-01`.

## Consequences

- Enables: latest viewer (multi-root serving, ARIA outline, new lib features),
  offline-publish + Cloudflare deploy path, and the upstream `tests/` suite
  (286 node-unit tests pass; 80 python-tool tests pass; both survey gates
  green; live boot/render confirmed).
- Forecloses: nothing in the survey workflow — hook-referenced tool filenames
  (`lint-math.py`, `renumber-equations.py`, `link-references.py`,
  `validate-refs.py`) are unchanged.
- Follow-up: bug `2026-06-17-01` (EISDIR crash) awaiting fix-location decision;
  `npm install` (no `--omit`) + `npx playwright install` required before the
  `tests/` e2e suite can run here.

## Refs

- bug `2026-06-17-01` (EISDIR crash surfaced during verification).
- verify-viewer-sync workflow run `wf_78b6042c-f19` (6-arm parallel verify).
- conversation log `prompts/2026-06-17-viewer-sync.md` (Conversation 1).
