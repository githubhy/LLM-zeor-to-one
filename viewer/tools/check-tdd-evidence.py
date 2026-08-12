#!/usr/bin/env python3
"""Mechanical TDD hard gate — promotes "test-first" from an evidence-only convention to a
gate that proves each guard test can actually FAIL.

TDD's core claim is "if you didn't watch the test fail, you don't know it tests the right
thing." A point-in-time checker can't see authoring order, but it CAN prove the test
*discriminates*: a registry maps each new case/fix to a guard test + a deterministic
`break` (a source substitution that reverts the fix). `prove` applies the break, runs the
guard test, and requires it to go RED; then restores the source and requires GREEN. A
break that leaves the test passing means the test does not catch its own bug — that FAILS
the gate. (Same discipline as method-eval's ME-RED-ORACLE, applied to unit tests.)

Registry (JSON list), e.g. tests/nr_pdsch_demod/tdd-evidence.json:
    [{"id": "case-A-repetition",
      "test": "tests/nr_pdsch_demod/test_cases_ae.py::test_case_a_requires_repetition",
      "break": {"file": "implementation/linear_receiver_irc/utils.py",
                "find": "np.add.at(received, cb.tx_by_rv[rv], e_des)",
                "replace": "received[cb.tx_by_rv[rv]] = e_des"}}]

Usage:
    python viewer/tools/check-tdd-evidence.py REGISTRY.json            # --check (cheap)
    python viewer/tools/check-tdd-evidence.py REGISTRY.json --prove    # run the RED proof

Exit codes: 0 PASS, 1 FAIL, 2 usage.
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

REQUIRED = ("id", "test", "break")
BREAK_REQUIRED = ("file", "find", "replace")

# Crash-safety sentinel. `prove()` mutates real source files; a `finally:` restore guarantees NOTHING
# against SIGKILL / process teardown, and the original bytes would otherwise live only in the dead
# process's memory — leaving the tree silently broken with no marker (bug 2026-07-13-06, which disabled
# slot aggregation in the working tree after a killed --full gate). So the original bytes are persisted
# to disk BEFORE the break, and any surviving sentinel is healed at startup.
INFLIGHT = Path(".claude") / "tdd-prove-inflight.json"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write_inflight(fpath: Path, original: bytes, broken: bytes) -> None:
    INFLIGHT.parent.mkdir(parents=True, exist_ok=True)
    INFLIGHT.write_text(json.dumps({
        "file": str(fpath),
        "original_b64": base64.b64encode(original).decode("ascii"),
        "broken_sha256": _sha(broken),
    }), encoding="utf-8")


def _clear_inflight() -> None:
    try:
        INFLIGHT.unlink()
    except FileNotFoundError:
        pass


def heal_inflight() -> bool:
    """Restore a source file left BROKEN by a killed prove() run. Returns True if it healed something.

    Safety: only heals when the on-disk content still byte-matches the break we applied. If a human (or
    another tool) edited the file since the crash, we refuse and tell them to restore from git rather
    than silently clobbering their work."""
    if not INFLIGHT.is_file():
        return False
    try:
        rec = json.loads(INFLIGHT.read_text(encoding="utf-8"))
        fpath = Path(rec["file"])
        original = base64.b64decode(rec["original_b64"])
        current = fpath.read_bytes()
    except (OSError, ValueError, KeyError) as e:
        print(f"  [!] unreadable in-flight sentinel {INFLIGHT} ({e}) — remove it manually", file=sys.stderr)
        return False
    if _sha(current) == _sha(original):
        _clear_inflight()                              # already restored; stale sentinel
        return False
    if _sha(current) != rec.get("broken_sha256"):
        print(f"  [!] {fpath} was left BROKEN by a killed --prove, but its content has changed since.\n"
              f"      REFUSING to auto-heal (would clobber an edit). Restore it from git:\n"
              f"          git checkout -- {fpath}", file=sys.stderr)
        return False
    fpath.write_bytes(original)
    _clear_inflight()
    print(f"  [healed] restored {fpath} — a previous --prove run was killed with its break applied "
          f"(bug 2026-07-13-06)", file=sys.stderr)
    return True


def _invalidate_bytecode(fpath: Path) -> None:
    """Delete the source file's cached bytecode so the next subprocess re-compiles from the
    CURRENT source. Without this, a stale __pycache__/*.pyc can mask a same-size source break:
    Python validates a .pyc by (source mtime, size), and a break that preserves the byte length
    (e.g. `num_heads=8` -> `num_heads=4`) leaves the size unchanged, so under coarse-resolution
    mtime (Windows) the interpreter can reuse bytecode compiled from the UNBROKEN source — the
    guard then reads unbroken behavior and reports RED=False (non-discriminating) though the fix
    is sound. Bug 2026-07-13-03."""
    try:
        pyc = Path(importlib.util.cache_from_source(str(fpath)))
    except (ValueError, NotImplementedError):
        return
    try:
        pyc.unlink()
    except (FileNotFoundError, OSError):
        pass


def load_registry(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate(entries, root: Path):
    """Cheap structural validation — no pytest run."""
    problems = []
    root = Path(root)
    if not isinstance(entries, list) or not entries:
        return ["registry is empty or not a list"]
    for e in entries:
        tag = e.get("id", "<no-id>")
        for f in REQUIRED:
            if f not in e:
                problems.append(f"[{tag}] missing required field: {f}")
        brk = e.get("break")
        if not isinstance(brk, dict):
            continue
        for f in BREAK_REQUIRED:
            if f not in brk:
                problems.append(f"[{tag}] break missing field: {f}")
        if all(f in brk for f in BREAK_REQUIRED):
            bf = root / brk["file"]
            if not bf.is_file():
                problems.append(f"[{tag}] break file not found: {brk['file']}")
            elif brk["find"] not in bf.read_text(encoding="utf-8"):
                problems.append(f"[{tag}] break `find` not present in {brk['file']}: {brk['find']!r}")
    return problems


def _run_test(test_nodeid: str, root: Path) -> int:
    # PYTHONDONTWRITEBYTECODE: the guard test subprocess must not write a .pyc that a LATER guard
    # (or the restored green run) could then reuse across a same-size source flip. Combined with
    # _invalidate_bytecode() this makes the RED proof deterministic on coarse-mtime filesystems
    # (bug 2026-07-13-03).
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", test_nodeid, "-q", "--no-header",
         "-p", "no:cacheprovider", "-o", "addopts="],
        cwd=str(root), env=env, capture_output=True,
        text=True, encoding="utf-8", errors="replace")  # parent-side UTF-8 decode (bug 2026-07-12-04)
    return r.returncode


def prove(entry, root: Path):
    """Apply the break, require the guard test to go RED, restore, require GREEN.
    Returns (ok, detail). File is always restored (finally) and the restore is verified."""
    root = Path(root)
    brk = entry["break"]
    fpath = root / brk["file"]
    # Byte-exact backup/restore — NEVER text mode: newline=None translates LF->CRLF on write
    # (Windows), silently corrupting line endings on restore. The find/replace operates on the
    # decoded text but single-line find strings preserve every newline byte.
    original = fpath.read_bytes()
    broken = original.decode("utf-8").replace(brk["find"], brk["replace"], 1).encode("utf-8")
    if broken == original:
        return False, {"red": False, "green": None,
                       "error": f"break made no change (find not applied): {brk['find']!r}"}
    red = green = None
    try:
        _write_inflight(fpath, original, broken)           # crash-safety: survive a SIGKILL mid-prove
        fpath.write_bytes(broken)
        _invalidate_bytecode(fpath)                        # force recompile from the broken source
        red = _run_test(entry["test"], root) != 0        # non-zero exit = test failed = RED
    finally:
        fpath.write_bytes(original)
        _invalidate_bytecode(fpath)                        # force recompile from the restored source
        if fpath.read_bytes() != original:                 # loud on a failed restore
            raise RuntimeError(f"FAILED TO RESTORE {fpath} — restore manually from git!")
        _clear_inflight()                                  # restored cleanly -> sentinel no longer needed
    if red:
        green = _run_test(entry["test"], root) == 0       # zero exit after restore = GREEN
    ok = bool(red) and bool(green)
    detail = {"red": bool(red), "green": (None if green is None else bool(green))}
    if not red:
        detail["error"] = "guard test stayed GREEN under its break — it does not discriminate"
    elif not green:
        detail["error"] = "guard test did not return GREEN after restore"
    return ok, detail


def main() -> int:
    heal_inflight()          # repair a previously-killed --prove BEFORE doing anything else
    argv = sys.argv[1:]
    do_prove = "--prove" in argv
    argv = [a for a in argv if a not in ("--prove", "--check")]
    if len(argv) != 1:
        print("Usage: check-tdd-evidence.py REGISTRY.json [--prove]", file=sys.stderr)
        return 2
    reg_path = Path(argv[0])
    if not reg_path.is_file():
        print(f"ERROR: not a file: {reg_path}", file=sys.stderr)
        return 2
    root = Path.cwd()
    entries = load_registry(reg_path)

    problems = validate(entries, root)
    for p in problems:
        print(f"  [-] {p}")
    if problems:
        print(f"tdd-evidence: FAIL (registry invalid, {len(problems)} problem(s))", file=sys.stderr)
        return 1

    if not do_prove:
        print(f"tdd-evidence: PASS (registry valid, {len(entries)} guard(s)) — run with --prove for the RED proof")
        return 0

    fails = 0
    for e in entries:
        ok, detail = prove(e, root)
        mark = "PASS" if ok else "FAIL"
        extra = "" if ok else f" — {detail.get('error', detail)}"
        print(f"  [{mark}] {e['id']}: RED={detail['red']} GREEN={detail['green']}{extra}")
        fails += 0 if ok else 1
    if fails:
        print(f"tdd-evidence: FAIL ({fails}/{len(entries)} guards non-discriminating)", file=sys.stderr)
        return 1
    print(f"tdd-evidence: PASS ({len(entries)} guards proven RED-capable then GREEN)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
