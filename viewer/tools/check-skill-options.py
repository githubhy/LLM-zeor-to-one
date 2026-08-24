#!/usr/bin/env python3
"""Every `[opt:<ID>]` site marker in a LIVE rule or skill resolves to a registry entry.

`CLAUDE.md` makes `.claude/skill-options.json` the mechanism for skill/rule options: *"an agent
following an annotated skill/rule reads the registry and, if an option is `off`, skips the marked
block and reverts to its documented `off_behavior`."* That only works if the two halves agree, and
nothing checked that they do -- 53 options across 30-odd files, maintained entirely by hand.

They had already drifted. `[opt:MATH-REDERIVE-GATE]` sat in `.claude/rules/workflow.md` from the
gate's landing with no registry entry, so the documented way to flip it had nothing to flip, and no
`off_behavior` was recorded anywhere
(`bugs/2026-08-23-a-site-marker-with-no-registry-entry-cannot-be-toggled`).

SCOPE IS THE WHOLE DESIGN HERE. Repo-wide the invariant is FALSE and should be: of the five
unregistered markers measured on 2026-08-23, exactly one was a defect. The others were a literal
`[opt:<ID>]` in a proposal documenting the SYNTAX, a `[opt:SP-...]` fragment in prose, an option a
proposal was proposing under a name it did not land under, and one a `todos/` has not built yet.
A `proposals/`, `todos/`, `bugs/` or `field-notes/` file talking about an option is not a live
annotation -- so this gate reads only files an agent actually FOLLOWS: `.claude/**/*.md` and
`CLAUDE.md`. A gate that reported four false positives out of five would be read by nobody, which
is the lesson of `decisions/2026-08-23-phrasing-gate-goes-to-error-at-a-zero-backlog`.

The reverse direction (a registry entry with no marker anywhere) is checked repo-WIDE, because
there the wide scope is the forgiving one: an entry is dead config only if nothing mentions it at
all.

Exit: 0 OK, 1 drift, 2 REFUSE (nothing inspected).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / ".claude/skill-options.json"
MARKER = re.compile(r"\[opt:([A-Za-z0-9_-]+)")
# A literal placeholder documenting the marker syntax, not a use of an option called "ID".
PLACEHOLDERS = {"ID"}


def live_files() -> list[Path]:
    out = [p for p in sorted((ROOT / ".claude").rglob("*.md")) if p.is_file()]
    c = ROOT / "CLAUDE.md"
    if c.is_file():
        out.append(c)
    return out


def tracked_text_files() -> list[Path]:
    r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "*.md", "*.json"],
                       capture_output=True, text=True, timeout=60)
    return [ROOT / f for f in r.stdout.split() if (ROOT / f).is_file()]


def markers_in(paths: list[Path]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for p in paths:
        if p.resolve() == REGISTRY.resolve():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in sorted(set(MARKER.findall(text))):
            if m in PLACEHOLDERS or m.endswith("-"):
                continue
            found.setdefault(m, []).append(str(p.relative_to(ROOT)))
    return found


def main() -> int:
    if not REGISTRY.is_file():
        print(f"[skill-options] REFUSING: {REGISTRY} not found — a green result here would "
              f"mean 'did not look'.", file=sys.stderr)
        return 2
    try:
        opts = json.loads(REGISTRY.read_text(encoding="utf-8"))["options"]
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
        print(f"[skill-options] REFUSING: registry unreadable ({e})", file=sys.stderr)
        return 2

    live = live_files()
    if not live:
        print("[skill-options] REFUSING: no rule/skill files to inspect.", file=sys.stderr)
        return 2

    live_markers = markers_in(live)
    wide_markers = markers_in(tracked_text_files())
    if not live_markers:
        print("[skill-options] REFUSING: 0 site markers found across "
              f"{len(live)} rule/skill file(s) — the marker syntax has probably changed.",
              file=sys.stderr)
        return 2

    problems = 0
    for m in sorted(set(live_markers) - set(opts)):
        problems += 1
        print(f"[skill-options] UNREGISTERED {m}\n"
              f"            marked in {', '.join(live_markers[m])} but absent from "
              f"{REGISTRY.relative_to(ROOT)} — so the toggle CLAUDE.md documents has nothing to "
              f"flip, and no off_behavior is recorded.", file=sys.stderr)
    for k in sorted(set(opts) - set(wide_markers)):
        problems += 1
        print(f"[skill-options] UNMARKED {k}\n"
              f"            registered but carries no [opt:{k}] site marker anywhere in the "
              f"repo — an option nothing points at cannot be applied or skipped.", file=sys.stderr)

    print(f"[skill-options] scope: {len(live)} rule/skill file(s), {len(live_markers)} distinct "
          f"site marker(s), {len(opts)} registry option(s)")
    if problems:
        print(f"[skill-options] {problems} drift(s)", file=sys.stderr)
        return 1
    print("[skill-options] OK — every site marker resolves, every option is pointed at")
    return 0


if __name__ == "__main__":
    sys.exit(main())
