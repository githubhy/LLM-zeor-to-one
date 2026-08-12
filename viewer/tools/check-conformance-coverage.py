#!/usr/bin/env python3
"""Gate: the conformance-coverage ratio is a gate OUTPUT, not an audit finding.

W7.6 (`G-PUB`) of `plans/2026-07-27-conformance-case-register.md`.

The 2026-07-26 audit had to re-derive coverage from the spec because **no artifact tracked it**.
This prints it on every push and fails on the states that made the old figure untrustworthy:

  1. a case with no `disposition`                      -> the register stops being 100% attributed
  2. a `deferred` with no `todos/` ref                  -> untracked work in a data field
  3. a value outside a closed enum                      -> how "cross-cutting" and "5.2.2.1.11-.14"
                                                           produced a 33% undercount
  4. a `margin` with no `basis`                         -> requirement-vs-reference conflation
                                                           (bugs/2026-07-22-hst-margin-...)
  5. a partition that does not sum                      -> how 32 scope-call cases went missing
  6. a coverage claim with no unit named                -> three counts are simultaneously correct

Severity: `.claude/conformance-coverage-severity` (off | warn | error, default warn).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "artifacts/nr-pdsch-demod/conformance-case-register.json"
SEVERITY_FILE = ROOT / ".claude/conformance-coverage-severity"

DISPOSITIONS = {"in-scope", "out-of-scope", "deferred"}
FR = {"FR1-conducted", "FR2-radiated"}
DUPLEX = {"FDD", "TDD"}
RX = {"1RX", "2RX", "4RX", "8RX"}
MARGIN_BASES = {"reference-performance", "requirement", "none"}


def check(reg: dict) -> list[str]:
    problems: list[str] = []
    cases = reg.get("cases") or []
    if not cases:
        return ["register has no cases — a green gate must mean 'looked and found nothing', "
                "never 'did not look'"]

    for c in cases:
        cid = c.get("case_id", "<no id>")
        d = c.get("disposition")
        if d not in DISPOSITIONS:
            problems.append(f"{cid}: disposition {d!r} not in {sorted(DISPOSITIONS)}")
        if d == "deferred" and not c.get("disposition_todo"):
            problems.append(f"{cid}: 'deferred' with no todos/ ref — untracked work")
        if d == "out-of-scope" and not c.get("disposition_reason"):
            problems.append(f"{cid}: 'out-of-scope' with no reason")
        for field, allowed in (("fr", FR), ("duplex", DUPLEX), ("rx_class", RX)):
            if c.get(field) not in allowed:
                problems.append(f"{cid}: {field}={c.get(field)!r} outside its closed enum")
        m = c.get("margin")
        if m is not None and m.get("basis") not in MARGIN_BASES:
            problems.append(f"{cid}: margin with basis={m.get('basis')!r} — a margin vs the "
                            f"requirement is mostly the RAN4 margin stack, not headroom")

    cov = reg.get("coverage") or {}
    if not cov.get("unit"):
        problems.append("coverage claim names no unit — 133 RAN5 cases / 104 RAN4 clauses / "
                        "279 RAN4 test rows are three correct answers to different questions")
    disp = reg.get("dispositions") or {}
    part = disp.get("by_scope_call") or {}
    if part and sum(part.values()) != len(cases):
        problems.append(f"scope-call partition sums to {sum(part.values())}, not {len(cases)}")
    if disp and disp.get("in_scope", 0) + disp.get("deferred", 0) + disp.get("out_of_scope", 0) \
            != len(cases):
        problems.append("disposition counts do not sum to the case total")
    return problems


def main() -> int:
    sev = (SEVERITY_FILE.read_text(encoding="utf-8").strip()
           if SEVERITY_FILE.is_file() else "warn")
    if sev == "off":
        return 0
    if not REGISTER.is_file():
        print(f"[conformance-coverage] register not found: {REGISTER.relative_to(ROOT)}")
        return 1 if sev == "error" else 0

    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    problems = check(reg)
    cov, disp = reg.get("coverage") or {}, reg.get("dispositions") or {}
    print(f"[conformance-coverage] {cov.get('covered', '?')}/{cov.get('total', '?')} "
          f"{cov.get('unit', 'UNIT NOT NAMED')} — "
          f"in-scope {disp.get('in_scope', '?')}, deferred {disp.get('deferred', '?')}, "
          f"out-of-scope {disp.get('out_of_scope', '?')}")
    for k, v in (cov.get("by_applicability") or {}).items():
        marker = "  <- compliance-relevant" if k == "mandatory" else ""
        print(f"[conformance-coverage]   {k:36} {v}{marker}")
    for p in problems:
        print(f"[conformance-coverage] {p}")
    if problems:
        print(f"[conformance-coverage] {len(problems)} problem(s), severity={sev}")
        return 1 if sev == "error" else 0
    print("[conformance-coverage] OK — every case attributed, enums closed, partitions sum")
    return 0


if __name__ == "__main__":
    sys.exit(main())
