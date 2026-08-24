#!/usr/bin/env python3
"""Does the bytecode Python will RUN match the source on disk?

Nothing in this repo asked that question until 2026-08-22, when the answer was no.

CPython invalidates a `__pycache__/*.pyc` by comparing the source's **mtime (to
one-second granularity) and size** against the header it wrote. Both are coarse,
and an edit that changes neither is invisible to it. That is not a hypothetical
pair of coincidences -- it is the signature of a **positive control**:

  * a control reintroduces a defect by swapping one character for another
    (`f"^{{{sup}}}"` -> `f"_{{{sup}}}"`), so the file size does not move;
  * the control is reverted seconds later with `git checkout --`, so the mtime
    lands in the same second the stale `.pyc` recorded.

The measured instance: `tools/specparse/mtef_parser.py` was byte-identical to
HEAD and to origin -- `git diff` clean, `git status` clean, `inspect.getsource`
showing the fix -- while the interpreter ran the pre-fix code object. Eleven
tests failed against a file whose source was correct. `inspect.getsource` cannot
see this: it reads the `.py`, never the loaded bytecode. Neither can any linter,
any diff, or any review.

The check that works is content, not metadata: recompile the source and compare
the code objects structurally. `co_filename` is excluded because importlib
records whatever path the finder used (relative or absolute, depending on how
`sys.path` was built), so comparing it produces false alarms; everything that
determines BEHAVIOUR -- opcodes, constants, names, nested code objects -- is
compared exactly.

Usage:
    check-bytecode-freshness.py [PATH ...] [--fix]

Exit 0 = every cache file matches its source (or there are none).
Exit 1 = at least one stale cache file; the interpreter would run it.
Exit 2 = REFUSE: could not establish what to check.
"""
from __future__ import annotations

import argparse
import importlib.util
import marshal
import struct
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "download", "_scratch",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
}

# Everything that decides what the code DOES. `co_filename` is deliberately absent
# (see the module docstring); `co_lnotab`/`co_linetable` are absent because a line
# table difference with identical opcodes is a formatting artefact, not a
# behavioural one -- and `co_firstlineno` already catches a moved function.
_CODE_FIELDS = (
    "co_argcount", "co_posonlyargcount", "co_kwonlyargcount", "co_nlocals",
    "co_flags", "co_code", "co_names", "co_varnames", "co_freevars",
    "co_cellvars", "co_name", "co_firstlineno",
)


def _const(c):
    """A stable description of a constant.

    `repr()` alone is wrong for sets: marshal rebuilds a `frozenset` with a
    different insertion order than the compiler produced, so two EQUAL sets
    print in different orders and a byte-identical module reads as stale. That
    false positive fired on the very first run of this tool
    (`_convert_function`'s 30-name function set in `omml_converter.py`), which
    is the point -- an oracle that cries wolf gets switched off, and then the
    real stale cache goes unreported. Order-insensitive for sets, exact for
    everything else.
    """
    if hasattr(c, "co_code"):
        return _digest(c)
    if isinstance(c, (frozenset, set)):
        return ("set", tuple(sorted(map(repr, c))))
    if isinstance(c, tuple):
        return ("tuple", tuple(_const(x) for x in c))
    return repr(c)


def _digest(code):
    """A structural, filename-independent description of a code object."""
    out = [getattr(code, f, None) for f in _CODE_FIELDS]
    out.append(tuple(_const(c) for c in code.co_consts))
    return tuple(out)


def _sources(roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        if root.is_file():
            if root.suffix == ".py":
                found.append(root)
            continue
        for p in root.rglob("*.py"):
            # Relative to the ROOT being walked, not to the repo: a caller may name a
            # directory outside the repo (the tests do), and `relative_to` raises there.
            if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
                continue
            found.append(p)
    return sorted(set(found))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="files or directories (default: repo root)")
    ap.add_argument("--fix", action="store_true",
                    help="delete stale cache files so the next import compiles from source")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    roots = [Path(p).resolve() for p in args.paths] or [repo]
    for r in roots:
        if not r.exists():
            print(f"[bytecode] REFUSE: {r} does not exist", file=sys.stderr)
            return 2

    sources = _sources(roots)
    if not sources:
        print(f"[bytecode] REFUSE: no .py files under {', '.join(str(r) for r in roots)}",
              file=sys.stderr)
        return 2

    checked = skipped = 0
    stale: list[tuple[Path, str]] = []

    for src in sources:
        try:
            cache = Path(importlib.util.cache_from_source(str(src)))
        except (ValueError, NotImplementedError):
            continue
        if not cache.is_file():
            continue  # no cache -> the next import compiles from source; safe by construction
        raw = cache.read_bytes()
        if len(raw) < 16 or raw[:4] != importlib.util.MAGIC_NUMBER:
            # A different interpreter version wrote it; ours will ignore it.
            skipped += 1
            continue
        flags = struct.unpack("<I", raw[4:8])[0]
        if flags & 0x1 and not flags & 0x2:
            # An UNCHECKED hash-based pyc is never validated by CPython at all --
            # strictly worse than the mtime hole this tool exists for. Flag it.
            stale.append((cache, "unchecked hash-based cache: CPython never validates it"))
            continue
        try:
            cached = marshal.loads(raw[16:])
            fresh = compile(src.read_bytes(), str(src), "exec", dont_inherit=True)
        except (ValueError, EOFError, SyntaxError, TypeError) as exc:
            stale.append((cache, f"unreadable: {exc}"))
            continue
        checked += 1
        if _digest(cached) != _digest(fresh):
            stale.append((cache, "bytecode does not match its source"))

    for cache, why in stale:
        try:
            rel = cache.relative_to(repo)
        except ValueError:
            rel = cache
        print(f"[bytecode] STALE {rel}: {why}")
        if args.fix:
            cache.unlink(missing_ok=True)
            print(f"[bytecode]   removed; the next import will compile from source")

    tail = f" ({skipped} written by another interpreter, ignored)" if skipped else ""
    if not stale:
        if checked:
            print(f"[bytecode] {checked} cache file(s) match their source{tail}")
        else:
            print(f"[bytecode] 0 cache files present for {len(sources)} source file(s); "
                  f"nothing can be stale{tail}")
        return 0
    print(f"[bytecode] {len(stale)} STALE of {checked + len(stale)} cache file(s) "
          f"over {len(sources)} source file(s){tail}")
    if not args.fix:
        print("[bytecode] re-run with --fix, or: find . -name __pycache__ -type d "
              "-not -path './.git/*' -exec rm -rf {} +")
    return 0 if args.fix else 1


if __name__ == "__main__":
    sys.exit(main())
