"""Shared helpers (RIS rule: shared helpers live in utils.py). Determinism, JSON I/O,
hashing, environment capture."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[2]


def set_determinism(seed: int = 0) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def tensor_hash(t: torch.Tensor) -> str:
    """Stable content hash of a tensor (for P0-1 determinism verification)."""
    arr = t.detach().to(torch.float64).cpu().numpy()
    arr = np.ascontiguousarray(np.round(arr, 6))
    return hashlib.sha256(arr.tobytes()).hexdigest()[:16]


def dict_hash(d: dict) -> str:
    payload = json.dumps({k: round(float(v), 6) for k, v in sorted(d.items())}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True, default=_default)


def save_npz(path: Path, **arrays) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **{k: np.asarray(v) for k, v in arrays.items()})


def _default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, torch.Tensor):
        return o.detach().cpu().tolist()
    raise TypeError(type(o))


def git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT,
                              capture_output=True, text=True).stdout.strip()
        return out.stdout.strip()[:12] + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def environment() -> dict:
    import scipy
    import transformers
    return {
        "os": platform.platform(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "git_commit": git_commit(),
    }
