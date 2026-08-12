#!/usr/bin/env python3
"""check-depth-tiers.py -- enforce the R-GOV depth-tier vocabulary.

The `deep-research-survey` skill's Phase-2 governor `[R-GOV]`
(`.claude/skills/deep-research-survey/addenda/phase-2.md`) tags every
method / variant / load-bearing result with a **depth tier** that decides how
much derivation, worked-example, and cross-check budget it gets. The tier is
authored as an inline `Depth tier: <value>` label at the head of each section
and is the durable in-document trace of the governor.

Until now the tier was an **agent-discipline** gate only: no mechanical check
read the label, so a mistyped or invented tier passed every gate green. Two
real instances motivated this checker -- an invented `derivation` tier and an
off-ladder `supporting` tier, neither of which any of the nine `/check-survey`
steps nor the PostToolUse hooks flagged (session
`prompts/2026-07-06-lte-transmission-modes.md`, decision 2026-07-08-02).

This checker is the deterministic vocabulary gate: it finds every authored
`Depth tier: <value>` label and asserts `<value>` is from the allowed set. It
does NOT judge whether the *assigned* tier matches the *delivered* depth (a
semantic call reserved for the outline sign-off and the end-of-run coverage
summary -- see `proposals/2026-07-08-depth-tier-gating.md`); it only enforces
the vocabulary, which is a pure, false-positive-free mechanical win.

Allowed vocabulary
------------------
The R-GOV depth-budget ladder is exactly three tiers:

    headline       flagship root-delta sections; deepest treatment
    load-bearing   full derivation + intuition + worked example
    catalog        compact stated-result + explicit `n/a (<reason>)` per
                   skipped heavy artifact

plus one ratified **off-ladder** label for non-method context sections:

    supporting     standardization-provenance / context material that is not
                   a method card and so does not sit on the method-depth
                   ladder (e.g. the §C.14 paper-provenance subsections). Kept
                   distinct on purpose; see decision 2026-07-08-02.

To add or retire a value, edit ALLOWED_TIERS below and record the taxonomy
change as a `decisions/` entry (the vocabulary is load-bearing governance).

Matching
--------
Only the authored label form is matched: a literal `Depth tier:` (capital D,
the word `tier`, a colon), optionally followed by markdown bold `**`. Prose
mentions such as "depth tier per R-GOV = ..." (lower-case, no colon) or
"depth-tier legend" (hyphen, no colon) are deliberately NOT matched.

Usage:
    python viewer/tools/check-depth-tiers.py FILE_OR_DIR [FILE_OR_DIR ...]

`--check` is accepted and ignored (the checker is always read-only) for flag
convention parity with the renumber scripts.

Exit code 0 if every authored depth-tier label is in the allowed vocabulary;
1 if any invalid label is found; 2 on a usage error.
"""
import re
import sys
from pathlib import Path

# The R-GOV depth-budget ladder (3) + the ratified off-ladder context label (1).
# Editing this set is a taxonomy change -- record it in decisions/.
ALLOWED_TIERS = ('headline', 'load-bearing', 'catalog', 'supporting')

# Authored label only: `Depth tier:` (capital D + colon), optional `**` bold,
# then the tier token (lower-case word, may contain a hyphen: `load-bearing`).
LABEL_RE = re.compile(r'Depth tier:\s*\*{0,2}\s*([a-z][a-z-]*)')


def check_file(path):
    """Return (violations, labels) for one file.

    violations: list of (lineno, col, value, context) for out-of-vocab labels.
    labels:     list of the tier value on every authored label (for the tally).
    """
    viol, labels = [], []
    text = Path(path).read_text(encoding='utf-8')
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in LABEL_RE.finditer(line):
            value = m.group(1)
            labels.append(value)
            if value not in ALLOWED_TIERS:
                ctx = line[m.start():min(len(line), m.end() + 20)]
                viol.append((lineno, m.start() + 1, value, ctx))
    return viol, labels


def iter_targets(args):
    for a in args:
        p = Path(a)
        if p.is_dir():
            for f in sorted(p.rglob('*.md')):
                # skip hidden dirs (.claude, .git worktrees, etc.)
                if any(part.startswith('.') for part in f.parts):
                    continue
                yield f
        elif p.is_file():
            yield p
        else:
            print(f'WARNING: not found: {a}', file=sys.stderr)


def main(argv):
    args = [a for a in argv if a != '--check']
    if not args:
        print('usage: check-depth-tiers.py FILE_OR_DIR [...]', file=sys.stderr)
        return 2
    total_viol = 0
    total_labels = 0
    files = 0
    tally = {}
    for path in iter_targets(args):
        files += 1
        viol, labels = check_file(path)
        total_labels += len(labels)
        for v in labels:
            tally[v] = tally.get(v, 0) + 1
        for lineno, col, value, ctx in viol:
            total_viol += 1
            allowed = ', '.join(ALLOWED_TIERS)
            print(f'{path}:{lineno}:{col}: [ERROR] invalid depth tier '
                  f'`{value}` (allowed: {allowed}) | ...{ctx}')
    dist = ', '.join(f'{k} {tally[k]}' for k in sorted(tally)) or '(none)'
    print(f'{files} file(s) scanned, {total_labels} depth-tier label(s) '
          f'[{dist}], {total_viol} violation(s).')
    return 1 if total_viol else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
