# LLM Deep-Research Survey Project Guide

These rules apply to all work in this repository.

## Core Role

Act as a Staff LLM/AI Research Engineer. Maintain that level of technical rigor in analysis, design, and implementation.

## Agent Fan-Out — Model Selection

When you fan out subagents (via the `Agent` tool's `model` option, a `Workflow` `agent()` call's `opts.model`, or any parallel dispatch), **make a deliberate per-fan-out decision: drop the workers to Sonnet, or keep them on Opus.** Do not blindly inherit Opus for every worker just because the main loop runs on it — that is the expensive default, and most fan-outs do not need it.

- **Sonnet** — mechanical, well-scoped, high-volume breadth where the rubric is explicit and verification is cheap: bulk search / extraction, formatting and renumber passes, applying a known transform across many files, evidence-gathering against a fixed schema. Cheaper and faster; lean here when the win is parallel breadth, not reasoning depth.
- **Opus** — work that needs reasoning depth, judgment, or correctness under ambiguity: math derivations, adversarial verification, design / judge / synthesis stages, anything where a wrong-but-plausible result would survive a casual read (the exact failure mode the `citation-integrity` and `sim-audit` rules guard against).

State the choice when you dispatch (e.g. "fanning out 6 Sonnet extractors", "keeping the verify stage on Opus"). When unsure, split it: Sonnet for the breadth, Opus for the stages that gate correctness.

## Agent Fan-Out — Sizing and Failure Diagnosis

When a fan-out agent (a `Workflow` `agent()` call or an `Agent` dispatch) returns empty or "dies" silently, the binding limit is almost always the **per-agent iteration / tool-call cap (~36–40 tool calls)** — **not** context-window exhaustion and **not** model tier. "Context window" and "wrong model tier" are the seductive default hypotheses; resist them. **Diagnose by reading the dead agent's transcript and counting its tool calls + token use**, never by pattern-matching to a plausible cause.

Measured precedent (a deep-research-survey evidence round): the dead agent had used only ~58K of its 200K-token context (not context-bound) while its Sonnet siblings returned gold-grade evidence (not tier-bound). The loss was step budget spent on ~18 `Glob` calls + a `WebFetch` firehose *before* the write step, so the agent was cut off (`stop_reason=tool_use`, empty text) with nothing written.

Mitigations — size and shape research agents so a step-cap death is survivable:

- **Size small.** ~3–4 questions per research agent, with tool-call headroom under the cap. Fewer-Q/agent is conservative step-budget headroom, not a depth or breadth cut (it *raises* per-question budget; coverage gates own completeness).
- **No exploration spend.** Give exact paths (no `Glob` discovery) and forbid the `WebFetch` firehose in favor of `WebSearch` snippets + local-source grep.
- **File-first deliverable.** Make an incrementally-written `_scratch/<id>.md` file the deliverable, so a step-cap death still leaves evidence on disk. Never rely on a terminal structured-output call as the only output — its throw silently nulls inside `parallel()`, jumping a null-only retry.

This is encoded as the `deep-research-survey` `DRS-HARDEN` default; the diagnosis discipline above applies to any agent fan-out, not just that skill.

## Survey Workflow

This repo's primary purpose is producing rigorous, fully-cited deep-research surveys of LLM/AI topics. The end-to-end flow is owned by the `deep-research-survey` skill (see Skills below); read it before starting or substantially expanding a survey.

- **Layout.** Each survey lives as a multi-file document under `surveys/<survey-slug>/`. The file set is driven by `order.json` (the ordered manifest of section/body markdown files that compose the document) and `references.md` (the single reference list, whose entries obey the source-tag invariant). Section bodies, equations, and cross-references are managed by the `viewer/tools/` toolchain (`split-markdown.py`, `build-index.py`, `renumber-equations.py`, `renumber-sections.py`, `renumber-paragraphs.py`, `link-references.py`, `validate-refs.py`, `check-citation-sources.py`, `init-doc.py`, `verify.py`). The worked example `surveys/attention-demo/` passes every gate step and is the reference for expected structure.
- **Source acquisition.** Full-text PDFs are acquired into `download/` (use the `source-fetch` skill); the `references.md` ↔ `download/` invariant (see `.claude/rules/citation-integrity.md`) must hold before delivery.
- **Validation gate.** Run `/check-survey <survey-slug>` to run full validation on a survey (the same checks the wired hooks run incrementally — see Validation Hooks below). Treat a green `/check-survey` as the delivery / sign-off gate. After a survey is drafted or expanded, run the `citation-audit` skill before sign-off.
- **Benchmarks.** `bench/deep-research-survey/` holds the skill's pressure-test scenarios and harness (`run-integration-test.sh`). RED-baseline arms must run context-isolated in a fresh temp project (no repo `CLAUDE.md`, no skill loaded) via that harness, because in-session agents auto-inherit this `CLAUDE.md` and the repo skills and would contaminate the baseline.

## Conversation Logging

Logging is required for every meaningful repo turn.

- **One log file per session** (not per day): `prompts/YYYY-MM-DD-<session-slug>.md` (the `prompts/` directory is created on demand). The date is the session's start date; `<session-slug>` is a short kebab-case identifier for the session's primary work (e.g. `rlhf-survey-eval`, `attention-citation-audit`), chosen at the session's first log write and reused unchanged for the rest of the session. Per-session files keep concurrent sessions on the same day from clobbering one shared log.
- Before sending the final response, update the current session's log file.
- If the session log does not exist yet, create it with a `# Conversation Log — YYYY-MM-DD — session: <session-slug>` header line and a `<!-- LOG-END -->` sentinel at the bottom.
- If two sessions independently choose the same date + slug, the later one appends a numeric disambiguator (`-2`, `-3`).
- Keep entries within the session file in chronological order; number them sequentially using `## Conversation N`.
- Log decision-only turns too, not only code edits or shell work.
- If an earlier turn in THIS session was missed, backfill it into the same session file immediately.
- Perform the logging in the background and only surface a `📒` indicator in CLI output.
- When the `<!-- LOG-END -->` sentinel exists, append by replacing it: `old_string="<!-- LOG-END -->"`, `new_string="## Conversation N\n...\n<!-- LOG-END -->"`. No Read required.

Each conversation entry should capture (compact format):

```markdown
## Conversation N
- **Request**: [user's ask]
- **Actions**: [what was done, files changed]
- **Result**: [outcome + next steps]
- **Findings**: [only if non-obvious technical insight was discovered]
```

## Todo Capture

**Every deferred, downstream, or out-of-scope item gets a `todos/` entry — no exceptions.** When an item is deferred, marked out of current scope, identified as downstream / follow-on work (a handoff, a `reference-implementation-study` target, a survey open problem or roadmap gap, a "recommended next step"), interrupted mid-task, or otherwise not completed in the current session, persist it under `./todos/` (created on demand) so any future session can pick it up. A handoff or "next step" named only in a report, survey, plan, or chat — but not filed under `todos/` — does **not** count as tracked; if you mention follow-on work, you file the todo in the same turn.

- **One file per todo.** File name pattern: `todos/YYYY-MM-DD-<short-slug>.md`. The date is when the todo was filed, not when it is expected to complete.
- **Master index.** Maintain `todos/INDEX.md` as the append-only index. One row per todo file: `date | slug | title | status (open / in-progress / closed) | one-line hook`. No frontmatter.
- **Body of each todo file.** Self-contained: *Context* (why this is deferred, what was done around it), *What is left* (concrete actions), *Acceptance* (how to know it's done), *Refs* (plan section, commit SHA, report path).
- **Status transitions.** When a todo is picked up, edit its file to `status: in-progress` and update `INDEX.md`. When resolved, set `status: closed`, append a `**Resolution.**` line, and update `INDEX.md`. Closed todos stay on disk (audit trail), they are not deleted.
- **When to file.** User says "defer" / "later" / "skip" / "not now" / "out of scope"; a review surfaces items the user explicitly does not land; work is interrupted mid-task; a plan amendment defers work to a follow-on plan; **a deliverable names any downstream / follow-on item — a `reference-implementation-study` target, a survey open problem or roadmap gap, a "recommended next step", a future-study handoff, an open question left for later — file it even if no one said "defer".**
- **When NOT to file.** Items resolved in the current turn (those go in the commit message / report / `prompts/` log per Conversation Logging); items that will complete before the final response lands.

## Decision Capture

Plan execution stays autonomous (no intermediate confirmation prompts). Instead, every judgment-call decision is persisted under `./decisions/` (created on demand) as the *why* trail, separate from the *what shipped* implementation report. Skills (e.g. `citation-audit`) defer to these conventions rather than restating them.

- **One file per decision.** File name pattern: `decisions/YYYY-MM-DD-NN-<short-slug>.md`. `NN` is a 2-digit per-day sequence so multiple decisions in one turn stay ordered.
- **Master index.** Maintain `decisions/INDEX.md` as the append-only index. One row per decision: `date | id | title | status (proposed / accepted / superseded) | one-line hook`. No frontmatter.
- **Body of each decision file.** YAML frontmatter (`id`, `title`, `status`, `date`, `plan` link if applicable), then sections: *Context* (what the plan said, what reality showed, what was ambiguous), *Decision* (one or two sentences), *Alternatives considered* (bulleted with reject reasons), *Consequences* (what this enables, forecloses, follow-up — link `todos/` if any), *Refs* (plan section, commit SHA, conversation log entry, related `bugs/` IDs).
- **Status transitions.** Decisions land as `accepted`. If a later decision overrides one, set the older to `superseded` with a `**Superseded by:**` line pointing at the new ID. Update `INDEX.md`. Superseded decisions stay on disk.
- **When to file.** Picking among real alternatives the plan did not pre-decide; resolving a plan-vs-reality conflict (assumption wrong, dependency missing, API differs); any scope change (also file `todos/` if work is deferred); choosing a non-obvious implementation approach (algorithm, data layout, dependency, file layout); a `citation-audit` fix that involved a real choice.
- **When NOT to file.** Trivial mechanical steps already specified in the plan; routine bug fixes within the planned approach (those go to `bugs/`); single-tool-call resolutions where there was no real alternative.

Risky/irreversible actions (force-push, destructive shell commands, public PR/issue creation, deleting branches) still warrant a pause-and-confirm — the decision-log rule does not override the harness safety rules.

## Bug Capture

Non-trivial bugs encountered during any work are persisted under `./bugs/` (created on demand) so they are queryable as a category by component, severity, and root-cause pattern. The `citation-audit` skill defers to this guide when filing wrong-value or fabricated-citation findings, so the severity scheme below is authoritative.

- **One file per bug.** File name pattern: `bugs/YYYY-MM-DD-NN-<short-slug>.md`. `NN` is a 2-digit per-day sequence. **Uniqueness is gated** by `viewer/tools/check-record-ids.py` (pre-push, severity `error`): two files sharing an `id:`, an `INDEX.md` row with no file (or vice versa), a frontmatter `id:` that disagrees with the filename, or a qualified `bugs/<id>` / `decisions/<id>` ref resolving to two files all fail the push. Nothing allocates `NN`, so on a long-lived branch run `git fetch && git log origin/main -- bugs/ decisions/` before choosing one — a parallel session on `main` may already hold it. The gate catches a collision, but a clean choice avoids a cross-branch renumber (the same convention and gate cover `decisions/`, `todos/`, `field-notes/`).
- **Master index.** Maintain `bugs/INDEX.md` as the append-only index. One row per bug: `date | id | title | severity (low / med / high / critical) | status (open / fixed / wontfix / duplicate) | one-line hook`. No frontmatter.
- **Body of each bug file.** YAML frontmatter (`id`, `title`, `severity`, `status`, `date`, `component`, `plan` link if applicable), then sections: *Symptom* (observed behavior, reproducer if non-trivial), *Root cause* (the underlying mechanism, not the surface fix), *Fix* (what changed, commit SHA once landed), *Regression test* (test added/extended, or `"none — <reason>"`), *Refs* (commit SHA, related `decisions/` ID if the fix was a real choice, related `todos/` ID if follow-up deferred, conversation log entry).
- **Status transitions.** New bug starts at `open`. When fixed, set `status: fixed` and fill in *Fix* + *Regression test* + commit SHA. When the user decides not to fix, `wontfix` with a `**Reason.**` line. When merged into another bug, `duplicate` pointing at the surviving ID. Update `INDEX.md`. Closed bugs stay on disk.
- **Severity guide.** `critical` = silent wrong output in nominal operation, or crashes a user-visible flow — e.g. a load-bearing citation that is fabricated or attributes a claim/value to a source that does not support it, where the survey's argument depends on it. `high` = wrong output under realistic conditions, or a load-bearing citation with a wrong value/locator that propagates into a derivation or headline claim. `med` = wrong output at edge cases, incorrect metrics/output, a non-load-bearing citation error, or a non-trivial perf regression. `low` = cosmetic or non-load-bearing nits.
- **When to file.** Root cause is non-obvious or the surface symptom hides the underlying mechanism; numerical/precision issues, race conditions, algorithm edge cases; a wrong/fabricated load-bearing citation surfaced by `citation-audit`; bug is deferred (also file `todos/`); bug is found but explicitly not-fixed.
- **When NOT to file.** Typos / syntax errors caught immediately during implementation; trivial mechanical fixes where the diff itself is the explanation; bugs in throwaway scratch code under `temp/`.

`decisions/` and `bugs/` cross-link via their *Refs* sections — `decisions/` answers *why we picked this fix*, `bugs/` answers *what was wrong and how we found out*. Implementation reports under `./reports/` get a "Bugs encountered" section listing the relevant IDs.

## Field Notes

Issues found *and resolved within the same session* — that didn't warrant a `todos/`, `decisions/`, or `bugs/` entry but are worth retrospective capture — are persisted under `./field-notes/` (created on demand) as a session retrospective.

- **One file per session that resolved retrospective-worthy items.** File name pattern: `field-notes/YYYY-MM-DD-<short-slug>.md`. The date is the session date.
- **No master index.** Field notes are read chronologically when retrospecting; no `INDEX.md` is needed.
- **Body.** Self-contained: *Context* (what the session was about), *Issues found and resolved* (one bullet per issue with: what was wrong, why it was missed before, how it was resolved inline, no-todo because <reason>), *Patterns / lessons* (what to watch for or systematize next time).
- **When to file.** Multiple inline-resolved issues in one session that share a theme (e.g. "caption-quality audit" or "stale-data audit"); a near-miss that would have been a bug if not caught quickly; a resolved problem whose root-cause pattern could recur and needs to be visible at retrospective time.
- **When NOT to file.** Single-issue sessions (those go in the conversation log); items already captured in `todos/` / `decisions/` / `bugs/` (those have their own audit trail); routine bug fixes already in commit messages.
- **Cross-links.** Field notes may reference `bugs/` / `decisions/` IDs when the session also produced one — they sit *alongside* those records, not as a substitute. `bugs/` answers what broke; `field-notes/` answers what the session learned.

## Validation Hooks

Validation is wired through `.claude/settings.json` (and `.claude/settings.local.json`); hook scripts live under `$CLAUDE_PROJECT_DIR/.claude/hooks/`. The `PostToolUse` / `Stop` Claude hooks need nothing installed. A git **pre-push** gate is also active, wired via `git config core.hooksPath .githooks` (the tracked hook is `.githooks/pre-push`).

| Hook | Trigger | Runs |
|---|---|---|
| `.claude/hooks/post-edit-lint.sh` | Auto-wired via `.claude/settings.json` `PostToolUse`; runs on every `Edit`/`Write` of a `.md` file. | `lint-math.py` (blocking) + `validate-refs.py --bare-refs-only` (severity per `.claude/bare-refs-severity`) + `renumber-equations.py` + `link-references.py`. |
| `.claude/hooks/validate-refs-on-dirty.sh` | Auto-wired via `.claude/settings.json` `Stop`. | Re-validates references across any dirty survey files at the end of a turn, plus an **advisory** `crosslink.py check --changed` gap detector (Tier-1 detection only — never blocks). |
| `.claude/hooks/guard-foreground-background.py` | Auto-wired via `.claude/settings.json` `PreToolUse` (matcher `Bash`). | Blocks a **foreground** Bash call that backgrounds a long job with a trailing `&` / `nohup` / `setsid` / `disown` — the harness reaps the call's children when it returns, so the job dies. Relaunch via the Bash tool's `run_in_background: true`. Severity `.claude/foreground-bg-severity` (`off｜warn｜error`, currently `error`); fails OPEN. |
| `git config core.hooksPath .githooks` | Auto-wired via `.claude/settings.json` `SessionStart`. | Re-points git at the tracked hooks on every session start, so a fresh clone cannot silently run with the push gate disabled. |

Other wired hooks, for reference: `statusLine` → `.claude/hooks/status-line.sh`; `UserPromptSubmit` → `.claude/hooks/cache-warmer-extend.sh` (the prompt-cache keep-warm loop; see the `/keep-cache-warm` command); `Stop` (async) → `.claude/hooks/log-turn-telemetry.py` via `py-launcher.sh` (per-turn API-usage telemetry to `.claude/diagnostics/<session>.jsonl`). These three now live in the **tracked** `.claude/settings.json` rather than the machine-local file, so they work in a fresh clone; `.claude/settings.local.json` is gitignored and reserved for genuinely machine-specific overrides. A flag-gated Pushover notifier (`.claude/scripts/notify.sh` + `compose-notify-msg.py`) is available but unwired/off by default (enable with `notify.sh on`).

**Bare-refs severity toggle.** `.claude/bare-refs-severity` controls whether the `PostToolUse` hook treats bare-ref findings as blocking errors or non-blocking warnings. Values: `warn` or `error`. The current value is `error` (after cleanup), so bare-ref findings are blocking.

**Cross-link gate toggle + scope.** `.claude/crosslink-severity` (`off | warn | error`, currently **`error`**; it blocks only at/above the block-score, cosine 0.30, and the group is at zero residual gaps) controls the `crosslink.py check` gap detector: `off` silences it; `warn` lists gaps advisory; `error` lets the pre-push gate block on an obvious missing link. `.claude/crosslink-scope` defines **named corpus groups** (`[group-name]` headers), each an independent TF-IDF corpus so a candidate never spans two groups; never hand-expand it with `grep` — use `crosslink.py groups [--group N]` or `--scope-file`. Derive/audit membership with `viewer/tools/crosslink-cluster.py propose|validate`. The current group is `llm-methods` (the three research surveys + the two wikis); `surveys/attention-demo` is a deliberate keep-out in `.claude/crosslink-keepout` (it is a tooling fixture, not research content). Two companion gates: `crosslink.py coverage` (severity `.claude/crosslink-coverage-severity`) reports any survey/wiki in neither a group nor the keep-out, so a new document is never silently unscanned; `crosslink.py reach` (severity `.claude/reachability-severity`, now **`error`** — zero unreachable) reports a wiki no survey links to by a reader-facing link. Judge-rejected pairs live in `.claude/crosslink-rejected.json` (a rejected pair is not a gap); recording them via `crosslink.py reject` is a mandatory step of `/cross-link`. Detection is deterministic and lives in the gates; **insertion needs judgment and is on-demand** via `/cross-link`. Full rule: `.claude/rules/cross-linking.md`.

**Other gate severity toggles.** Each is a one-word file under `.claude/` (`off | warn | error`) read by its gate in `.githooks/pre-push`: `math-basis-severity` (+ per-survey `math-basis-strict`) for the two-bases declaration gate; `math-rederive-severity` (+ `math-rederive-strict`) for the independent-re-derivation gate; `math-oracle-severity` for the published-value-vs-recomputation gate; `derivation-dag-severity`; `value-ledger-severity`; `record-ids-severity`; `figure-labels-severity`; `section-placeholders-severity`; `reproduce-block-severity`; `ris-derivation-severity`; `duplicate-anchor-severity`; `foreground-bg-severity`; `conformance-coverage-severity`. Two registries gate opt-in checks and are empty until a first entry is added: `.claude/rollup-pages` (rollup-freshness) and `.claude/program-manifests` (plan-progress anti-drift).

**Pre-push gate (active).** `.githooks/pre-push`, activated via `git config core.hooksPath .githooks`, runs the full survey-wide validation on every `git push`. It chains `git lfs pre-push` first (this hook REPLACES the stock LFS hook, so without the chain LFS pointers would push without their blobs), then: `validate-refs.py`; the `--check` modes of the renumber scripts (equations / paragraphs / sections, the last over `surveys/ wikis/`); bare-refs at `--severity=error`; depth-tiers; section-ownership; basis-declarations; derivation-review; math-oracles; derivation-DAG; value-ledger; `check-citation-sources.py --index` over every tracked `references.md`; per-survey `link-references --check` (orphaned citations); cross-file ref-markers; link-fragments; section-placeholders; `crosslink.py check | coverage | reach`; record-IDs; figure-labels; the reference-implementation-study G0 advisory; plan-progress; rollup-freshness; reproduce-blocks; and the TDD-evidence registry. `/check-survey <survey-slug>` runs the survey-scoped subset on demand — run it before any delivery or sign-off; `/normalize-survey <dir>` is its write-mode twin. Bypass for an explicit reason with `git push --no-verify` — but note there is no server-side mirror of these checks here, so a bypassed push is simply unchecked.

A **pre-commit** hook (`.githooks/pre-commit`) also refuses to commit while `check-tdd-evidence.py --prove` has source files deliberately broken in-flight (the sentinel is `.claude/tdd-prove-inflight.json`): a concurrent commit would freeze the break into history, and the prove would then restore the file so nothing looks wrong.

`core.hooksPath .githooks` is the **active** wiring (git reads the tracked hooks directly; a copy into `.git/hooks/` is a snapshot and drifts, which is why the hook refuses to run unless the pointer names `.githooks`). It is re-applied on every `SessionStart`. `core.hooksPath` alone is **not** the install: git *silently* skips a non-executable hook, so the tracked mode must stay `100755`. `scripts/install-git-hooks.sh` (+ `.ps1` for Windows) is the idempotent installer that sets both the pointer and the exec bit — run it once per clone.

## Rules Loaded on Demand

The following files hold detailed rules that are **not** eagerly inlined. Read them when the task matches, before doing the work. Do not auto-load them.

- `.claude/rules/math-authoring.md` — Inline/display math delimiter rules, equation numbering with stable-ID markers, reference cross-linking, paragraph anchors. This file is the source of record for the math-formatting conventions the `lint-math.py` linter enforces. **Read before:** editing any `surveys/**/*.md` or any other markdown file that contains display-math blocks, inline math, numbered equations, numbered references, or paragraph anchors; authoring a new section body or template that will hold math; or dispatching a subagent to write math-bearing content. The `PostToolUse` `lint-math.py` hook enforces these rules (no multi-line inline math; no display-math line starting with `> * + - # _` or a backtick at column 1; `ref`/`cite`/`xref`/`secref`/`secxref` comment markers not at column 1; no bare pipe in inline math inside table rows; an inline-math `$` delimiter must not abut a decimal digit; tight ordered-list / prose display-math spacing) and will block edits that violate them.
- `.claude/rules/citation-integrity.md` — Citation integrity rule: never write an external citation from memory; every cited claim and value must be traceable to a source acquired in `download/`, and the reference list must satisfy the `references.md` ↔ `download/` invariant. **Read before:** writing or expanding any document that carries external citations (surveys, appendices, reports, proposals); adding or editing entries in a `references.md`; resolving or reconciling citations during a `citation-audit`; and before dispatching a subagent to author or expand any externally-cited content.
- `.claude/rules/cross-linking.md` — Cross-linking rule: detection is deterministic and runs in the lint / Stop / pre-push gates (`crosslink.py check`, advisory, severity-toggleable); insertion needs judgment and is on-demand and batched (`/cross-link`) — never an agent in a per-edit hook. Defines the directional syntax convention (survey-section target → `secxref` + `§`; out-of-manifest doc → plain link) and the mandatory cross-link sign-off step for authoring tasks. **Read before:** authoring or substantially expanding any survey document or section, signing off such a task, or changing the cross-link tooling / gates.
- `.claude/rules/sim-report-completeness.md` — Completeness rule for reproduction / evaluation-study reports: the section spine and the load-bearing `[M]` artifacts (executive summary, protocol-vs-eval conformance matrix, theory-as-predictor overlays, CI on every result, quantization section, reproduce block, audit trail). Mechanically gated by `viewer/tools/check-report-completeness.py` (the `REPORT` gate). **Read before:** writing or signing off any reproduction / benchmark-evaluation report under `docs/` or `reports/` (e.g. a `reference-implementation-study` Phase-6 deliverable).
- `.claude/rules/deferred-tracking.md` — Deferred-item tracking: when a task defers a batch of actionable items, open a `todos/YYYY-MM-DD-<slug>.md` tracking file (indexed in `todos/INDEX.md`) before sign-off — the durable, cross-session record of "what did we say we'd come back to?". Generalises the `todos/` convention from `## Todo Capture` to every deferring task and defines the file format. **Read before:** signing off any task — plan, report, review, audit, survey, or implementation — that defers work.
- `.claude/rules/figure-operating-conditions.md` — Figure operating-conditions disclosure rule: every figure must disclose its operating conditions (model + size, method/variant, precision, context length, decoding params, few-shot $k$, sampling $n$, benchmark + split, eval harness + version, metric + CI, seed, pass@k convention) numerically in § 1 of its caption — "production default" labels without the numeric value do not satisfy it. The concrete home for the disclosure conventions `sim-report-completeness.md` builds on. **Read before:** generating, captioning, or auditing any figure that reports LLM/method behavior under specified operating conditions.
- `.claude/rules/workflow.md` — The plan → implementation → report workflow, the development timeline, proposal and survey rules, diagram determinism, and the Math Derivation Rules. Also the home of five default-on options: `[opt:PLAN-REDFIRST]` (a plan that ships code names its RED-first test deliverable per phase), `[opt:UTF8-WRITE]` (explicit `encoding='utf-8'` on every read and write), `[opt:BG-RUNINBG]` + `[opt:BG-GUARD]` (a long job is launched via `run_in_background`, never a trailing `&` — enforced by a `PreToolUse` gate), `[opt:MATH-BASIS]` (a quantity measurable on two bases declares which), and `[opt:MATH-REDERIVE]` (a new or materially-changed numbered derivation gets one independent re-derivation before it lands). **Read before:** producing a plan, report, diagram, proposal, survey, or math derivation, or touching `docs/development-timeline.md`.
- `.claude/rules/calibration-residuals.md` — Calibration-residual attribution rule (domain-agnostic): a residual between two numbers that ought to agree — a reproduction vs a published benchmark score, a port vs its source, a fast kernel vs its reference — is root-caused only when you can state how much of the gap the proposed cause closes *at the representative operating point*, and name what is left. Forbids "brackets" / "agrees with" / "qualitative match" as attributions; requires metric-basis reconciliation before believing agreement or disagreement; an independent implementation excludes hypotheses but is not an oracle. **Read before:** attributing any measured-vs-reference residual to a cause, and before any report states such an attribution as fact.
- `.claude/rules/cross-language-port.md` — Cross-language port rule: a port is a **proof obligation, not a translation** — scope it provably by call-graph closure, port it verbatim (never fuse kernel bodies), and gate every kernel against goldens dumped from the *unmodified* reference on a fixed tolerance ladder. **Read before:** porting a validated numerical implementation to another language or runtime (PyTorch → Triton/CUDA, Python → C++, PyTorch → JAX), and before signing off such a port.
- `.claude/rules/release-documentation.md` — Release-documentation rule: a release ships a **deliverable set** — an implementation/port report to the `sim-report-completeness` spine, a README that is the sole user-facing documentation (with a Verification section carrying *numbers*, never a bare "validated"), and a cross-document sign-off via `results-reconciliation` + `citation-audit`. **Read before:** releasing a validated implementation as a self-contained package, i.e. before writing or signing off its report and README.
- `.claude/rules/reset-durability.md` — Reset-durability rule: **origin is the only durable store.** A container-snapshot rollback can revert the working tree, `.git`, and even the `origin/<branch>` remote-tracking ref; only what is pushed survives. Commit **and push** after every meaningful step, never force-push to "reconcile" a reset, and treat a gate-blocked commit as an unsafe checkpoint. **Read before:** any long cloud session, parking work, launching a long-running job, or reconciling a suspected reset.

## Skills

A skill is a local instruction set stored in a `SKILL.md` file. Use a skill when the user names it directly or when the request clearly matches its purpose.

Prefer repo-local skills under `.claude/skills/` when they exist.

**Skill/rule options (toggle registry).** Individually-switchable *post-hoc* refinements to skills and rules — workflow corrections, extra checks, hardening defaults that are NOT part of a skill's own mode/flag lattice — are registered in `.claude/skill-options.json`, each with a stable `[opt:<ID>]` marker at its point of use and a `default` (on/off). To turn one on or off, flip its `default` there; an agent following an annotated skill/rule reads the registry and, if an option is `off`, skips the marked block and reverts to its documented `off_behavior`. This mirrors the repo's other `.claude/*` toggle files. Do not reinvent a per-skill toggle mechanism — extend this registry.

### Available Skills

- `deep-research-survey`: Use when the user asks for a deep research survey, literature review, technical landscape, or state-of-the-art review of an LLM / AI topic — e.g. transformer & attention architectures, pretraining & scaling laws, fine-tuning and alignment (SFT/RLHF/DPO/RLAIF/PEFT/LoRA), retrieval-augmented generation, LLM agents & tool use, inference & serving (KV-cache, quantization, speculative decoding, batching), evaluation & benchmarks, long-context methods, multimodal models, or safety & interpretability — and expects first-principles explanation, broad method coverage, tradeoff analysis, current practice, cited references, or a reusable research prompt. File: `.claude/skills/deep-research-survey/SKILL.md`
- `source-fetch`: Acquire full-text papers and books as PDFs from open-access sources — Semantic Scholar, OpenAlex, arXiv, Crossref, and (optional) Unpaywall — via the keyless `oa_fetch.py` resolver, with keyless LibGen+ and an optional Anna's Archive as shadow-library fallbacks. Use when deep-research-survey Phase 3 needs full-text acquisition, or standalone when the user asks to download a specific paper or book. File: `.claude/skills/source-fetch/SKILL.md`
- `citation-audit`: Verify every external citation in a document against its actual source, then trace whether wrong citations affect the derivations. Use after a survey, appendix, report, or proposal with external citations is drafted or substantially expanded — especially subagent-authored or memory-sourced content — and before any delivery or sign-off gate. File: `.claude/skills/citation-audit/SKILL.md`
- `survey-explainer-fold`: Fold a just-answered conceptual "why/how is X like this?" or "how large is X in real models?" Q&A into a survey as two linked artifacts — a compact inline `> **Note —**` blockquote at the host equation/paragraph, plus a dedicated anchored subsection (appended at the end of its block, cascade-free) holding the full answer in answer-format — then run the mandatory renumber/validate sweep. Use when the user says "fold this in" / "put this in the survey" while reading a survey or appendix. Adapted from the `data-channel-receiver` original. File: `.claude/skills/survey-explainer-fold/SKILL.md`
- `cross-link`: Add high-value cross-links across the survey corpus cheaply — a deterministic TF-IDF pre-filter proposes candidates, a small batched agent judges only keep/where, and a deterministic idempotent applier inserts them with the correct directional syntax. Use to clear the gaps the crosslink gate (`crosslink.py check`) reports, or as the sign-off step after authoring / expanding a survey. Tier-2 of `.claude/rules/cross-linking.md`; replaces the all-agent sweep at far lower cost. File: `.claude/skills/cross-link/SKILL.md`
- `capability-decomposition`: Exhaustively map what a codebase implements vs does NOT — drilled module → class → procedure → STEP, every leaf tagged ✅ in / ⚠️ partial / ❌ out with `path:line` evidence and adversarially verified against source, rendered as a conformant multi-file survey under `surveys/`. Use when you need a source-grounded, step-granular "what's in / out of the box, and why" map of a library or subsystem. NOT for a high-level narrative or literature/SOTA landscape (use `deep-research-survey`), evaluating a single candidate method, or auditing an experiment/eval. Token-heavy (~2 agents × every subtree); invoke explicitly. File: `.claude/skills/capability-decomposition/SKILL.md`
- `reference-implementation-study`: Drive a topic from survey findings through reference implementation, comparative evaluation, sensitivity analysis, reduced-precision / quantized realization, and a final engineering recommendation. Use after a `deep-research-survey` has produced a completed survey with method inventory, math derivations, and SOTA assessment. Applicable to any LLM / AI method, ML-systems, or algorithm-engineering domain. File: `.claude/skills/reference-implementation-study/SKILL.md`
- `sim-audit`: Verify an experiment's correctness through an untrusting, multi-lens audit — independent re-derivation, property/invariant tests, statistical validity (seeds / CIs / contamination), published-baseline anchors, edge-case robustness, and determinism / software-quality. Use after a `reference-implementation-study` reproduction/eval experiment is drafted or substantially changed (especially after a shared-API rewrite or subagent-authored kernels), and before any Phase-6 / sign-off gate. Runs standalone on any experiment. File: `.claude/skills/sim-audit/SKILL.md`
- `ui-review-loop`: Full-coverage screenshot review of the running markdown viewer (`viewer/`): capture each representative doc across the viewer STATE MATRIX (chrome × theme × density × width) with Playwright, fan out a multi-agent vision review, VERIFY each finding against code/DOM (high false-alarm rate — do not trust raw agent output), then loop fix → recapture → re-review until it converges. Plus a Layer-2 assertion-backed interaction driver for the viewer surfaces (immersive toggle, command palette, settings sheet, right-pane segments, in-situ peeks, split view, margin sidenotes, drawer, mobile bar, highlight gesture). Use during a viewer UI redesign / large front-end change; token-heavy, invoke explicitly. File: `.claude/skills/ui-review-loop/SKILL.md`
- `method-eval`: Rigorously evaluate a candidate LLM/AI method (an attention or positional-encoding variant, a decoding/sampling method, a quantization scheme, a KV-cache or speculative-decoding trick, a retriever/reranker, a PEFT variant) through an independent N-agent pipeline (derive → independent math review + implement → independent implementation review + test), score it against fixed oracles on a fixed viability rubric, and archive a uniform dossier in a `surveys/<survey>/method-search/` register. Use as a fast accept/reject viability gate UPSTREAM of a full `reference-implementation-study`. NOT for an already-standard method, a one-line sanity check, or a task with no measurable oracle. File: `.claude/skills/method-eval/SKILL.md`
- `skill-improvement`: Run a rigorous, repeatable improvement cycle on an existing skill — landscape scan, comparison, tiered proposal, a switchable lazy-loaded flag-lattice implementation, A/B verification (per-item + optional end-to-end), report, and merge. Use when asked to improve, upgrade, enhance, A/B, or harden an existing skill (or its prompts/workflow). Applies the progressive-disclosure + A/B discipline it installs into the target skill to itself. File: `.claude/skills/skill-improvement/SKILL.md`
- `spec-provenance`: Trace a claim about *why* a model, method, benchmark, or protocol is built the way it is — a value, a rationale, a default — to the primary record (published version, model/system card, benchmark's defining paper, harness release), and gate every preprint / draft / blog-post number against the CURRENT published artifact before it is stated as fact. Composes with `source-fetch` and `citation-audit`. File: `.claude/skills/spec-provenance/SKILL.md`
- `results-reconciliation`: After results are folded into docs incrementally across many turns, adversarially audit every doc against the result-of-record artifacts (the data files, not prose or memory) and reconcile **framing-staleness** — the "still-open / not-measured / do-not-cite / X remains" sentences that go stale while the data blocks stay correct. Use before a sign-off gate when a report/survey/manifest has accreted results over many edits. File: `.claude/skills/results-reconciliation/SKILL.md`
- `harness-harvest`: Turn a session's persisted learnings (`field-notes/`, `bugs/`, `todos/`, `decisions/`, the conversation log) into the RIGHT harness changes across every layer — skill, tool, command, hook, rule, config — with honesty triage, mechanism verification (prefer *deleting* a workaround to adding a tool), the `.claude/skill-options.json` toggle registry, and a recurrence bar before creating anything new. The cross-layer counterpart to `skill-improvement`. File: `.claude/skills/harness-harvest/SKILL.md`
- `upstream-pr`: Open a pull request from a fork to its upstream (parent) repository when the session is scoped to the fork only. Produces the cross-fork compare URL, a PR title/body derived from the commits, and the new-session-rooted-at-upstream alternative. File: `.claude/skills/upstream-pr/SKILL.md`
- `kernel-bringup` *(accelerator-realization family)*: Turn a validated reference implementation of an LLM operator into an optimized/fused kernel (Triton, CUDA, `torch.compile`, a custom attention or quantized matmul) proven numerically equivalent to a **deterministic** golden reference within a *derived* error bound — not an eyeballed `allclose`. Also the first phase of `accelerator-cost-study`. File: `.claude/skills/kernel-bringup/SKILL.md`
- `accelerator-cost-study` *(accelerator-realization family)*: Take an equivalence-proven kernel through a real measurement flow on named hardware and produce flow-measured **absolute** cost — latency distribution, achieved FLOP/s vs peak, HBM bandwidth, roofline placement, memory footprint, energy per token — gated by a pre-registered CONFIRM/REFUTE window against the analytic cost model and anchored to an external published datapoint. Consumes `kernel-bringup`. File: `.claude/skills/accelerator-cost-study/SKILL.md`

The `kernel-bringup` → `accelerator-cost-study` pair extends the study pipeline into hardware realization: `deep-research-survey` → `reference-implementation-study` → `kernel-bringup` → `accelerator-cost-study` (→ `results-reconciliation` for doc sign-off).

### Commands

- `/check-survey <survey-slug>` — Run full validation on the specified survey (the survey delivery / sign-off gate; read-only). Defined in `.claude/commands/check-survey.md`.
- `/normalize-survey <survey-dir>` — The **write-mode twin** of `/check-survey`: applies the renumber/link tools in the one correct order (with the `references.md` paragraph-init exception and the `secref`/`secxref` promotion baked in), then runs the check suite. Use after authoring a multi-file survey or whenever `/check-survey` reports anchor/marker drift. Defined in `.claude/commands/normalize-survey.md`.
- `/keep-cache-warm` — Keep the Anthropic prompt cache warm via self-paced `/loop` wake-ups. Defined in `.claude/commands/keep-cache-warm.md`.
- `/enrich-equation <file> (<equation-number>)` — Expand one numbered equation into a multi-line, first-principles derivation with no intermediate step missing (same `\tag`, no cascade), then run the validation sweep. Defined in `.claude/commands/enrich-equation.md`.
- `/sync-upstream [--dry-run | <range> | --back]` — **Two-directional** sync of the harness config **and the viewer application** with the upstream template repo (`../data-channel-receiver`). **Inbound** (default): port upstream config + `viewer/**` + shared-infra (`bench/`, `.gitignore`, `.viewerignore`) deltas since the high-water mark in `.claude/upstream-sync.json`, re-adapting each telecom/3GPP → LLM/AI surveys (never research content; viewer framework code is domain-agnostic — only embedded demo/fixture content is re-adapted, local divergences preserved), then advance the mark. **Outbound** (`--back`): discover generic improvements made HERE, strip provenance, branch `sync-from-llm-zero-to-one`, and (on go-ahead) open a PR to upstream. Defined in `.claude/commands/sync-upstream.md`.
- `/study-signoff <study> [<topic>] [--gates …] [--report <path>]` — Run the full `reference-implementation-study` sign-off gate sequence (G1–G4 + REPORT + CITE) for a method-reproduction / evaluation study. Defined in `.claude/commands/study-signoff.md`.
- `/enrich <survey> <section(s)>` — Enrich survey section(s) by the right mode(s) (derivation / evidence / structural / cross-reference), then run the renumber/link/index validation sweep. (Broader sibling of `/enrich-equation`, which expands a single numbered equation.) Defined in `.claude/commands/enrich.md`.
- `/add-reference <survey>` — Add a bibliography entry (`<!-- bib:N -->`) + in-text `<!-- cite:N -->` markers to a survey and run `link-references.py`. Defined in `.claude/commands/add-reference.md`.
- `/add-dataset <benchmark> [<subset/version>]` — Register an evaluation benchmark / dataset into `download/datasets/` (MANIFEST row with sha256 + mandatory licence + citation; openly-fetchable vs gated acquisition; contamination hygiene). Defined in `.claude/commands/add-dataset.md`.
- `/review-plan <plan>` — Review a plan as a Staff Engineer (read-only critique; concrete issues only). Defined in `.claude/commands/review-plan.md`.
- `/refine-plan <plan>` — Review a plan against the real code AND update the plan in place to fix every issue found. Defined in `.claude/commands/refine-plan.md`.
- `/bg` — Report only the background task count (single integer; calls `TaskList` once). Compose with `/loop` for polling. Defined in `.claude/commands/bg.md`.

### Agents

Custom subagent definitions under `.claude/agents/`, dispatched via the `Agent` tool's `subagent_type`/`agentType` (or a `Workflow` `agent()` call's `opts.agentType`). Re-adapt model choice per the Agent Fan-Out rule above.

- `survey-enricher` (opus) — Staff LLM/AI Research Engineer that enriches a survey section with first-principles derivations, method inventory, and SOTA assessment under the math-authoring + citation-integrity rules. Referenced by `/enrich` (Delegation) and the `method-eval` Derive stage. File: `.claude/agents/survey-enricher.md`
- `evidence-collector` (sonnet) — parallel evidence-gatherer that returns a structured evidence ledger (quality-graded, citation-faithful) for a research question. Referenced by `deep-research-survey` Phase 3 and the `skill-improvement` landscape workflow. File: `.claude/agents/evidence-collector.md`
- `viewer-dev` (sonnet) — frontend developer for the local markdown viewer (`viewer/` HTML/CSS/JS + `serve.js`); preserves KaTeX/math shielding, no build step. File: `.claude/agents/viewer-dev.md`

### Skill Usage Rules

- Check `.claude/skills/` first for a matching repo-local skill.
- Read only enough of the relevant `SKILL.md` to follow the workflow.
- Resolve relative paths from the skill directory first.
- Load only the specific referenced files needed for the task.
- Reuse provided scripts, templates, and assets when available.
- If multiple skills fit, use the smallest set that covers the request and state the order briefly.
- If a skill cannot be used cleanly, say so briefly and continue with the best fallback.
- Keep context tight by summarizing large references instead of loading everything.

## Agent skills

Configuration the installed engineering skills (`mattpocock-skills`) read. These files are
the contract; edit them directly rather than re-running the setup skill.

### Issue tracker

**Two surfaces, one rule.** **GitHub Issues** (`githubhy/LLM-zeor-to-one`, via `gh`) is the
**intake and triage** surface — where a request or report lands before anyone has decided
what it is. **`todos/` / `bugs/` / `decisions/` / `field-notes/`** remain the **durable
record of record**, governed by the Capture sections above and gated by
`viewer/tools/check-record-ids.py` at pre-push. An issue is transient and **graduates**
into a record, which is permanent; the two cross-link in both directions and a fact never
lives in both places unlinked. "Publish to the issue tracker" means create an issue;
"record this deferral / bug / decision" means write the in-repo record. See
`docs/agents/issue-tracker.md`.

### Triage labels

The five canonical labels verbatim on GitHub (`needs-triage`, `needs-info`,
`ready-for-agent`, `ready-for-human`, `wontfix` — the last already shared with this repo's
`bugs/` status vocabulary), each with a documented projection onto the in-repo record
`status` fields for when an issue graduates. No completion or in-progress label: those are
already carried by the record's own status transition and by GitHub assignment. See
`docs/agents/triage-labels.md`.

### Domain docs

**Single-context** — `CONTEXT.md` + `docs/adr/` at the repo root, neither of which exists
yet (created lazily by `/domain-modeling`; their absence is not a defect). Scoped to the
harness and tooling (`viewer/`, `.claude/`, `.githooks/`, `scripts/`) — **not** to survey
content under `surveys/**`, which is governed by `order.json`, `references.md`, and
`.claude/rules/`. For "why we did it this way", prefer a `decisions/` record: that is the
mandated, mechanically-checked convention here. See `docs/agents/domain.md`.
