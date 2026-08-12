#!/usr/bin/env python3
"""Fold a standalone flat survey into a multi-file survey as a re-lettered appendix.

A "fold-in" moves a single-file survey (e.g. `surveys/foo-survey.md`) into an
existing multi-file survey directory (e.g. `surveys/bar/`) as an appendix, so the
former survey's `## N` / `### N.x` sections become `## Appendix P` / `### P.x`. The
original file is then left as a redirect stub.

This tool performs the deterministic parts of that move:

1. Re-letter the source body: H1 title -> `## Appendix P - <title>`; every
   `sec:`/`secref:` marker, heading anchor, visible heading number, and same-file
   `[§N](#sec-N)` link renumbered `N -> P.N`; headings demoted one level.
2. Adjust paths for the +1 directory depth: links that pointed INTO the
   destination survey become same-directory; shared-asset `figures/` paths gain a
   `../` (flat `surveys/` -> nested `surveys/<dir>/`).
3. **Sweep the destination survey for stale links to the superseded file.** Any
   pre-existing link elsewhere in the destination survey that pointed at the old
   flat survey (`../old.md#sec-N`) is now stale: the redirect stub still resolves
   as a file, but `#sec-N` is a dead anchor (it became `#sec-P.N` in the appendix).
   The sweep repairs each such same-survey link to a `secxref` into the new
   appendix.

Step 3 is the step whose ABSENCE shipped three silently-broken links on 2026-07-12
(only the fourth, high-cosine, was caught by the crosslink gate; `validate-refs`
Check 9 verifies the target file exists, not the anchor, so it passed all four).
See `field-notes/2026-07-12-foldin-stale-links.md`.

What this tool does NOT do (still manual, by design):
- add the appendix to the destination survey's `order.json`;
- repair links to the old file from OTHER surveys (cross-survey links need the
  plain-link, no-glyph form and judgment — they are reported, not rewritten);
- run the renumber/validate sweep. After folding in, run
  `python viewer/tools/normalize-survey.py surveys/<dir>` (or `/normalize-survey`).

Usage:
    python viewer/tools/foldin.py SRC DST --letter P --title "TITLE"
                                  [--decision REF] [--sweep-scope DIR]
                                  [--no-sweep] [--sweep-only] [--dry-run]

Example (the 2026-07-12 survey fold-in):
    python viewer/tools/foldin.py \
        surveys/attention-head-specialization-explainer.md \
        surveys/llms-for-coding/appendix-h-head-specialization.md \
        --letter H --title "Degree-Distribution Standardization" \
        --decision decisions/2026-07-12-03
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

SECTION = "§"  # section glyph, written into .md files (never to the console)


def transform_source(text: str, letter: str, title: str, dest_dirname: str,
                     decision: str) -> str:
    """Re-letter a flat survey's body into appendix-`letter` form."""
    out: list[str] = []
    h1_done = False
    for ln in text.split("\n"):
        # First H1 title -> appendix top heading (H2, unnumbered; matches appendix-a).
        if not h1_done and re.match(r"^# [^#]", ln):
            out.append(f"## Appendix {letter} — {title}")
            out.append("")
            out.append(f"<!-- Folded in from the former standalone survey "
                       f"({decision}); section numbers re-lettered to {letter}.x. -->")
            h1_done = True
            continue
        # sec / secref markers: N -> P.N
        ln = re.sub(r"<!-- sec:(\d+(?:\.\d+)*) -->",
                    lambda m: f"<!-- sec:{letter}.{m.group(1)} -->", ln)
        ln = re.sub(r"<!-- secref:(\d+(?:\.\d+)*) -->",
                    lambda m: f"<!-- secref:{letter}.{m.group(1)} -->", ln)
        # anchored heading: demote one level, renumber N -> P.N
        m = re.match(r'^(#{2,5}) <a id="sec-(\d+(?:\.\d+)*)"></a>(\d+(?:\.\d+)*)\.?\s+(.*)$', ln)
        if m:
            lvl, anum, vnum, htitle = m.groups()
            out.append(f"#{lvl} <a id=\"sec-{letter}.{anum}\"></a>{letter}.{vnum} {htitle}")
            continue
        # non-anchored heading (#### RAN1#86 ...): demote one level
        if re.match(r"^#{2,4} ", ln):
            out.append("#" + ln)
            continue
        # same-file secref links [§N](#sec-N) -> [§P.N](#sec-P.N)
        ln = re.sub(rf"\[{SECTION}(\d+(?:\.\d+)*)\]\(#sec-(\d+(?:\.\d+)*)\)",
                    lambda m: f"[{SECTION}{letter}.{m.group(1)}](#sec-{letter}.{m.group(2)})", ln)
        # links that pointed INTO the destination survey are now same-directory
        ln = ln.replace(f"{dest_dirname}/", "")
        # shared-asset paths move up one level (flat surveys/ -> nested surveys/<dir>/)
        ln = re.sub(r"\]\(figures/", "](../figures/", ln)
        out.append(ln)
    return "\n".join(out)


def stale_link_re(old_basename: str) -> re.Pattern:
    """Match a link to the superseded flat survey, with an optional leading marker."""
    return re.compile(
        r"(?P<marker><!--\s*sec[a-z]*:[^>]*-->)?"
        r"\[(?P<text>[^\]]*)\]"
        r"\((?P<rel>(?:\.\./)*)" + re.escape(old_basename) +
        r"#sec-(?P<num>\d+(?:\.\d+)*)(?P<sub>(?:-[\w.\-]+)?)\)"
    )


def sweep_destination(scope_dir: Path, old_basename: str, dst: Path, letter: str,
                      dry_run: bool):
    """Repair same-survey links to the superseded file; report the rest.

    Returns (repairs, out_of_dir, anchorless) where each is a list of
    (file, lineno, before, after|reason) tuples for reporting.
    """
    pat = stale_link_re(old_basename)
    bare_ref_re = re.compile(re.escape(old_basename))
    anchored_re = re.compile(re.escape(old_basename) + r"#sec-")
    dst_dir = dst.parent.resolve()
    repairs, out_of_dir, anchorless = [], [], []

    for md in sorted(scope_dir.rglob("*.md")):
        if md.resolve() == dst.resolve():
            continue  # never rewrite the new appendix itself
        text = md.read_text(encoding="utf-8")
        if old_basename not in text:
            continue
        same_survey = md.parent.resolve() == dst_dir
        new_lines, changed = [], False
        for i, line in enumerate(text.split("\n"), 1):
            # Report anchor-less references to the old file (stub redirect covers
            # them, but the operator may want to update them).
            if bare_ref_re.search(line) and not anchored_re.search(line):
                anchorless.append((str(md), i, line.strip()[:120]))

            if not same_survey:
                if anchored_re.search(line):
                    out_of_dir.append((str(md), i, line.strip()[:120]))
                new_lines.append(line)
                continue

            def repl(m: re.Match) -> str:
                num, sub = m.group("num"), m.group("sub")
                rel = os.path.relpath(dst, md.parent).replace(os.sep, "/")
                marker_id = f"{letter}.{num}{sub}"
                anchor = f"sec-{letter}.{num}{sub}"
                new = (f"<!-- secxref:{marker_id} -->"
                       f"[{SECTION}{letter}.{num}]({rel}#{anchor})")
                repairs.append((str(md), i, m.group(0), new))
                return new

            new_line = pat.sub(repl, line)
            new_lines.append(new_line)
            if new_line != line:
                changed = True

        if changed and not dry_run:
            md.write_text("\n".join(new_lines), encoding="utf-8", newline="\n")

    return repairs, out_of_dir, anchorless


def main() -> int:
    ap = argparse.ArgumentParser(description="Fold a flat survey into a multi-file "
                                 "survey as a re-lettered appendix (with stale-link sweep).")
    ap.add_argument("src", help="the flat survey being folded in (also the future redirect stub)")
    ap.add_argument("dst", help="destination appendix file, e.g. surveys/bar/appendix-h-foo.md")
    ap.add_argument("--letter", required=True, help="appendix letter P (e.g. H)")
    ap.add_argument("--title", default="", help="appendix title (defaults to '<letter> content')")
    ap.add_argument("--decision", default="decisions/", help="decision ref for the fold-in comment")
    ap.add_argument("--sweep-scope", default=None,
                    help="directory to sweep for stale links (default: destination survey dir)")
    ap.add_argument("--no-sweep", action="store_true", help="skip the destination stale-link sweep")
    ap.add_argument("--sweep-only", action="store_true",
                    help="run only the sweep (do not transform/write the appendix)")
    ap.add_argument("--dry-run", action="store_true", help="print what would change; write nothing")
    args = ap.parse_args()

    src, dst = Path(args.src), Path(args.dst)
    letter = args.letter
    title = args.title or f"{letter} content"
    old_basename = src.name
    dest_dirname = dst.parent.name

    # 1-2. Transform + write the appendix (unless sweep-only).
    if not args.sweep_only:
        if not src.exists():
            print(f"ERROR: source {src} does not exist", file=sys.stderr)
            return 1
        body = transform_source(src.read_text(encoding="utf-8"), letter, title,
                                dest_dirname, args.decision)
        n_lines = len(body.split("\n"))
        if args.dry_run:
            print(f"[dry-run] would write {dst} ({n_lines} lines)")
        else:
            dst.write_text(body, encoding="utf-8", newline="\n")
            print(f"wrote {dst} ({n_lines} lines)")

    # 3. Sweep the destination survey for stale links to the superseded file.
    if not args.no_sweep:
        scope = Path(args.sweep_scope) if args.sweep_scope else dst.parent
        repairs, out_of_dir, anchorless = sweep_destination(
            scope, old_basename, dst, letter, args.dry_run)

        verb = "would repair" if args.dry_run else "repaired"
        print(f"\nsweep: {scope} for links to '{old_basename}'")
        if repairs:
            print(f"  {verb} {len(repairs)} same-survey link(s):")
            for f, ln, before, after in repairs:
                # ASCII-only console: strip the section glyph from the echo.
                print(f"    {f}:{ln}")
                print(f"      - {before.replace(SECTION, 'sec ')}")
                print(f"      + {after.replace(SECTION, 'sec ')}")
        else:
            print("  no same-survey stale links found (clean or already repaired)")
        if out_of_dir:
            print(f"  REVIEW: {len(out_of_dir)} cross-survey link(s) to the old file "
                  f"(repair by hand to plain no-glyph links):")
            for f, ln, snippet in out_of_dir:
                print(f"    {f}:{ln}  {snippet}")
        if anchorless:
            print(f"  note: {len(anchorless)} anchor-less reference(s) to the old file "
                  f"(stub redirect covers these):")
            for f, ln, snippet in anchorless:
                print(f"    {f}:{ln}  {snippet}")

    if not args.sweep_only:
        print("\nnext: add the appendix to order.json, then run "
              "`python viewer/tools/normalize-survey.py " + str(dst.parent) + "`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
