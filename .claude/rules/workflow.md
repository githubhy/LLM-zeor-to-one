# Workflow Rules

Loaded on demand by `CLAUDE.md`. Read this file before starting any task that produces a plan, report, diagram, proposal, survey, or math derivation, or any task that touches `docs/development-timeline.md`.

## Development Timeline

Maintain `docs/development-timeline.md` as the lightweight project timeline.

- Keep it markdown-native.
- Include a `Current Snapshot` table for quick status updates.
- Include a visual roadmap section.
- Include a milestone table aligned with `docs/implementation-roadmap.md`.
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

### Implementation

When the user asks to implement an approved plan:

- Execute the plan end-to-end automatically without stopping for intermediate confirmation.
- When finished, write a full implementation report to `./reports/` as a markdown file.
- Present the report to the user.

## Diagram Rules

Every generated diagram must satisfy both of the following:

- Persistent data: save the underlying experiment or computation results so the figure can be regenerated later without rerunning the full workflow.
- Interactive behavior: support zoom, pan, or similar interaction unless the diagram is embedded in a document, in which case a static figure is acceptable.

Prototype and experiment code that backs a figure must be deterministic: seed numpy (`numpy.random.default_rng(seed)`) explicitly, and never call wall-clock or unseeded randomness (no `Date.now`-style time-seeding, no bare `numpy.random.*` without a fixed generator) inside a workflow or figure-generation script. The disclosed seed must be the seed actually used.

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
