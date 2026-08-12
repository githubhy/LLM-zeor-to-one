#!/usr/bin/env python3
"""Check that every documented `python -m` command names flags its target module actually accepts.

`todos/2026-08-01-reproduce-block-executability-gate`, from
`bugs/2026-08-01-w42-reproduce-blocks-cite-a-flag-that-does-not-exist`: two published `w42_hst`
commands pass `--append`, a flag that module has never accepted. Both abort on argparse and have
therefore never run. They were found only because a provenance audit had to use reproduce blocks as
its top authority for attributing producers -- and discovered that authority is a claim, not a
receipt.

A reproduce block is the one artifact a stranger is told to trust
(`.claude/rules/sim-report-completeness.md` § 12: "a stranger regenerates every number from one
command"). An unexecutable one is worse than none: it reads as provenance and is not.

## Why this is STATIC, and does not import anything

The obvious implementation drives each module's real `ArgumentParser` by intercepting `parse_args`.
It was built that way first, and it is unusable as a gate:

* importing runs module-level code -- `w31_a4_fit` reads `sys.argv` at import, parsed the CHECKER's
  own arguments, printed a usage message and exited, taking the gate down with it;
* reaching `parse_args` runs everything `main()` does *before* it, which for these modules means
  loading artifacts and, measured, **blocking indefinitely** (0.0 % CPU after 2+ minutes).

A pre-push gate must not execute the code it is checking. So this parses each module's source with
`ast` and collects the option strings of every `add_argument` call -- no import, no side effects,
milliseconds.

## What it catches, and what it does not

Catches: a documented flag that appears in **no** `add_argument` call in the target module. That is
exactly the originating bug, and it is the check that can be made soundly without executing.

Does NOT catch, stated so a green result is not over-read:

* a flag that exists but whose *value* is wrong (a grid that disagrees with the artifact the command
  claims to produce -- also part of the originating bug);
* a missing REQUIRED argument (requiredness is a keyword this scan deliberately does not model);
* flags added dynamically or via `parents=` (reported as unknown-parser and skipped, never as a
  failure -- a static scan must not fail a module it cannot read).

Usage:
    check-reproduce-blocks.py [paths...] [--severity off|warn|error] [--list]
"""
from __future__ import annotations

import argparse
import ast
import re
import shlex
import sys
from pathlib import Path

#: A fenced line invoking a repo module.
CMD = re.compile(r"^\s*(?:\$\s*)?python3?\s+-m\s+([\w.]+)\s*(.*)$")

#: Not ours to introspect.
SKIP_MODULES = {"pytest", "pip", "venv", "http.server", "json.tool", "unittest", "IPython",
                "py_compile", "compileall", "timeit", "pdb", "cProfile", "site", "ensurepip"}

REPO = Path(__file__).resolve().parents[2]

#: Roots a `python -m` in this repo may be resolved against. The sims add their own directory to
#: sys.path, so `common.density` lives under sim/llms-for-coding/, not at the repo root.
MODULE_ROOTS = [REPO, REPO / "sim" / "llms-for-coding", REPO / "sim", REPO / "implementation"]


def _is_number(tok: str) -> bool:
    """`-4`, `-0.5`, `-1e3` are VALUES, not flags.

    Without this the checker reports `--snr -4 -5 -6` as three unknown flags. Measured on the first
    run: 9 of 13 findings were negative SNR values, i.e. the check was mostly wrong. A numeric token
    can never be an option string a module would have to declare."""
    try:
        float(tok)
    except ValueError:
        return False
    return True


def _commands(text: str):
    """Yield `(line_no, module, argstring)` for every `python -m` line inside a fenced block.

    Deliberately not restricted to blocks under a "Reproduce" heading: a command a reader can copy
    is a command a reader will copy, wherever it sits.
    """
    fenced = False
    pending = ""
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            fenced, pending = not fenced, ""
            continue
        if not fenced:
            continue
        if pending:                                   # continuation of a `\`-wrapped command
            joined = pending + " " + line.strip().rstrip("\\")
            if line.endswith("\\"):
                pending = joined
                continue
            line, pending = joined, ""
        elif line.endswith("\\"):
            pending = line.rstrip("\\").rstrip()
            continue
        m = CMD.match(line)
        if m:
            yield i, m.group(1), m.group(2)


def _accepted_flags(module: str):
    """`(set_of_option_strings, note)` collected statically from the module's `add_argument` calls.

    Returns `(None, why)` when the module cannot be read or defines no parser -- never a failure.
    """
    rel = module.replace(".", "/") + ".py"
    path = next((r / rel for r in MODULE_ROOTS if (r / rel).exists()), None)
    if path is None:
        # Last-resort repo-wide search before declaring a module missing. MODULE_ROOTS is a guess at
        # the sys.path roots, and a guess that is merely incomplete must not BLOCK a push -- the
        # gate's job is to catch a flag that does not exist, not to police where modules live.
        tail = rel.split("/")[-1]
        for cand in REPO.rglob(tail):
            if cand.as_posix().endswith(rel):
                path = cand
                break
    if path is None:
        return None, f"module file not found ({rel})"
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as e:
        return None, f"unparseable source: {type(e).__name__}"

    flags, saw_parser, dynamic = set(), False, False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == "ArgumentParser":
            saw_parser = True
            # `parents=` is an ArgumentParser kwarg, NOT an add_argument one -- checking it only on
            # add_argument (as this did first) misses every inherited flag and would report them as
            # unknown, i.e. FALSE-BLOCK a correct command. Caught by
            # test_a_dynamically_built_parser_is_SKIPPED_not_failed before the gate reached error.
            if any(kw.arg == "parents" for kw in node.keywords):
                dynamic = True
            continue
        if node.func.attr == "add_subparsers":
            dynamic = True                            # sub-command flags live on another parser
            continue
        if node.func.attr != "add_argument":
            continue
        saw_parser = True
        for a in node.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                if a.value.startswith("-"):
                    flags.add(a.value)
            else:
                dynamic = True                        # a computed option string: cannot be sound
        for kw in node.keywords:
            if kw.arg == "parents":
                dynamic = True
    if dynamic:
        return None, "parser built dynamically (computed option strings or parents=)"
    if not saw_parser:
        return None, "no ArgumentParser in module"
    return flags, None


#: A PLAN proposes work not yet done, so a command naming a module that does not exist yet is
#: correct there and wrong in a report. A report ATTESTS -- its commands claim to have produced the
#: numbers beside them. Only the attesting documents are gated. (Measured: the sole finding left
#: after the real fixes was `python -m drivers.drv_step` in a 2026-05-20 plan, a module never built
#: under that name -- a proposal, not a broken receipt.)
EXCLUDE_PARTS = ("/plans/", "/proposals/")


def check(paths, severity="warn", show_ok=False):
    files = []
    for p in paths:
        p = Path(p)
        cand = sorted(p.rglob("*.md")) if p.is_dir() else ([p] if p.is_file() else [])
        files.extend(f for f in cand
                     if not any(x in "/" + f.as_posix() for x in EXCLUDE_PARTS))

    n_cmd = n_bad = n_skip = 0
    problems = []
    cache: dict[str, tuple] = {}
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, module, argstr in _commands(text):
            if module in SKIP_MODULES or module.split(".")[0] in SKIP_MODULES:
                n_skip += 1
                continue
            n_cmd += 1
            if module not in cache:
                cache[module] = _accepted_flags(module)
            known, why = cache[module]
            if known is None:
                if "not found" in (why or ""):
                    problems.append((f, lineno, module, why))
                    n_bad += 1
                else:
                    n_skip += 1
                continue
            try:
                argv = shlex.split(argstr, comments=True)
            except ValueError as e:
                problems.append((f, lineno, module, f"unparseable command line: {e}"))
                n_bad += 1
                continue
            used = [a.split("=", 1)[0] for a in argv
                    if a.startswith("-") and a != "-" and not _is_number(a)]
            unknown = [u for u in used if u not in known]
            if unknown:
                problems.append((f, lineno, module,
                                 f"flag(s) the module does not accept: {' '.join(sorted(set(unknown)))}"
                                 f"  (accepts: {' '.join(sorted(known)) or 'no flags'})"))
                n_bad += 1
            elif show_ok:
                print(f"  [ok] {f}:{lineno}  {module} {argstr}")

    for f, lineno, module, why in problems:
        print(f"  [--] {f}:{lineno}  python -m {module}: {why}")

    if n_cmd == 0:
        # A gate that looked at nothing must not report success (bugs/2026-07-09-13's lesson).
        print(f"reproduce-blocks: NOTHING CHECKED - no `python -m` commands in {len(files)} file(s)")
        return 2
    print(f"reproduce-blocks: {n_cmd - n_bad}/{n_cmd} documented commands use only flags their "
          f"module accepts ({n_skip} skipped: parser not statically readable)")
    if n_bad:
        print(f"reproduce-blocks: {n_bad} unexecutable command(s)"
              + ("" if severity == "error" else "  [warn]"))
    return 1 if (n_bad and severity == "error") else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--severity", default="warn", choices=["off", "warn", "error"])
    ap.add_argument("--list", action="store_true", help="also print commands that pass")
    a = ap.parse_args()
    if a.severity == "off":
        print("reproduce-blocks: off")
        return 0
    return check(a.paths or ["reports", "docs"], severity=a.severity, show_ok=a.list)


if __name__ == "__main__":
    raise SystemExit(main())
