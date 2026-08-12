"""Shared corpus expansion for the survey gate tools.

`.githooks/pre-push` validates the corpus by handing each tool the `surveys/`
directory. Four of the five marker/anchor tools understood that argument as
**one survey directory** — `order.json` if present, else `glob('*.md')` — so
`surveys/`, which has no `order.json`, resolved to the 12 flat legacy files at
its root and none of the 27 survey subdirectories. The gate scanned ~1% of an
811-file corpus and exited 0 (`bugs/2026-07-10-09`, high, open since
2026-07-10; independently re-found in `check-value-ledger.py` as
`bugs/2026-07-31-value-ledger-scope-not-recursive`).

The fix is **not** a blanket `rglob`. These tools resolve `secxref` markers and
equation/paragraph numbering *per survey*, against that survey's own
`order.json`; flattening `surveys/` into one 811-file list would conflate 27
independent numbering domains and mis-resolve cross-references — strictly worse
than scanning too little. What is needed is the distinction the tools never
had:

    a SURVEY   is a directory holding markdown (canonically with an order.json)
    a CORPUS   is a directory whose members are surveys

so a corpus root expands into survey **units**, each processed exactly as
before.

Coverage is not silent (`.claude/rules/cross-linking.md`): `describe_scope`
renders what was scanned *and* what was skipped, so a green gate can never mean
"did not look".
"""
from __future__ import annotations

import json
from pathlib import Path

# Directories that are never corpus content.
#   _scratch  — evidence ledgers and working notes (311 of the 320 nested
#               markdown files under surveys/); already excluded by
#               normalize-survey.py and validate-refs --bare-refs-only.
#   specs     — mirrored external standards, not authored content.
#   archive   — superseded documents nobody maintains; gating a push on them
#               would block work on live surveys. Excluded but REPORTED.
DEFAULT_EXCLUDES = frozenset({"_scratch", "specs", "archive", ".git", "node_modules"})


class Unit:
    """One independent numbering domain: a survey, or a root's flat files."""

    __slots__ = ("root", "files", "ordered")

    def __init__(self, root: Path, files: list[Path], ordered: bool):
        self.root, self.files, self.ordered = root, files, ordered

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"Unit({self.root}, {len(self.files)} files, ordered={self.ordered})"


def _ordered_md(directory: Path) -> tuple[list[Path], bool]:
    """The directory's markdown in order.json order when it declares one."""
    order_file = directory / "order.json"
    if order_file.exists():
        try:
            names = json.loads(order_file.read_text(encoding="utf-8"))
            files = [directory / n for n in names if (directory / n).exists()]
            if files:
                return files, True
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return sorted(directory.glob("*.md")), False


def is_survey_dir(directory: Path) -> bool:
    """A survey declares its own file order."""
    return (directory / "order.json").exists()


def survey_units(target, excludes=DEFAULT_EXCLUDES):
    """Expand `target` into (units, skipped) .

    A file yields a single one-file unit. A directory that declares an
    `order.json` is a survey and yields one unit — the pre-existing behaviour,
    unchanged. Any other directory is treated as a corpus root: its own
    top-level markdown becomes one unit (the flat legacy surveys) and each
    subdirectory is expanded in turn.

    `skipped` lists excluded directories that actually exist, so callers can
    report them instead of dropping them silently.
    """
    target = Path(target)
    if target.is_file():
        return [Unit(target.parent, [target], False)], []
    if not target.is_dir():
        return [], []

    units: list[Unit] = []
    skipped: list[Path] = []

    def walk(d: Path):
        # A survey's OWN top-level markdown is one ordered unit. Its
        # subdirectories are not part of that ordering (they are absent from
        # order.json) but may still hold real content — e.g. the method-eval
        # registers in `<survey>/method-search/` — so they are walked and
        # become units of their own rather than being silently dropped or
        # folded into the survey's numbering.
        own, ordered = _ordered_md(d) if is_survey_dir(d) else (sorted(d.glob("*.md")), False)
        if own:
            units.append(Unit(d, own, ordered))
        for sub in sorted(p for p in d.iterdir() if p.is_dir()):
            if sub.name in excludes:
                skipped.append(sub)
                continue
            walk(sub)

    walk(target)
    return units, skipped


def all_files(units) -> list[Path]:
    return [f for u in units for f in u.files]


def describe_scope(units, skipped, label="scope") -> str:
    """A one-line coverage statement. A gate must say what it looked at."""
    n_files = sum(len(u.files) for u in units)
    parts = [f"[{label}] {len(units)} unit(s), {n_files} file(s)"]
    if skipped:
        # Collapse by name: '_scratch' occurs once per survey and listing all
        # 24 buries the one that matters.
        counts: dict[str, int] = {}
        for p in skipped:
            counts[p.name] = counts.get(p.name, 0) + 1
        parts.append("skipped " + ", ".join(
            n if c == 1 else f"{n}×{c}" for n, c in sorted(counts.items())))
    return "; ".join(parts)
