#!/usr/bin/env python3
"""Fail when a survey file claims a section number whose subsections live elsewhere.

`secxref:N` resolves through `build_survey_heading_index`, which is
first-definition-wins over the survey's `order.json`. So if one file declares
section `N` while a *different* file owns `N.1`, `N.2`, …, every reference to
`N` silently lands in the wrong document.

That is `bugs/2026-07-09-09`. In `surveys/cochannel-interference-mitigation-ue`,
`index.md` numbered its front matter `## 1.` … `## 5.` while `linear-receivers.md`
owned `3.1`, `3.2`, … and carried no `## 3` heading of its own. The appendix's
"the three linear-combiner families of §3" resolved to
"3. Reader's guide — section dependency map".

**No duplicate-heading check catches this.** `## 3` really does appear exactly
once. The heading is not duplicated; it claims a number the survey's *content*
already uses. This tool checks ownership, not duplication.

A file "declares" section N if it has a heading parsed as N, or a heading line
carrying an `<a id="sec-N">` anchor — the same two ways `build_survey_heading_index`
learns ownership.

    python viewer/tools/check-section-ownership.py surveys/
    python viewer/tools/check-section-ownership.py surveys/noma        # one survey

Exit 0 = clean, 1 = conflicts found, 2 = nothing to check.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

_HG = Path(__file__).with_name("heading_grammar.py")
_spec = importlib.util.spec_from_file_location("heading_grammar", _HG)
heading_grammar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(heading_grammar)

match_heading = heading_grammar.match_heading
ANY_SEC_ANCHOR_RE = heading_grammar.ANY_SEC_ANCHOR_RE

SKIP_SUFFIX = ".index.md"


def survey_files(survey_dir: Path) -> list[Path]:
    """The files `build_survey_heading_index` would consult, in its order."""
    order = survey_dir / "order.json"
    try:
        names = json.loads(order.read_text(encoding="utf-8"))
        if not isinstance(names, list):
            raise ValueError
    except (json.JSONDecodeError, OSError, ValueError):
        names = sorted(f.name for f in survey_dir.glob("*.md")
                       if not f.name.endswith(SKIP_SUFFIX))
    return [survey_dir / n for n in names if (survey_dir / n).exists()]


def declared_sections(path: Path) -> set[str]:
    """Section numbers this file declares, by heading or by heading anchor."""
    out: set[str] = set()
    in_fence = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.lstrip().startswith("#"):
            am = ANY_SEC_ANCHOR_RE.search(line)
            if am:
                out.add(am.group("sec"))
        m = match_heading(line)
        if m:
            out.add(m.group("num"))
    return out


def check_survey(survey_dir: Path) -> list[str]:
    files = survey_files(survey_dir)
    if not files:
        return []

    declares: dict[str, list[str]] = defaultdict(list)
    for f in files:
        for num in declared_sections(f):
            declares[num].append(f.name)

    problems: list[str] = []

    # (a) two files claim the same top-level number -> first-definition-wins picks one
    for num, owners in sorted(declares.items()):
        if len(set(owners)) > 1:
            problems.append(
                f"{survey_dir}: section '{num}' is declared by "
                f"{sorted(set(owners))} — first-definition-wins will pick "
                f"'{sorted(set(owners))[0]}' for every secxref:{num}"
            )

    # (b) file X declares N, but N.x subsections live in a different file
    for num, owners in sorted(declares.items()):
        if "." in num:
            continue
        owner = owners[0]
        sub_owners = {
            f for k, v in declares.items()
            if k.startswith(num + ".") for f in v
        }
        foreign = sorted(sub_owners - {owner})
        if foreign:
            problems.append(
                f"{survey_dir}: '{owner}' declares section '{num}', but its "
                f"subsections {num}.x live in {foreign} — a secxref:{num} will "
                f"resolve to '{owner}', not to the content"
            )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="+",
                    help="survey root(s) or individual survey directories")
    args = ap.parse_args()

    dirs: list[Path] = []
    for raw in args.paths:
        p = Path(raw)
        if (p / "order.json").exists():
            dirs.append(p)
        elif p.is_dir():
            dirs.extend(sorted(oj.parent for oj in p.rglob("order.json")))

    if not dirs:
        print("[check-section-ownership] ERROR: no survey directory (order.json) "
              "found under the given paths. Refusing to report success over "
              "nothing.", file=sys.stderr)
        return 2

    problems: list[str] = []
    for d in dirs:
        problems.extend(check_survey(d))

    for p in problems:
        print(f"[check-section-ownership] {p}", file=sys.stderr)

    if problems:
        print(f"\n[check-section-ownership] {len(problems)} conflict(s) across "
              f"{len(dirs)} survey directories.", file=sys.stderr)
        return 1

    print(f"[check-section-ownership] OK: {len(dirs)} survey directories, "
          f"no section-ownership conflicts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
