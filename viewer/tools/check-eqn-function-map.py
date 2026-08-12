#!/usr/bin/env python3
"""Mechanical strict math-to-code mapping gate for a sim/implementation-study report.

Promotes Section 4's equation↔function correspondence
(`.claude/rules/sim-report-completeness.md`, the load-bearing [M] "equation↔function
table") from an evidence-only artifact a reviewer eyeballs to a HARD GATE. The report
carries a machine-checkable ```eqnmap fenced block; each line ties a load-bearing
equation to the source symbol that implements it:

    ```eqnmap
    (rep) <- implementation/linear_receiver_irc/utils.py :: decode_codeblock   # LLR soft-combine
    (E)   <- implementation/nr_pdsch_demod/g2_reproduce.py :: _mute_layout      # coexistence muting
    ```

The gate opens each source file and asserts the named symbol is actually **defined**
there (a `def`/`class`/module-level binding — dotted `Class.method` resolves on its leaf).
A symbol that was renamed or deleted FAILs — the exact "code silently drifted off the
API" failure mode the attention-kernel study hit by hand (`precision.py` drifted off the
rewritten `utils` API; bug 2026-06-14-01).

Design note — SYMBOL form, not `path:line`. Line numbers drift on every unrelated edit
above a function, so a line-number gate would false-FAIL constantly; the symbol resolves
the *meaningful* drift (rename/delete) robustly and idempotently. Companion of
`check-signoff-checklist.py` (numbers) and `check-tdd-evidence.py` (tests): G0 attests the
equation is sound, this attests the code that claims to implement it still exists.

Completeness (opt-in, `--ledger`). Integrity above proves every eqnmap ROW resolves; it
does NOT prove every load-bearing EQUATION has a row (that was floored only by `--min N` +
reviewer judgment). With `--ledger artifacts/<study>/study-manifest.json` the gate also
asserts that every equation the G0 derivation ledger marks load-bearing — via a
machine-readable `load_bearing_eqs: ["(7)", "(E)", …]` list on each load-bearing
`derivation_ledger` entry — appears as an eqnmap row, and FAILs on any that is missing (an
unmapped load-bearing equation, not just a stale symbol). It is an advisory no-op when the
ledger declares no `load_bearing_eqs` (a study whose ledger predates the index format), so
adding `--ledger` never FAILs an un-annotated study
(todos/2026-07-12-eqnmap-ledger-completeness-crosscheck).

Usage:
    python viewer/tools/check-eqn-function-map.py REPORT.md [--check] [--min N] \
        [--ledger STUDY-MANIFEST.json]

Exit codes: 0 PASS, 1 FAIL (missing symbol / missing source / malformed / no block /
unmapped load-bearing equation), 2 usage.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BLOCK_RE = re.compile(r"```eqnmap\s*\n(.*?)\n```", re.DOTALL)
# <eq_id> <- <source_path> :: <symbol>   [# label]
LINE_RE = re.compile(r"^\s*(?P<eq>\S+)\s*<-\s*(?P<path>.+?)\s*::\s*(?P<sym>[^#\s]+)\s*(#.*)?$")


def _symbol_defined(src: str, sym: str) -> bool:
    """True if `sym` is DEFINED in the source (not merely called/imported).

    Accepts a Python `def`/`async def`, a `class`, a module-level/attribute binding
    (`SYM = ...` / `SYM: T`), or a MATLAB/Octave `function` declaration (`function out =
    SYM(args)` / `function SYM(args)` / `function [a,b] = SYM(args)`, incl. a classdef
    static method). A dotted `Class.method` resolves on its leaf segment, so a method or
    nested name is checked by its own definition.

    The MATLAB/Octave arm was added 2026-07-16: the repo carries 200+ `.m` sources and a
    MATLAB deliverable (`matlab/oms-de/`), whose `function out = name(...)` form matched
    none of the Python arms, so a `.m` study report could not be gated at all."""
    leaf = sym.split(".")[-1]
    pat = re.compile(
        rf"^[ \t]*(?:async[ \t]+)?def[ \t]+{re.escape(leaf)}\b"     # def / async def
        rf"|^[ \t]*class[ \t]+{re.escape(leaf)}\b"                  # class
        rf"|^[ \t]*function\b[^\n]*?\b{re.escape(leaf)}[ \t]*\("    # MATLAB/Octave function decl
        rf"|^[ \t]*{re.escape(leaf)}[ \t]*[:=](?!=)",              # binding: `x =` / `x:` (not `==`)
        re.MULTILINE,
    )
    return bool(pat.search(src))


def _norm_eq(s: str) -> str:
    """Canonicalise an equation id for matching: strip surrounding whitespace and one
    layer of parentheses, so a ledger `7` matches an eqnmap `(7)`."""
    return s.strip().strip("()").strip()


def _load_required_eqs(ledger_path) -> dict:
    """Return ``{normalised-eq-id: candidate}`` for every load-bearing equation the G0
    derivation ledger declares via ``load_bearing_eqs``. Accepts a study-manifest.json
    (``derivation_ledger`` block) or a standalone sidecar (a bare JSON list). Returns ``{}``
    — an advisory no-op — for an unreadable ledger, or one that predates the
    ``load_bearing_eqs`` index (nothing declared)."""
    try:
        data = json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    ledger = data.get("derivation_ledger") if isinstance(data, dict) else data
    if isinstance(ledger, dict):
        entries = (list(ledger.values())
                   if ledger and all(isinstance(v, dict) for v in ledger.values())
                   else [ledger])
    elif isinstance(ledger, list):
        entries = ledger
    else:
        entries = []
    req: dict[str, str] = {}
    for e in entries:
        if not isinstance(e, dict) or e.get("tier") != "load-bearing":
            continue
        for q in (e.get("load_bearing_eqs") or []):
            req[_norm_eq(str(q))] = e.get("candidate", "?")
    return req


def _completeness_problems(mapped: set, ledger_path) -> list:
    """Every load-bearing equation in the ledger must have an eqnmap row. Advisory no-op
    when the ledger declares no ``load_bearing_eqs`` (predates the index format)."""
    req = _load_required_eqs(ledger_path)
    if not req:
        return []
    mapped_norm = {_norm_eq(q) for q in mapped}
    return [
        f"load-bearing equation {q!r} (ledger candidate {cand!r}) has no eqnmap row "
        f"— the equation->function map is INCOMPLETE for this study"
        for q, cand in sorted(req.items()) if q not in mapped_norm
    ]


def check(report_path: Path, ledger_path=None):
    """Return a list of human-readable problems; empty list == PASS.

    Integrity: every eqnmap row names a symbol that is DEFINED in its source (always on).
    Completeness (opt-in via ``ledger_path``): every load-bearing equation the G0 ledger
    declares (``load_bearing_eqs``) has an eqnmap row — advisory no-op until declared."""
    text = Path(report_path).read_text(encoding="utf-8")
    blocks = BLOCK_RE.findall(text)
    if not blocks:
        return ["no eqnmap block (```eqnmap …```) found — add one mapping each "
                "load-bearing equation to its implementing symbol"]

    problems: list[str] = []
    n_entries = 0
    mapped: set[str] = set()
    for block in blocks:
        for raw in block.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            mm = LINE_RE.match(line)
            if not mm:
                problems.append(f"malformed eqnmap line: {line!r}")
                continue
            n_entries += 1
            eq, path_str, sym = mm["eq"], mm["path"].strip(), mm["sym"]
            mapped.add(eq)
            p = Path(path_str)
            if not p.is_absolute():
                p = Path.cwd() / p
            if not p.is_file():
                problems.append(f"source not found: {path_str} (eq {eq}, line: {line!r})")
                continue
            try:
                src = p.read_text(encoding="utf-8")
            except OSError as e:
                problems.append(f"source unreadable: {path_str}: {e}")
                continue
            if not _symbol_defined(src, sym):
                problems.append(
                    f"symbol not defined: {sym!r} for eq {eq} in {path_str} "
                    f"(renamed or deleted — the math-to-code link is stale)")
    if n_entries == 0 and not problems:
        problems.append("eqnmap block present but has no entries")
    if ledger_path is not None:
        problems += _completeness_problems(mapped, ledger_path)
    return problems


def _count_entries(text: str) -> int:
    return sum(1 for b in BLOCK_RE.findall(text) for ln in b.splitlines()
               if LINE_RE.match(ln.strip() or "#"))


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--check"]
    min_n = 0
    ledger_path = None
    if "--ledger" in argv:
        i = argv.index("--ledger")
        try:
            ledger_path = argv[i + 1]
            del argv[i:i + 2]
        except IndexError:
            print("Usage: --ledger PATH", file=sys.stderr)
            return 2
    if "--min" in argv:
        i = argv.index("--min")
        try:
            min_n = int(argv[i + 1])
            del argv[i:i + 2]
        except (IndexError, ValueError):
            print("Usage: --min N", file=sys.stderr)
            return 2
    if len(argv) != 1:
        print("Usage: check-eqn-function-map.py REPORT.md [--check] [--min N] "
              "[--ledger STUDY-MANIFEST.json]", file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.is_file():
        print(f"ERROR: not a file: {path}", file=sys.stderr)
        return 2

    problems = check(path, ledger_path=ledger_path)
    if not problems:
        n_ok = _count_entries(path.read_text(encoding="utf-8"))
        if n_ok < min_n:
            print(f"eqnmap: FAIL — {n_ok} mappings < required {min_n}", file=sys.stderr)
            return 1
        print(f"eqnmap: PASS ({n_ok} equation->function links resolved) -- {path.name}")
        return 0
    for p in problems:
        print(f"  [-] {p}")
    print(f"eqnmap: FAIL ({len(problems)} problem(s)) -- {path.name}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
