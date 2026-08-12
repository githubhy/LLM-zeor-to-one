#!/usr/bin/env python3
"""Duplicate figure-label gate.

On 2026-07-16 two independent authors both concluded "the next free
appendix-G figure number is G10" by grepping ONE of three generator
scripts that all write into the same `sim/llms-for-coding/tools/figures/`
directory. Nothing failed loudly: PNG filenames differ, so no file was
overwritten and no existing gate fired -- the survey would simply have
carried two figures both captioned "Fig. G10", and every prose reference
to "Fig. G10" would have become ambiguous. It was caught only by a human
noticing. See `decisions/2026-07-16-02-hdq-figure-number-g14-not-g10.md`
and `todos/2026-07-16-hdq-figure-label-g10-collision.md`.

This is the sibling of `check-record-ids.py` (which gates the same
failure shape -- a claimed identifier colliding -- for the bugs/
decisions/ todos/ id namespace) for the figure-label namespace.

**A figure label MENTIONED in prose is not a label DECLARATION.** Only a
caption -- a bold span opening "**Fig. <ID>" or "**Figure <ID>" that
carries more content before its bold closes (an em-dash title, or at
least a trailing '.') -- declares a label. Running prose that happens to
bold a forward-reference, e.g. "**Figure F1** confirms both properties
numerically." (the bold closes immediately after the raw ID, nothing in
between), is not a declaration and must not count as a second one. This
distinction is load-bearing: an earlier draft of this checker treated
every "**Fig[ure] <ID>" match as a declaration and reported 8 false
"duplicates" that were actually one real caption plus a bolded prose
mention of the same figure (`surveys/attention-demo/*.md` F1-F7,
`surveys/llms-for-coding/appendix-e.md` E.2-c). See the test suite for both
shapes.

Scope (mirrors `check-section-ownership.py`): a "survey" is a directory
carrying `order.json` (scope = every `*.md` file directly inside it --
order.json is used to weight nothing here, membership is enough), OR a
single flat `.md` file directly under a corpus root with no order.json
covering it (its own singleton scope). Sub-dossiers in a nested
subdirectory of a survey (e.g. `method-search/`) are not part of the
survey's own file list and fall through to their own singleton scope --
inclusive, not silently skipped. `_scratch/` is excluded (matches the
exclusion already applied by `validate-refs.py --bare-refs-only`).

    python viewer/tools/check-figure-labels.py surveys/
    python viewer/tools/check-figure-labels.py surveys/llms-for-coding   # one survey
    python viewer/tools/check-figure-labels.py surveys/some-file.md  # one file

Exit 0 = clean, 1 = duplicate label(s) found, 2 = nothing to check.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# A declaration opens "**Fig. " or "**Figure " (always capitalized "F" in
# this corpus -- verified, no lowercase "**fig."/"**figure " variant exists)
# immediately followed by an ID token. The ID group is greedy but must END
# on an alnum char, which is what correctly excludes a sentence-final "."
# from the captured token (e.g. "Figure B.1." -> captures "B.1", not "B.1.").
FIG_DECL_RE = re.compile(
    r'\*\*Fig(?:ure|\.)\s+([A-Za-z0-9](?:[A-Za-z0-9.\-]*[A-Za-z0-9])?)'
)


def compute_fence_state(lines: list[str]) -> list[bool]:
    """Return list[bool], True iff that line is inside a fenced code block."""
    state = [False] * len(lines)
    in_fence = False
    fence_marker = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not in_fence:
            m = re.match(r"^(`{3,}|~{3,})", stripped)
            if m:
                in_fence = True
                fence_marker = m.group(1)[0] * len(m.group(1))
                state[i] = True
                continue
        else:
            state[i] = True
            if stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = None
    return state


def find_declarations(path: Path) -> list[tuple[str, int, str]]:
    """Return [(label, lineno, matched_text), ...] -- DECLARATIONS only.

    Excludes a bolded prose forward-reference ("**Figure F1** confirms..."):
    its bold span closes immediately after the raw ID with nothing between,
    whereas a real caption always carries more content (an em-dash title, or
    at minimum a trailing '.') inside the same bold span before it closes.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    lines = text.split("\n")
    fence = compute_fence_state(lines)
    out = []
    for i, line in enumerate(lines):
        if fence[i]:
            continue
        for m in FIG_DECL_RE.finditer(line):
            token = m.group(1)
            if not any(c.isdigit() for c in token):
                continue  # e.g. "**Figure of merit**" -- not a label
            after = line[m.end(1):]
            if after.lstrip(" ").startswith("**"):
                continue  # bold closed right after the raw ID -> prose mention
            out.append((token, i + 1, m.group(0)))
    return out


def list_survey_files(survey_dir: Path) -> list[Path]:
    """Every file counted in this survey's figure-label scope.

    order.json is used when present and non-empty (listed files only);
    otherwise every `*.md` directly in the directory (non-recursive,
    matching `list_md_files` in validate-refs.py and the fallback branch of
    `survey_files` in check-section-ownership.py).
    """
    order = survey_dir / "order.json"
    try:
        names = json.loads(order.read_text(encoding="utf-8"))
        if isinstance(names, list) and names:
            files = [survey_dir / n for n in names if (survey_dir / n).exists()]
            if files:
                return files
    except (json.JSONDecodeError, OSError, ValueError):
        pass
    return sorted(survey_dir.glob("*.md"))


def discover_scopes(paths: list[str]) -> dict[str, list[Path]]:
    """Return {scope_id: [file, ...]} for every figure-label scope under the
    given paths. A scope is either one order.json survey directory, or one
    singleton flat `.md` file (a "single-file survey", or an uncovered file
    inside a non-survey subdirectory / a survey's own sub-dossier)."""
    scopes: dict[str, list[Path]] = {}
    for raw in paths:
        p = Path(raw)
        if (p / "order.json").exists():
            scopes[str(p)] = list_survey_files(p)
            continue
        if p.is_file():
            if p.suffix == ".md":
                scopes[str(p)] = [p]
            continue
        if not p.is_dir():
            continue

        # p is a corpus root (e.g. surveys/): decompose it.
        oj_dirs: list[Path] = []
        for oj in sorted(p.rglob("order.json")):
            d = oj.parent
            if "_scratch" in d.parts:
                continue
            scopes[str(d)] = list_survey_files(d)
            oj_dirs.append(d.resolve())

        for md in sorted(p.rglob("*.md")):
            if "_scratch" in md.parts:
                continue
            # Only a file living DIRECTLY inside an order.json survey dir is
            # already covered by that survey's own scope above -- a file in a
            # nested subdirectory (e.g. method-search/) is NOT in
            # list_survey_files()'s non-recursive glob, so it must still get
            # its own scope here rather than being silently dropped.
            if any(md.parent.resolve() == d for d in oj_dirs):
                continue
            scopes[str(md)] = [md]
    return scopes


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("paths", nargs="+",
                     help="corpus root(s), survey directory/directories, or file(s)")
    args = ap.parse_args()

    scopes = discover_scopes(args.paths)
    if not scopes:
        print("[figure-labels] ERROR: no survey directory or .md file found under "
              "the given paths. Refusing to report success over nothing.",
              file=sys.stderr)
        return 2

    total_decls = 0
    total_files = 0
    dupes: list[tuple[str, str, list[tuple[Path, int, str]]]] = []
    for scope_id, files in sorted(scopes.items()):
        by_label: dict[str, list[tuple[Path, int, str]]] = defaultdict(list)
        for f in files:
            total_files += 1
            for label, lineno, matched in find_declarations(f):
                by_label[label].append((f, lineno, matched))
                total_decls += 1
        for label, occs in sorted(by_label.items()):
            if len(occs) > 1:
                dupes.append((scope_id, label, occs))

    if dupes:
        print(f"[figure-labels] {len(dupes)} duplicate label(s):", file=sys.stderr)
        for scope_id, label, occs in dupes:
            print(f"  - scope {scope_id}: label '{label}' declared "
                  f"{len(occs)} times:", file=sys.stderr)
            for f, lineno, matched in occs:
                print(f"      {f}:{lineno}: {matched!r}", file=sys.stderr)
        return 1

    print(f"[figure-labels] OK -- {len(scopes)} scope(s), {total_files} file(s), "
          f"{total_decls} declared label(s), no duplicates", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
