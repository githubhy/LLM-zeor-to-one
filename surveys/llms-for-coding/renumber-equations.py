#!/usr/bin/env python3
"""Thin wrapper — delegates to viewer/tools/renumber-equations.py."""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MASTER = HERE.parent.parent / 'viewer' / 'tools' / 'renumber-equations.py'

if not MASTER.exists():
    print(f'Master script not found: {MASTER}', file=sys.stderr)
    sys.exit(1)

args = []
for arg in sys.argv[1:]:
    if not arg.startswith('-'):
        p = Path(arg)
        if not p.is_absolute() and not p.exists():
            resolved = HERE / p
            if resolved.exists():
                arg = str(resolved)
    args.append(arg)

sys.exit(subprocess.call([sys.executable, str(MASTER)] + args))
