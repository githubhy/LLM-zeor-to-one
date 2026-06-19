---
description: Expand one numbered equation into a multi-line, first-principles derivation with no intermediate step missing — same tag, no cascade — then run the validation sweep.
argument-hint: "<file> (<equation-number>)  e.g. surveys/llms-for-coding/appendix-a-qkv-first-principles.md (11)"
---

Enrich one numbered equation into a complete, **multi-line, first-principles** derivation in which **no intermediate step is missing**: $ARGUMENTS

Parse the arguments into a target `<file>` and an equation number `N`. Turn that equation's terse statement into a step-by-step `aligned` derivation, every line carrying the rule that justifies it, starting from definitions/results already established in the same document — **without changing the equation's number**, so nothing downstream renumbers.

Before editing, read `.claude/rules/math-authoring.md` (the aligned / tag / marker / delimiter rules enforced by `lint-math`) and, only if the equation involves an externally-sourced value, `.claude/rules/citation-integrity.md` (never introduce a value or citation from memory — a derivation is *proved inline*, not cited).

## Steps

1. **Locate the equation and its foundations.** Find the target's `<a id="eq-N"></a>` anchor, its `<!-- eq:ID -->` marker, and its `\tag{N}` in `<file>`. Read the surrounding prose and — crucially — the equations and definitions it rests on (the defining equation of every symbol that appears). The derivation must begin from those and reach the target using nothing that is not either a prior result in the document or an elementary rule (chain rule, quotient rule, a definition, a substitution, an algebraic identity).

2. **Set up the lead-in prose so each later line is one rule.** Rewrite the sentence that introduces the equation to make the derivation self-contained: name the starting definition (with a marked ref to its equation, e.g. ``<!-- ref:ID -->[(M)](#eq-M)``), introduce any abbreviation the steps will reuse (e.g. a normalizer `Z`), and state the elementary facts the steps invoke (e.g. "the chain rule gives …; only the m-th term depends on …"). State any domain restriction the derivative needs (e.g. an unmasked index). End the sentence with a colon leading into the equation.

3. **Replace the equation with a multi-line `aligned` block, same tag.** Convert the single line (or compressed `=` chain) into a fully stepped block:

   ````markdown
   <a id="eq-N"></a><!-- eq:ID -->
   $$
   \begin{aligned}
   \text{LHS}
   &= \text{first rewrite}        &&\text{(the rule applied)}\\
   &= \text{next form}            &&\text{(the rule applied)}\\
   &= \text{target RHS}.          &&\text{(final rule)}
   \end{aligned} \tag{N}
   $$
   ````

   - **Keep the original `\tag{N}` and the `<!-- eq:ID -->` marker / `<a id="eq-N">` anchor unchanged** — same number, same ID. This is what prevents an equation-number cascade and keeps every existing `<!-- ref:ID -->` to this equation valid (no ref edits needed).
   - **One algebraic move per line**, each annotated on the right with ``&&\text{(justification)}`` — the rule, substitution, cancellation, or prior equation that licenses that line. If a line would bundle two non-obvious moves, split it into two lines. That is the "no intermediate step missing" contract.
   - Put `\tag{N}` immediately after `\end{aligned}`, before the closing `$$` (the corpus convention; same placement the document's other `aligned` block uses).
   - If the source equation was already a compressed multi-`=` chain on one render line, expand every `=` into its own justified `aligned` line.

4. **Remove now-redundant prose.** If the new lead-in introduces a symbol or fact that the post-equation prose used to introduce (e.g. "with δ the Kronecker delta"), delete the duplicate so the surrounding text still reads cleanly.

5. **Run the validation sweep** (paths relative to repo root; `<dir>` is the survey directory containing `<file>`):

   ```bash
   python viewer/tools/renumber-equations.py  <file> --check   # MUST stay sequential — proves no cascade
   python viewer/tools/renumber-sections.py   <dir>  --check
   python viewer/tools/renumber-paragraphs.py <file> --check
   python viewer/tools/link-references.py      <dir>  --check
   python viewer/tools/validate-refs.py        <dir>
   python viewer/tools/validate-refs.py --bare-refs-only --severity=error <dir>
   python viewer/tools/check-citation-sources.py <dir>/references.md
   ```

   `lint-math.py` already ran (and blocked the edit, if needed) via the PostToolUse hook. A green `/check-survey <survey-slug>` is the equivalent one-command gate — run it for sign-off.

6. **Log** the turn per `CLAUDE.md` Conversation Logging (one `## Conversation N` entry, `📒` indicator). Commit only if the user asks.

## Rules the derivation must obey

- **No new equation numbers.** The block stays one equation with one `\tag{N}`. Do **not** split the derivation into several numbered equations — that cascades every later tag and breaks refs. (Verbatim multi-line content that genuinely should *not* be numbered belongs in a fenced block instead; but a derivation *of an existing numbered equation* stays that one tag.)
- **KaTeX-safe macros only** (this viewer is KaTeX via markdown-it-texmath): use `\left( … \right)` (not `\big`), `\frac`, `\mathrm`, `\mathbf`, `\sum`, `\delta_{jm}`, `\vdots`, etc. Multi-line alignment is `\begin{aligned} … \end{aligned}` with `&=` columns, ``&&\text{(…)}`` annotations, and `\\` row breaks.
- **A blank line must follow the closing `$$`** (else the next paragraph's inline math renders as literal source).
- **No display-math line may begin with** `>` `*` `+` `-` `#` `_` or a backtick at column 1; `aligned` lines begin with `&=` or a macro, which is safe.
- **Inline math in the lead-in must respect the digit-abut rule**: an opening `$` may not follow a digit and a closing `$` may not precede one — keep numerals inside the math span (`$10^\circ$`, not `10$^\circ$`).
- **Reference other equations only in prose, via the marked form** ``<!-- ref:ID -->[(M)](#eq-M)``; never a bare `Eq. (M)`. Inside the `aligned` block, name the *rule* in `\text{…}`, not an equation number, so the bare-ref check stays clean.

## Worked example (the pattern this command generalizes)

Equation 11 of `surveys/llms-for-coding/appendix-a-qkv-first-principles.md` — the softmax Jacobian — expanded from one line to a six-step `aligned` derivation: softmax definition → quotient rule → substitute the two elementary derivatives → split and cancel → recognize the softmax weights → factor; each line annotated, same `\tag{11}`, no cascade. The lead-in was first rewritten to define the normalizer `Z_i` and state the two elementary derivatives, and the redundant "Kronecker delta" clause after the equation was removed. Session `prompts/2026-06-17-viewer-sync.md`.
