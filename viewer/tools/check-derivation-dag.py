#!/usr/bin/env python3
"""Phase-6 gate: make "first-principled" a checkable property.

THE PROBLEM THIS EXISTS FOR
    Nothing distinguishes a derivation from an assertion with equations near it. §7.6's
    ISI reconciliation rested on an assumption attributed to a paper that does not make
    it, and passed every check the survey had. "Derived from first principles" was a
    claim about the prose, verifiable only by reading it.

THE ANNOTATION
    An equation declares its antecedents in a SIBLING marker on the same line:

        <!-- eq:6-18 --><!-- deps:6-18=6-17,def:beta,assume:small-eps -->

    A sibling rather than an attribute on `eq:` — deliberately. The first version wrote
    `<!-- eq:6-18 deps:... -->` and that broke `validate-refs`' marker regex: 49 of 99
    markers went invisible and it reported 81 phantom orphaned refs. When a marker
    already has consumers, the additive change is a new marker, not a richer old one.

    Three kinds of antecedent, and the distinction is the whole point:

      * `<eq-id>`      another equation in the same survey.
      * `def:<name>`    a stated definition.       } these are the only
      * `assume:<name>` a stated modelling assumption. } LEGAL ROOTS,
      * `cite:<bib-N>`  a cited primary result.     } plus nothing else.

    Definitions and assumptions are declared once, anywhere in the survey, as

        <!-- declare:def:beta -->      <!-- declare:assume:small-eps -->

FOUR PROPERTIES ENFORCED
    1. NO ORPHANS       every equation reaches a declared root.
    2. ROOTS ARE LEGAL  a root is a definition, a modelling assumption, or a cited
                        primary. An equation rooted in nothing is an ASSERTION, and is
                        named as one rather than passing as a derivation.
    3. NO CYCLES        eq A depending on B depending on A is not a derivation.
    4. ASSUMPTION INHERITANCE
                        every equation inherits its antecedents' assumptions
                        transitively, so a linearisation propagates automatically to
                        everything downstream. This is the property that pays for the
                        phase: it is what would have caught §6.6's "sigma_eps is an
                        ensemble variance" ambiguity and §8.5's `R > 0` gap
                        mechanically. `--show-assumptions <eq-id>` prints the closure.

WHAT THIS DELIBERATELY DOES NOT DO
    It does not verify that the declared dependency is mathematically real — only that
    it is declared, reachable, acyclic, and that the assumption closure is computable.
    A wrong `deps:` is still a wrong claim; this gate makes the claim EXPLICIT and
    checkable rather than implicit and unfalsifiable. Annotating is an authoring act,
    which is why coverage is REPORTED rather than assumed (see `--require-coverage`).

CONFIG
    .claude/derivation-dag-severity    off | warn | error   (default: warn)

USAGE
    check-derivation-dag.py --survey surveys/adc-calibration
    check-derivation-dag.py --survey surveys/adc-calibration --show-assumptions 6-18
    check-derivation-dag.py --survey surveys/adc-calibration --require-coverage 0.25
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SEVERITY_FILE = REPO / ".claude" / "derivation-dag-severity"

# A SIBLING marker, not an attribute on eq:. Extending the eq: marker itself broke
# validate-refs' parser -- 49 of 99 markers went invisible and it reported 81 phantom
# orphaned refs. Additive beats invasive when a marker already has consumers.
EQ_RE = re.compile(r"<!--\s*eq:([A-Za-z0-9._-]+)\s*-->")
DEPS_RE = re.compile(r"<!--\s*deps:([A-Za-z0-9._-]+)=([^\s>]+)\s*-->")
DECLARE_RE = re.compile(r"<!--\s*declare:(def|assume):([A-Za-z0-9._-]+)\s*-->")
BIB_RE = re.compile(r"<!--\s*bib:(\d+)\s*-->")

ROOT_KINDS = ("def:", "assume:", "cite:")


def severity(cli: str | None) -> str:
    if cli:
        return cli
    if SEVERITY_FILE.exists():
        for line in SEVERITY_FILE.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line in ("off", "warn", "error"):
                return line
    return "warn"


SEC_RE = re.compile(r"<!--\s*sec:([0-9]+(?:\.[0-9]+)*)\s*-->")


def parse(survey: Path):
    """(deps, declared, cites, where, sec_of) — deps maps eq-id -> [antecedent, ...]."""
    deps: dict[str, list[str]] = {}
    declared: set[str] = set()
    cites: set[str] = set()
    where: dict[str, str] = {}
    sec_of: dict[str, str] = {}
    for f in sorted(survey.rglob("*.md")):
        if "_scratch" in f.parts:
            continue
        cur_sec = "?"
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            sm = SEC_RE.search(line)
            if sm:
                cur_sec = sm.group(1)
            for m in DECLARE_RE.finditer(line):
                declared.add(f"{m.group(1)}:{m.group(2)}")
            for m in BIB_RE.finditer(line):
                cites.add(f"cite:{m.group(1)}")
            for m in EQ_RE.finditer(line):
                where[m.group(1)] = f"{f.relative_to(REPO)}:{i}"
                sec_of[m.group(1)] = cur_sec
            for m in DEPS_RE.finditer(line):
                deps[m.group(1)] = [x for x in m.group(2).split(",") if x]
    return deps, declared, cites, where, sec_of


def assumption_closure(eq: str, deps: dict[str, list[str]],
                       seen: set[str] | None = None) -> set[str]:
    """Every assumption reachable from `eq`. Property 4."""
    seen = seen or set()
    if eq in seen:
        return set()
    seen.add(eq)
    out: set[str] = set()
    for a in deps.get(eq, []):
        if a.startswith("assume:"):
            out.add(a)
        elif not a.startswith(ROOT_KINDS):
            out |= assumption_closure(a, deps, seen)
    return out


def find_cycle(deps: dict[str, list[str]]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def walk(n: str) -> list[str] | None:
        if state.get(n) == 2:
            return None
        if state.get(n) == 1:
            return stack[stack.index(n):] + [n]
        state[n] = 1
        stack.append(n)
        for a in deps.get(n, []):
            if a.startswith(ROOT_KINDS):
                continue
            c = walk(a)
            if c:
                return c
        stack.pop()
        state[n] = 2
        return None

    for n in list(deps):
        c = walk(n)
        if c:
            return c
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-6 derivation-DAG gate.")
    ap.add_argument("--survey", action="append", required=True)
    ap.add_argument("--severity", choices=["off", "warn", "error"])
    ap.add_argument("--show-assumptions", metavar="EQ_ID",
                    help="print the transitive assumption closure of one equation")
    ap.add_argument("--strict-cross-section", action="store_true",
                    help="treat cross-section antecedents as problems (audit mode)")
    ap.add_argument("--require-coverage", type=float, default=0.0,
                    help="fail if fewer than this fraction of equations declare deps")
    args = ap.parse_args()

    sev = severity(args.severity)
    if sev == "off" and not args.show_assumptions:
        print("[derivation-dag] off")
        return 0

    failures = 0
    for s in args.survey:
        survey = REPO / s.rstrip("/")
        deps, declared, cites, where, sec_of = parse(survey)
        if not where:
            print(f"[derivation-dag] {s}: parsed ZERO equation markers — refusing to "
                  "report a clean result on an empty corpus")
            return 2

        if args.show_assumptions:
            eq = args.show_assumptions
            if eq not in where:
                print(f"[derivation-dag] no such equation marker: {eq}")
                return 2
            cl = sorted(assumption_closure(eq, deps))
            print(f"[derivation-dag] eq:{eq} inherits {len(cl)} assumption(s):")
            for a in cl:
                print(f"  {a}" + ("" if a in declared else "   <-- NOT DECLARED"))
            return 0

        problems: list[str] = []

        # property 3 first: a cycle makes reachability meaningless
        cyc = find_cycle(deps)
        if cyc:
            problems.append("CYCLE: " + " -> ".join(cyc))

        for eq, ants in sorted(deps.items()):
            for a in ants:
                if a.startswith("def:") or a.startswith("assume:"):
                    # property 2: a root must be DECLARED, not merely well-shaped
                    if a not in declared:
                        problems.append(
                            f"{where[eq]}: eq:{eq} roots in {a}, which is never declared "
                            f"(add <!-- declare:{a} --> where it is stated)")
                elif a.startswith("cite:"):
                    if cites and a not in cites:
                        problems.append(
                            f"{where[eq]}: eq:{eq} roots in {a}, but no <!-- bib:"
                            f"{a.split(':')[1]} --> exists")
                elif a not in where:
                    problems.append(
                        f"{where[eq]}: eq:{eq} depends on eq:{a}, which does not exist")
                elif a not in deps:
                    # property 1: the antecedent is itself un-rooted, so the chain
                    # does not reach a root. Named as an ASSERTION, per the rule.
                    problems.append(
                        f"{where[eq]}: eq:{eq} depends on eq:{a}, which declares no "
                        f"antecedents — the chain reaches no root, so eq:{a} is an "
                        f"ASSERTION rather than a derivation")

        # PROPERTY 5 (advisory) -- CROSS-SECTION antecedents.
        #
        # Earned, not invented: three §8 annotations were rooted in an unrelated
        # section's equations (the LMS update rule in the split-ADC identity, the
        # stability bound in the VOLTERRA SERIES) and properties 1-4 passed all three.
        # A derivation chain is usually within-section, so a cross-section antecedent is
        # the shape a mis-mapped marker takes. It is NOT a defect -- §10.2 genuinely
        # follows from §5.1 -- so this is a REVIEW LIST, printed rather than failed,
        # and --strict-cross-section turns it into one for an audit pass.
        xsec: list[str] = []
        for eq, ants in sorted(deps.items()):
            for a in ants:
                if a.startswith(ROOT_KINDS) or a not in sec_of:
                    continue
                if sec_of.get(eq) != sec_of.get(a):
                    xsec.append(f"{where[eq]}: eq:{eq} (§{sec_of.get(eq)}) "
                                f"depends on eq:{a} (§{sec_of.get(a)})")
        if xsec:
            print(f"[derivation-dag]   {len(xsec)} cross-section antecedent(s) — review "
                  "these first, a mis-mapped marker looks exactly like this:")
            for x in xsec:
                print(f"    {x}")
            if args.strict_cross_section:
                problems.extend(xsec)

        n_eq, n_ann = len(where), len(deps)
        frac = n_ann / n_eq if n_eq else 0.0
        print(f"[derivation-dag] {s}: {n_eq} equation(s), {n_ann} annotated "
              f"({frac:.0%}), {len(declared)} declared root(s), {len(problems)} problem(s)")
        if frac < args.require_coverage:
            problems.append(
                f"COVERAGE: {frac:.0%} of equations declare deps, below the required "
                f"{args.require_coverage:.0%} — an unannotated equation is invisible to "
                "every property above, so partial coverage must not read as clean")
        for p in problems:
            print(f"  [{'ERROR' if sev == 'error' else 'warn'}] {p}")
        failures += len(problems)

    print(f"\n[derivation-dag] {failures} problem(s), severity={sev}")
    return 1 if (failures and sev == "error") else 0


if __name__ == "__main__":
    sys.exit(main())
