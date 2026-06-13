---
description: Equation numbering, cross-reference markers, and bibliography link syntax for survey authoring
globs: ["surveys/**/*.md"]
---

# Inline Math Delimiters

The viewer uses `markdown-it-texmath@1.0.0` with the `dollars` delimiter rule. Its `$_pre`/`$_post` hooks impose two rules that KaTeX itself does not enforce:

- **Opening `$` cannot be preceded by a decimal digit (0–9).** `10$\degree$` fails because the opening `$` follows `0`. The plugin emits a literal `$` and the math fragment renders as source.
- **Closing `$` cannot be followed by a decimal digit (0–9).** `$\pm$200`, `$-$10.2`, `$\sim$0.01`, `$\S$3.6`, `GPT$\times$2` all fail at the closing `$` because the next char is a digit. Letters (`$\degree$C`, `$^\circ$C`) are still allowed on the closing side.

When a single failure occurs the parser cascades — adjacent `$...$` pairs on the same line often render literally as well, because the unmatched `$` shifts pair detection.

**Convention.** Keep the numeric token *inside* the math span instead of fragmenting a symbol into a bare `$X$` next to digits:

| Don't | Do |
|---|---|
| `10$\degree$` | `$10^\circ$` |
| `$\pm$200 tokens/s` | `$\pm 200$ tokens/s` |
| `$-$10.2 GB` | `$-10.2$ GB` |
| `$\sim$0.01` | `$\sim 0.01$` |
| `$\S$3.6` | `$\S 3.6$` |
| `GPT$\times$2` | `GPT$\times 2$` |
| `2.1$^*$` | `$2.1^*$` |
| `$<$0.1 tokens/s` | `$<0.1$ tokens/s` |

The `lint-math.py` linter walks each non-display, non-fence line tracking inline `$` open/close state and flags any opening `$` preceded by a digit or any closing `$` followed by a digit as an error. The PostToolUse hook will block edits that introduce these patterns.

# Equation Numbering and Cross-References

Every standalone display-math equation (`$$...$$`) must be numbered with `\tag{N}`. Use a stable-ID marker system so that inserting or removing equations does not require manual cascading renumber.

**Equation markers.** Place a unique HTML-comment marker on the line immediately before the opening `$$`. The renumber script will prepend an `<a id="eq-N">` anchor for clickable cross-references:

```markdown
<a id="eq-1"></a><!-- eq:SECTION-N -->
$$
\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right)V \tag{1}
$$
```

**Cross-reference markers.** When prose references an equation by number, place a ref marker immediately before a Markdown link to the equation anchor:

```markdown
Substituting Equation <!-- ref:SECTION-N -->[(1)](#eq-1) into ...
```

When writing new refs, use the bare form `<!-- ref:SECTION-N -->(N)` — the renumber script will convert it to the linked form automatically. **Never let a `<!-- ref:... -->`, `<!-- cite:... -->`, `<!-- xref:... -->`, `<!-- secref:... -->`, or `<!-- secxref:... -->` comment be the first non-blank, non-list-marker content of a block** (i.e., at column 0–3 in a paragraph, or as the first child of a list item with only `- `/`* `/`N. ` and whitespace before it). CommonMark parses any line whose first content is `<!--` as a Type-2 HTML block, and the block ends on the line containing `-->`, so whatever follows the marker on the same line (a markdown link, inline math, etc.) is consumed as raw HTML and rendered literally rather than parsed as markdown. The list-item case fails the same way because CommonMark parses list-item content as a sub-document — the same Type-2 trigger fires inside the `<li>` and swallows the link as raw text. Both cases fail on the local markdown-it viewer (empirically reproduced 2026-05-25 against a live viewer probe, see bug `2026-05-25-01`), not just GitHub. Always keep these comments inline after preceding prose, a glyph like `§`, or a paragraph anchor on the same line; the `lint-math.py` hook enforces this.

**ID format.** Use `SECTION-N` where `SECTION` is the containing section number (lowercase, e.g. `5.2.3`, `a.8.3`) and `N` is a sequential index within that section. Choose IDs that are stable across insertions — adding a new equation in one section does not change IDs in other sections.

**Renumber script.** Each document that uses this system must have a companion `renumber-equations.py` (or equivalent) that:

1. Scans `<a id="eq-3"></a><!-- eq:ID -->` markers in document order and assigns sequential `\tag{1}`, `\tag{2}`, ...
2. Inserts or updates `<a id="eq-N"></a>` anchors on each marker line.
3. Scans `<!-- ref:ID -->` markers and updates `[(N)](#eq-N)` links (converting bare `(N)` to linked form).
4. Reports orphaned refs (ref ID not matching any eq ID) and duplicate eq IDs.
5. Supports a `--check` dry-run mode.

**Workflow.** After adding, removing, or reordering equations:

1. Add or remove the `<a id="eq-3"></a><!-- eq:ID -->` marker. For new equations, add `<!-- ref:ID -->` markers at every prose reference.
2. Run the renumber script.
3. Verify: the script must exit cleanly with all tags sequential and no orphans.

Never manually renumber equations by hand. Always use the script.

# Reference Cross-Linking

Documents with a numbered reference list (e.g., `[1]`, `[2]`, ... in a `## References` section) use a marker system for clickable citation links.

**Bibliography markers.** Place a marker and anchor on the line immediately before each reference entry:

```markdown
<a id="ref-1"></a><!-- bib:1 -->
[1] A. Vaswani et al., "Attention Is All You Need," NeurIPS 2017. arXiv:1706.03762
```

**Citation markers.** When prose cites a reference by number, place a cite marker immediately before the linked number:

```markdown
...as specified in <!-- cite:1 -->[[1]](#ref-1) and <!-- cite:2 -->[[2]](#ref-2).
```

When writing new citations, use the bare form `[N]` — the link-references script will convert it to the marked+linked form automatically via `--init`.

Compound citations `[N, M]` are split into individual linked entries: `<!-- cite:N -->[[N]](#ref-N), <!-- cite:M -->[[M]](#ref-M)`.

**Link-references script.** Each document that uses this system must have a companion `link-references.py` (or equivalent wrapper to `viewer/tools/link-references.py`) that:

1. Scans `<!-- bib:N -->` markers and inserts/updates `<a id="ref-N"></a>` anchors.
2. Scans `<!-- cite:N -->` markers and updates `[[N]](#ref-N)` links.
3. Reports orphaned citations (cite with no matching bib) and uncited references.
4. Supports `--check` (dry-run) and `--init` (one-time migration from bare `[N]` to marked form) modes.

**Workflow.** After adding or removing references:

1. Add the `<!-- bib:N -->` marker before new reference entries.
2. Add `<!-- cite:N -->` markers at in-text citations (or use bare `[N]` and run `--init`).
3. Run the link-references script.
4. Verify: the script must exit cleanly with no orphaned citations.

**Bare-form prohibition.** Bare same-document `Eq. (N)` mentions in prose are forbidden; every reference to a same-document equation must carry a `<!-- ref:ID -->` marker and the `[(N)](#eq-N)` linked form. `validate-refs.py` check #11 enforces this. External-paper Eq citations are exempt when they sit inside a citation context (author-year, bracketed `[bib-N, Eq (...)]`, or `Source:` line) — see the rule's exemption list.

# Section Cross-Linking

Documents with numbered sections (e.g., `### 3.7.6 Scaled Dot-Product Attention`) use a marker system parallel to the eq-N / ref / xref scheme for clickable section cross-references.

**Section anchors.** Place a marker on the line above each numbered heading; the renumber script will inject a matching `<a id="sec-X.Y.Z"></a>` anchor **immediately after the `### ` (or `####`, etc.) ATX prefix**, before the visible heading text:

```markdown
<!-- sec:3.7.6 -->
### <a id="sec-3.7.6"></a>3.7.6 Scaled Dot-Product Attention
```

The anchor must NOT precede the `#` characters. CommonMark requires the ATX prefix to start at column 0–3, and any leading inline HTML (like an `<a id>`) demotes the line to a paragraph with literal `### ` visible in the rendered body — every numbered heading would render as plain prose instead of as `<h3>`/`<h4>`/etc. The failure mode was empirically reproduced 2026-05-25 against `markdown-it@14.1.0` and the live viewer (819 affected lines corpus-wide before the migration). See bug `2026-05-25-02` and `plans/heading-anchor-architecture-2026-05-25.md` for the architectural rationale (Option A1 — anchor inline after the ATX prefix is the only placement that satisfies both stable `sec-X.Y.Z` IDs and GitHub-compatible heading rendering). The `inject_heading_anchor()` function in `renumber-sections.py` performs the placement and migrates any pre-existing column-0 anchors to the correct position on its next run; `lint-math.py` check #11 catches regressions.

Section numbers may be digit-first (`3.7.6`, `4.4`, `10.2.1`) or letter-dot (`D.7`, `D.7.5`, `A.8.3`). Both forms are accepted by `renumber-sections.py` and `validate-refs.py` check #12.

**Sub-section landmarks.** Bold or italic landmark phrases of the form `**<Kind> <Index>**` (e.g., `**Step 3 — Recombine.**`, `**Lemma D.6-A**`) inside a numbered section get their own anchor. The renumber script's heuristic auto-injects `<a id="sec-X.Y.Z-<kind>-<index>"></a>` for landmarks whose `<Kind>` is in the configurable `LANDMARK_KINDS` list (`Step | Stage | Phase | Case | Part | Path | Variant | Branch | Note | Item | Assumption | Lemma | Theorem | Proposition | Corollary | Definition | Example | Remark | Algorithm | Procedure | Fact | Claim | Table | Figure`) and whose `<Index>` is an enumerator-shaped token (a digit, single letter, or compound ID like `D.6-A`).

**Section ref markers.** When prose references a section by number, place a ref marker immediately before a Markdown link to the section anchor:

```markdown
Substituting <!-- secref:3.7.6 -->[§3.7.6](#sec-3.7.6) into ...
See <!-- secxref:3.7.6 -->[§3.7.6](fundamentals.md#sec-3.7.6) for the derivation.
See <!-- secref:3.7.6-step-3 -->[§3.7.6 Step 3](#sec-3.7.6-step-3) for the recombine step.
```

Use `secref:` for same-file refs and `secxref:` for cross-file refs.

When writing new refs, use the bare form `§X.Y.Z` (or `§X.Y.Z Kind N` for a sub-landmark) — `renumber-sections.py --init` converts bare forms to the marked + linked form automatically.

**Bare-form prohibition.** A bare `§X.Y.Z` mention in prose that is *not* inside a marker + link is forbidden; `validate-refs.py` check #12 enforces this. The bare-form prohibition is the gate that ensures every section reference is clickable.

**External-spec section refs.** When prose mentions a section number that belongs to an EXTERNAL standard (IEEE, RFC, etc.) rather than to a section within the local survey corpus, the `§X.Y.Z` is not a candidate for auto-linking. Wrap it in a single pair of square brackets — `[RFC 8259 §7]` or `[§7]` — so the linter's bracket-span exclusion silences the bare-ref check. This is the same exclusion that handles `[Smith 2020, §17.5]` author-year+section citation forms. The bracket-wrap is the canonical opt-out for prose section numbers that should not be auto-linked.

**Renumber script.** `viewer/tools/renumber-sections.py` has the same contract as `renumber-equations.py`:

1. Walk the document; at each `### X.Y.Z …` heading, inject the `<!-- sec:X.Y.Z -->` marker and `<a id="sec-X.Y.Z">` anchor (if missing).
2. Walk content lines and detect sub-section landmarks via the heuristic; inject sub-anchors (if missing).
3. Walk `<!-- secref:ID -->` markers and rewrite the visible link to `[§X.Y.Z](#sec-X.Y.Z)` form.
4. Walk `<!-- secxref:ID -->` markers and resolve the owning file via the survey's `order.json`; rewrite the visible link to `[§X.Y.Z](owner.md#sec-X.Y.Z)` form.
5. Report orphaned refs (marker with no matching anchor), duplicate section numbers, and unresolved bare refs (with `--init`).
6. Supports `--check` (dry-run), `--init` (bulk bare-ref promotion), and `--dry-run-diff` (preview unified diff) modes.

**Workflow.** After adding, removing, or reordering sections:

1. For new sections, the `--init` pass detects the heading and injects the anchor.
2. For ordinary edits, run `python viewer/tools/renumber-sections.py <file>` without `--init` to keep anchors in sync.
3. Verify: `--check` exits cleanly with no orphans.

The `/check-survey` command runs `--check` so CI catches drift before it lands.

# Ordered Lists Containing Display Math

GitHub's CommonMark parser has two failure modes around ordered-list items that embed `$$...$$` display math. The local viewer (markdown-it + markdown-it-texmath) handles both cases permissively, so these bugs are invisible on the dev loop and only surface on the public GitHub rendering. `lint-math.py` catches both at author time.

**Failure mode 1 — list restart numbering.** If a `$$` close is followed by a blank line and then the next `N.` marker, GitHub ends the list at the blank line and renumbers the next item from 1. Source `1. 2. 3. 4.` renders as `1. 1. 1. 1.` on GitHub.

```
1. Step:
   $$
   eq
   $$
                    ← blank line
2. Next.            ← renders as "1." on GitHub
```

**Fix:** keep list items tight — no blank lines between consecutive ordered-list items that contain `$$...$$`:

```
1. Step:
   $$
   eq
   $$
2. Next.            ← renders as "2." on GitHub
```

**Failure mode 2 — inline-math dropout in continuation.** If a `$$` close is followed by a continuation paragraph inside the same list item, and that paragraph contains inline `$...$` math, GitHub fails to render the inline math. Every `$x$` in the continuation renders as literal source text:

```
1. Compute X:
   $$
   X = ...
   $$
   where $d_k = 64$ is the per-head dimension.
         ^^^^^^^^^^^
         renders as literal `$d_k = 64$` on GitHub
```

**Fix:** keep list items minimal — only the step's core artifact (equation, short phrase). Move prose elaborations with inline math *outside* the list as a standalone bold-headed paragraph before or after:

```
**Scaling factor $\sqrt{d_k}$.** The quantity $\sqrt{d_k}$ is the...
                     (long explanation with inline math)

1. Compute the scaled scores at step $t$:
   $$
   S(t) = \frac{Q K^\top}{\sqrt{d_k}} \tag{2}
   $$
2. Apply the softmax...
```

**Failure mode 3 — inline-math dropout in next-item opener.** Same parser-state pollution as failure mode 2, but the inline `$...$` math sits in the *opener line of the next list item* rather than a same-item continuation paragraph. GitHub fails to render the inline math: `2. Normalize the scores into $p$:` immediately after the previous item's `$$` close renders with `$p$` literal:

```
1. Compute X:
   $$
   X = ...
   $$
2. Solve for $p$:               ← `$p$` renders as literal source on GitHub
   $$
   p = ...
   $$
```

**Fix:** lift the symbol out of the opener — define the symbol once in a setup paragraph *before* the list, and use plain prose in the openers:

```
**The procedure** uses logits $z$, probabilities $p$, and...

1. Compute the logits:
   $$ z = ... $$
2. Apply the softmax to obtain the probabilities:
   $$ \mathrm{softmax}(z)_i = \frac{e^{z_i}}{\sum_j e^{z_j}} $$
```

All three failure modes are enforced by `lint-math.py` check #6. Running the lint hook at edit time surfaces these failures before they reach GitHub.

# `$$` Display Blocks Need a Blank Line After the Close

A `$$...$$` display block in *plain prose* (not a list item) whose close `$$` is immediately followed by a non-blank, non-`$$` line — i.e., the continuation paragraph begins on the very next line with no blank-line gap — causes the **continuation to inherit parser state from the math block**. Every inline `$...$` math span (and every `<!-- ref:... -->`-style reference link) in that continuation renders as **literal source** — `$x$` shows up as the four characters `$`, `x`, `$` rather than as italic *x*. Unlike the ordered-list failure modes above, this one fails on the local viewer too, not just on GitHub.

Bug `2026-05-21-03`. Example failure (`appendix-e.md` §E.5.1 before the fix):

```
$$
w \equiv p_\tau(x) = \Pr(X \leq x \mid \tau).
$$
By construction $w \in [0, 1)$ for $\tau < \infty$, ...
                ^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^
                both render as literal `$...$` text
```

**Fix:** insert a single blank line after the `$$` close. Reading flow is preserved — `$$ equation $$` then paragraph break then prose reads the same as the bug pattern, and the math now renders correctly:

```
$$
w \equiv p_\tau(x) = \Pr(X \leq x \mid \tau).
$$

By construction $w \in [0, 1)$ for $\tau < \infty$, ...
```

This failure mode is enforced by `lint-math.py` check #6d (the `check_display_math_blank_line` function — a sibling of the ordered-list checks). Running the lint hook at edit time surfaces it before commit. The fix is mechanical — insert a blank line — and idempotent under re-running.

**Single-line `$$...$$` blocks count too.** The rule applies identically when the whole equation is written on one line, e.g. `$$f(\pm m) = g(m),$$` immediately followed by a prose line — the next paragraph's inline math still renders literally. The original check #6d only toggled on a `$$` delimiter alone on its own line and so missed single-line blocks (bug `2026-06-01-03`, found when a wiki headline equation rendered its following paragraph's `$f_M$` / `$\varphi$` as source); the check now also fires on a complete single-line `$$...$$` whose next line is non-blank prose. Always leave a blank line after the close regardless of whether the equation is one line or three.

# Paragraph Anchors

Paragraph anchors give the citation toolbar a stable, paragraph-level link target. The viewer's `Copy citation` action looks up `block.querySelector('a[id^="p-"]')` on the block containing the selection and embeds that ID (or `user-content-<id>` in GitHub mode) in the URL it writes to the clipboard.

**Marker placement.** The anchor is injected **inline at the start of the block's first text line**, not on its own preceding line. This keeps `data-source-line` pointing at the paragraph itself and lets a single DOM query find the anchor from any selection inside the block.

```markdown
<a id="p-attention-mechanics-1"></a><!-- para:attention-mechanics-1 --> First paragraph text starts here.

- <a id="p-attention-mechanics-2"></a><!-- para:attention-mechanics-2 --> First list item only.
- Second item has no anchor.

> <a id="p-attention-mechanics-3"></a><!-- para:attention-mechanics-3 --> First blockquote line only.
```

**Eligible blocks.** Paragraphs, first paragraph of the first list item in a top-level list, first paragraph of a top-level blockquote. **Skip:** headings (slug IDs already exist), display math (`eq-N` anchors already exist), tables, fenced code, HTML raw blocks, nested list items, nested blockquotes, YAML frontmatter. These exclusions are enforced by `markdown-it-py` block classification, not by a regex.

**ID format.** `p-<section-slug>-<N>` where `<section-slug>` is the slug of the nearest preceding heading and `<N>` is a sequential index that resets at each heading. Section slugs use the same lowercase + hyphen rules as GitHub heading anchors.

**Renumber script.** `viewer/tools/renumber-paragraphs.py` has the same contract as `renumber-equations.py`:

1. Walk the parsed token stream in document order and assign `(section-slug, N)` per eligible block.
2. Rewrite `<!-- para:... -->` markers and `<a id="p-...">` anchors to match the current position.
3. Report orphaned `para:` IDs (marker with no live block) and any block whose list/blockquote prefix could not be detected.
4. Supports `--check` (dry-run, exit non-zero on drift) and `--init` (one-time bulk insert).

**Workflow.** After adding, removing, or reordering paragraphs:

1. For new paragraphs, run `python viewer/tools/renumber-paragraphs.py FILE --init` to insert missing markers.
2. For ordinary edits, run the script without `--init` to renumber in place.
3. Verify: `--check` must exit cleanly with no orphans.

The `/check-survey` command runs `--check` as step 4 so CI catches drift before it lands.
