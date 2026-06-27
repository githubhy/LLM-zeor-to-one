#!/usr/bin/env python3
"""Quality-gate validator for the reference-implementation-study skill.

Usage:
    python validate_gate.py <study-name> <gate> <topic>

Gates:
    G1  Phase 2 → 3  (Implementation → Baseline)
    G2  Phase 3 → 4  (Baseline → Sensitivity)
    G3  Phase 4 → 5  (Sensitivity → Precision)
    G4  Phase 5 → 6  (Precision → Report)
    REPORT  Report completeness — runs viewer/tools/check-report-completeness.py
            on the study report (the report-completeness gate).

Exit codes:
    0  PASS — all checks succeeded
    1  FAIL — one or more checks failed (details printed to stderr)
    2  Usage error
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # .claude/skills/<skill>/ → repo root


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check(ok: bool, msg: str, results: list[tuple[bool, str]]) -> None:
    results.append((ok, msg))


def _find_candidate_modules(study: str, topic: str) -> list[str]:
    """Return importable module names under implementation/<topic>/ (excluding utils)."""
    impl_dir = REPO_ROOT / "implementation" / topic
    if not impl_dir.is_dir():
        return []
    return [
        p.stem
        for p in impl_dir.glob("*.py")
        if p.stem not in ("__init__", "utils", "__pycache__")
    ]


def _json_loadable(path: Path) -> tuple[bool, dict | list | None]:
    try:
        with open(path) as f:
            data = json.load(f)
        return True, data
    except (json.JSONDecodeError, OSError):
        return False, None


def _npz_loadable(path: Path) -> bool:
    try:
        import numpy as np
        np.load(path, allow_pickle=False)
        return True
    except Exception:
        return False


def _resolve_topic(topic: str) -> str:
    """Return the topic form whose implementation/<form>/ exists (tolerate -/_)."""
    for cand in (topic, topic.replace("-", "_"), topic.replace("_", "-")):
        if (REPO_ROOT / "implementation" / cand).is_dir():
            return cand
    return topic


# ---------------------------------------------------------------------------
# Gate validators
# ---------------------------------------------------------------------------

def gate_g1(study: str, topic: str) -> list[tuple[bool, str]]:
    """G1: Implementation → Baseline."""
    results: list[tuple[bool, str]] = []
    topic = _resolve_topic(topic)              # tolerate slug (-) vs module dir (_)

    # Check implementation/<topic>/ exists
    impl_dir = REPO_ROOT / "implementation" / topic
    _check(impl_dir.is_dir(), f"implementation/{topic}/ directory exists", results)

    # Check utils.py exists
    _check(
        (impl_dir / "utils.py").is_file(),
        f"implementation/{topic}/utils.py exists",
        results,
    )

    # Check candidate modules are importable
    modules = _find_candidate_modules(study, topic)
    _check(len(modules) >= 2, f"At least 2 candidate modules found ({len(modules)})", results)

    sys.path.insert(0, str(REPO_ROOT))
    for mod_name in modules:
        try:
            importlib.import_module(f"implementation.{topic}.{mod_name}")
            _check(True, f"implementation.{topic}.{mod_name} importable", results)
        except Exception as exc:
            _check(False, f"implementation.{topic}.{mod_name} import failed: {exc}", results)
    sys.path.pop(0)

    # Check tests/<topic>/ exists
    tests_dir = REPO_ROOT / "tests" / topic
    _check(tests_dir.is_dir(), f"tests/{topic}/ directory exists", results)

    # Run pytest
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    _check(
        proc.returncode == 0,
        f"pytest tests/{topic}/ passes (rc={proc.returncode})",
        results,
    )
    if proc.returncode != 0:
        # Append abbreviated output for diagnostics
        for line in proc.stdout.splitlines()[-20:]:
            results.append((False, f"  pytest: {line}"))

    return results


def gate_g2(study: str) -> list[tuple[bool, str]]:
    """G2: Baseline → Sensitivity."""
    results: list[tuple[bool, str]] = []
    base = REPO_ROOT / "artifacts" / study / "baseline"

    # summary.json
    summary_path = base / "summary.json"
    ok, data = _json_loadable(summary_path)
    _check(ok, f"{summary_path.relative_to(REPO_ROOT)} is valid JSON", results)

    if ok and isinstance(data, dict):
        # Check metrics present
        methods = data.get("methods") or data.get("results") or {}
        _check(
            len(methods) >= 2,
            f"summary.json contains >= 2 methods ({len(methods)})",
            results,
        )
        # Check aggregated statistics present
        has_stats = any(
            "mean" in str(v) or "std" in str(v)
            for v in (methods.values() if isinstance(methods, dict) else methods)
        )
        _check(has_stats, "summary.json contains aggregated statistics (mean/std)", results)

    # .npz loadable
    npz_files = list(base.glob("*.npz"))
    _check(len(npz_files) >= 1, f"At least one .npz in baseline/ ({len(npz_files)})", results)
    for npz in npz_files:
        _check(
            _npz_loadable(npz),
            f"{npz.name} is loadable",
            results,
        )

    # manifest updated
    manifest_path = REPO_ROOT / "artifacts" / study / "study-manifest.json"
    mok, mdata = _json_loadable(manifest_path)
    _check(mok, "study-manifest.json exists and is valid JSON", results)
    if mok and isinstance(mdata, dict):
        iters = mdata.get("iterations", [])
        phase3 = [i for i in iters if i.get("phase") == 3]
        _check(len(phase3) >= 1, "study-manifest.json has Phase 3 entry", results)

    return results


def gate_g3(study: str) -> list[tuple[bool, str]]:
    """G3: Sensitivity → Precision."""
    results: list[tuple[bool, str]] = []
    art_dir = REPO_ROOT / "artifacts" / study

    # Look for sweep artifacts (any subdir that isn't baseline or precision)
    sweep_dirs = [
        d for d in art_dir.iterdir()
        if d.is_dir() and d.name not in ("baseline", "precision")
    ]
    _check(
        len(sweep_dirs) >= 1,
        f"At least one sweep artifact directory ({len(sweep_dirs)})",
        results,
    )

    for sd in sweep_dirs:
        jsons = list(sd.glob("*.json"))
        _check(
            len(jsons) >= 1,
            f"{sd.name}/ contains at least one .json summary",
            results,
        )

    # manifest updated
    manifest_path = art_dir / "study-manifest.json"
    mok, mdata = _json_loadable(manifest_path)
    _check(mok, "study-manifest.json exists and is valid JSON", results)
    if mok and isinstance(mdata, dict):
        iters = mdata.get("iterations", [])
        phase4 = [i for i in iters if i.get("phase") == 4]
        _check(len(phase4) >= 1, "study-manifest.json has Phase 4 entry", results)

    return results


def gate_g4(study: str) -> list[tuple[bool, str]]:
    """G4: Precision → Report."""
    results: list[tuple[bool, str]] = []
    prec_dir = REPO_ROOT / "artifacts" / study / "precision"

    _check(prec_dir.is_dir(), "artifacts/<study>/precision/ exists", results)

    if prec_dir.is_dir():
        npz_files = list(prec_dir.glob("*.npz"))
        _check(
            len(npz_files) >= 1,
            f"At least one .npz in precision/ ({len(npz_files)})",
            results,
        )
        for npz in npz_files:
            _check(_npz_loadable(npz), f"{npz.name} is loadable", results)

    # manifest updated
    manifest_path = REPO_ROOT / "artifacts" / study / "study-manifest.json"
    mok, mdata = _json_loadable(manifest_path)
    _check(mok, "study-manifest.json exists and is valid JSON", results)
    if mok and isinstance(mdata, dict):
        iters = mdata.get("iterations", [])
        phase5 = [i for i in iters if i.get("phase") == 5]
        _check(len(phase5) >= 1, "study-manifest.json has Phase 5 entry", results)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Flag-gated optional checks (proposed-mode items; ADDITIVE, default-off).
# Activated only via `--flags <ids>`; with no flags the gates are unchanged.
# ---------------------------------------------------------------------------

FLAG_GATE = {
    "P0-1": "G1", "P0-2": "G2", "P1-3": "G2", "P2-1": "G2", "P2-2": "G2", "P2-3": "G4",
    # v1.1 additions:
    "P0-4": "G2", "P0-5": "G1", "P1-4": "G2",
}


def _flag_checks(flag: str, study: str, topic: str) -> list[tuple[bool, str]]:
    results: list[tuple[bool, str]] = []
    base = REPO_ROOT / "artifacts" / study
    _, summary = _json_loadable(base / "baseline" / "summary.json")
    _, manifest = _json_loadable(base / "study-manifest.json")
    summary = summary if isinstance(summary, dict) else {}
    manifest = manifest if isinstance(manifest, dict) else {}
    methods = summary.get("methods") or summary.get("results") or {}

    if flag == "P0-1":  # determinism verified, not asserted
        det = manifest.get("determinism") or summary.get("determinism") or {}
        entries = list(det.values()) if isinstance(det, dict) else (det if isinstance(det, list) else [])
        ok = bool(entries) and all(
            isinstance(e, dict) and (
                e.get("hashes_match") is True
                or (isinstance(e.get("run_hashes"), list) and len(e["run_hashes"]) >= 2 and len(set(e["run_hashes"])) == 1)
            )
            for e in entries
        )
        _check(ok, "[P0-1] determinism verified: each candidate re-run twice, output hashes match ('determinism' in manifest/summary)", results)

    elif flag == "P0-2":  # pairwise paired-seed significance, not just per-candidate CIs
        pw = summary.get("pairwise") or summary.get("pairwise_comparisons")
        _check(bool(pw), "[P0-2] summary.json has a 'pairwise' comparison block", results)
        entries = (list(pw.values()) if isinstance(pw, dict) else pw) if pw else []
        ok = bool(entries) and all(
            isinstance(e, dict)
            and any(k in e for k in ("p_value", "pvalue", "p"))
            and any(k in e for k in ("effect_size", "effect", "cohens_d", "cliffs_delta"))
            for e in entries
        )
        _check(ok, "[P0-2] each pair reports a significance test (p-value) + effect size", results)
        _check(bool(summary.get("shared_seed_set") or summary.get("paired_seeds") or summary.get("seeds")),
               "[P0-2] a shared/paired seed set is recorded", results)

    elif flag == "P1-3":  # environment + provenance pinned
        env = manifest.get("environment")
        _check(isinstance(env, dict) and bool(env),
               "[P1-3] manifest records an 'environment' block (OS / Python / lib versions)", results)
        git = manifest.get("git_commit") or (env.get("git_commit") if isinstance(env, dict) else None)
        _check(bool(git), "[P1-3] manifest records a git commit hash", results)

    elif flag == "P2-1":  # uniform data+metric contract (shared metric key-set)
        keysets = []
        if isinstance(methods, dict):
            for v in methods.values():
                mk = v.get("metrics") if isinstance(v, dict) and isinstance(v.get("metrics"), dict) else (v if isinstance(v, dict) else {})
                keysets.append(frozenset(mk.keys()))
        ok = len(keysets) >= 2 and len(set(keysets)) == 1 and len(keysets[0]) > 0
        _check(ok, "[P2-1] all candidates report an identical metric key-set (shared data+metric contract)", results)

    elif flag == "P2-2":  # reproduce-from-artifacts validator + raw-output release
        repro = list(base.glob("reproduce*.py")) + list((REPO_ROOT / "implementation" / topic).glob("reproduce*.py"))
        _check(bool(repro), "[P2-2] a reproduce-from-artifacts script exists (reproduce*.py)", results)
        raw = list((base / "baseline").glob("*.npz"))
        _check(bool(raw), "[P2-2] per-trial raw outputs are released (.npz)", results)

    elif flag == "P2-3":  # reduced-precision DoE over >= 2 quantization structures
        prec: dict = {}
        for sub in ("precision", "phase5", "baseline"):
            o, d = _json_loadable(base / sub / "summary.json")
            if o and isinstance(d, dict) and (d.get("structures") or d.get("realisation_structures")):
                prec = d
                break
        structs = prec.get("structures") or prec.get("realisation_structures") or []
        _check(len(structs) >= 2, f"[P2-3] precision DoE covers >= 2 realisation structures ({len(structs)})", results)
        _check("saturation" in json.dumps(prec).lower(), "[P2-3] saturation flags recorded in the precision sweep", results)

    elif flag == "P0-5":  # correctness anchored to an external oracle (analytical|reference|metamorphic)
        oc = (manifest.get("oracle_checks") or manifest.get("oracle_check")
              or summary.get("oracle_checks") or summary.get("oracle_check"))
        if not oc:  # fallback: a standalone oracle artifact
            for f in list(base.glob("oracle*.json")) + list((REPO_ROOT / "implementation" / topic).glob("oracle*.json")):
                o, d = _json_loadable(f)
                if o:
                    oc = d
                    break
        if isinstance(oc, dict):
            entries = list(oc.values()) if (oc and all(isinstance(v, dict) for v in oc.values())) else [oc]
        elif isinstance(oc, list):
            entries = oc
        else:
            entries = []
        valid_types = {"analytical", "reference", "metamorphic"}
        ok = bool(entries) and all(
            isinstance(e, dict)
            and str(e.get("type", "")).lower() in valid_types
            and e.get("passed") is True
            for e in entries
        )
        _check(ok, "[P0-5] every candidate has a passing oracle_check (type in {analytical,reference,metamorphic})", results)

    elif flag == "P0-4":  # confidence-driven MC for rate metrics: error-event stopping + binomial CI
        binom = {"wilson", "clopper_pearson", "clopper-pearson", "cp"}
        rate_entries: list[dict] = []

        def _walk_rate(node: object) -> None:
            if isinstance(node, dict):
                if "ci_method" in node or "error_count" in node:
                    rate_entries.append(node)
                for v in node.values():
                    _walk_rate(v)
            elif isinstance(node, list):
                for v in node:
                    _walk_rate(v)

        _walk_rate(summary)
        _check(bool(rate_entries), "[P0-4] summary.json has >= 1 rate-metric entry (error_count/ci_method present)", results)
        ok = bool(rate_entries) and all(
            all(k in e for k in ("error_count", "total_trials", "stop_reason", "ci_method"))
            and str(e.get("ci_method", "")).lower() in binom
            for e in rate_entries
        )
        _check(ok, "[P0-4] each rate-metric entry carries error_count, total_trials, stop_reason, and a binomial ci_method", results)

    elif flag == "P1-4":  # measured complexity/runtime: warmup + distribution + op-count + scaling cross-check
        prof_entries: list[dict] = []

        def _walk_prof(node: object) -> None:
            if isinstance(node, dict):
                if "op_count" in node or "measured_scaling" in node or ("percentiles" in node and "repeats" in node):
                    prof_entries.append(node)
                for v in node.values():
                    _walk_prof(v)
            elif isinstance(node, list):
                for v in node:
                    _walk_prof(v)

        _walk_prof(summary)
        _check(bool(prof_entries), "[P1-4] summary.json has >= 1 cost-profiling entry (op_count/measured_scaling present)", results)
        ok = bool(prof_entries) and all(
            all(k in e for k in ("repeats", "percentiles", "op_count", "asymptotic_claim", "measured_scaling"))
            for e in prof_entries
        )
        _check(ok, "[P1-4] each cost-profiling entry carries repeats, percentiles, op_count, asymptotic_claim, measured_scaling", results)

    return results


def gate_report(study: str, topic: str) -> list[tuple[bool, str]]:
    """REPORT: completeness of the study report.

    Locates the study report under docs/ or reports/ (by topic in the filename) and
    runs viewer/tools/check-report-completeness.py on it.
    """
    results: list[tuple[bool, str]] = []
    candidates: list[Path] = []
    forms = {topic, topic.replace("_", "-"), topic.replace("-", "_")}
    for d in ("docs", "reports"):
        base = REPO_ROOT / d
        if base.is_dir():
            for form in forms:
                candidates += base.glob(f"*{form}*.md")
    candidates = sorted(set(candidates))
    candidates.sort(key=lambda p: (0 if "report" in p.name else 1, len(p.name)))
    _check(bool(candidates), f"study report found in docs/ or reports/ (topic={topic})", results)
    if not candidates:
        return results

    report = candidates[0]
    checker = REPO_ROOT / "viewer" / "tools" / "check-report-completeness.py"
    proc = subprocess.run([sys.executable, str(checker), str(report)],
                          capture_output=True, text=True)
    _check(proc.returncode == 0, f"report-completeness PASS ({report.name})", results)
    if proc.returncode != 0:
        for line in (proc.stdout + proc.stderr).strip().splitlines():
            if line.strip():
                results.append((False, f"  {line.strip()}"))
    return results


GATES = {
    "G1": gate_g1,
    "G2": gate_g2,
    "G3": gate_g3,
    "G4": gate_g4,
    "REPORT": gate_report,
}


def main() -> int:
    argv = sys.argv[1:]
    flags_csv = ""
    if "--flags" in argv:
        i = argv.index("--flags")
        flags_csv = argv[i + 1] if i + 1 < len(argv) else ""
        del argv[i:i + 2]

    if len(argv) < 2 or argv[1].upper() not in GATES:
        print(f"Usage: {sys.argv[0]} <study-name> <G1|G2|G3|G4|REPORT> [<topic>] [--flags <ids>]", file=sys.stderr)
        return 2

    study = argv[0]
    gate = argv[1].upper()
    topic = argv[2] if len(argv) > 2 else study
    active_flags = [f.strip().upper() for f in flags_csv.split(",") if f.strip()]

    gate_fn = GATES[gate]
    # G1 + REPORT use the topic (module / report-filename lookup); G2–G4 use study-namespaced paths
    if gate in ("G1", "REPORT"):
        results = gate_fn(study, topic)
    else:
        results = gate_fn(study)

    # Append flag-gated optional checks whose target gate is the current gate (additive).
    for fl in active_flags:
        if FLAG_GATE.get(fl) == gate:
            results += _flag_checks(fl, study, topic)

    passed = sum(1 for ok, _ in results if ok)
    failed = sum(1 for ok, _ in results if not ok)

    print(f"\n{'=' * 60}")
    print(f"  Gate {gate} — study: {study}")
    print(f"{'=' * 60}\n")

    for ok, msg in results:
        status = "PASS" if ok else "FAIL"
        marker = "  [+]" if ok else "  [-]"
        print(f"{marker} {status}: {msg}")

    print(f"\n{'=' * 60}")
    if failed == 0:
        print(f"  GATE {gate}: PASS  ({passed}/{passed} checks)")
        print(f"{'=' * 60}\n")
        return 0
    else:
        print(f"  GATE {gate}: FAIL  ({passed} passed, {failed} failed)")
        print(f"{'=' * 60}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
