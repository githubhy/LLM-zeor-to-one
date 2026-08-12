#!/usr/bin/env python3
"""Detect unresolved section-number placeholders in survey markdown.

A draft authored before its final section number is known uses a placeholder --
`### 15.X A decision rule`, `#### 10.X.3 The window has an interior optimum`,
`<!-- sec:14.X.1 -->`, `§9.X returns to it at the end`. An applier is supposed to
resolve those to the real number when the draft lands. When it does not, the
placeholder ships.

Nothing else catches this, and the reason is worth stating: `X` is neither a digit
nor a letter-dot token, so `validate-refs` check #12 does not recognise `§10.X.3` as
a section reference at all, and `renumber-sections` skips the heading rather than
flagging it. The document's most-referenced internal pointers end up unclickable
*because* they are malformed -- malformed enough to fall outside the checker built to
catch exactly this. Every other gate stays green.

Measured: 4 chapters of `surveys/llms-for-coding` shipped with 48 placeholder
references, 15 headings and 7 orphan markers, past lint-math, validate-refs,
renumber-* --check, check-section-ownership, check-depth-tiers and the push gate.
Three of the four were found only on the third independent structure review.
See bugs/2026-08-02-edit-applier-silent-partial-success.md.

Usage:
    check-section-placeholders.py <path> [<path> ...]     # files or directories
    check-section-placeholders.py surveys/ --severity=warn
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# A placeholder segment is a single uppercase letter where a number belongs. `N` and
# `X` are the conventional ones; any bare uppercase letter in a dotted position is
# equally wrong. Letter-dot section numbers (A.5, D.7.2) are legal and must NOT match,
# so the letter has to be preceded by a digit-and-dot.
HEADING = re.compile(r"^(#{2,6})\s+(\d+\.(?:\d+\.)*[A-Z](?:\.\d+)*)\s", re.M)
MARKER = re.compile(r"<!--\s*sec:(\d+\.(?:\d+\.)*[A-Z](?:\.\d+)*)\s*-->")
PROSE = re.compile(r"§\s*(\d+\.(?:\d+\.)*[A-Z](?:\.\d+)*)")
ANCHOR = re.compile(r'id="(?:sec|p)-(\d+[.\-](?:\d+[.\-])*[A-Zx](?:[.\-]\d+)*)"')

CHECKS = (
    ("heading", HEADING, "heading carries an unresolved section placeholder"),
    ("marker", MARKER, "sec: marker carries an unresolved section placeholder"),
    ("prose", PROSE, "prose reference to an unresolved section placeholder"),
)


def scan(path: Path) -> list[tuple[int, str, str, str]]:
    out: list[tuple[int, str, str, str]] = []
    text = path.read_text(encoding="utf-8")
    for kind, pat, msg in CHECKS:
        for m in pat.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            token = m.group(2) if kind == "heading" else m.group(1)
            out.append((line, kind, token, msg))
    return sorted(out)


def iter_files(paths: list[str]):
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for f in sorted(p.rglob("*.md")):
                if "_scratch" in f.parts or "archive" in f.parts:
                    continue
                yield f
        elif p.suffix == ".md":
            yield p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--severity", choices=("off", "warn", "error"), default="error")
    args = ap.parse_args()

    if args.severity == "off":
        return 0

    total = files = 0
    for f in iter_files(args.paths):
        files += 1
        for line, kind, token, msg in scan(f):
            label = "ERROR" if args.severity == "error" else "WARNING"
            print(f"{f}:{line}: [{label}] {msg}: {token!r} ({kind})")
            total += 1

    if total:
        print(
            f"\n[section-placeholders] {total} unresolved placeholder(s) in {files} file(s).\n"
            f"  Resolve the section number, or demote the heading to a bold landmark and\n"
            f"  repoint its references -- a placeholder is invisible to every other gate."
        )
        return 1 if args.severity == "error" else 0

    print(f"[section-placeholders] OK -- {files} file(s), no unresolved placeholders.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
