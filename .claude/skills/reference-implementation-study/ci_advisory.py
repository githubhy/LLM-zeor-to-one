#!/usr/bin/env python3
"""Advisory (warn-only by default) scan of the G0 derivation-soundness gate across all studies.

Wired into .githooks/pre-push. Severity from ``.claude/ris-derivation-severity``
(``off | warn | error``, default ``warn``) — mirrors ``.claude/bare-refs-severity``
and ``.claude/crosslink-severity``:

  off    -> print nothing, exit 0
  warn   -> print a ⚠️ line per failing study, ALWAYS exit 0 (never blocks a push)
  error  -> print a ❌ line per failing study, exit 1 if any study fails

Only studies that ALREADY carry a ``derivation_ledger`` are scanned. A study with no
ledger is skipped silently — this gate does not retroactively demand ledgers on legacy
studies (that back-port is tracked in todos/2026-07-04-ris-g0-backport-completed-studies.md).
So the scan is non-breaking: it enforces consistency only where a ledger was opted into.

Run directly to check status:
    python .claude/skills/reference-implementation-study/ci_advisory.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
REPO_ROOT = _SKILL_DIR.parents[2]  # .claude/skills/<skill>/ -> repo root

# Load the gate validator as a module (same pattern as test_validate_gate_g0.py).
_spec = importlib.util.spec_from_file_location("ris_validate_gate", _SKILL_DIR / "validate_gate.py")
vg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vg)


# read_text() without encoding= resolves to the locale codepage (cp936/GBK on this
# clone), so a UTF-8 manifest raises UnicodeDecodeError — which is a ValueError, not a
# JSONDecodeError, and so escapes the handlers below. Pin UTF-8 and widen the guard.
_DEGRADE = (OSError, UnicodeDecodeError, json.JSONDecodeError)


def _read_severity() -> str:
    try:
        val = (REPO_ROOT / ".claude" / "ris-derivation-severity").read_text(
            encoding="utf-8").strip().lower()
    except _DEGRADE:
        return "warn"
    return val if val in ("off", "warn", "error") else "warn"


def _has_ledger(study_dir: Path) -> bool:
    """True iff the study already carries a derivation ledger (manifest block or sidecar)."""
    manifest = study_dir / "study-manifest.json"
    try:
        if manifest.is_file():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("derivation_ledger"):
                return True
    except _DEGRADE:
        pass
    for sidecar in study_dir.glob("derivation*ledger*.json"):
        try:
            if json.loads(sidecar.read_text(encoding="utf-8")):
                return True
        except _DEGRADE:
            continue
    return False


def _topic_for(study_dir: Path, study: str) -> str:
    try:
        data = json.loads((study_dir / "study-manifest.json").read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("topic"):
            return str(data["topic"])
    except _DEGRADE:
        pass
    return study


def main() -> int:
    severity = _read_severity()
    if severity == "off":
        return 0

    art = REPO_ROOT / "artifacts"
    if not art.is_dir():
        return 0

    studies = sorted(d for d in art.iterdir() if d.is_dir() and _has_ledger(d))
    if not studies:
        return 0  # no opted-in studies yet — quiet, non-breaking

    any_fail = False
    for sd in studies:
        study = sd.name
        results = vg.gate_g0(study, _topic_for(sd, study))
        fails = [msg for ok, msg in results if not ok]
        if fails:
            any_fail = True
            mark = "❌" if severity == "error" else "⚠️ "
            print(f"{mark} [G0-advisory] study '{study}': {len(fails)} derivation-ledger issue(s):",
                  file=sys.stderr)
            for m in fails:
                print(f"      - {m}", file=sys.stderr)

    if not any_fail:
        return 0
    if severity == "error":
        print("[G0-advisory] BLOCKED at severity=error. Fix the ledger(s), or set "
              ".claude/ris-derivation-severity to 'warn'.", file=sys.stderr)
        return 1
    print("[G0-advisory] advisory only (severity=warn) — not blocking the push.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
