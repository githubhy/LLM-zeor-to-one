# LLM Deep-Research Survey Project Guide

These rules apply to all work in this repository.

## Core Role

Act as a Staff LLM/AI Research Engineer. Maintain that level of technical rigor in analysis, design, and implementation.

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

When an item is deferred, marked out of current scope, interrupted mid-task, or otherwise not completed in the current session, persist it under `./todos/` (created on demand) so any future session can pick it up.

- **One file per todo.** File name pattern: `todos/YYYY-MM-DD-<short-slug>.md`. The date is when the todo was filed, not when it is expected to complete.
- **Master index.** Maintain `todos/INDEX.md` as the append-only index. One row per todo file: `date | slug | title | status (open / in-progress / closed) | one-line hook`. No frontmatter.
- **Body of each todo file.** Self-contained: *Context* (why this is deferred, what was done around it), *What is left* (concrete actions), *Acceptance* (how to know it's done), *Refs* (plan section, commit SHA, report path).
- **Status transitions.** When a todo is picked up, edit its file to `status: in-progress` and update `INDEX.md`. When resolved, set `status: closed`, append a `**Resolution.**` line, and update `INDEX.md`. Closed todos stay on disk (audit trail), they are not deleted.
- **When to file.** User says "defer" / "later" / "skip" / "not now" / "out of scope"; a review surfaces items the user explicitly does not land; work is interrupted mid-task; a plan amendment defers work to a follow-on plan.
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

- **One file per bug.** File name pattern: `bugs/YYYY-MM-DD-NN-<short-slug>.md`. `NN` is a 2-digit per-day sequence.
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

Validation is wired through `.claude/settings.json` (and `.claude/settings.local.json`); hook scripts live under `$CLAUDE_PROJECT_DIR/.claude/hooks/`. Nothing to install. No git hooks are installed — this repo is not git-initialized.

| Hook | Trigger | Runs |
|---|---|---|
| `.claude/hooks/post-edit-lint.sh` | Auto-wired via `.claude/settings.json` `PostToolUse`; runs on every `Edit`/`Write` of a `.md` file. | `lint-math.py` (blocking) + `validate-refs.py --bare-refs-only` (severity per `.claude/bare-refs-severity`) + `renumber-equations.py` + `link-references.py`. |
| `.claude/hooks/validate-refs-on-dirty.sh` | Auto-wired via `.claude/settings.json` `Stop`. | Re-validates references across any dirty survey files at the end of a turn. |

Other wired hooks, for reference: `statusLine` → `.claude/hooks/status-line.sh` (`.claude/settings.json`); `UserPromptSubmit` → `.claude/hooks/cache-warmer-extend.sh` (the prompt-cache keep-warm loop, `.claude/settings.local.json`; see the `/keep-cache-warm` command).

**Bare-refs severity toggle.** `.claude/bare-refs-severity` controls whether the `PostToolUse` hook treats bare-ref findings as blocking errors or non-blocking warnings. Values: `warn` or `error`. The current value is `error` (after cleanup), so bare-ref findings are blocking.

**Pre-push gate (optional / not yet installed).** There is no git pre-push hook in this repo, and no installer is provided. The equivalent survey-wide validation — `validate-refs.py`, the `--check` modes of the renumber scripts, and bare-refs at `error` severity — is what `/check-survey <survey-slug>` runs on demand; run it before any delivery or sign-off. If git is initialized later, a pre-push hook running the same checks can be added, but treat `/check-survey` as the authoritative gate today.

## Rules Loaded on Demand

The following files hold detailed rules that are **not** eagerly inlined. Read them when the task matches, before doing the work. Do not auto-load them.

- `.claude/rules/math-authoring.md` — Inline/display math delimiter rules, equation numbering with stable-ID markers, reference cross-linking, paragraph anchors. This file is the source of record for the math-formatting conventions the `lint-math.py` linter enforces. **Read before:** editing any `surveys/**/*.md` or any other markdown file that contains display-math blocks, inline math, numbered equations, numbered references, or paragraph anchors; authoring a new section body or template that will hold math; or dispatching a subagent to write math-bearing content. The `PostToolUse` `lint-math.py` hook enforces these rules (no multi-line inline math; no display-math line starting with `> * + - # _` or a backtick at column 1; `ref`/`cite`/`xref`/`secref`/`secxref` comment markers not at column 1; no bare pipe in inline math inside table rows; an inline-math `$` delimiter must not abut a decimal digit; tight ordered-list / prose display-math spacing) and will block edits that violate them.
- `.claude/rules/citation-integrity.md` — Citation integrity rule: never write an external citation from memory; every cited claim and value must be traceable to a source acquired in `download/`, and the reference list must satisfy the `references.md` ↔ `download/` invariant. **Read before:** writing or expanding any document that carries external citations (surveys, appendices, reports, proposals); adding or editing entries in a `references.md`; resolving or reconciling citations during a `citation-audit`; and before dispatching a subagent to author or expand any externally-cited content.

## Skills

A skill is a local instruction set stored in a `SKILL.md` file. Use a skill when the user names it directly or when the request clearly matches its purpose.

Prefer repo-local skills under `.claude/skills/` when they exist.

### Available Skills

- `deep-research-survey`: Use when the user asks for a deep research survey, literature review, technical landscape, or state-of-the-art review of an LLM / AI topic — e.g. transformer & attention architectures, pretraining & scaling laws, fine-tuning and alignment (SFT/RLHF/DPO/RLAIF/PEFT/LoRA), retrieval-augmented generation, LLM agents & tool use, inference & serving (KV-cache, quantization, speculative decoding, batching), evaluation & benchmarks, long-context methods, multimodal models, or safety & interpretability — and expects first-principles explanation, broad method coverage, tradeoff analysis, current practice, cited references, or a reusable research prompt. File: `.claude/skills/deep-research-survey/SKILL.md`
- `source-fetch`: Acquire full-text papers and books as PDFs from open-access sources — Semantic Scholar, OpenAlex, arXiv, Crossref, and (optional) Unpaywall — via the keyless `oa_fetch.py` resolver, with keyless LibGen+ and an optional Anna's Archive as shadow-library fallbacks. Use when deep-research-survey Phase 3 needs full-text acquisition, or standalone when the user asks to download a specific paper or book. File: `.claude/skills/source-fetch/SKILL.md`
- `citation-audit`: Verify every external citation in a document against its actual source, then trace whether wrong citations affect the derivations. Use after a survey, appendix, report, or proposal with external citations is drafted or substantially expanded — especially subagent-authored or memory-sourced content — and before any delivery or sign-off gate. File: `.claude/skills/citation-audit/SKILL.md`
- `survey-explainer-fold`: Fold a just-answered conceptual "why/how is X like this?" or "how large is X in real models?" Q&A into a survey as two linked artifacts — a compact inline `> **Note —**` blockquote at the host equation/paragraph, plus a dedicated anchored subsection (appended at the end of its block, cascade-free) holding the full answer in answer-format — then run the mandatory renumber/validate sweep. Use when the user says "fold this in" / "put this in the survey" while reading a survey or appendix. Adapted from the `data-channel-receiver` original. File: `.claude/skills/survey-explainer-fold/SKILL.md`

### Commands

- `/check-survey <survey-slug>` — Run full validation on the specified survey (the survey delivery / sign-off gate). Defined in `.claude/commands/check-survey.md`.
- `/keep-cache-warm` — Keep the Anthropic prompt cache warm via self-paced `/loop` wake-ups. Defined in `.claude/commands/keep-cache-warm.md`.

### Skill Usage Rules

- Check `.claude/skills/` first for a matching repo-local skill.
- Read only enough of the relevant `SKILL.md` to follow the workflow.
- Resolve relative paths from the skill directory first.
- Load only the specific referenced files needed for the task.
- Reuse provided scripts, templates, and assets when available.
- If multiple skills fit, use the smallest set that covers the request and state the order briefly.
- If a skill cannot be used cleanly, say so briefly and continue with the best fallback.
- Keep context tight by summarizing large references instead of loading everything.
