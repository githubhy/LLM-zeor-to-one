#!/usr/bin/env python3
"""Verification orchestrator.

Single entry point for all verification invocations. Reads a manifest of
checks and dispatches the existing 8 viewer/tools/ scripts per --tier=
flag. Tier policy hardcoded in TIER_POLICY.

See docs/superpowers/specs/2026-05-23-verification-tier-redesign.md.

Usage:
  python viewer/tools/verify.py --tier=per-edit FILE
  python viewer/tools/verify.py --tier=per-turn
  python viewer/tools/verify.py --tier=per-commit
  python viewer/tools/verify.py --tier=pre-push
  python viewer/tools/verify.py --tier=ci
  python viewer/tools/verify.py --tier=on-demand PATH
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "viewer" / "tools"
SURVEYS_DIR = REPO_ROOT / "surveys"
STATE_DIR = REPO_ROOT / ".claude" / "state"
STATE_FILE_AGE_MAX_SECONDS = 24 * 60 * 60


class Mode(Enum):
    CHECK = "check"
    FIX = "fix"


TIERS = {"per-edit", "per-turn", "per-commit", "pre-push", "ci", "on-demand"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tier", required=True, choices=sorted(TIERS),
        help="Verification tier to run."
    )
    parser.add_argument("paths", nargs="*",
                        help="File or directory paths (required for per-edit and on-demand).")
    parser.add_argument("--verbose", action="store_true",
                        help="Show output from every script invocation, not just failures.")
    args = parser.parse_args()
    # Dispatch logic added in Task 1.3 onward
    sys.exit(0)


if __name__ == "__main__":
    main()
