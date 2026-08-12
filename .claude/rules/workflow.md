# Workflow Rules

Loaded on demand by `CLAUDE.md`. Read this file before starting any task that produces a plan, report, diagram, proposal, survey, or math derivation, or any task that touches `docs/development-timeline.md`.

## Development Timeline

Maintain `docs/development-timeline.md` as the lightweight project timeline.

- Keep it markdown-native.
- Include a `Current Snapshot` table for quick status updates.
- Include a visual roadmap section.
- Include a milestone table. (This bullet used to require alignment with
  `docs/implementation-roadmap.md`, a file that has never existed in this repo — a dangling
  requirement no one could satisfy or check. The timeline's milestone table is self-contained.
  If a separate roadmap document is ever created, re-add the alignment requirement then.)
- Include a dated `Update Log`.
- Update `Current Snapshot` whenever status, phase, dates, or key notes change.
- Update the visual roadmap only when phase ordering, dates, statuses, or major structure changes.
- Append to the `Update Log` for meaningful deliveries, blockers, or re-scopes.
- Use only these statuses unless the user says otherwise: `Planned`, `Active`, `Blocked`, `Done`.

## Plan and Implementation Workflow

### Planning

When a task requires a plan:

- Develop the plan, then save it to `./plans/` as a markdown file.
- Ask the user to review before proceeding. Do not implement until the user approves.
- **A plan that ships code names its RED-first test deliverable per phase — the test module, and the
  discriminating input it must FAIL against before the implementation makes it pass.** A phase's exit
  criterion is not met until that test passes. This is `[opt:RIS-RED-FIRST]`
  (`.claude/skills/reference-implementation-study/phases/phase-2-implementation.md`, default ON)
  routed to the moment the plan is *written* rather than the moment code is: the rule already existed
  and was already default-on, and still did not fire, because nothing connects "I am authoring a
  plan" to "this plan ships parsers." The failure mode it guards is *silent success* — an extractor
  that exits 0 having converted a fraction of its input, a parser that returns an empty match set
  and reports no error. A promise to verify is not a deliverable; a named failing test is.
  `[opt:PLAN-REDFIRST · default ON · toggle .claude/skill-options.json]`

### Implementation

When the user asks to implement an approved plan:

- Execute the plan end-to-end automatically without stopping for intermediate confirmation.
- When finished, write a full implementation report to `./reports/` as a markdown file.
- Present the report to the user.

## Diagram Rules

Every generated diagram must satisfy both of the following:

- Persistent data: save the underlying experiment or computation results so the figure can be regenerated later without rerunning the full workflow.
- Interactive behavior: support zoom, pan, or similar interaction unless the diagram is embedded in a document, in which case a static figure is acceptable.

Prototype and experiment code that backs a figure must be deterministic: seed numpy (`numpy.random.default_rng(seed)`) explicitly, and never call wall-clock or unseeded randomness (no `Date.now`-style time-seeding, no bare `numpy.random.*` without a fixed generator) inside a workflow or figure-generation script. The disclosed seed must be the seed actually used. For a torch-backed experiment the same discipline covers `torch.manual_seed`, `torch.cuda.manual_seed_all`, and the dataloader worker seed; disclose whether nondeterministic kernels were disabled, because attention and reduction kernels are not bit-reproducible by default.

Every repo tool/script that does file I/O with possibly-non-ASCII content must pass `encoding='utf-8'` — on both writes (`Path.write_text`, `open(path, 'w')`, `json.dump` to a handle) and reads (`Path.read_text`, `open(path)`, `json.load(open(path))`). On Windows the default is the locale code page (GBK/CP936), so a non-ASCII glyph (minus-sign `−` U+2212, `×`, superscript, em-dash, box-drawing) raises `UnicodeEncodeError` on write or `UnicodeDecodeError` on read. For stdout, set `PYTHONIOENCODING=utf-8` or route non-ASCII to a file. `[opt:UTF8-WRITE · default ON · toggle .claude/skill-options.json]`

A long-running job (a training run, an eval sweep, a batched generation) must be launched via the tool's own **`run_in_background: true`**, never via a trailing `&`, `nohup`, `setsid`, or `disown` inside a *foreground* tool call. On this harness a foreground tool call reaps its child processes when it returns, so a `&`/`nohup`-detached job is killed the moment the launching call completes — durable backgrounding is a property of the *launch mechanism*, not of `nohup`/`&` syntax. Additionally, design any long-running driver to flush and resume per unit of work (per-checkpoint, per-benchmark-shard, per-prompt-batch), so if a job is interrupted a relaunch re-uses completed units at zero recompute. Because the documented rule kept being violated upstream, it is **enforced by a PreToolUse gate** (`.claude/hooks/guard-foreground-background.py`, wired in `.claude/settings.json`): a foreground Bash call that backgrounds a job with a trailing `&`/`nohup`/`setsid`/`disown` is BLOCKED (exit 2) with a message to relaunch via `run_in_background: true`. The gate is high-precision (it never flags `&&`, fd-redirects, arithmetic `$((a & b))`, or a `&` inside quotes/comments) and fails OPEN. Operative runtime toggle: `.claude/foreground-bg-severity` (`off | warn | error`, default `error`; `warn` is advisory only and does NOT prevent the reap). `[opt:BG-RUNINBG · default ON · toggle .claude/skill-options.json]` `[opt:BG-GUARD · default ON · toggle .claude/foreground-bg-severity]`

**Exactly one live writer per resumable checkpoint file.** The flush-and-resume design above makes it tempting to "extend" a running job by relaunching it with a larger target — but relaunching *without killing the original* leaves two processes doing read-modify-write on the same checkpoint. To extend or re-scope a running job: **kill it first, then relaunch**; to run shards in parallel, give each its **own** output file and merge at analysis time. The tell in a corrupted run is a **non-monotonic** progress counter in the log (`…10000 11000 → 8000 9000…`) as the two writers clobber each other. Whether the clobbering also corrupts *values* depends on whether the per-batch seed is a deterministic function of the accumulated offset — **do not rely on that**, it is a property of one seeding scheme, not of checkpointing. Cheap audit before trusting a resumed artifact: the progress sequence in its log must be strictly increasing.

## Proposal Rules

When preparing a proposal:

- Review state-of-the-art (SOTA) practice first.
- Combine that research with domain judgment into a detailed, actionable proposal.
- Save the proposal under `./proposals/`.
- Do not move proposal content into `./docs/` unless the user explicitly asks to harden or persist it there.

## Survey Rules

When preparing a survey of a technology or algorithm:

- start from mathematical fundamentals before moving into higher-level discussion
- decompose the overall system into its core architecture and conceptual building blocks
- assemble a complete and thorough inventory of the methods, architectures, and implementation variants that can be found
- provide a rigorous first-principles mathematical derivation for every method, architecture, or implementation variant that is included
- state the practical advantages, limitations, and applicability boundaries of each item
- compare performance, complexity, implementation cost, and engineering tradeoffs
- review state-of-the-art (SOTA) practice and identify what is actually preferred in modern use
- close with the likely roadmap, next directions, and open technical gaps
- save the survey under `./surveys/`
- at sign-off, run the cross-link pass (`/cross-link` or `crosslink.py check`) over the new/expanded content and clear the reported high-value gaps, or file a `todos/` entry — per `.claude/rules/cross-linking.md`

Before editing any file under `surveys/`, also Read `.claude/rules/math-authoring.md` for equation numbering, reference cross-linking, and paragraph-anchor marker syntax.

## Math Derivation Rules

All derivations must be built from first principles and shown step by step.

- Do not skip steps.
- Include definitions, assumptions, numbered equations, and intuition for each major result.
- In multiline display equations, keep chained equalities compact on adjacent lines; do not place a standalone `=` on its own line.
- In standalone display math (between `$$` delimiters), never start a line with a character that markdown could interpret as formatting — specifically `>`, `*`, `+`, `-`, `#`, `_`, or `` ` ``. Restructure the expression so the symbol does not appear at column 1: move the operator to the end of the previous line, or use `\begin{aligned}...\end{aligned}` for multi-line equations. (Standard markdown/KaTeX renderers do not shield `$$` blocks from the parser, so this restructuring is mandatory.)
- Never split inline math (`$...$`) across multiple lines. Most markdown/KaTeX renderers require inline math delimiters and their content to be on a single line. If an inline expression makes a line too long, either shorten the expression or promote it to a display-math block (`$$...$$`).
- Inside markdown tables, never use a bare `|` (pipe) character in inline math — the markdown parser will interpret it as a column separator before KaTeX sees it. Use `\lvert` and `\rvert` for absolute value, or `\mid` for a conditional separator. For example, write `$\lvert x \rvert$` instead of `$|x|$`.

**Every quantity that can be measured on two bases declares which one, at the point of use.** In LLM
work the recurring pairs are: parameter count $N$ **non-embedding vs total** (the scaling-law
literature is split, and the gap is large enough at small scale to move a fitted exponent); token
budget $D$ **unique corpus tokens vs tokens seen** (they differ by the epoch count); batch size $B$
**sequences vs tokens**; a loss or entropy in **bits vs nats** (a factor $\ln 2$); context length in
**tokens vs characters**; throughput **per-accelerator vs aggregate**; and `pass@k` over **$k$
independent samples vs a single greedy sample**. Two values on different bases are never compared
without a stated reconciliation. `.claude/rules/calibration-residuals.md` check 4 already requires
this — but it owns the moment of **attribution**, and nothing owned the moment of **authoring**.
Mechanically gated by `viewer/tools/check-basis-declarations.py`.
`[opt:MATH-BASIS · default ON · toggle .claude/skill-options.json]`

**A new or materially-changed numbered derivation gets one independent re-derivation before it lands.**
The reviewer derives from first principles *before* reading the target text, and its findings are applied
or explicitly rejected with a reason; raw output is preserved under the document's `_scratch/`. Size it
per DRS-HARDEN — exact paths, no Glob, file-first incremental deliverable, under ~30 tool calls — and
keep it on **Opus**, because this is adversarial verification gating correctness. It catches a class a
value-checking oracle structurally cannot: an oracle confirms the arithmetic while the conclusion drawn
from it is inverted. **Oracles test values; re-derivation tests reasoning.**

**Mechanically gated by `viewer/tools/check-derivation-review.py`.** The trigger is an added or
modified `\tag{}` line in the push range; a renumber pass that only rewrites the tag *integer* does
not fire. Evidence is a `_scratch/review*.md` artifact under the survey, or an explicit
`Reviewed-by: <path>` commit trailer. **A NEW equation and a MODIFIED one carry different
requirements**, and collapsing them is what made the gate's first version pass the very range it
was written to fail: a correction may legitimately cite a review that *predates* it (that review is
what produced the fix, and demanding a further one would deadlock the cycle), but a brand-new
derivation needs evidence committed at or after the commit that introduced it, because nothing
earlier can have reviewed it. Severity `.claude/math-rederive-severity` (`off | warn | error`,
currently **`warn`**) with per-survey error opt-in in `.claude/math-rederive-strict`.
`[opt:MATH-REDERIVE · default ON · toggle .claude/skill-options.json]`
`[opt:MATH-REDERIVE-GATE · default ON · toggle .claude/math-rederive-severity]`
