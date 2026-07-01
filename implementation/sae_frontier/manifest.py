"""Study manifest: the versioned iteration log with the P1-3 environment/provenance block.

A stored config + seed is only reproducible if the environment that produced it is
pinned too — so every phase entry carries the OS, Python, library versions, and the git
commit hash (+ dirty flag).
"""
from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STUDY = "sae-frontier"
ARTIFACTS = REPO / "artifacts" / STUDY
MANIFEST = ARTIFACTS / "study-manifest.json"


def _git(*args) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()
    except Exception:
        return "unknown"


def env_block() -> dict:
    def ver(mod):
        try:
            return __import__(mod).__version__
        except Exception:
            return "absent"
    return {
        "os": platform.platform(),
        "python": platform.python_version(),
        "numpy": ver("numpy"),
        "torch": ver("torch"),
        "transformers": ver("transformers"),
        "datasets": ver("datasets"),
        "git_commit": _git("rev-parse", "--short", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
    }


def load() -> dict:
    if MANIFEST.is_file():
        return json.loads(MANIFEST.read_text())
    return {"study": STUDY, "iterations": []}


def append_phase(phase: int, name: str, record: dict) -> dict:
    """Append an iteration entry. `phase` is the integer phase number (the RIS gate
    validator matches on `phase == N`); `name` is the human-readable label."""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    m = load()
    m["iterations"].append({"phase": phase, "name": name, "environment": env_block(), **record})
    MANIFEST.write_text(json.dumps(m, indent=2))
    return m
