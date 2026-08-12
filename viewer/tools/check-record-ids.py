#!/usr/bin/env python3
"""Record-ID collision gate.

Scans bugs/, decisions/, todos/ for the failure modes in
todos/2026-07-10-duplicate-record-ids:

  1. Two files sharing one record id — the audit trail's pointer becomes ambiguous.
  2. An INDEX.md row whose id has no file, or a record file with no row.
  3. A fully-qualified `bugs/<id>` / `decisions/<id>` reference that resolves
     to more than one file (a collision the ref inherits).
  4. Frontmatter `id:` that disagrees with the filename.

TWO ID FORMS are accepted for bugs/ and decisions/:

  * `YYYY-MM-DD-<slug>`     — the CURRENT scheme (as todos/ and field-notes/ already
    use). Collision-free without coordination: two sessions would have to pick the
    same descriptive slug for different records on the same day.
  * `YYYY-MM-DD-NN-<slug>`  — LEGACY, grandfathered. `NN` was a per-day sequence that
    nothing allocated, so concurrent branches collided on it repeatedly
    (2026-07-04, -07-10, -07-11 x25, -07-16). No new `NN` records are minted.
    See proposals/record-id-collision-structural-fix.md.

Disambiguation is legacy-first: a name whose post-date segment is exactly two digits
is read as legacy `NN`. Therefore a NEW slug must not begin with a two-digit segment
(`2026-07-16-02-foo` is legacy id `2026-07-16-02`, not slug `02-foo`); check_slug_form()
enforces this.

Exit non-zero on any violation. Shorthand refs (`bugs/-NN`, no date) are
inherently un-resolvable and reported as an advisory count, not an error.
"""
import argparse
import re
import pathlib
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ID_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}-\d{2})-.+\.md$")          # LEGACY: DATE-NN-slug
SLUG_ID_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}-(?!\d{2}(?!\d))[^.]+)\.md$")  # NEW: DATE-slug
TODO_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$")            # todos: date+slug
FM_ID_RE = re.compile(r"^id:\s*(\S+)\s*$", re.M)
INDEX_ROW_RE = re.compile(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*([^|]+?)\s*\|")
# fully-qualified inbound refs (date present); shorthand (bugs/-NN) counted separately
QUAL_REF_RE = re.compile(r"\b(bugs|decisions)/(\d{4}-\d{2}-\d{2}-\d{2})(?!\d)")   # legacy
# new-form refs: post-date segment is NOT a bare NN, so legacy refs are never re-read here
SLUG_REF_RE = re.compile(
    r"\b(bugs|decisions)/(\d{4}-\d{2}-\d{2}-(?!\d{2}(?!\d))[a-z0-9][a-z0-9-]*)")
SHORT_REF_RE = re.compile(r"\b(bugs|decisions)/-\d{2}\b")


def record_id(name):
    """Record id from a bugs/ or decisions/ filename: legacy DATE-NN, else DATE-slug."""
    if (m := ID_RE.match(name)):
        return m.group(1)
    if (m := SLUG_ID_RE.match(name)):
        return m.group(1)
    return None


def scan_area(area, id_from_name):
    """Return {id: [files]} and per-file frontmatter-id, for one area dir."""
    by_id = defaultdict(list)
    fm = {}
    d = ROOT / area
    if not d.is_dir():
        return by_id, fm
    for f in sorted(d.glob("*.md")):
        if f.name == "INDEX.md":
            continue
        rid = id_from_name(f.name)
        if rid is None:
            continue
        by_id[rid].append(f.name)
        m = FM_ID_RE.search(f.read_text(encoding="utf-8"))
        fm[f.name] = m.group(1) if m else None
    return by_id, fm


def index_ids(area):
    p = ROOT / area / "INDEX.md"
    if not p.exists():
        return []
    return [m.group(1).strip() for line in p.read_text(encoding="utf-8").splitlines()
            if (m := INDEX_ROW_RE.match(line))]


#: `todos/INDEX.md` keys on `date | slug` (two columns), not on a single id, so the id-keyed
#: `index_ids` cannot read it.
INDEX_TODO_ROW_RE = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|")


def index_todo_keys():
    p = ROOT / "todos" / "INDEX.md"
    if not p.exists():
        return []
    return [f"{m.group(1)}-{m.group(2)}" for line in p.read_text(encoding="utf-8").splitlines()
            if (m := INDEX_TODO_ROW_RE.match(line))]


# Generated / vendored trees that are NOT part of the record corpus. A record ref
# inside one is not an authored citation, so gating on it is a false positive --
# and these dirs are gitignored, so their contents vary per machine and per run.
# Playwright's `test-results/**/error-context.md` was the concrete case: it copies
# the *source comment* of a failing test (bug IDs included) into a generated file,
# so simply RUNNING the viewer suite made this gate fail the push.
_SCAN_EXCLUDE = {".git", "node_modules", "test-results", "playwright-report",
                 "dist", "__pycache__", ".venv", ".viewer-highlights"}


def _scan_files():
    """Authored `*.md` under the repo, preferring git's tracked set.

    Tracked-only is the correct semantic -- a record ID lives in an authored,
    committed document -- and it inherits .gitignore for free. Falls back to a
    filtered rglob outside a git checkout (or if git is unavailable).
    """
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "*.md"],
                             capture_output=True, check=True).stdout
        names = [n for n in out.decode("utf-8", "replace").split("\0") if n]
        if names:
            return [ROOT / n for n in names
                    if not (set(pathlib.Path(n).parts) & _SCAN_EXCLUDE)]
    except (OSError, subprocess.CalledProcessError):
        pass
    return [f for f in ROOT.rglob("*.md")
            if not (set(f.parts) & _SCAN_EXCLUDE)]

def main():
    global ROOT
    # [opt:UTF8-WRITE] This gate prints an em-dash. On Windows stdout/stderr default to the
    # locale code page (GBK), which mangles it to '??' on the console and makes a utf-8
    # capture lose the stream entirely. Same defect and same fix as bugs/2026-07-14-05.
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):        # not a reconfigurable stream
            pass
    ap = argparse.ArgumentParser(description="Record-ID collision gate.")
    ap.add_argument("--root", type=Path, help="repo root to scan (default: this repo)")
    args = ap.parse_args()
    if args.root:
        ROOT = args.root.resolve()
    errors, advisories = [], []

    # -- bugs / decisions: id-keyed (legacy DATE-NN or new DATE-slug) --
    for area in ("bugs", "decisions"):
        by_id, fm = scan_area(area, record_id)
        for rid, files in by_id.items():
            if len(files) > 1:
                errors.append(f"{area}: id {rid} claimed by {len(files)} files: {files}")
        for name, fid in fm.items():
            fname_id = record_id(name)
            if fid is not None and fid != fname_id:
                errors.append(f"{area}/{name}: frontmatter id '{fid}' != filename id '{fname_id}'")
        # INDEX <-> file consistency
        file_ids = set(by_id)
        idx = index_ids(area)
        idx_set = set(idx)
        for rid in sorted(file_ids - idx_set):
            errors.append(f"{area}: file id {rid} has no INDEX.md row")
        for rid in sorted(idx_set - file_ids):
            errors.append(f"{area}: INDEX.md row {rid} has no file")
        for rid in [x for x in idx if idx.count(x) > 1]:
            errors.append(f"{area}: INDEX.md has duplicate row for {rid}")

    # -- todos: date+slug-keyed --
    by_key, _ = scan_area("todos", lambda n: (f"{m.group(1)}|{m.group(2)}"
                                               if (m := TODO_RE.match(n)) else None))
    for key, files in by_key.items():
        if len(files) > 1:
            errors.append(f"todos: date+slug {key} claimed by {len(files)} files: {files}")

    # INDEX <-> file consistency for todos. This ran for bugs/ and decisions/ only, and the gap was
    # invisible BY CONSTRUCTION: a todo missing from the index is exactly the thing an index-grep
    # cannot find, so the only signal was this gate -- which was not looking.
    # Measured 2026-08-07: two files (`2026-08-03-4rx-rank2-rank3-arms`,
    # `2026-08-01-reproduce-block-executability-gate`) had no row, one of them after a re-index was
    # lost to a container rollback and "verified" against this gate's OK.
    # `.claude/rules/deferred-tracking.md` makes `todos/INDEX.md` the durable cross-session record;
    # an unindexed todo is tracked in prose, which the whole convention exists to prevent.
    #
    # ADVISORY for now, not blocking, per the repo's own gate-rollout convention (off -> warn ->
    # error; same path `.claude/bare-refs-severity` and `.claude/crosslink-severity` took). Turning
    # it on measured a backlog of 34 -- 26 files with no row, 6 rows with no file, 2 duplicates --
    # and blocking on a backlog the gate itself just revealed would stop unrelated work. Clear it,
    # then flip these three appends to `errors`. Tracked: todos/2026-08-07-todos-index-drift.
    todo_files = {k.replace("|", "-") for k in by_key}
    todo_idx = index_todo_keys()
    todo_drift = []
    for key in sorted(todo_files - set(todo_idx)):
        todo_drift.append(f"todos: file {key} has no INDEX.md row — invisible to an index grep")
    for key in sorted(set(todo_idx) - todo_files):
        todo_drift.append(f"todos: INDEX.md row {key} has no file")
    for key in sorted({x for x in todo_idx if todo_idx.count(x) > 1}):
        todo_drift.append(f"todos: INDEX.md has duplicate row for {key}")
    if todo_drift:
        advisories.append(f"todos/INDEX.md drift: {len(todo_drift)} (advisory — "
                          f"todos/2026-08-07-todos-index-drift). First 3: "
                          + "; ".join(x.split(": ", 1)[1] for x in todo_drift[:3]))

    # -- inbound reference resolution (whole repo) --
    existing = {}
    for area in ("bugs", "decisions"):
        for f in (ROOT / area).glob("*.md"):
            if (rid := record_id(f.name)):
                existing.setdefault(f"{area}/{rid}", []).append(f.name)
    short_count = slug_unresolved = 0
    for f in _scan_files():
        try:
            t = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        # LEGACY `DATE-NN` refs are hard-gated: NN was allocator-free, so an id really can
        # be claimed by two files and a ref really can inherit that ambiguity.
        for m in QUAL_REF_RE.finditer(t):
            key = f"{m.group(1)}/{m.group(2)}"
            hits = existing.get(key, [])
            if len(hits) == 0:
                errors.append(f"{f.relative_to(ROOT)}: ref '{key}' resolves to no file")
            elif len(hits) > 1:
                errors.append(f"{f.relative_to(ROOT)}: ref '{key}' resolves to {len(hits)} files")
        # NEW `DATE-slug` refs are advisory only, for two reasons:
        #   1. The ambiguity this gate exists to catch is STRUCTURALLY IMPOSSIBLE here — the
        #      id IS the filename stem, and one directory cannot hold two files of one name.
        #      The filesystem enforces uniqueness; no gate is needed to.
        #   2. The pattern cannot separate a deliberate ref from prose that merely looks like
        #      one (e.g. "closed by [bugs/2026-04-24-fixed]"), so erroring would force prose
        #      to contort — the same false positive reworded away on 2026-07-11.
        # Unresolved ones are counted and surfaced, never gated (as with shorthand refs).
        for m in SLUG_REF_RE.finditer(t):
            if f"{m.group(1)}/{m.group(2)}" not in existing:
                slug_unresolved += 1
        short_count += len(SHORT_REF_RE.findall(t))

    if short_count or slug_unresolved:
        print(f"[record-ids] advisory: {short_count} dateless shorthand ref(s) (bugs/-NN) + "
              f"{slug_unresolved} unresolved slug-form ref(s) — un-resolvable or prose-shaped, "
              f"not gated", file=sys.stderr)
    # `advisories` was collected and never printed. A finding nobody sees is the same as one nobody
    # collected -- and this gate is the only place a missing todos/INDEX.md row can surface, because
    # the absence is precisely what an index grep cannot find.
    for a in advisories:
        print(f"[record-ids] advisory: {a}", file=sys.stderr)
    if errors:
        print(f"[record-ids] {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    ok = "OK — no id/slug collisions, refs resolve"
    ok += "; bugs/ + decisions/ INDEX consistent" + (
        ", todos/ has advisory drift (see above)" if advisories else ", todos/ INDEX consistent")
    print(f"[record-ids] {ok}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
