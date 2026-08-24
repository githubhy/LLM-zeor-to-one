#!/usr/bin/env python3
"""Pre-registration commit-order verifier — UNIVERSAL, not campaign-specific.

A pre-registration is only worth anything if it PRECEDES the result. Otherwise the
threshold quietly becomes whatever the data cleared, and the "hypothesis" is a
post-hoc rationalisation wearing a lab coat.

Git is a tamper-evident clock, so that claim is mechanically checkable:

  1. `pre-registration.md` must be committed STRICTLY BEFORE the first result
     artifact.  Same-commit is a FAILURE (see below).
  2. Its hypotheses/threshold block must not be silently edited once results
     exist.  An amendment is allowed, but only as a visible `## Amendment`
     section — never a quiet rewrite of the table.
  3. Every hypothesis must carry a numeric threshold AND a falsifier.  A
     pre-registration you cannot fail is not a pre-registration.

WHY SAME-COMMIT IS A FAILURE
    If the pre-registration and the result land in one commit, their order is
    unverifiable — which is precisely how the discipline gets bypassed, whether
    by intent or by a tidy `git add -A`.  Refusing it costs an author one extra
    commit and closes the only hole in the mechanism.

THIS IS A LIBRARY, NOT A GATE.  Consumers:
  - viewer/tools/check-campaign-tasks.py      campaigns/<slug>/tasks/<TID>/
  - viewer/tools/check-report-completeness.py sim reports claiming pre-registered
                                              hypotheses (sim-report-completeness
                                              Section 1 promises this and has never
                                              enforced the "pre-")
  - method-eval (fixed viability rubric), asic-synthesis-cost-study
    ("pre-registered CONFIRM/REFUTE window" — likewise promised, never enforced)

Ref: plans/2026-07-12-channel-calibration-completion.md, sections 2.7-2.9.
"""
from __future__ import annotations

import re
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# --- frontmatter / body parsing ------------------------------------------------

FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
HYP_HEADING_RE = re.compile(r"^##\s+Hypotheses\b.*$", re.M)
AMENDMENT_RE = re.compile(r"^##\s+Amendment\b", re.M)
NEXT_H2_RE = re.compile(r"^##\s+", re.M)

REQUIRED_FM = ("campaign", "task", "tier", "registered", "status")
# A hypothesis row is a markdown table row; we require a threshold and a falsifier
# column to be non-empty. Header names are matched case-insensitively by substring
# so "falsifier" / "falsifies" / "what would refute it" all count.
THRESHOLD_KEYS = ("threshold",)
FALSIFIER_KEYS = ("falsifier", "falsif", "refute")


@dataclass
class Finding:
    level: str  # "error" | "warn" | "info" | "refuse" | "refuse"
    code: str
    path: str
    message: str


@dataclass
class Prereg:
    path: Path
    frontmatter: dict = field(default_factory=dict)
    hypotheses: list[dict] = field(default_factory=list)
    has_amendment: bool = False
    raw: str = ""


def _yaml_lite(block: str) -> dict:
    """Minimal frontmatter parser (key: value, and `key: [a, b]` lists).

    Deliberately not a YAML dependency — the repo's other tools parse frontmatter
    with regex too, and the schema here is flat.
    """
    out: dict = {}
    for line in block.splitlines():
        line = line.split("#", 1)[0].rstrip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            items = [x.strip().strip("'\"") for x in v[1:-1].split(",")]
            out[k] = [x for x in items if x]
        else:
            out[k] = v.strip("'\"")
    return out


def _hypotheses_block(text: str) -> str:
    """The text between the `## Hypotheses` heading and the next H2 (or EOF)."""
    m = HYP_HEADING_RE.search(text)
    if not m:
        return ""
    start = m.end()
    nxt = NEXT_H2_RE.search(text, start)
    return text[start : nxt.start() if nxt else len(text)]


def _parse_table(block: str) -> list[dict]:
    """Parse the first markdown table in `block` into a list of {col: cell} dicts."""
    rows = [ln.strip() for ln in block.splitlines() if ln.strip().startswith("|")]
    if len(rows) < 2:
        return []

    def cells(r: str) -> list[str]:
        return [c.strip() for c in r.strip().strip("|").split("|")]

    header = [h.lower() for h in cells(rows[0])]
    out = []
    for r in rows[1:]:
        c = cells(r)
        # skip the |---|---| separator
        if all(set(x) <= set("-: ") for x in c):
            continue
        if len(c) != len(header):
            continue
        out.append(dict(zip(header, c)))
    return out


def _col(row: dict, keys: tuple[str, ...]) -> str | None:
    for name, val in row.items():
        if any(k in name for k in keys):
            return val
    return None


def parse(path: Path) -> Prereg:
    text = path.read_text(encoding="utf-8")
    p = Prereg(path=path, raw=text)
    m = FM_RE.match(text)
    if m:
        p.frontmatter = _yaml_lite(m.group(1))
    p.hypotheses = _parse_table(_hypotheses_block(text))
    p.has_amendment = bool(AMENDMENT_RE.search(text))
    return p


def validate_content(p: Prereg) -> list[Finding]:
    """Schema checks that need no git history — the anti-rubber-stamping gates."""
    f: list[Finding] = []
    rel = str(p.path)

    for k in REQUIRED_FM:
        if not p.frontmatter.get(k):
            f.append(Finding("error", "PR-FM", rel, f"frontmatter missing required key: {k}"))

    if not p.hypotheses:
        f.append(
            Finding(
                "error",
                "PR-NOHYP",
                rel,
                "no `## Hypotheses` table — a pre-registration with no falsifiable "
                "hypothesis is not a pre-registration",
            )
        )
        return f

    for i, row in enumerate(p.hypotheses, 1):
        hid = _col(row, ("id",)) or f"row {i}"
        thr = _col(row, THRESHOLD_KEYS)
        fal = _col(row, FALSIFIER_KEYS)
        if thr is None:
            f.append(Finding("error", "PR-NOTHRESHCOL", rel, "hypotheses table has no `threshold` column"))
        elif not thr or thr in ("-", "—", "TBD", "tbd"):
            f.append(Finding("error", "PR-THRESH", rel, f"hypothesis {hid}: empty/TBD threshold"))
        if fal is None:
            f.append(
                Finding(
                    "error",
                    "PR-NOFALSCOL",
                    rel,
                    "hypotheses table has no `falsifier` column — the mandatory "
                    "anti-rubber-stamping field",
                )
            )
        elif not fal or fal in ("-", "—", "TBD", "tbd"):
            f.append(
                Finding(
                    "error",
                    "PR-FALSIFIER",
                    rel,
                    f"hypothesis {hid}: no falsifier. State what would DISPROVE it, "
                    "or it can never fail.",
                )
            )
    return f


# --- git plumbing --------------------------------------------------------------

# Git exports these to every hook it runs, and they OUTRANK `-C <dir>`: with
# GIT_DIR set, `git -C some/other/repo log` reports on GIT_DIR's repo instead.
# So a verifier invoked from a pre-push hook would silently check the AMBIENT
# repository rather than the campaign root it was handed -- and the pre-push hook
# is exactly where this runs. `-C` looks like isolation and is not; it sets the
# working directory, it does not clear the environment that outranks it.
# See bugs/2026-08-22-prereg-tests-mutate-the-real-repo-under-a-git-hook.
_GIT_ENV_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
)


def git_env() -> dict:
    """The ambient environment with git's repo-location variables removed.

    One definition, exported so the tests pin the same scrub the library uses --
    a second copy would drift, and the drift would be invisible until a hook ran.
    """
    return {k: v for k, v in os.environ.items() if k not in _GIT_ENV_VARS}


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, check=False, env=git_env(),
    ).stdout.strip()


_BOUNDARY: dict[str, frozenset] = {}


def boundary_shas(root: Path) -> frozenset:
    """The shallow GRAFT BOUNDARY commits — those whose parents this clone does not have.

    THE PRE-REGISTRATION MECHANISM RESTS ON GIT BEING A TAMPER-EVIDENT CLOCK
    (`.claude/rules/campaign-execution.md`). A boundary commit is where that clock stops:
    git reports it as parentless, so `--diff-filter=A` attributes to it every path that
    actually existed BEFORE it, and no ancestry question across it can be answered.

    Two consequences, both of which look exactly like a violation and are artifacts:
      * every file "added" at the same boundary reads as ONE commit -> PR-SAMECOMMIT, which
        `campaign-execution.md` calls a failure;
      * nothing is an ancestor of anything across the boundary -> CM-MEASUREFIRST.

    Measured 2026-08-23: `actions/checkout@v4` defaults to `fetch-depth: 1`, where the single
    commit IS the boundary, so CI reported 16 errors against a tree that reports 5 with more
    history — 11 fabricated. Reproduced exactly with `git clone --depth 1`.

    Repo-level `--is-shallow-repository` is the WRONG predicate: this working clone is itself
    shallow (875 commits, 39 boundaries) and answers most ancestry questions perfectly well.
    The question is per-path — *is THIS path's adding-commit a boundary* — so that a deep
    clone keeps its real findings and a depth-1 clone refuses.
    """
    key = str(root)
    if key not in _BOUNDARY:
        gd = _git(root, "rev-parse", "--git-dir").strip()
        f = (root / gd if not Path(gd).is_absolute() else Path(gd)) / "shallow"
        try:
            _BOUNDARY[key] = frozenset(f.read_text(encoding="utf-8").split())
        except OSError:
            _BOUNDARY[key] = frozenset()
    return _BOUNDARY[key]


def is_boundary(root: Path, sha: str | None) -> bool:
    """True if `sha` sits on the shallow boundary, i.e. git cannot see behind it."""
    return bool(sha) and sha in boundary_shas(root)


NO_HISTORY = (
    "git cannot order these commits: at least one resolves to the shallow GRAFT BOUNDARY, "
    "where `--diff-filter=A` attributes every pre-existing path to one commit and no "
    "ancestry question can be answered. This is REFUSE, not PASS and not FAIL — in a "
    "depth-1 clone it fabricates a same-commit or out-of-order verdict for every task. "
    "Fetch history (`fetch-depth: 0`, or `git fetch --unshallow`) to get a verdict."
)


def add_commit(root: Path, path: Path) -> tuple[str, int] | None:
    """(sha, unix_time) of the commit that ADDED `path`, or None if uncommitted."""
    rel = str(path.relative_to(root)) if path.is_absolute() else str(path)
    out = _git(root, "log", "--follow", "--diff-filter=A", "--format=%H %ct", "--", rel)
    if not out:
        return None
    sha, ct = out.splitlines()[-1].split()  # last = earliest add
    return sha, int(ct)


def commits_touching(root: Path, path: Path) -> list[tuple[str, int]]:
    rel = str(path.relative_to(root)) if path.is_absolute() else str(path)
    out = _git(root, "log", "--format=%H %ct", "--", rel)
    if not out:
        return []
    return [(l.split()[0], int(l.split()[1])) for l in out.splitlines()]


def show_at(root: Path, sha: str, path: Path) -> str | None:
    rel = str(path.relative_to(root)) if path.is_absolute() else str(path)
    r = subprocess.run(
        ["git", "-C", str(root), "show", f"{sha}:{rel}"],
        capture_output=True, text=True, check=False, env=git_env(),
    )
    return r.stdout if r.returncode == 0 else None


def is_ancestor(root: Path, a: str, b: str) -> bool:
    """True if commit `a` strictly precedes `b` in history.

    ORDER BY ANCESTRY, NOT BY TIMESTAMP. A commit's `%ct` is second-granularity and
    forgeable (`git commit --date=...`), and two scripted commits routinely land in
    the same second — which made the timestamp comparison silently no-op, and
    NON-DETERMINISTICALLY so (it depended on whether the commits straddled a second
    boundary). The unit tests caught it.

    Ancestry is the tamper-evident structure: you cannot reorder it without
    rewriting every downstream SHA.
    """
    if a == b:
        return False
    return subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", a, b],
        capture_output=True, check=False, env=git_env(),
    ).returncode == 0


# --- the core check ------------------------------------------------------------


def verify(root: Path, prereg_path: Path, result_paths: list[Path]) -> list[Finding]:
    """Verify pre-registration precedes results, and was not silently rewritten.

    `result_paths` = the artifacts whose claims the pre-registration governs.
    Uncommitted results are ignored (nothing to gate yet); an uncommitted
    pre-registration alongside COMMITTED results is a hard error.
    """
    f: list[Finding] = []
    rel_pr = str(prereg_path)

    pr_add = add_commit(root, prereg_path)
    committed_results = [(p, add_commit(root, p)) for p in result_paths]
    committed_results = [(p, c) for p, c in committed_results if c is not None]

    if not committed_results:
        if pr_add is None:
            f.append(Finding("info", "PR-PENDING", rel_pr,
                             "pre-registration not yet committed (no results committed either)"))
        return f

    if pr_add is None:
        f.append(Finding(
            "error", "PR-UNCOMMITTED", rel_pr,
            "results are committed but the pre-registration is NOT. It cannot "
            "have preceded them.",
        ))
        return f

    pr_sha, _pr_t = pr_add

    pr_boundary = is_boundary(root, pr_sha)

    for rpath, (r_sha, _r_t) in committed_results:
        # "Same commit" is a real failure only when it is a real commit. At the graft
        # boundary git attributes every pre-existing path to one sha, so the equality is an
        # artifact of clone depth -- in a depth-1 checkout EVERY prereg reads same-commit.
        if (pr_boundary or is_boundary(root, r_sha)) and (
                r_sha == pr_sha or not is_ancestor(root, pr_sha, r_sha)):
            f.append(Finding("refuse", "PR-NOHISTORY", rel_pr,
                             f"result `{rpath}`: " + NO_HISTORY))
        elif r_sha == pr_sha:
            f.append(Finding(
                "error", "PR-SAMECOMMIT", rel_pr,
                f"pre-registration and result `{rpath}` landed in the SAME commit "
                f"({pr_sha[:8]}) — the order is unverifiable, so the registration "
                f"proves nothing. Commit the pre-registration FIRST.",
            ))
        elif not is_ancestor(root, pr_sha, r_sha):
            f.append(Finding(
                "error", "PR-ORDER", rel_pr,
                f"the pre-registration commit ({pr_sha[:8]}) is NOT an ancestor of the "
                f"result `{rpath}` ({r_sha[:8]}) — it did not precede it. Thresholds "
                f"fitted after the fact.",
            ))

    # Silent post-hoc edits to the hypotheses block: any commit touching the
    # pre-registration that DESCENDS from a committed result.
    result_shas = [s for _, (s, _) in committed_results]
    later_edits = [s for s, _ in commits_touching(root, prereg_path)
                   if s != pr_sha and any(is_ancestor(root, rs, s) for rs in result_shas)]
    if later_edits:
        original = show_at(root, pr_sha, prereg_path)
        current = prereg_path.read_text(encoding="utf-8") if prereg_path.exists() else ""
        if original is not None:
            orig_block = _hypotheses_block(original).strip()
            curr_block = _hypotheses_block(current).strip()
            if orig_block != curr_block:
                if AMENDMENT_RE.search(current):
                    f.append(Finding(
                        "warn", "PR-AMENDED", rel_pr,
                        "hypotheses block changed after results landed, but a visible "
                        "`## Amendment` section is present. A reviewer must read it.",
                    ))
                else:
                    f.append(Finding(
                        "error", "PR-SILENT-EDIT", rel_pr,
                        "hypotheses/threshold block was edited AFTER results were "
                        "committed, with no `## Amendment` section. This is post-hoc "
                        "threshold fitting.",
                    ))
    return f
