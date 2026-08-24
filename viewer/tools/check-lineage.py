#!/usr/bin/env python3
"""Gate: an artifact records WHO produced it, not just what it contains.

Phase 2 of `plans/2026-08-15-campaign-lifecycle-harness.md` (mechanism 1).

The measured problem. Artifact `meta` blocks carry configuration -- case, decoder,
channel, seeds, RMC -- and no lineage. Nothing records the producing driver, the code
identity, or the spec pin. So a tool that needs to know "which driver made this" has to
INFER it from a configuration field, and `meta.case` resolving in `g2_reproduce`'s
registry is not evidence that `g2_reproduce` wrote the file. That inference regenerated
`R2_idd2` with the wrong driver and the resulting margin was reported as a finding before
a meta diff caught it (`bugs/2026-07-29-regen-artifact-dispatched-on-a-resolving-case-not-the-producer`);
five further recurrences followed, most recently the w3 family
(`bugs/2026-08-01-regen-dispatched-w3-artifacts-to-g2-reproduce`).

`regen_artifact.build_command` now refuses several unattributable shapes. This gate is the
other half: it MEASURES how much of the corpus can be attributed at all, so the refusals
stop being the only thing standing between an unattributable artifact and a wrong rebuild.

Baseline at authoring (2026-08-15), 247 artifacts carrying a `meta` block:

    producer recorded   70  (28%)
    seed0 recorded      99  (40%)
    code identity        0  ( 0%)
    config hash          0  ( 0%)
    produced_by          0  ( 0%)

Because coverage starts at zero, this gate ships at `warn` and RATCHETS: `--min-coverage`
sets a floor that CI can raise as artifacts are stamped. A gate introduced at `error`
against 0% coverage blocks every push and gets disabled, which is worse than not having it.

Field names mirror SLSA Provenance / in-toto deliberately -- see the DIVERGENCE NOTE below.

Severity: `.claude/lineage-severity` (off | warn | error, default warn).

Usage:
    python viewer/tools/check-lineage.py ARTIFACT.json [...]
    python viewer/tools/check-lineage.py --scan artifacts/<campaign-slug>
    python viewer/tools/check-lineage.py --scan DIR --min-coverage 0.25

Exit codes: 0 PASS, 1 FAIL (at error severity, or coverage below the floor), 2 nothing inspected.

DIVERGENCE NOTE (decisions/2026-08-15-execute-original-plan-over-verdict-rewrite).
`reports/2026-08-15-campaign-lifecycle-prior-art-review.md` section 2 returned REJECT on
building a bespoke lineage schema: the in-toto Attestation Framework and SLSA v1.0
Provenance predicate already specify this record, signed, and -- the load-bearing part --
match subjects **purely by digest, never by name or path**, which is precisely the fix the
refusals above implement by hand. The owner directed executing the original plan, so this
builds `produced_by`. The field names are chosen to mirror SLSA's (`build_type`,
`builder_version`, `external_parameters`, `resolved_dependencies`, `byproducts`) so that
adopting the real thing later is a rename rather than a redesign. Two things SLSA has that
this deliberately does not: a signature, and the trust-boundary split between
externally-supplied and platform-asserted parameters.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEVERITY_FILE = ROOT / ".claude/lineage-severity"

#: Mirrors SLSA Provenance. `build_type` is the producer identity (SLSA: buildDefinition.buildType);
#: `builder_version` is the code identity (SLSA: runDetails.builder.version).
REQUIRED = ("build_type", "builder_version")
RECOMMENDED = ("external_parameters", "resolved_dependencies", "seed0")

#: Files that are descriptors/registers, not produced artifacts -- they have no producer.
NOT_ARTIFACTS = {
    "campaign.json",
    "program-manifest.json",
    "study-manifest.json",
    "conformance-case-register.json",
}


def validate_record(doc: dict, name: str) -> list[str]:
    """Return problems with `doc`'s lineage record. Empty list == attributable."""
    problems: list[str] = []
    if not isinstance(doc, dict):
        return [f"{name}: not a JSON object"]

    meta = doc.get("meta")
    if not isinstance(meta, dict):
        return [f"{name}: no meta block - nothing to attribute"]

    pb = meta.get("produced_by") or doc.get("produced_by")
    if pb is None:
        return [
            f"{name}: no produced_by record. Configuration is not lineage - a tool that must "
            f"know which driver made this file has to INFER it from a config field, and a "
            f"resolving identifier proves nothing about the producer"
        ]
    if not isinstance(pb, dict):
        return [f"{name}: produced_by is not an object"]

    for f in REQUIRED:
        if not pb.get(f):
            problems.append(
                f"{name}: produced_by.{f} is missing - "
                + (
                    "this is the producer identity, the whole point of the record"
                    if f == "build_type"
                    else "without the code identity, 'same inputs' cannot imply 'same output'"
                )
            )
    return problems


def scan(paths: list[Path]) -> tuple[int, int, list[str], list[str]]:
    """Return (attributable, total, problems, unreadable) over produced artifacts."""
    attributable = total = 0
    problems: list[str] = []
    unreadable: list[str] = []
    for p in paths:
        if p.name in NOT_ARTIFACTS:
            continue
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except FileNotFoundError:
            unreadable.append(f"{p}: not found")
            continue
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            unreadable.append(f"{p}: unreadable ({type(e).__name__})")
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("meta"), dict):
            continue  # not a produced artifact
        total += 1
        found = validate_record(doc, str(p.relative_to(ROOT)) if ROOT in p.parents else p.name)
        if found:
            problems.extend(found)
        else:
            attributable += 1
    return attributable, total, problems, unreadable


def _severity() -> str:
    if SEVERITY_FILE.exists():
        v = SEVERITY_FILE.read_text(encoding="utf-8").strip().lower()
        if v in {"off", "warn", "error"}:
            return v
    return "warn"


def main(argv: list[str]) -> int:
    severity = _severity()
    min_cov = 0.0
    max_unattr: int | None = None
    targets: list[Path] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--scan" and i + 1 < len(argv):
            targets.extend(sorted(Path(argv[i + 1]).rglob("*.json")))
            i += 2
        elif a == "--min-coverage" and i + 1 < len(argv):
            min_cov = float(argv[i + 1])
            i += 2
        elif a == "--max-unattributable" and i + 1 < len(argv):
            max_unattr = int(argv[i + 1])
            i += 2
        elif a == "--severity" and i + 1 < len(argv):
            severity = argv[i + 1]
            i += 2
        elif a.startswith("--"):
            # NEVER silently swallow an unknown flag. This branch used to be `i += 1`, which
            # accepted `--severity error` and ignored it -- so the documented way to ask "would
            # this block?" answered 0 from a tool that had not read the flag. A gate that
            # discards its own controls is the failure of
            # bugs/2026-08-23-a-gate-with-no-usable-severity-is-a-gate-nobody-wires.
            print(f"[check-lineage] REFUSING: unknown flag {a!r}. A flag this tool does not "
                  f"understand is a verdict it was not asked for.", file=sys.stderr)
            return 2
        else:
            targets.append(Path(a))
            i += 1

    if severity not in {"off", "warn", "error"}:
        print(f"[check-lineage] REFUSING: bad severity {severity!r}", file=sys.stderr)
        return 2
    if severity == "off":
        print("[check-lineage] severity=off - skipped")
        return 0

    # Mechanism 2 -- refuse rather than print green on an empty scope.
    if not targets:
        print(
            "[check-lineage] REFUSING: no artifacts to inspect. A green gate must mean "
            "'looked and found nothing', never 'did not look'.",
            file=sys.stderr,
        )
        return 2

    attributable, total, problems, unreadable = scan(targets)

    if total == 0:
        print(
            f"[check-lineage] REFUSING: {len(targets)} path(s) named, none of them a produced "
            f"artifact (no meta block). That is a scope failure, not a pass.",
            file=sys.stderr,
        )
        return 2

    cov = attributable / total
    print(
        f"[check-lineage] scope: {total} produced artifact(s) inspected of {len(targets)} "
        f"path(s) named; {len(unreadable)} unreadable; "
        f"attributable {attributable}/{total} ({cov:.0%}); floor {min_cov:.0%}"
    )
    for u in unreadable:
        print(f"  UNREADABLE  {u}", file=sys.stderr)

    if cov < min_cov:
        print(
            f"[check-lineage] FAIL: coverage {cov:.1%} is below the floor {min_cov:.1%} - "
            f"the ratchet has slipped",
            file=sys.stderr,
        )
        return 1

    # RATCHET. The coverage floor is a PERCENTAGE, and at 0% attributable it can only be 0 --
    # so it cannot notice the population GROWING while nothing gets stamped, which is exactly
    # what happened: 247 unattributable artifacts at the gate's introduction, 339 now, with
    # attributable stuck at 0/0%. `campaign-lifecycle.md` prescribes "warn-plus-ratchet for a
    # gate whose baseline is zero"; the percentage floor is the warn half, this is the ratchet.
    if max_unattr is not None and len(problems) > max_unattr:
        print(
            f"[check-lineage] {len(problems)} unattributable artifact(s) exceeds the ratchet "
            f"of {max_unattr} - the debt GREW. Stamp the new artifacts with `produced_by`, or "
            f"raise the ratchet deliberately with a decisions/ record.",
            file=sys.stderr,
        )
        return 1

    if problems:
        label = "ERROR" if severity == "error" else "WARN "
        for p in problems[:40]:
            print(f"  {label}  {p}", file=sys.stderr)
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more", file=sys.stderr)
        print(
            f"[check-lineage] {len(problems)} unattributable artifact(s), severity={severity}",
            file=sys.stderr,
        )
        return 1 if severity == "error" else 0

    print(f"[check-lineage] OK - all {total} artifact(s) attributable")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
