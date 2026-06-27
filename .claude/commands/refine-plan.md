Review the plan at `$ARGUMENTS` thoroughly as a Staff Engineer, then update the plan in place to fix every issue you find.

## Phase 1 — Review

Read the plan end-to-end. Also read every file the plan touches so your review is grounded in the real code (not the plan's description of the code). For each referenced file, verify:

- Line numbers cited in the plan still match.
- Function, variable, class, and selector names exist and are spelled correctly.
- DOM structure, regex patterns, and call sites match what the plan assumes.
- CSS selectors (`nth-child`, class combinations) resolve against the actual markup.

Audit the plan against this checklist:

- **Correctness** — Does every code snippet compile/parse? Are regexes valid? Do selectors match real DOM? Are cited line numbers and symbol names accurate? Any logic bugs (e.g., operator precedence, off-by-one, wrong variable)?
- **Completeness** — Are all touched files listed? Any missing step that would leave the feature half-wired (event listener not bound, state not invalidated, style not scoped)? Any cross-cutting concern ignored (undo/redo, persistence, a11y, keyboard focus, print, mobile)?
- **Consistency** — Do sections contradict each other? Do variable/function names stay consistent across sections? Does the implementation order match the dependencies between steps?
- **Assumptions** — What does the plan assume about the existing code that may not be true? Flag each one and verify against the real files.
- **Risks & failure modes** — What breaks under edge cases (empty input, concurrent edits, large files, stale cache, missing DOM node)? What are the rollback and undo semantics?
- **Scope** — Too broad (bundled unrelated work)? Too narrow (missing obvious adjacent fix)? Any dead code or unused helpers introduced?
- **Simplicity** — Any simpler alternative that achieves the same outcome with less code or fewer moving parts? Any premature abstraction?
- **Testing** — Are the manual smoke steps sufficient to catch the actual risks, or do they only test the happy path?

Be direct and critical. Every issue must be concrete: cite a file, line, or snippet from the plan. Vague concerns are not useful.

## Phase 2 — Update the plan

After the review, edit the plan file in place to fix every issue you identified. Do not produce a separate review document — the fixes belong in the plan itself.

- Bump the `Rev:` header (if present) and add a one-line note describing what changed.
- Correct wrong line numbers, symbol names, selectors, and snippets.
- Add missing steps, missing files, and missing edge-case handling.
- Rewrite ambiguous instructions to be precise and actionable.
- Remove contradictions and dead sections.
- Tighten the manual smoke test list so it exercises the risks you flagged.
- Preserve the plan's existing structure and voice; do not rewrite sections that were already correct.

## Phase 3 — Report

End with a concise summary (under 150 words) listing the categories of issues fixed and any residual risks that the user still needs to decide on. Do not restate the full review — the diff against the plan is the record.
