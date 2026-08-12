#!/usr/bin/env python3
"""The [opt:MATH-REDERIVE] gate: a changed numbered derivation needs review evidence.

`.claude/rules/workflow.md` requires that every new or materially-changed numbered
derivation get one independent re-derivation before it lands. The rule was adopted
on 2026-07-29 and violated by the commits that immediately followed its adoption,
in the same session, by the author who adopted it -- 32 corrections including
several entirely new derivations, none independently re-derived, two merged to
`main`. That is the third instance of one pattern: a correct rule, loaded, with no
trigger at the moment it applies. This is the trigger.

WHAT COUNTS AS A CHANGED DERIVATION
    An added or modified line containing `\\tag{` inside a `$$` display block. That
    is the mechanical definition, and it is deliberately narrow: it does not fire on
    prose, on marker/anchor churn, or on a renumber pass that only rewrites the
    integer inside an existing `\\tag{}` (those are filtered -- see `_tag_body`).

ADDED VERSUS MODIFIED -- THE DISTINCTION THAT MAKES THIS WORK
    The two cases have different evidence requirements, and collapsing them is what
    made the first version of this gate pass the very range it was written to fail.

    A MODIFIED equation is usually a correction applied in response to a review. Its
    evidence may legitimately PREDATE the fix -- indeed it normally does, because the
    review is what produced the fix. Demanding a further review before a fix can land
    would deadlock: every fix needs a review, whose findings need a fix, forever.

    A NEW equation cannot have been reviewed by anything that predates it. There is
    no tension here and no deadlock: a brand-new derivation needs evidence committed
    at or after the commit that introduced it.

    An equation is NEW when its `<!-- eq:ID -->` marker is absent from the file at the
    range's base. That is exact, and it is why the marker discipline of
    `.claude/rules/math-authoring.md` is load-bearing for this gate and not only for
    cross-references.

WHAT COUNTS AS EVIDENCE
    Either of:

    (a) A review artifact matching `_scratch/review*.md` under the survey directory,
        resolved AS OF the range's head, whose most recent commit is not older than
          * for a MODIFIED equation: the commit that last touched the file before the
            range -- i.e. the review could see the version being changed;
          * for a NEW equation: the commit inside the range that introduced it.

    (b) A `Reviewed-by: <path>` trailer in any commit message in the range, naming a
        file that exists. This is the escape for evidence that lives where the glob
        does not reach, and it is deliberately an explicit, attributable act.

    The gate deliberately does NOT check that the review is any good, or that it
    covers the specific equation. It checks that a review capable of seeing the
    change exists. A gate that tried to judge coverage would be a reviewer, and
    reviewing is the agent's job -- detection is the gate's.

CONFIG
    .claude/math-rederive-severity   off | warn | error      (default: warn)
    .claude/math-rederive-strict     one survey path per line, held at error
                                     regardless of the global severity

USAGE
    check-derivation-review.py --range <base>..<head>
    check-derivation-review.py --range HEAD~5..HEAD --severity error
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SEVERITY_FILE = REPO / ".claude" / "math-rederive-severity"
STRICT_FILE = REPO / ".claude" / "math-rederive-strict"

TAG_RE = re.compile(r"\\tag\{")
# a line that is ONLY a tag-number change is a renumber, not a derivation change
TAG_NUM_RE = re.compile(r"\\tag\{\d+\}")
REVIEW_GLOB = "_scratch/review*.md"
REVIEWED_BY_RE = re.compile(r"^\s*Reviewed-by:\s*(\S+)\s*$", re.M | re.I)


def _git(*args: str) -> str:
    # `text=True` alone decodes git's stdout with the LOCALE codec (gbk on a zh
    # Windows box). A diff or log carrying a curly quote then raises
    # UnicodeDecodeError inside subprocess.run's reader thread, .stdout comes
    # back None, and the caller's .splitlines() dies with an AttributeError that
    # names neither the file nor the real cause. Pin utf-8 and never fail on a
    # stray byte. Same genus as normalize-survey.py::run and
    # check-plan-progress.py::_run (bugs/2026-07-09-12, bug 2026-07-12-04).
    return subprocess.run(
        ["git", *args], cwd=str(REPO), capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False
    ).stdout or ""


def severity(cli: str | None) -> str:
    if cli:
        return cli
    if SEVERITY_FILE.exists():
        for line in SEVERITY_FILE.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line in ("off", "warn", "error"):
                return line
    return "warn"


def strict_paths() -> list[str]:
    if not STRICT_FILE.exists():
        return []
    out = []
    for line in STRICT_FILE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line.rstrip("/"))
    return out


def _tag_body(line: str) -> str:
    """The line with its tag NUMBER blanked, so a renumber is not a change."""
    return TAG_NUM_RE.sub(r"\\tag{}", line.strip())


EQ_MARKER_RE = re.compile(r"<!--\s*eq:([^\s>]+?)\s*-->")


def new_equation_ids(rng: str) -> dict[str, set[str]]:
    """{file -> {eq IDs whose marker is absent at the range base}}.

    These are brand-new derivations. Nothing committed before them can be their
    review, so they carry the stricter evidence requirement.
    """
    base, _, head = rng.partition("..")
    base = base or "HEAD~1"
    head = head or "HEAD"
    out: dict[str, set[str]] = {}
    files = _git("diff", "--name-only", rng, "--", "*.md").split()
    for path in files:
        after = set(EQ_MARKER_RE.findall(_git("show", f"{head}:{path}")))
        before = set(EQ_MARKER_RE.findall(_git("show", f"{base}:{path}")))
        fresh = after - before
        if fresh:
            out[path] = fresh
    return out


def changed_equations(rng: str) -> dict[str, list[str]]:
    """{file -> [changed equation lines]} for lines carrying \\tag{ in the range.

    A line whose only difference is the integer inside \\tag{} is excluded: that is
    `renumber-equations.py` doing its job, not a derivation changing.
    """
    diff = _git("diff", "--unified=0", rng, "--", "*.md")
    out: dict[str, list[str]] = {}
    cur: str | None = None
    added: list[str] = []
    removed: list[str] = []

    def flush() -> None:
        if cur is None:
            return
        removed_bodies = {_tag_body(r) for r in removed}
        real = [a for a in added if TAG_RE.search(a) and _tag_body(a) not in removed_bodies]
        if real:
            out.setdefault(cur, []).extend(real)

    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            flush()
            cur, added, removed = line[6:], [], []
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
    flush()
    return out


def survey_of(path: str) -> str | None:
    """The survey directory owning a file, or None if it is not in one."""
    p = Path(path)
    parts = p.parts
    if len(parts) >= 2 and parts[0] == "surveys":
        # multi-file survey: surveys/<name>/file.md ; flat: surveys/file.md
        return f"surveys/{parts[1]}" if len(parts) >= 3 else "surveys"
    return None


def _commit_time(rev: str, path: str | None = None) -> int:
    args = ["log", "-1", "--format=%ct", rev]
    if path:
        args += ["--", path]
    out = _git(*args).strip()
    return int(out) if out.isdigit() else 0


def newest_review(survey: str, head: str) -> tuple[str | None, int]:
    """The survey's newest review artifact AS OF `head`, and its commit time.

    Resolving against `head` rather than the working tree is load-bearing: an
    artifact written *after* the range cannot be evidence for it, and a
    working-tree glob would happily accept one. That was the first version of
    this function and it made the gate pass the very range it was written to
    fail.
    """
    best, best_t = None, 0
    listing = _git("ls-tree", "-r", "--name-only", head, "--", f"{survey}/_scratch/")
    for rel in listing.splitlines():
        rel = rel.strip()
        if not rel or not Path(rel).match(f"{survey}/{REVIEW_GLOB}"):
            continue
        t = _commit_time(head, rel)
        if t > best_t:
            best, best_t = rel, t
    # an UNCOMMITTED artifact in the working tree counts only when the range ends
    # at HEAD, i.e. we are gating a push of work in progress
    if head in ("HEAD", _git("rev-parse", "HEAD").strip()[:len(head)]):
        for f in sorted((REPO / survey).glob(REVIEW_GLOB)):
            rel = str(f.relative_to(REPO))
            if _commit_time("HEAD", rel) == 0:
                t = int(f.stat().st_mtime)
                if t > best_t:
                    best, best_t = rel + " (uncommitted)", t
    return best, best_t


def reviewed_by_trailers(rng: str) -> list[str]:
    bodies = _git("log", "--format=%B", rng)
    return [m for m in REVIEWED_BY_RE.findall(bodies) if (REPO / m).exists()]


def main() -> int:
    ap = argparse.ArgumentParser(description="[opt:MATH-REDERIVE] gate.")
    ap.add_argument("--range", required=True, help="git range, e.g. base..head")
    ap.add_argument("--severity", choices=["off", "warn", "error"])
    args = ap.parse_args()

    sev = severity(args.severity)
    if sev == "off":
        print("[derivation-review] off")
        return 0

    changed = changed_equations(args.range)
    if not changed:
        print("[derivation-review] OK — no numbered derivation changed in "
              f"{args.range}")
        return 0

    trailers = reviewed_by_trailers(args.range)
    fresh_ids = new_equation_ids(args.range)
    strict = strict_paths()
    findings: list[tuple[str, str]] = []   # (survey, message)
    by_survey: dict[str, list[tuple[str, list[str]]]] = {}
    for path, lines in changed.items():
        s = survey_of(path)
        if s is None:
            continue
        by_survey.setdefault(s, []).append((path, lines))

    for s, files in sorted(by_survey.items()):
        n_eq = sum(len(l) for _, l in files)
        if trailers:
            print(f"[derivation-review] {s}: {n_eq} changed derivation(s) — "
                  f"evidence via Reviewed-by: {', '.join(trailers)}")
            continue
        base, _, head = args.range.partition("..")
        base, head = base or "HEAD~1", head or "HEAD"
        artifact, art_t = newest_review(s, head)

        # MODIFIED equations: the review may predate the fix, so compare against the
        # file's last commit BEFORE the range.
        prev_t = max(_commit_time(base, p) for p, _ in files)
        # NEW equations: compare against the commit that introduced them, inside the
        # range. Nothing earlier can be their review.
        new_here = {p: sorted(fresh_ids[p]) for p, _ in files if p in fresh_ids}
        need_t, need_why = prev_t, "the version being changed"
        for p in new_here:
            t_add = _commit_time(head, p)
            if t_add > need_t:
                need_t = t_add
                need_why = (f"the NEW derivation(s) {', '.join(new_here[p][:3])}"
                            f"{' …' if len(new_here[p]) > 3 else ''} in {p}")

        if artifact is None:
            findings.append((s, f"no review artifact under {s}/_scratch/review*.md"))
        elif art_t < need_t:
            findings.append((s, f"newest review {artifact} predates {need_why} "
                                f"(review {art_t} < required {need_t})"))
        else:
            print(f"[derivation-review] {s}: {n_eq} changed derivation(s) — "
                  f"evidence {artifact}")

    if not findings:
        print(f"[derivation-review] OK — every changed derivation in {args.range} "
              "has review evidence")
        return 0

    for s, msg in findings:
        blocking = sev == "error" or any(s.startswith(sp) for sp in strict)
        tag = "ERROR" if blocking else "warn"
        eqs = sum(len(l) for _, l in by_survey[s])
        print(f"{s}: [{tag}] {eqs} changed numbered derivation(s) with no review "
              f"evidence — {msg}")
        for path, lines in by_survey[s]:
            for l in lines[:4]:
                print(f"    {path}: {l.strip()[:100]}")
            if len(lines) > 4:
                print(f"    {path}: … and {len(lines) - 4} more")

    blocking = [s for s, _ in findings
                if sev == "error" or any(s.startswith(sp) for sp in strict)]
    print(f"\n[derivation-review] {len(findings)} survey(s) with unreviewed "
          f"derivations, severity={sev}, {len(blocking)} blocking")
    if blocking:
        print("[derivation-review] Run an independent re-derivation and commit its "
              "output under the survey's _scratch/, or add a "
              "'Reviewed-by: <path>' trailer naming the artifact.")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
