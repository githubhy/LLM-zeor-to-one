Normalize (write-mode) the marker/anchor discipline of a survey, then verify: $ARGUMENTS

`normalize-survey` is the **write-mode twin of `/check-survey`**. `/check-survey`
*verifies* (all `--check`); this *applies* the renumber/link tools in the one
correct order — with the hard-won exceptions baked in — then runs the check
suite. Use it after authoring a multi-file survey, after a Phase-4 synthesis
merge, or any time `/check-survey` reports anchor/marker drift.

Run:

```
python viewer/tools/normalize-survey.py <survey-dir>
```

What it does, in order (each step feeds the next):

1. `renumber-sections <dir> --init` — inject section anchors and convert every
   **bare same-survey `§X.Y`** to `secref` (same-file) or `secxref` (cross-file,
   owning file resolved via `order.json`). **This is why you author section refs
   BARE and never pre-link them** (deep-research-survey `[opt:SX-INIT]`).
2. `renumber-equations <file>` — sequential `\tag{N}` + `eq-N` anchors, per file.
3. `renumber-paragraphs <file> --init` — paragraph anchors, **skipping
   `references.md`** (init would push each `[N]` off column 0 and break
   `check-citation-sources`).
4. `link-references <file>` — sync existing cite/bib markers. It does **not**
   run `--init` (that is a one-time plain-`[N]` → marked-citation *style*
   migration); pass `--cite-init` only if you want that migration.
5. Check suite — `lint-math`, `validate-refs`, bare-refs `--severity=error`,
   `check-citation-sources`.

**Cross-survey guard (`[opt:SX-DEGLYPH]`).** Any bare `§X.Y` that survives step 1
points to a section **not in this survey** (a different survey, or an external
spec) — `--init` cannot resolve it. The tool lists these as `SX-DEGLYPH`
candidates: de-glyph to a plain relative link (different survey) or bracket-wrap
`[MCP spec §X.Y]` / `[RFC 8259 §7]` (external spec); never leave them bare.

Flags: `--check-only` (skip writes, run only the check suite — same as
`/check-survey` but via this driver), `--cite-init` (also migrate bare `[N]`
citations to the marked form), `--quiet` (summary + errors only).

Exit non-zero and print a fix list if anything is still not clean.
