#!/usr/bin/env python3
"""Gate: a conformance/calibration register's coverage claim is decidable.

Mechanism 3 of the campaign-lifecycle harness. Generalizes `check-conformance-coverage.py`,
which hardcoded a single register path at module scope and could therefore gate exactly
one campaign.

Coverage is a gate OUTPUT, not an audit finding. Upstream an audit had to re-derive
coverage from the source-of-record because no artifact tracked it, and the figure it
replaced carried a 33% undercount.

Checks:

  1. no disposition                    -> the register stops being 100% attributed
  2. deferred with no todos ref        -> untracked work hiding in a data field
  3. disposition outside a closed enum -> how "cross-cutting" produced the undercount
  4. margin with no basis              -> requirement-vs-reference conflation
  5. margin basis outside the enum     -> an unknown basis resolves to no decidable quantity
  6. margin vs PUBLISHED claimed as HEADROOM -> the measured failure class: a "+N point"
     headline that is mostly prompt template and answer extraction, not capability
     (.claude/rules/sim-report-completeness.md [opt:SIM-REQBASIS])
  7. a reference-performance spread pooled across DIFFERENT conditions -> a 0-shot, a
     5-shot and a 5-shot-CoT number for one model on one benchmark are three quantities,
     not a spread; pooling them manufactures dispersion that does not exist
  8. partition that does not sum       -> how 32 scope-call cases went missing
  9. coverage claim with no unit named -> three counts are simultaneously correct

Severity: `.claude/coverage-severity` (off | warn | error, default warn).

Usage:
    python viewer/tools/check-coverage.py REGISTER.json [...]
    python viewer/tools/check-coverage.py --all       # every register named in .claude/campaigns

Exit codes: 0 PASS, 1 FAIL, 2 nothing inspected.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("campaign_common", ROOT / "viewer/tools/campaign_common.py")
_cc = importlib.util.module_from_spec(_spec)          # type: ignore[arg-type]
sys.modules["campaign_common"] = _cc
_spec.loader.exec_module(_cc)                          # type: ignore[union-attr]

Scope, REFUSE = _cc.Scope, _cc.REFUSE
BASES, NOT_HEADROOM = _cc.BASES, _cc.NOT_HEADROOM

DISPOSITIONS = {"in-scope", "out-of-scope", "deferred", "covered"}

#: Shared with viewer/tools/check-campaign.py BASES. TS 38.521-4 clause 4.1 establishes
#: three distinct levels a margin can be measured against, not two.

#: A margin against these is NOT receiver headroom -- it is mostly the margin stack.


#: Where contributing populations ACTUALLY live in the register today, as a dotted path from a
#: case. This is an INVENTORY OF THE DEFECT, not a lookup table -- the pooling guard below still
#: reads only `reference_performance`, deliberately. Teaching it five paths would make five names
#: for one concept permanently workable, which is the thing
#: `todos/2026-08-23-reference-population-schema-convergence` exists to end.
#:
#: What this list is for is the DENOMINATOR: a gate that inspects nothing must say so
#: (`.claude/rules/campaign-lifecycle.md`, "every gate reports its own denominator"). Measured at
#: introduction: the guard inspects 0 blocks while 81 exist.
POPULATION_PATHS = (
    "arms[].impairment_basis",
    "margin.impairment_population",
    "arms[].reference_population_unresolved.candidate",
    "arms[].reference_population",
    "margin.reference_performance_population",
)

#: The one path the guard reads. Nothing writes it yet; that is the finding.
GUARD_PATH = "reference_performance"


def _blocks_at(case: dict, path: str) -> list[dict]:
    """Every dict at a dotted path, where `arms[]` fans out over the case's arms."""
    nodes = [case]
    for part in path.split("."):
        nxt = []
        for n in nodes:
            if not isinstance(n, dict):
                continue
            if part.endswith("[]"):
                v = n.get(part[:-2])
                nxt.extend(x for x in (v or []) if isinstance(x, dict))
            else:
                v = n.get(part)
                if isinstance(v, dict):
                    nxt.append(v)
        nodes = nxt
    return nodes


def population_denominator(reg: dict) -> dict:
    """What the pooling guard looked at, against what exists. A report, never a finding.

    Returns `inspected` (blocks the guard actually reads) and `present` (blocks carrying a
    `contributors` list anywhere this campaign puts one). `inspected == 0 < present` is the
    signature of a guard reading a key nothing writes --
    `bugs/2026-08-23-refperf-pooling-guard-reads-a-key-nothing-writes`.
    """
    cases = reg.get("cases") or []
    inspected = sum(1 for c in cases if isinstance(c.get(GUARD_PATH), dict))
    by_path = {}
    for path in POPULATION_PATHS:
        n = sum(1 for c in cases for b in _blocks_at(c, path) if b.get("contributors"))
        if n:
            by_path[path] = n
    return {"inspected": inspected, "present": sum(by_path.values()),
            "by_path": by_path, "cases": len(cases)}


def check_register(reg: dict) -> list[str]:
    problems: list[str] = []
    if not isinstance(reg, dict):
        return ["register is not a JSON object"]

    cov = reg.get("coverage") or {}
    if isinstance(cov, dict) and cov and not cov.get("unit"):
        problems.append(
            "coverage: no unit named - several different counts are simultaneously correct "
            "until the unit is stated"
        )

    scope = reg.get("scope") or {}
    total = scope.get("total_cases_in_spec")
    part = scope.get("partition_by_family")
    if isinstance(total, int) and isinstance(part, dict):
        s = sum(v for v in part.values() if isinstance(v, int))
        if s != total:
            problems.append(
                f"scope.partition_by_family sums to {s} but total_cases_in_spec is {total} - "
                f"every family must be counted and named, never silently excluded"
            )

    for c in reg.get("cases") or []:
        if not isinstance(c, dict):
            continue
        cid = c.get("case_id", "<no id>")
        d = c.get("disposition")
        if d is None:
            problems.append(f"{cid}: no disposition - the register is not 100% attributed")
        elif d not in DISPOSITIONS:
            problems.append(f"{cid}: disposition {d!r} outside the closed enum {sorted(DISPOSITIONS)}")
        # Field-name note: the PDSCH register spells this `disposition_todo`. An earlier
        # draft of this check looked only for `todos`/`todo` and would have fired on all 93
        # deferred cases -- a check answering a question adjacent to the one it was asked,
        # the exact class of field-notes/2026-07-30-structural-checks-that-pass-for-the-wrong-reason.
        # Caught by reading the register's actual keys, not by the finding count looking wrong.
        if d == "deferred" and not (
            c.get("todos") or c.get("todo") or c.get("disposition_todo")
        ):
            problems.append(f"{cid}: deferred with no todos ref - untracked work in a data field")

        m = c.get("margin")
        if isinstance(m, dict):
            b = m.get("basis")
            if b is None:
                problems.append(f"{cid}: margin with no basis declared")
            elif b not in BASES:
                problems.append(
                    f"{cid}: margin basis {b!r} outside the closed enum {sorted(BASES)} - "
                    f"it resolves to no decidable quantity"
                )
            elif b in NOT_HEADROOM and str(m.get("claim", "")).lower() == "headroom":
                problems.append(
                    f"{cid}: margin vs {b!r} claimed as HEADROOM. A margin against a "
                    f"published value is mostly the configuration stack (prompt template, "
                    f"few-shot k, decoding params, answer extraction), not capability headroom"
                )

        rp = c.get("reference_performance")
        if isinstance(rp, dict):
            contribs = rp.get("contributors") or []
            conds = {x.get("condition") for x in contribs if isinstance(x, dict)}
            conds.discard(None)
            if rp.get("spread_db") is not None and len(conds) > 1:
                problems.append(
                    f"{cid}: reference_performance.spread_db pooled across {len(conds)} "
                    f"different conditions {sorted(conds)} - those are different quantities, "
                    f"not a company spread; pooling them manufactures dispersion"
                )
    return problems


def _registered_registers() -> list[Path]:
    """Registers named by any registered campaign descriptor."""
    reg_file = ROOT / ".claude/campaigns"
    out: list[Path] = []
    if not reg_file.exists():
        return out
    for line in reg_file.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        try:
            desc = json.loads((ROOT / line).read_text(encoding="utf-8"))
        except Exception:
            continue
        for cand in desc.get("_derived_from") or []:
            if "register" in cand:
                out.append(ROOT / cand)
    return out


def main(argv: list[str]) -> int:
    severity = _cc.severity_from(ROOT / ".claude/coverage-severity", "warn")
    if severity == "off":
        print("[check-coverage] severity=off - skipped")
        return 0

    targets = _registered_registers() if "--all" in argv else [Path(a) for a in argv if not a.startswith("--")]
    scope = Scope("check-coverage")
    problems: list[str] = []

    for p in targets:
        try:
            reg = json.loads(p.read_text(encoding="utf-8"))
        except FileNotFoundError:
            scope.could_not_read(p, "not found"); continue
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            scope.could_not_read(p, f"{type(e).__name__}"); continue
        scope.saw(p)
        problems.extend(f"{p.name}: {x}" for x in check_register(reg))

    if scope.verdict() == REFUSE:
        print(scope.refuse_message(), file=sys.stderr)
        return 2
    scope.emit()

    for p in targets:
        try:
            reg = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        d = population_denominator(reg)
        if not d["present"] and not d["inspected"]:
            continue
        print(f"[check-coverage] pooling guard: inspected {d['inspected']} of {d['present']} "
              f"contributing-population block(s) across {d['cases']} case(s)", file=sys.stderr)
        if d["inspected"] == 0 and d["present"]:
            for path, n in sorted(d["by_path"].items(), key=lambda kv: -kv[1]):
                print(f"    {n:>4}  cases[].{path}", file=sys.stderr)
            print("    the guard reads cases[].reference_performance, which nothing writes - "
                  "so the same-basis pooling check has no verdict here. NOT taught these paths "
                  "on purpose: five names for one concept is the defect. See "
                  "todos/2026-08-23-reference-population-schema-convergence.", file=sys.stderr)

    if problems:
        label = "ERROR" if severity == "error" else "WARN "
        for x in problems[:60]:
            print(f"  {label}  {x}", file=sys.stderr)
        if len(problems) > 60:
            print(f"  ... and {len(problems)-60} more", file=sys.stderr)
        print(f"[check-coverage] {len(problems)} problem(s), severity={severity}", file=sys.stderr)
        return 1 if severity == "error" else 0

    print("[check-coverage] OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
