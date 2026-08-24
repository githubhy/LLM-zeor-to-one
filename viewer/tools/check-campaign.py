#!/usr/bin/env python3
"""Gate: a campaign descriptor is well-formed, and its denominator is declared.

Phase 1 of `plans/2026-08-15-campaign-lifecycle-harness.md`. The descriptor
(`artifacts/<campaign>/campaign.json`) is the scope oracle a long campaign is
executed against; this validates its shape before anything reads it.

Registered descriptors are listed one per line in `.claude/campaigns` (opt-in,
`#` comments), mirroring `.claude/program-manifests` and `.claude/crosslink-scope`.
An unregistered campaign is never touched.

Checks, each earned from a measured failure in this repo:

  1. unknown/missing `schema`            -> the descriptor cannot be interpreted at all
  2. missing charter field               -> an exit criterion nobody wrote is not falsifiable
  3. population with no named `unit`     -> three counts are simultaneously correct
                                            (bugs/2026-08-07-coverage-scope-asserts-no-limitation)
  4. partition that does not sum         -> how 32 scope-call cases went missing (2026-07-26 audit)
  5. result with no declared `basis`     -> published-vs-reference conflation: a margin
                                            against a vendor-published number read as headroom
  6. basis outside the closed enum       -> how "cross-cutting" produced a 33% undercount
  7. duplicate result ids                -> two rows, one identity, silent last-write-wins

MECHANISM 2 (denominator self-report). Every run prints what it actually read --
descriptors found, descriptors unreadable, checks applied -- and REFUSES (exit 2)
rather than printing a green "no problems" when it was given nothing or could parse
nothing. A green gate must mean "looked and found nothing", never "did not look".
This is the residue of `field-notes/2026-07-31-blind-gates.md`, where
`check-value-ledger` read 12 of 811 files and `validate-refs` read 1, both exiting 0.

Severity: `.claude/campaign-severity` (off | warn | error, default error).

Usage:
    python viewer/tools/check-campaign.py DESCRIPTOR.json [DESCRIPTOR.json ...]
    python viewer/tools/check-campaign.py --all      # every registered descriptor

Exit codes: 0 PASS, 1 FAIL (a problem at error severity), 2 usage / nothing inspected.

DIVERGENCE NOTE (decisions/2026-08-15-execute-original-plan-over-verdict-rewrite):
`reports/2026-08-15-campaign-lifecycle-prior-art-review.md` section 4 found that
metrology (VIM) supplies "measurand" and "kind-of-quantity" as the formal vocabulary
here, and that no units library enforces "kind" -- so this closed enum is the repo's
own instrument rather than an adopted standard. The owner chose the original plan;
this implements it. The enum's CONTENTS, however, follow the tier-1 spec reading in
`surveys/campaign-lifecycle-management/_scratch/A4b-mainthread-local-spec-verification.md`:
TS 38.521-4 clause 4.1 establishes THREE distinct levels a margin can be measured
against, not two, so `test-requirement` is a member. That is a domain fact, not a
design change.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("campaign_common", ROOT / "viewer/tools/campaign_common.py")
_cc = importlib.util.module_from_spec(_s)          # type: ignore[arg-type]
sys.modules["campaign_common"] = _cc
_s.loader.exec_module(_cc)                          # type: ignore[union-attr]
BASES = _cc.BASES
REGISTRY = ROOT / ".claude/campaigns"
SEVERITY_FILE = ROOT / ".claude/campaign-severity"

KNOWN_SCHEMAS = {"campaign/v1"}

# Closed enum. A margin is meaningless until it names which of these it is measured
# against; see the module docstring's DIVERGENCE NOTE for why `test-requirement` exists.

CHARTER_FIELDS = ("question", "authority", "exit_criterion", "owner")
REQUIRED_TOP = ("schema", "campaign", "charter", "population")


PLACEHOLDER_NOTE = ("`campaign new` writes these; leaving one means the field was never "
                    "answered. A descriptor of placeholders is shape-valid and says "
                    "nothing, and it validated clean until this check existed.")


def _placeholders(node, path: str = "") -> list[str]:
    """Every `<...>` scaffold placeholder still in the descriptor, by path.

    DELIBERATELY CONSERVATIVE: it fires only on a WHOLE value (or key) wrapped in angle
    brackets, never on prose that merely contains one -- a `_note` reading "x < y" or a
    unit label like "<= 3 dB" must not be flagged, or the gate becomes one people
    switch off. Both live descriptors are the control: neither may trip it.
    """
    found: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            here = f"{path}.{k}" if path else str(k)
            if isinstance(k, str) and k.startswith("<") and k.endswith(">"):
                found.append(f"{here}: unfilled placeholder KEY {k!r}")
            found.extend(_placeholders(v, here))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            found.extend(_placeholders(v, f"{path}[{i}]"))
    elif isinstance(node, str):
        t = node.strip()
        if len(t) > 2 and t.startswith("<") and t.endswith(">"):
            found.append(f"{path}: unfilled placeholder {node!r}")
    return found


def validate(desc: dict) -> list[str]:
    """Return a list of problems. Empty list == the descriptor is well-formed."""
    problems: list[str] = []

    if not isinstance(desc, dict):
        return ["descriptor is not a JSON object"]

    schema = desc.get("schema")
    if schema not in KNOWN_SCHEMAS:
        problems.append(
            f"schema: {schema!r} is not a known campaign schema "
            f"(expected one of {sorted(KNOWN_SCHEMAS)})"
        )

    for key in REQUIRED_TOP:
        if key not in desc:
            problems.append(f"missing required top-level key {key!r}")

    charter = desc.get("charter") or {}
    if isinstance(charter, dict):
        for f in CHARTER_FIELDS:
            if not charter.get(f):
                problems.append(
                    f"charter.{f} is missing or empty - an exit criterion nobody wrote "
                    f"is not falsifiable"
                )
    else:
        problems.append("charter is not an object")

    ph = _placeholders(desc)
    if ph:
        problems.append(f"{len(ph)} unfilled scaffold placeholder(s) - {PLACEHOLDER_NOTE}")
        problems.extend(f"  {x}" for x in ph[:12])
        if len(ph) > 12:
            problems.append(f"  ... and {len(ph) - 12} more")

    problems.extend(_check_population(desc.get("population")))
    problems.extend(_check_results(desc))
    problems.extend(_check_closure(desc.get("closure")))
    problems.extend(_check_stages(desc.get("stages")))

    return problems


CLOSURE_KINDS = ("coverage", "defect-search")
STATISTICAL_KEYS = ("alpha", "beta", "p0", "p1", "confidence", "power")
DEFECT_SEARCH_RULES = ("sprt", "alpha-spending", "bayes-factor")


def _check_closure(cl) -> list[str]:
    """"When does the campaign stop" is TWO questions and only one is statistical.

    coverage       a SET DIFFERENCE over an enumerated population. It must acquire no
                   statistics -- a confidence level on a set difference is a category
                   error, and a checker that demands one makes coverage unpassable.
    defect-search  over an UNKNOWN population, where sequential analysis applies. A bare
                   consecutive-clean-rounds count is the naive instrument that theory
                   exists to supersede, and this repo's own five-pass review record
                   shows it does not converge.

    The prior-art review treated the two as one question. That was its own error.
    """
    problems: list[str] = []
    if cl is None:
        return ["closure is missing - a campaign that never says how it ends cannot be "
                "said to be running (v2 P5)"]
    if not isinstance(cl, dict):
        return ["closure is not an object"]

    kind = cl.get("kind")
    if kind not in CLOSURE_KINDS:
        return [f"closure.kind {kind!r} is not one of {list(CLOSURE_KINDS)}"]

    if kind == "coverage":
        stray = sorted(k for k in STATISTICAL_KEYS if k in cl)
        if stray:
            problems.append(
                f"closure.kind='coverage' carries statistical parameter(s) {stray} - "
                f"coverage closure is a deterministic set difference and must acquire "
                f"no statistics")
    else:
        if "consecutive_clean_rounds" in cl and not cl.get("rule"):
            problems.append(
                "closure declares 'consecutive_clean_rounds' as its defect-search rule - "
                "a consecutive-clean-rounds count is the naive instrument sequential "
                "analysis supersedes; name a rule "
                f"({', '.join(DEFECT_SEARCH_RULES)}) with its parameters")
        elif cl.get("rule") not in DEFECT_SEARCH_RULES:
            problems.append(
                f"closure.rule {cl.get('rule')!r} is not one of {list(DEFECT_SEARCH_RULES)} - "
                f"a defect-search closure over an unknown population needs a stated rule")
    return problems


def _check_stages(stages) -> list[str]:
    """D10: the stage list is per-campaign, drawn from a KNOWN set. Omission is the point
    (a calibration campaign has no pilot unit and no external sign-off); invention is not."""
    if stages is None:
        return []
    if not isinstance(stages, list) or not stages:
        return ["stages, when declared, must be a non-empty list"]
    known = {"charter", "enumerate", "attribute", "anchor", "pilot", "scale", "close", "signoff"}
    unknown = sorted(set(stages) - known)
    if unknown:
        return [f"stages names {unknown}, which is outside the known lifecycle "
                f"{sorted(known)} - a campaign may OMIT a stage, never invent one"]
    return []


def _check_population(pop) -> list[str]:
    problems: list[str] = []
    if pop is None:
        return problems  # already reported as a missing required key
    if not isinstance(pop, dict):
        return ["population is not an object"]

    if not pop.get("unit"):
        problems.append(
            "population.unit is missing - a coverage claim with no named unit is "
            "un-interpretable, because several different counts are simultaneously correct"
        )

    total = pop.get("total")
    partition = pop.get("partition")
    if total is None:
        problems.append("population.total is missing - there is no denominator to check against")
    if partition is None:
        problems.append("population.partition is missing - the denominator is not decomposed")

    if isinstance(total, int) and isinstance(partition, dict):
        bad = [k for k, v in partition.items() if not isinstance(v, int)]
        if bad:
            problems.append(f"population.partition has non-integer counts for {sorted(bad)}")
        else:
            summed = sum(partition.values())
            if summed != total:
                problems.append(
                    f"population.partition sums to {summed} but population.total is {total} - "
                    f"a partition that does not sum is how whole families go missing without "
                    f"anyone noticing; every member must be COUNTED AND NAMED, never "
                    f"silently excluded"
                )
    return problems


def _check_results(desc: dict) -> list[str]:
    problems: list[str] = []
    results = desc.get("results") or []
    if not isinstance(results, list):
        return ["results is not a list"]

    seen: set[str] = set()
    for i, r in enumerate(results):
        if not isinstance(r, dict):
            problems.append(f"results[{i}] is not an object")
            continue
        rid = r.get("id") or f"<results[{i}] with no id>"
        if rid in seen:
            problems.append(f"result {rid!r}: duplicate id - two rows sharing one identity")
        seen.add(rid)

        if "basis" not in r:
            problems.append(
                f"result {rid!r}: no basis declared. A margin is not a number until it names "
                f"what it is measured against - a margin against a REQUIREMENT is mostly the "
                f"margin stack and must not be cited as receiver headroom"
            )
        elif r["basis"] not in BASES:
            problems.append(
                f"result {rid!r}: basis {r['basis']!r} is outside the closed enum "
                f"{sorted(BASES)} - an open enum is how a coverage figure drifts"
            )

    declared = desc.get("bases") or {}
    if isinstance(declared, dict):
        for quantity, basis in declared.items():
            if basis not in BASES:
                problems.append(
                    f"bases[{quantity!r}]: {basis!r} is outside the closed enum {sorted(BASES)}"
                )
    return problems


# --------------------------------------------------------------------------- CLI


def _severity() -> str:
    if SEVERITY_FILE.exists():
        v = SEVERITY_FILE.read_text(encoding="utf-8").strip().lower()
        if v in {"off", "warn", "error"}:
            return v
    return "error"


def _registered() -> list[Path]:
    if not REGISTRY.exists():
        return []
    out = []
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(ROOT / line)
    return out


def main(argv: list[str]) -> int:
    severity = _severity()
    if severity == "off":
        print("[check-campaign] severity=off - skipped")
        return 0

    args = [a for a in argv if not a.startswith("--")]
    if "--all" in argv:
        targets = _registered()
        origin = f"{REGISTRY.relative_to(ROOT)} ({len(targets)} registered)"
    else:
        targets = [Path(a) for a in args]
        origin = "command line"

    # MECHANISM 2 -- the denominator self-report. Report scope BEFORE any verdict,
    # and refuse rather than print a green result when the scope is empty.
    if not targets:
        print(
            "[check-campaign] REFUSING: no campaign descriptors to inspect "
            f"(source: {origin}). A green gate must mean 'looked and found nothing', "
            "never 'did not look'.",
            file=sys.stderr,
        )
        return 2

    read, unreadable, problems_by_file = 0, [], {}
    for path in targets:
        try:
            desc = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            unreadable.append(f"{path}: not found")
            continue
        except json.JSONDecodeError as e:
            unreadable.append(f"{path}: invalid JSON ({e})")
            continue
        read += 1
        found = validate(desc)
        if found:
            problems_by_file[path] = found

    print(
        f"[check-campaign] scope: {read} descriptor(s) read of {len(targets)} named "
        f"(source: {origin}); {len(unreadable)} unreadable; "
        f"{len(BASES)} bases in the closed enum"
    )
    for u in unreadable:
        print(f"  UNREADABLE  {u}", file=sys.stderr)

    if read == 0:
        print(
            "[check-campaign] REFUSING: every named descriptor was unreadable - "
            "this is a scope failure, not a pass.",
            file=sys.stderr,
        )
        return 2

    if unreadable:
        # An unreadable descriptor is a failure in its own right: it is a registered
        # campaign the gate cannot see, which is exactly the blind-gate class.
        problems_by_file[Path("<registry>")] = [
            f"{len(unreadable)} registered descriptor(s) could not be read"
        ]

    if not problems_by_file:
        print(f"[check-campaign] OK - {read} descriptor(s) valid")
        return 0

    for path, found in problems_by_file.items():
        print(f"\n{path}", file=sys.stderr)
        for p in found:
            print(f"  {'ERROR' if severity == 'error' else 'WARN '}  {p}", file=sys.stderr)

    total = sum(len(v) for v in problems_by_file.values())
    print(f"\n[check-campaign] {total} problem(s) across {len(problems_by_file)} file(s)", file=sys.stderr)
    return 1 if severity == "error" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
