"""Tests for verify.py orchestrator.

Covers: manifest dispatch, tier-mode selection, applicability filtering,
per-session state file lifecycle, exit code semantics.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / "viewer" / "tools" / "verify.py"


def run_verify(args, stdin=None, env=None):
    """Invoke verify.py and return (rc, stdout, stderr)."""
    cmd = [sys.executable, str(VERIFY), *args]
    r = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8",
        input=stdin, env=env, timeout=60
    )
    return r.returncode, r.stdout, r.stderr


def test_verify_script_exists_and_runs(tmp_path):
    """Sanity: verify.py is invokable with --help."""
    rc, out, err = run_verify(["--help"])
    assert rc == 0
    assert "--tier" in (out + err).lower()


def test_unknown_tier_errors(tmp_path):
    """An unknown --tier value rejects with non-zero exit."""
    rc, out, err = run_verify(["--tier=bogus"])
    assert rc != 0
