"""Study-manifest reader/writer — the versioned iteration log with environment +
provenance pinning (P1-3), determinism (P0-1), and oracle checks (P0-5)."""
from __future__ import annotations

from pathlib import Path

from .utils import REPO_ROOT, environment, git_commit, save_json


def _path(study: str) -> Path:
    return REPO_ROOT / "artifacts" / study / "study-manifest.json"


def load(study: str) -> dict:
    p = _path(study)
    if p.is_file():
        import json
        return json.loads(p.read_text())
    return {"study": study, "iterations": []}


def ensure_env(m: dict) -> dict:
    m.setdefault("study", m.get("study", ""))
    m["environment"] = environment()
    m["git_commit"] = git_commit()
    m.setdefault("iterations", [])
    return m


def add_iteration(m: dict, phase: int, note: str, **extra) -> dict:
    m.setdefault("iterations", []).append({"phase": phase, "note": note, **extra})
    return m


def save(study: str, m: dict) -> None:
    save_json(_path(study), m)
