Enrich the specified survey section(s): $ARGUMENTS

## Argument parsing

The user may specify:
- **Survey** by shorthand ("attention/transformer survey", "scaling-laws survey", "RLHF/alignment survey", "RAG survey", "coding-LLM survey") or file path. Resolve shorthand by matching against filenames in `surveys/`. For a split survey, the target is a specific file under the survey's subdirectory (e.g. `surveys/llms-for-coding/`).
- **Section(s)** by number ("§7.4", "section 8.1", "8.1", "Appendix B") — one or several. Accept `§`, `section`, or bare numbers as equivalent.
- **Enrichment direction** (optional): "with derivations", "with evidence from [papers]", "add missing steps", "add cross-references". If omitted, assess what's missing and choose the right mode.

## Enrichment modes

Assess which mode(s) apply based on the section's current state and the user's direction:

1. **Derivation** — section has bare equations or results without step-by-step math. Expand to first-principles derivations with definitions, assumptions, intermediate steps, and intuition. Target depth: neighboring enriched sections (typically ~80-100 words per equation).
2. **Evidence** — claims lack citations or cite secondary sources. Find primary sources (LLM/AI papers — NeurIPS, ICML, ICLR, ACL/EMNLP, arXiv — plus model cards and eval-harness documentation), verify facts, add citations with `<!-- cite:N -->` markers, correct errors found in primary sources. Never write a citation from memory — acquire the source first (`source-fetch`) per `.claude/rules/citation-integrity.md`.
3. **Structural** — section is a thin stub (few lines, no subsections). Restructure into subsections with comparison tables, parameter tables, worked examples, and practical context.
4. **Cross-reference** — section lists methods or results without pointing to their derivations elsewhere in the survey. Add equation/section cross-references.

Multiple modes may apply to a single section. Apply all that are needed.

## Workflow

1. **Resolve survey file.** Match the user's shorthand to a file in `surveys/`. For a split survey, identify which file under the survey's subdirectory (e.g. `surveys/llms-for-coding/`) contains the target section.
2. **Find section line range.** Check for a companion `.index.md` file. If none exists, run `python viewer/tools/build-index.py <file>` (when present). Read the index to get the target section's line range.
3. **Read only the target section** using offset/limit. Also read the immediately preceding and following sections (first 10 lines each) for context on depth and style.
4. **Assess current state.** Note: equation density, citation density, subsection structure, unsupported claims, derivation gaps. Compare against neighboring sections.
5. **Enrich.** Apply the appropriate mode(s). Follow all rules from `.claude/rules/` (equation markers, citation markers, display-math formatting, no split inline math, `\lvert`/`\rvert` in tables).
6. **Validate.** Run in order:
   - `python viewer/tools/renumber-equations.py <file>` (or the survey's `renumber-all.sh` for a split survey, e.g. `surveys/llms-for-coding/renumber-all.sh`)
   - `python viewer/tools/link-references.py <file>`
   - `python viewer/tools/build-index.py <file>` (when present)
7. **Report.** State what was added: number of new equations, new subsections, new references, new lines.

## Multi-section requests

When the user requests multiple sections in one command, process them sequentially in document order. Run validation once after all sections are done.

## Delegation

For large enrichment tasks (3+ sections, or a section that needs both derivation and evidence enrichment), consider delegating to the `survey-enricher` agent via the Agent tool. Provide the agent with: survey file path, target section number(s), enrichment direction, the relevant `.claude/rules/` (math-authoring, citation-integrity), and any specific papers to integrate. Dispatch survey/citation work per the Agent Fan-Out model-selection guidance in `CLAUDE.md` (keep correctness-gating evidence work on Opus).
