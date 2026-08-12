#!/usr/bin/env python3
"""Plan-execution anti-drift gate — makes multi-wave program drift unable to LAND undetected.

A long, multi-subset program (e.g. the 38.101-4 PDSCH-demod expansion) drifts when a
subset is called "done" without its gates, a wave closes with a family or its TDD mirror
missing, work starts past a planned pause, or a gate config is silently weakened. This
driver reads a machine-readable *program manifest* (the scope oracle) and fails ONLY on a
contradiction between the manifest and reality — never on honest incompleteness, so an
in-progress program is the normal PASS state and blocking at pre-push is safe.

The guarantee is "re-derive, don't trust": a subset's done-ness is established by
re-running its gates NOW (report-completeness / signoff / eqnmap fast; tdd --prove +
pytest under --full), not by trusting the status string. This is the multi-subset
generalization of `validate_gate.py` + the re-derivation principle of the signoff gate.

Contradictions checked (all cheap except the --full gate re-runs):
  1. claimed-done-but-red — a `status: done` subset whose gates do not pass
  2. complete-but-missing — a `status: complete` wave missing a planned family × duplex
  3. pause-violation      — a subset started in a wave > pause_after_wave with no go_no_go token
  4. ordering-on-complete — a wave marked complete while an earlier wave is not
  5. config-erosion       — a gate-config file drifted from `gate_config_fingerprint`
  6. min-tdd-guards       — the tdd-evidence registry dropped below `min_tdd_guards`
  7. wave-branch-drift    — in-flight commits mix >1 wave, or a wave's commits sit on a branch
                            that is not that wave's dedicated one (opt-in via `branch_policy`;
                            a commit's wave is read from its `wave<N>(...)` subject tag)

Scope (answers "does it gate other campaigns?"): a single manifest gates only ITS OWN
program. `--all` checks every manifest listed in `.claude/program-manifests` (opt-in, one
path per line, `#` comments — mirrors `.claude/crosslink-scope`); a campaign with no
registered manifest is never touched, and each registered campaign fails only on its own
contradictions.

Usage:
    python viewer/tools/check-plan-progress.py MANIFEST.json [--full] [--check]
    python viewer/tools/check-plan-progress.py --all [--full]      # every registered manifest

Exit codes: 0 PASS, 1 FAIL (a contradiction), 2 usage.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REGISTRY = ".claude/program-manifests"

# A commit's owning wave is read from its subject tag. The repo uses two forms
# interchangeably — the canonical `wave<N>(...)` / `wave<N>: ...` and the shorthand
# `W<N>.<subset>` (e.g. `W4.1`, `W5.1`) that names a subset directly. BOTH must be
# recognized: on 2026-07-25 a whole wave (W5.1 RAN5) went unregulated because its
# commits used only the `W5.1 ...` shorthand, which the old `^wave(\d+)`-only regex
# never matched, so `waves_present` came back empty and the drift check silently
# skipped. Patterns are overridable per manifest via `branch_policy.wave_tag_patterns`;
# each must expose the wave number as capture group 1.
DEFAULT_WAVE_TAG_PATTERNS = [r"^wave(\d+)\b", r"^W(\d+)\.\d+\b"]


def _wave_patterns(pol):
    """Compiled wave-tag patterns for this manifest (config override or the defaults)."""
    return [re.compile(p) for p in (pol.get("wave_tag_patterns") or DEFAULT_WAVE_TAG_PATTERNS)]


def _wave_of(subject, patterns):
    """The wave number a commit subject declares, or None if it carries no wave tag."""
    s = subject.strip()
    for pat in patterns:
        m = pat.match(s)
        if m:
            return int(m.group(1))
    return None

# gate-name -> (tool relative path, builds argv from (report, spec), fast?)
_FAST_GATES = {
    "report_completeness": ("viewer/tools/check-report-completeness.py", False),
    "signoff":             ("viewer/tools/check-signoff-checklist.py", False),
    "eqnmap":              ("viewer/tools/check-eqn-function-map.py", False),
}
_SLOW_GATES = {
    "tdd":    ("viewer/tools/check-tdd-evidence.py", True),
    "pytest": (None, True),
}


def load_manifest(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _pause_unlocked(manifest) -> bool:
    token = manifest.get("go_no_go")
    if isinstance(token, dict):
        return any(bool(v) for v in token.values())
    return bool(token)


def _run(argv, root):
    # Decode the child's output as UTF-8 on the PARENT side. text=True alone decodes with the
    # parent's locale codec (GBK on Windows), which throws on the checkers' non-ASCII output even
    # though PYTHONIOENCODING makes the *child* write UTF-8 (bug 2026-07-12-04).
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(argv, cwd=str(root), env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    tail = (r.stderr or r.stdout or "").strip().splitlines()
    return r.returncode == 0, (tail[-1] if tail else "")


def _default_gate_runner(subset, root, full):
    """Re-run a done subset's declared gates as subprocesses; return [(gate, ok, detail)]."""
    root = Path(root)
    report = subset.get("report")
    spec = subset.get("gates", {})
    results = []
    for gate, cfg in spec.items():
        if gate in _FAST_GATES:
            tool, _ = _FAST_GATES[gate]
            argv = [sys.executable, tool, report]
            if gate == "eqnmap" and isinstance(cfg, dict) and "min" in cfg:
                argv += ["--min", str(cfg["min"])]
            ok, detail = _run(argv, root)
            results.append((gate, ok, detail))
        elif gate in _SLOW_GATES and full:
            if gate == "tdd":
                reg = cfg.get("registry") if isinstance(cfg, dict) else cfg
                ok, detail = _run([sys.executable, _SLOW_GATES["tdd"][0], reg, "--prove"], root)
            else:  # pytest
                paths = cfg if isinstance(cfg, list) else [cfg]
                ok, detail = _run([sys.executable, "-m", "pytest", *paths, "-q",
                                   "-p", "no:cacheprovider", "-o", "addopts="], root)
            results.append((gate, ok, detail))
        # slow gates without --full are simply not evaluated (fast mode)
    return results


def _git(args, root):
    """Run a git command; return stripped stdout, or None on any failure (never raise)."""
    try:
        r = subprocess.run(["git", *args], cwd=str(root), capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _git_branch_ctx(root, main_ref):
    """(current_branch, [in-flight commit subjects], [in-flight changed files]) or None.

    In-flight = commits on HEAD not yet in the base (origin/<main> if present, else <main>).
    The changed-files list feeds the manifest ground-truth cross-check (a wave-N report
    touched in-flight but carrying no wave-N tag). Defensive by construction: any missing
    ref or git error yields None (skip, never block). Consumers must tolerate a 2-tuple
    too — the hermetic test doubles inject `(cur, subjects)`.
    """
    cur = _git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    if not cur or cur == "HEAD":              # not a repo, or detached HEAD
        return None
    base = f"origin/{main_ref}"
    if _git(["rev-parse", "--verify", "--quiet", base], root) is None:
        base = main_ref
        if _git(["rev-parse", "--verify", "--quiet", base], root) is None:
            return (cur, [], [])             # no base to diff against -> no in-flight info
    log = _git(["log", "--format=%s", f"{base}..HEAD"], root)
    diff = _git(["diff", "--name-only", f"{base}..HEAD"], root)
    subjects = [ln for ln in log.splitlines() if ln.strip()] if log is not None else []
    changed = [ln for ln in diff.splitlines() if ln.strip()] if diff is not None else []
    return (cur, subjects, changed)


def _expected_branch(manifest, pol, wave_num):
    """The dedicated branch for a wave: per-wave `branch` override, else the policy pattern."""
    for w in manifest.get("waves", []):
        if w.get("wave") == wave_num and w.get("branch"):
            return w["branch"]
    pattern = pol.get("pattern")
    return pattern.format(wave=wave_num) if pattern else None


def _report_wave_map(manifest):
    """{report_path -> wave} for reports owned by exactly one wave (the manifest's
    ground truth). A report shared across two DIFFERENT waves is ambiguous and excluded
    (never a basis to flag)."""
    owner, ambiguous = {}, set()
    for w in manifest.get("waves", []):
        wn = w.get("wave")
        for s in w.get("subsets", []):
            rep = s.get("report")
            if not rep:
                continue
            if rep in owner and owner[rep] != wn:
                ambiguous.add(rep)
            owner.setdefault(rep, wn)
    return {rep: wn for rep, wn in owner.items() if rep not in ambiguous}


def _untagged_wave_problems(manifest, pol, waves_present, changed_files):
    """Manifest ground-truth cross-check (the regulator that does not trust tag format).

    A commit that changes a wave-N report but whose wave never surfaces in the tag-derived
    `waves_present` is wave work the drift check would otherwise miss — whether the tag was
    absent or in a form no pattern recognized. Severity via `branch_policy.untagged_wave_severity`
    (`off` | `warn` | `error`, default `warn`): `error` returns blocking problems, `warn` prints
    an advisory and blocks nothing, `off` disables the cross-check. Returns the blocking list.
    """
    sev = (pol.get("untagged_wave_severity") or "warn").lower()
    if sev == "off" or not changed_files:
        return []
    report_wave = _report_wave_map(manifest)
    present = set(waves_present)
    untagged = {}
    for f in changed_files:
        wn = report_wave.get(f)
        if wn is not None and wn not in present:
            untagged.setdefault(wn, set()).add(f)
    blocking = []
    for wn in sorted(untagged):
        reps = ", ".join(sorted(untagged[wn]))
        msg = (f"[branch policy] wave-{wn} artifact(s) changed in-flight ({reps}) but no "
               f"in-flight commit carries a wave-{wn} tag — tag them 'wave{wn}(...)' or "
               f"'W{wn}.<subset>' so wave-branch-drift regulation applies")
        if sev == "error":
            blocking.append(msg)
        else:
            print(f"⚠️  [branch-policy-advisory] {msg}", file=sys.stderr)
    return blocking


def _branch_policy_problems(manifest, root, branch_ctx):
    """Contradiction 7: each wave must land on its own branch.

    Opt-in per manifest (`branch_policy.enabled`). The wave a commit belongs to is read from
    its subject tag (`wave<N>(...)` or the `W<N>.<subset>` shorthand; patterns configurable via
    `branch_policy.wave_tag_patterns`). Two tag-derived failure modes: a branch mixing >1 wave's
    in-flight commits, or a single wave's commits on a branch that is not that wave's dedicated
    one. Because tags are author-written and easy to miss, a manifest ground-truth cross-check
    (`_untagged_wave_problems`) also runs — it flags a wave-N report changed in-flight with no
    wave-N tag, and CRUCIALLY runs even when `waves_present` is empty, which is the exact hole
    that let the untagged W5.1 wave escape on 2026-07-25.
    """
    pol = manifest.get("branch_policy") or {}
    if not pol.get("enabled"):
        return []
    ctx = branch_ctx(root, pol.get("main", "main"))
    if ctx is None:                          # git unavailable -> never block
        return []
    cur, subjects, *rest = ctx               # tolerate 2-tuple (hermetic test doubles)
    changed_files = rest[0] if rest else []
    patterns = _wave_patterns(pol)
    waves_present = sorted({w for s in subjects if (w := _wave_of(s, patterns)) is not None})
    main_ref = pol.get("main", "main")

    problems = _untagged_wave_problems(manifest, pol, waves_present, changed_files)

    if len(waves_present) > 1:
        problems.append(f"[branch policy] '{cur}' mixes commits from waves {waves_present} ahead "
                        f"of '{main_ref}' — each wave must land on its own branch (split the later "
                        f"wave(s) onto their own branch)")
    elif len(waves_present) == 1:
        n = waves_present[0]
        expected = _expected_branch(manifest, pol, n)
        if expected and cur != expected:
            problems.append(f"[branch policy] '{cur}' carries wave-{n} commits but wave {n}'s "
                            f"dedicated branch is '{expected}' — put wave-{n} work on its own branch")
    return problems


def check_program(manifest, root, gate_runner=None, full=False, branch_ctx=None):
    """Return a list of contradiction strings; empty == PASS (in-progress is PASS)."""
    gate_runner = gate_runner or _default_gate_runner
    branch_ctx = branch_ctx if branch_ctx is not None else _git_branch_ctx
    root = Path(root)
    problems: list[str] = []
    waves = manifest.get("waves", [])
    pause = manifest.get("pause_after_wave")
    unlocked = _pause_unlocked(manifest)

    complete_nums = {w.get("wave") for w in waves if w.get("status") == "complete"}

    for w in waves:
        wnum = w.get("wave")
        wstatus = w.get("status", "planned")
        subsets = w.get("subsets", [])

        # 1. claimed-done-but-red
        for s in subsets:
            if s.get("status") == "done":
                for gate, ok, detail in gate_runner(s, root, full):
                    if not ok:
                        problems.append(
                            f"[{s.get('id')}] claimed done but gate {gate!r} FAILED: {detail}")

        # 3. pause-violation — any started subset in a post-pause wave needs the token
        if pause is not None and isinstance(wnum, (int, float)) and wnum > pause and not unlocked:
            if any(s.get("status") in ("done", "in-progress") for s in subsets):
                problems.append(
                    f"[wave {wnum}] work started past pause_after_wave={pause} but go_no_go "
                    f"token is not set — the pause gate is not unlocked")

        if wstatus == "complete":
            # 2. complete-but-missing-coverage
            done = {(s.get("family"), s.get("duplex")) for s in subsets if s.get("status") == "done"}
            for fam in w.get("families", []):
                fid = fam.get("family")
                for dup in fam.get("duplex", []):
                    if (fid, dup) not in done:
                        problems.append(
                            f"[wave {wnum}] marked complete but family {fid} {dup} has no done "
                            f"subset — missing coverage (the {dup} mirror?)")
            # 4. ordering-on-complete
            for other in waves:
                onum = other.get("wave")
                if (isinstance(onum, (int, float)) and isinstance(wnum, (int, float))
                        and onum < wnum and onum not in complete_nums):
                    problems.append(
                        f"[wave {wnum}] marked complete but earlier wave {onum} is not complete "
                        f"— out-of-order completion")

    # 5. config-erosion fingerprint
    for path, expected in (manifest.get("gate_config_fingerprint") or {}).items():
        f = root / path
        if not f.is_file():
            problems.append(f"gate config missing: {path} (fingerprint expects {expected!r})")
            continue
        actual = f.read_text(encoding="utf-8").strip()
        if actual != str(expected):
            problems.append(
                f"gate config {path} = {actual!r} but manifest fingerprint expects {expected!r} "
                f"— erosion/drift? re-confirm intentionally, then update the fingerprint")

    # 6. min-tdd-guards floor
    mtg = manifest.get("min_tdd_guards")
    if mtg is not None:
        reg = manifest.get("tdd_registry")
        try:
            n = len(json.loads((root / reg).read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError) as e:
            problems.append(f"tdd_registry unreadable ({reg}): {e}")
        else:
            if n < mtg:
                problems.append(
                    f"tdd-evidence registry has {n} guards < floor {mtg} — a guard was removed?")

    # 7. wave-branch-drift — each wave lands on its own branch (opt-in per manifest)
    problems.extend(_branch_policy_problems(manifest, root, branch_ctx))

    return problems


def _check_one(path: Path, full: bool) -> int:
    manifest = load_manifest(path)
    problems = check_program(manifest, Path.cwd(), full=full)
    if problems:
        for p in problems:
            print(f"  [-] {p}")
        print(f"plan-progress: FAIL ({len(problems)} contradiction(s)) -- {path.name}", file=sys.stderr)
        return 1
    n_done = sum(1 for w in manifest.get("waves", []) for s in w.get("subsets", [])
                 if s.get("status") == "done")
    mode = "full" if full else "fast"
    print(f"plan-progress: PASS ({mode}; {n_done} done subset(s), no contradictions) -- {path.name}")
    return 0


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--check"]
    full = "--full" in argv
    argv = [a for a in argv if a != "--full"]

    if "--all" in argv:
        reg = Path.cwd() / REGISTRY
        if not reg.is_file():
            print(f"plan-progress: no registry ({REGISTRY}) — nothing to check")
            return 0
        paths = [ln.strip() for ln in reg.read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.strip().startswith("#")]
        rc = 0
        for pstr in paths:
            p = Path.cwd() / pstr
            if not p.is_file():
                print(f"  [-] registered manifest not found: {pstr}")
                rc = 1
                continue
            rc |= _check_one(p, full)
        return rc

    if len(argv) != 1:
        print("Usage: check-plan-progress.py MANIFEST.json [--full] | --all [--full]", file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.is_file():
        print(f"ERROR: not a file: {path}", file=sys.stderr)
        return 2
    return _check_one(path, full)


if __name__ == "__main__":
    sys.exit(main())
