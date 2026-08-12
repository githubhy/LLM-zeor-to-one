#!/usr/bin/env python3
"""Phase-5 gate: the survey's published numbers must still match their recomputation.

`sim/adc-calibration/oracles/` recomputes the survey's numbered results from first
principles. On its own that only checks the *oracle's* transcription — the expected
values live in the oracle, so editing a number in the survey would go completely
unnoticed. This gate closes that loop.

HOW THE LOOP CLOSES
    An oracle check may carry a `val_id`. The survey declares the same id at the
    point of use, with the value it prints:

        <!-- val:jitter-snr-5ghz-50fs = 56.08 dB -->

    The gate runs the oracles, parses every `val:` DECLARATION out of the survey,
    and compares. A perturbed survey number fails; a perturbed oracle fails; a
    number that appears in the survey with no oracle behind it is reported as
    unbacked, and an oracle export with no survey declaration is reported as
    unused. All four states are visible, which is the point.

WHY A GATE RATHER THAN DISCIPLINE
    `bugs/2026-05-26-03` recommended a check instead of building one, and the same
    class fired twice more. A recommendation is a deferral.

WHAT IT DELIBERATELY DOES NOT DO
    It does not parse free prose for numbers. A value earns gating by being given a
    `val:` id — an explicit, reviewable act — because a prose scraper would either
    miss most values or drown the gate in false positives, and a gate that cries
    wolf gets switched off. Coverage is therefore reported (`N of M exports
    declared`) so partial coverage cannot read as complete.

CONFIG
    .claude/math-oracle-severity    off | warn | error   (default: warn)

USAGE
    check-math-oracles.py                       # the whole corpus
    check-math-oracles.py --survey surveys/adc-calibration
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SEVERITY_FILE = REPO / ".claude" / "math-oracle-severity"

# The value-ledger declaration form, already defined by check-value-ledger.py.
DECL_RE = re.compile(r"<!--\s*val:([A-Za-z0-9._-]+)\s*=\s*(.+?)\s*-->")
# Leading number of a declared value: "56.08 dB", "1.25e7 samples", "-2.16 dB",
# "6.35 fs", "96 %". The unit suffix is captured too, because a UNIT MISMATCH is a
# real defect this gate should report rather than paper over: the first version
# ignored units and flagged "96 %" against a computed 0.9615 as value drift, when
# the actual fault was that survey and oracle were on different bases -- precisely
# the class this survey spent five review passes on.
NUM_RE = re.compile(r"^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*(\S*)")

# A declared value carries its own precision. "0.09 dB" asserts two decimal places,
# so the gate must accept anything that ROUNDS to it -- half a unit in the last
# place. Gating a 2-significant-figure value to 1e-9 would fail every correctly
# rounded number in the survey, and loosening to a flat relative tolerance instead
# would stop catching real drift in the precise ones. Precision-derived is both.
def _half_ulp(raw: str) -> float:
    m = re.match(r"^\s*[+-]?(\d+)?(?:\.(\d+))?(?:[eE]([+-]?\d+))?", raw)
    if not m:
        return 0.0
    frac, exp = m.group(2) or "", int(m.group(3) or 0)
    return 0.5 * 10.0 ** (-len(frac) + exp)


# Unit aliases that mean the same thing to the oracle. Anything not listed is
# compared literally, so a genuine unit change is reported.
UNIT_EQUIV = {
    "": {"", "—"}, "%": {"%"}, "dB": {"dB", "dBc", "dBFS"}, "fs": {"fs"},
    "bits": {"bits", "bit", "ENOB"}, "ENOB": {"ENOB", "bits", "bit"},
    "LSB": {"LSB"}, "samples": {"samples", "sample"},
}

# Where the oracles live, per survey.
# survey path -> oracle package that recomputes its published val: ids.
# Empty until a survey ships an oracle package: the gate is a no-op with no
# registered survey, which is correct -- there is nothing to recompute yet.
# Register a survey by adding its pair here once sim/<survey>/oracles/ exists.
ORACLE_DIRS: dict[str, str] = {}


def severity(cli: str | None) -> str:
    if cli:
        return cli
    if SEVERITY_FILE.exists():
        for line in SEVERITY_FILE.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line in ("off", "warn", "error"):
                return line
    return "warn"


KNOWN_UNITS = {
    "dB", "dBc", "dBFS", "fs", "ps", "ns", "bits", "bit", "ENOB", "LSB",
    "samples", "sample", "%", "uV", "V", "GHz", "MHz", "Hz",
}
# A trailing parenthetical counts as a unit ONLY if it is in KNOWN_UNITS.
# "(Gaussian)", "(ratio)" and "(the 'half an LSB' basis gap)" are all trailing
# parentheticals and none is a unit, so a purely positional heuristic manufactures
# false drift -- it did, on this gate's second run. High-precision-or-silent, like
# the repo's other gates: an unrecognised parenthetical means "no unit declared",
# and the unit comparison does not run for that value.


def unit_of(oracle_what: str) -> str:
    """The unit an oracle check declares, if it declares a KNOWN one."""
    m = re.search(r"\(([^()]{1,12})\)\s*$", oracle_what)
    u = (m.group(1) if m else "").strip()
    return u if u in KNOWN_UNITS else ""


def declarations(survey: Path) -> dict[str, tuple[float, str, str, str]]:
    """{val_id: (number, unit, raw text, "file:line")} from the survey's markers."""
    out: dict[str, tuple[float, str, str, str]] = {}
    for f in sorted(survey.rglob("*.md")):
        if "_scratch" in f.parts:
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in DECL_RE.finditer(line):
                key, raw = m.group(1), m.group(2)
                num = NUM_RE.match(raw)
                # An out-of-tree declarations dir (--declarations-from) is not under
                # REPO, so relative_to would raise. Fall back to the bare path.
                try:
                    where = f"{f.relative_to(REPO)}:{i}"
                except ValueError:
                    where = f"{f}:{i}"
                if not num:
                    print(f"{where}: [warn] val:{key} = {raw!r} has no leading number")
                    continue
                if key in out:
                    print(f"{where}: [warn] val:{key} declared more than once")
                out[key] = (float(num.group(1)), num.group(2), raw, where)
    return out


def oracle_exports(oracle_dir: Path) -> dict[str, tuple[float, float, str, str]]:
    """Run the oracles in a subprocess and collect their val_id exports.

    The fourth element is the unit the oracle's own description declares, so a
    survey/oracle UNIT mismatch is reported rather than silently rescaled. That
    was a real finding on this gate's first run: the survey prints "96 %" where
    the oracle computed 0.9615, and reporting it as *value* drift would have sent
    a reader looking for an arithmetic error that was not there.
    """
    code = (
        "import json,sys;sys.path.insert(0,'.');"
        "import run_all_oracles as R;from _oracle import exported;"
        "print('@@JSON@@'+json.dumps({k:[v[0],v[1],v[2],v[3]] "
        "for k,v in exported([m.build() for m in R.MODULES]).items()}))"
    )
    r = subprocess.run([sys.executable, "-c", code], cwd=str(oracle_dir),
                       capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        print(f"[math-oracles] the oracle suite failed to run:\n{r.stderr[-3000:]}")
        raise SystemExit(2)
    tag = "@@JSON@@"
    line = next((l for l in r.stdout.splitlines() if l.startswith(tag)), None)
    if line is None:
        print(f"[math-oracles] no export payload from the oracles:\n{r.stdout[-2000:]}")
        raise SystemExit(2)
    import json
    return {k: (v[0], v[1], v[2], v[3]) for k, v in json.loads(line[len(tag):]).items()}


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-5 oracle-vs-survey gate.")
    ap.add_argument("--survey", action="append", default=None,
                    help="survey directory (default: every one with an oracle suite)")
    ap.add_argument("--declarations-from", metavar="DIR",
                    help="parse val: declarations from DIR instead of --survey, while "
                         "still running --survey's registered oracle suite. Exists so "
                         "the gate's own RED anchor can perturb a COPY: the anchor test "
                         "used to mutate the real survey and restore it in a `finally`, "
                         "and its docstring claimed 'a crash cannot leave the survey "
                         "modified' — which is false for SIGKILL. A pytest timeout "
                         "killed it mid-mutation and left a +5 dB perturbation on disk, "
                         "one `git commit -a` away from being frozen into history "
                         "(the failure bugs/2026-07-14-06 already recorded once).")
    ap.add_argument("--severity", choices=["off", "warn", "error"])
    args = ap.parse_args()

    sev = severity(args.severity)
    if sev == "off":
        print("[math-oracles] off")
        return 0

    targets = args.survey or list(ORACLE_DIRS)
    failures = 0
    for t in targets:
        t = t.rstrip("/")
        if t not in ORACLE_DIRS:
            print(f"[math-oracles] {t}: no oracle suite registered — skipped")
            continue
        survey, odir = REPO / t, REPO / ORACLE_DIRS[t]
        if not odir.exists():
            print(f"[math-oracles] {t}: oracle dir {odir} missing")
            failures += 1
            continue

        exports = oracle_exports(odir)
        decls = declarations(Path(args.declarations_from).resolve()
                             if args.declarations_from else survey)
        drift, unbacked = [], []

        for key, (want, unit, raw, where) in sorted(decls.items()):
            if key not in exports:
                unbacked.append((key, where, raw))
                continue
            got, tol, src, o_unit = exports[key]
            # A UNIT change is drift too, and the more dangerous kind: the number
            # can stay right while the basis silently moves under it.
            if o_unit and unit and unit not in UNIT_EQUIV.get(o_unit, {o_unit}):
                drift.append((key, where, raw, want, got, src + f" [unit {o_unit!r}]",
                              0.0))
                continue
            # accept anything that ROUNDS to the declared value, plus the oracle's
            # own tolerance for its NUMERIC checks
            allow = _half_ulp(raw) + tol * max(abs(got), 1e-300) + 1e-12
            if abs(got - want) > allow:
                drift.append((key, where, raw, want, got, src, allow))

        for key, where, raw, want, got, src, allow in drift:
            print(f"{where}: [{'ERROR' if sev == 'error' else 'warn'}] "
                  f"VALUE-DRIFT val:{key} — the survey prints {raw!r} "
                  f"({want:.6g}) but {src} recomputes {got:.6g} "
                  f"(allowed {allow:.3g})")
        for key, where, raw in unbacked:
            print(f"{where}: [warn] val:{key} = {raw!r} has no oracle behind it")

        unused = sorted(set(exports) - set(decls))
        n_ok = len(decls) - len(drift) - len(unbacked)
        print(f"[math-oracles] {t}: {len(exports)} oracle export(s), "
              f"{len(decls)} survey declaration(s), {n_ok} matched, "
              f"{len(drift)} drifted, {len(unbacked)} unbacked, "
              f"{len(unused)} export(s) not yet declared")
        if unused:
            print(f"[math-oracles]   undeclared exports: {', '.join(unused[:8])}"
                  f"{' …' if len(unused) > 8 else ''}")
        failures += len(drift)

    print(f"\n[math-oracles] {failures} value-drift(s), severity={sev}")
    return 1 if (failures and sev == "error") else 0


if __name__ == "__main__":
    sys.exit(main())
