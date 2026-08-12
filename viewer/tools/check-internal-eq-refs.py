#!/usr/bin/env python3
"""Deterministic §<->Eq consistency gate for `# survey-ref` / `% survey-ref` code comments.

Tier-1 pre-filter for the `citation-audit` skill's INTERNAL-reference mode. A code comment
often pairs a SECTION anchor with an inline equation number, e.g. (all real, from
`sim/llms-for-coding/common/attention.py`):

    # survey-ref: appendix-d.md#sec-D.3.7 (Eq. 15 prefix-suffix product; Eq. 16 O(d_c B log B) cost)
    # survey-ref: appendix-d.md#sec-D.4.5 (Eq. D.4-2)
    # survey-ref: appendix-d.md#sec-D.4.4, #sec-D.4.5 (Eq. D.4-3)

This gate flags a comment whose cited equation N does NOT live in the cited section S of the
named survey file -- the "wrong-but-resolving" copy-paste defect: a survey-ref pointing at
`#sec-D.3.7` while citing an `Eq.` whose tag lives in a *different* section (the real 19-site
pde.py-family defect on 2026-07-20: `#sec-D.3.7 (Eq. 13/14)` when Eq. 13 lives in D.3.6). Every
existing gate (`chk_eq_code_correspondence.py`, `chk_survey_traceability.py`) only checks the
anchor RESOLVES; none checks the section and the equation number are mutually consistent. That
is the whole gap this fills.

Two equation-token forms are supported:
  * a PLAIN INTEGER `N` (`Eq. 15`, `eq 61`, `Eqs. (60)-(61)`) -- its owning section is resolved
    by opening the named survey `.md`, finding the byte offset of `id="eq-N"`, and taking the
    section number of the nearest PRECEDING heading anchor `id="sec-<num>"`.
  * a SECTION-SCOPED MARKER `X.Y-Z` (`Eq. D.4-2`, `Eq. D.3.8-1`, `Eq. E.3-1`) -- its owning
    section IS its prefix `X.Y`; no survey lookup is needed.

Consistency rule: a token passes if its owning section is dotted-prefix-consistent with ANY
cited `#sec-S` on that comment -- owning is a prefix of S, or S is a prefix of owning, compared
component-wise on the dotted path ("D.3" ~ "D.3.7" ok; "D.3.6" vs "D.3.7" NOT; "D.4" ~ "D.4.5"
ok). Otherwise it is flagged.

Known limitations (necessary-not-sufficient BY DESIGN -- this is a Tier-1 pre-filter, not the
semantic pass):
  * PRESENT-BUT-WRONG is invisible. If the cited `Eq. N` genuinely lives in the cited section but
    the code computes a different object (a multi-argument order-statistic / survival-product /
    convolution where the equation is a single-argument scalar map), the number is consistent and
    this gate passes it -- only the `citation-audit` arity/pushforward discriminator catches it.
  * MULTI-LINE survey-refs: only the line literally containing `survey-ref:` is scanned, so an
    `Eq. N` or `#sec-S` on a CONTINUATION line is not paired
    (todos/2026-07-21-internal-eq-refs-gate-multiline).
  * MARKER granularity: a section-scoped marker `D.4-2` self-resolves to its top-level `D.4`, so a
    marker cited under a wrong SUBSECTION of the right section is not flagged (plain integers DO
    resolve to the exact subsection). `Eq. (D.4-2)` (a marker in parens) is not matched (0 in corpus).

Advisory by default (exit 0, warnings only). `--severity error` exits 1 when any un-suppressed
flag remains. A flag is suppressed by an entry in the rejection ledger
`.claude/internal-eq-refs-rejected.json` (a JSON list of {source, sec, eq, note}); the key is
(source-relpath, cited-sec, eq-token), direction-independent between the cited and the owning
section. This mirrors the crosslink `off -> warn -> error` rollout; the tool is standalone and
is NOT wired into any git hook.

Usage:
    python viewer/tools/check-internal-eq-refs.py PATH [PATH ...] \
        [--survey-root DIR] [--ledger FILE] [--severity warn|error] [--check]

`PATH` is a file, or a directory (every `.py`/`.m` under it is scanned). Exit codes: 0 advisory
PASS (or warn), 1 (--severity error with un-suppressed flags), 2 usage error.
"""
from __future__ import annotations

import argparse
import bisect
import json
import sys
from pathlib import Path
from typing import Optional
import re

# ---------------------------------------------------------------------------
# Repo layout
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SURVEY_ROOT = REPO_ROOT / "surveys" / "llms-for-coding"
DEFAULT_LEDGER = REPO_ROOT / ".claude" / "internal-eq-refs-rejected.json"

# ---------------------------------------------------------------------------
# Line/anchor/equation regexes
# ---------------------------------------------------------------------------
# A `.md` path token (may include a wikis/... directory prefix).
_MD = r"[A-Za-z0-9_\-./]+\.md"

# A `#sec-<S>` anchor, optionally file-qualified. The qualified alternative is tried first so a
# bare `#sec-` never steals a qualified one.
_SEC_RE = re.compile(rf"(?:(?P<qmd>{_MD}))?#sec-(?P<sec>[A-Za-z0-9][A-Za-z0-9.\-]*)")
# A `#eq-<N>` anchor, optionally file-qualified (rare in survey-refs; supported for completeness).
_EQANCHOR_RE = re.compile(rf"(?:(?P<qmd>{_MD}))?#eq-(?P<n>\d+)")
# Every `.md` path occurrence on a line, with position (used to attribute a plain-int eq to a file).
_MDPOS_RE = re.compile(_MD)

# A section-scoped marker: letters, then one or more `.<num>` groups, then `-<index>`.
_MARKER = r"[A-Za-z]+(?:\.\d+)+-[0-9A-Za-z]+"

# Inline equation mentions after an `Eq`/`Eqs`/`Equation` keyword. Ordered alternation
# (leftmost-longest via finditer): parenthesised pair, parenthesised single, marker pair,
# marker single, integer pair/range, integer single.
_EQ_RE = re.compile(
    r"(?ix)"
    r"\beq(?:s|uation|uations)?\b\.?\s*"
    r"(?:"
    r"    \(\s*(?P<pa>\d+)\s*\)\s*[-/]\s*\(\s*(?P<pb>\d+)\s*\)"     # (60)-(61)
    r"  | \(\s*(?P<ps>\d+)\s*\)"                                    # (40)
    rf"  | (?P<mp1>{_MARKER})\s*/\s*(?P<mp2>{_MARKER})"             # D.4-2/D.4-3
    rf"  | (?P<ms>{_MARKER})"                                       # D.4-2
    r"  | (?P<ia>\d+)\s*[/\-]\s*(?P<ib>\d+)"                        # 15/16 or 9-11
    r"  | (?P<is_>\d+)"                                             # 61
    r")"
)

# A heading section anchor `id="sec-<num>"` whose section number is a pure dotted
# alphanumeric run with NO hyphen -- this EXCLUDES landmark/part anchors such as
# `id="sec-D.10-part-a"`, which must not be read as a section owner.
_HEADING_RE = re.compile(r'id="sec-([0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*)"')
_EQID_RE = re.compile(r'id="eq-(\d+)"')

# Prefix of a section-scoped marker, e.g. "D.3.8-1" -> "D.3.8".
_MARKER_PREFIX_RE = re.compile(r"^([A-Za-z]+(?:\.\d+)+)-")


# ---------------------------------------------------------------------------
# Survey-file index (cached per resolved path)
# ---------------------------------------------------------------------------
class SurveyIndex:
    """Heading-anchor offsets + eq-anchor offsets for one survey `.md`."""

    def __init__(self, text: str) -> None:
        # sorted heading anchors as parallel arrays for bisect
        heads = [(m.start(), m.group(1)) for m in _HEADING_RE.finditer(text)]
        heads.sort()
        self._head_pos = [p for p, _ in heads]
        self._head_sec = [s for _, s in heads]
        self._eq_pos = {int(m.group(1)): m.start() for m in _EQID_RE.finditer(text)}

    def owning_section(self, n: int) -> Optional[str]:
        """Section number owning `id="eq-n"`, or None if the eq anchor is absent."""
        pos = self._eq_pos.get(n)
        if pos is None:
            return None
        i = bisect.bisect_right(self._head_pos, pos) - 1
        if i < 0:
            return ""  # eq precedes every heading -> owned by document front matter
        return self._head_sec[i]

    def has_eq(self, n: int) -> bool:
        return n in self._eq_pos


class SurveyStore:
    """Resolves + caches `.md` names to a `SurveyIndex`, tracking unreadable files."""

    def __init__(self, survey_root: Path) -> None:
        self.survey_root = survey_root
        self._cache: dict[str, Optional[SurveyIndex]] = {}
        self.unreadable: dict[str, str] = {}   # name -> reason
        self.opened: set[str] = set()

    def _resolve(self, name: str) -> Path:
        # A wikis/... (or any slash-bearing) path resolves from the repo root; a bare
        # `foo.md` resolves under the survey root.
        if "/" in name:
            return (REPO_ROOT / name)
        return self.survey_root / name

    def index(self, name: str) -> Optional[SurveyIndex]:
        if name in self._cache:
            return self._cache[name]
        path = self._resolve(name)
        idx: Optional[SurveyIndex] = None
        try:
            text = path.read_text(encoding="utf-8")
            idx = SurveyIndex(text)
            self.opened.add(name)
        except (OSError, UnicodeDecodeError) as e:
            self.unreadable[name] = f"{type(e).__name__}: {e}"
        self._cache[name] = idx
        return idx


# ---------------------------------------------------------------------------
# Consistency primitives
# ---------------------------------------------------------------------------
def _norm_sec(sec: str) -> str:
    """Lowercase; strip any landmark/part suffix so a cited `#sec-D.7.5-part-b`
    compares as the section number `D.7.5`."""
    core = re.match(r"^([A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)", sec)
    return (core.group(1) if core else sec).lower()


def prefix_consistent(a: str, b: str) -> bool:
    """True if the dotted paths `a` and `b` agree component-wise up to the shorter
    length -- i.e. one is a prefix of the other."""
    pa = _norm_sec(a).split(".")
    pb = _norm_sec(b).split(".")
    n = min(len(pa), len(pb))
    return pa[:n] == pb[:n]


# ---------------------------------------------------------------------------
# Per-line extraction
# ---------------------------------------------------------------------------
class CitedSec:
    __slots__ = ("md", "sec", "pos")

    def __init__(self, md: Optional[str], sec: str, pos: int) -> None:
        self.md = md          # survey file name, or None if no .md named on the line
        self.sec = sec        # raw cited section string (may carry a landmark suffix)
        self.pos = pos


class EqToken:
    __slots__ = ("kind", "value", "pos", "raw")

    def __init__(self, kind: str, value, pos: int, raw: str) -> None:
        self.kind = kind      # "int" or "marker"
        self.value = value    # int for "int"; section-prefix str for "marker"
        self.pos = pos
        self.raw = raw        # display token, e.g. "15", "D.4-2"


def _extract_cited_secs(line: str) -> list[CitedSec]:
    """All `#sec-S` anchors on the line, in order; a bare `#sec-` inherits the last
    `.md` named to its left."""
    out: list[CitedSec] = []
    current_md: Optional[str] = None
    for m in _SEC_RE.finditer(line):
        if m.group("qmd"):
            current_md = m.group("qmd")
        out.append(CitedSec(current_md, m.group("sec"), m.start()))
    return out


def _md_positions(line: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group(0)) for m in _MDPOS_RE.finditer(line)]


def _md_for_pos(md_pos: list[tuple[int, str]], pos: int) -> Optional[str]:
    """The `.md` a plain-int eq at `pos` belongs to: the last `.md` to its left, else
    the first `.md` on the line, else None."""
    best: Optional[str] = None
    for p, name in md_pos:
        if p < pos:
            best = name
        else:
            break
    if best is None and md_pos:
        best = md_pos[0][1]
    return best


def _extract_eq_tokens(line: str) -> list[EqToken]:
    """All inline `Eq.`-keyworded equation mentions on the line, expanded to individual
    tokens (a range/pair yields both endpoints)."""
    out: list[EqToken] = []
    for m in _EQ_RE.finditer(line):
        pos = m.start()
        if m.group("pa") is not None:
            out.append(EqToken("int", int(m.group("pa")), pos, m.group("pa")))
            out.append(EqToken("int", int(m.group("pb")), pos, m.group("pb")))
        elif m.group("ps") is not None:
            out.append(EqToken("int", int(m.group("ps")), pos, m.group("ps")))
        elif m.group("mp1") is not None:
            for raw in (m.group("mp1"), m.group("mp2")):
                pref = _MARKER_PREFIX_RE.match(raw)
                out.append(EqToken("marker", pref.group(1), pos, raw))
        elif m.group("ms") is not None:
            raw = m.group("ms")
            pref = _MARKER_PREFIX_RE.match(raw)
            out.append(EqToken("marker", pref.group(1), pos, raw))
        elif m.group("ia") is not None:
            out.append(EqToken("int", int(m.group("ia")), pos, m.group("ia")))
            out.append(EqToken("int", int(m.group("ib")), pos, m.group("ib")))
        elif m.group("is_") is not None:
            out.append(EqToken("int", int(m.group("is_")), pos, m.group("is_")))
    return out


# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
class Flag:
    __slots__ = ("source", "lineno", "cited_sec", "eq_raw", "owning", "eq_file", "kind")

    def __init__(self, source: str, lineno: int, cited_sec: str, eq_raw: str,
                 owning: str, eq_file: Optional[str], kind: str) -> None:
        self.source = source          # repo-relative posix path
        self.lineno = lineno
        self.cited_sec = cited_sec    # normalized cited section it is inconsistent with
        self.eq_raw = eq_raw          # display token, e.g. "83" or "41"
        self.owning = owning          # normalized owning section
        self.eq_file = eq_file        # survey file the eq lives in (None for markers)
        self.kind = kind

    def message(self) -> str:
        where = f" of {self.eq_file}" if self.eq_file else ""
        return (f"{self.source}:{self.lineno} cites #sec-{self.cited_sec} but "
                f"Eq. {self.eq_raw} lives in section {self.owning}{where}")

    def key(self) -> tuple[str, str, str]:
        return (self.source, _norm_sec(self.cited_sec), self.eq_raw)


class Resolution:
    """A resolution failure: a plain-int eq that could not be found in its survey file."""
    __slots__ = ("source", "lineno", "eq_raw", "eq_file", "reason")

    def __init__(self, source: str, lineno: int, eq_raw: str, eq_file: Optional[str],
                 reason: str) -> None:
        self.source = source
        self.lineno = lineno
        self.eq_raw = eq_raw
        self.eq_file = eq_file
        self.reason = reason

    def message(self) -> str:
        return f"{self.source}:{self.lineno} {self.reason}"


# ---------------------------------------------------------------------------
# Core scan
# ---------------------------------------------------------------------------
def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def scan_file(path: Path, store: SurveyStore) -> tuple[list[Flag], list[Resolution], int, int]:
    """Return (flags, resolution_failures, n_ref_lines, n_tokens_checked) for one source file."""
    source = _rel(path)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as e:
        # A source we cannot read is itself a coverage gap.
        return ([], [Resolution(source, 0, "-", None, f"source unreadable ({e})")], 0, 0)

    flags: list[Flag] = []
    resolutions: list[Resolution] = []
    n_ref_lines = 0
    n_checked = 0

    for lineno, line in enumerate(lines, start=1):
        if "survey-ref:" not in line:
            continue
        n_ref_lines += 1

        cited = _extract_cited_secs(line)
        eqs = _extract_eq_tokens(line)
        if not eqs or not cited:
            continue
        md_pos = _md_positions(line)

        for tok in eqs:
            if tok.kind == "marker":
                owning = tok.value                       # section prefix, no lookup needed
                # A marker carries no file, so compare against every cited section number.
                candidates = [c.sec for c in cited]
                if not candidates:
                    continue
                n_checked += 1
                if not any(prefix_consistent(owning, c) for c in candidates):
                    # Attribute the flag to the nearest cited section (first, for stability).
                    flags.append(Flag(source, lineno, _norm_sec(cited[0].sec),
                                      tok.raw, _norm_sec(owning), None, "marker"))
                continue

            # plain integer -> resolve owning section from its survey file
            eq_file = _md_for_pos(md_pos, tok.pos)
            if eq_file is None:
                resolutions.append(Resolution(source, lineno, tok.raw, None,
                                              f"Eq. {tok.raw} cited with no survey .md named on the line"))
                continue
            idx = store.index(eq_file)
            if idx is None:
                resolutions.append(Resolution(source, lineno, tok.raw, eq_file,
                                              f"survey file {eq_file} could not be opened (Eq. {tok.raw})"))
                continue
            owning = idx.owning_section(tok.value)
            if owning is None:
                resolutions.append(Resolution(source, lineno, tok.raw, eq_file,
                                              f"eq {tok.raw} not found in {eq_file}"))
                continue
            # Compare only against cited sections in the SAME survey file.
            same_file = [c.sec for c in cited if c.md == eq_file]
            if not same_file:
                continue
            n_checked += 1
            if not any(prefix_consistent(owning, c) for c in same_file):
                flags.append(Flag(source, lineno, _norm_sec(same_file[0]),
                                  tok.raw, _norm_sec(owning), eq_file, "int"))

    return flags, resolutions, n_ref_lines, n_checked


# ---------------------------------------------------------------------------
# Rejection ledger
# ---------------------------------------------------------------------------
def _ledger_source_match(flag_source: str, ledger_source: str) -> bool:
    a = flag_source.replace("\\", "/").lstrip("./")
    b = ledger_source.replace("\\", "/").lstrip("./")
    return a == b or a.endswith("/" + b) or b.endswith("/" + a) or Path(a).name == Path(b).name


def load_ledger(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"WARNING: rejection ledger {path} unreadable ({e}); treating as empty",
              file=sys.stderr)
        return []
    if not isinstance(data, list):
        print(f"WARNING: rejection ledger {path} is not a JSON list; treating as empty",
              file=sys.stderr)
        return []
    return data


def is_suppressed(flag: Flag, ledger: list[dict]) -> bool:
    """A flag is suppressed by an entry matching (source, sec, eq). Direction-independent:
    the ledger's `sec` may be either the cited OR the owning section of the flag."""
    f_eq = str(flag.eq_raw)
    f_cited = _norm_sec(flag.cited_sec)
    f_owning = _norm_sec(flag.owning)
    for e in ledger:
        if not isinstance(e, dict):
            continue
        if not _ledger_source_match(flag.source, str(e.get("source", ""))):
            continue
        if str(e.get("eq", "")) != f_eq:
            continue
        e_sec = _norm_sec(str(e.get("sec", "")))
        if e_sec in (f_cited, f_owning):
            return True
    return False


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------
def iter_sources(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for p in paths:
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.suffix in (".py", ".m") and "__pycache__" not in f.parts:
                    r = f.resolve()
                    if r not in seen:
                        seen.add(r)
                        out.append(f)
        elif p.is_file():
            r = p.resolve()
            if r not in seen:
                seen.add(r)
                out.append(p)
        else:
            print(f"WARNING: not a file or directory: {p}", file=sys.stderr)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Deterministic section<->equation consistency gate for survey-ref comments.")
    ap.add_argument("paths", nargs="+", help="source file(s) or directory(ies) to scan (.py/.m)")
    ap.add_argument("--survey-root", default=str(DEFAULT_SURVEY_ROOT),
                    help="directory holding the survey .md files (default: surveys/llms-for-coding)")
    ap.add_argument("--ledger", default=str(DEFAULT_LEDGER),
                    help="rejection ledger JSON (default: .claude/internal-eq-refs-rejected.json)")
    ap.add_argument("--severity", choices=("warn", "error"), default="warn",
                    help="warn (advisory, exit 0) or error (exit 1 on un-suppressed flags)")
    ap.add_argument("--check", action="store_true", help="accepted no-op alias")
    args = ap.parse_args(argv)

    survey_root = Path(args.survey_root)
    if not survey_root.is_absolute():
        survey_root = (Path.cwd() / survey_root)
    if not survey_root.is_dir():
        print(f"ERROR: --survey-root is not a directory: {survey_root}", file=sys.stderr)
        return 2

    sources = iter_sources([Path(p) for p in args.paths])
    if not sources:
        print("ERROR: no .py/.m sources found in the given paths", file=sys.stderr)
        return 2

    store = SurveyStore(survey_root)
    ledger = load_ledger(Path(args.ledger))

    all_flags: list[Flag] = []
    all_res: list[Resolution] = []
    total_ref_lines = 0
    total_checked = 0
    for src in sources:
        flags, res, nref, nchk = scan_file(src, store)
        all_flags.extend(flags)
        all_res.extend(res)
        total_ref_lines += nref
        total_checked += nchk

    kept = [f for f in all_flags if not is_suppressed(f, ledger)]
    suppressed = len(all_flags) - len(kept)

    # ---- report ----
    print(f"check-internal-eq-refs: scanned {len(sources)} source file(s), "
          f"{total_ref_lines} survey-ref line(s), {total_checked} equation token(s) checked "
          f"against survey sections.")

    if store.unreadable:
        print("COVERAGE WARNING -- survey file(s) referenced but NOT opened "
              "(a '0 flags' result is meaningless for these):")
        for name, reason in sorted(store.unreadable.items()):
            print(f"  [?] {name}: {reason}")

    if all_res:
        print(f"RESOLUTION notes ({len(all_res)} -- eq anchor absent / no file / unreadable):")
        for r in all_res:
            print(f"  [~] {r.message()}")

    if kept:
        print(f"FLAGS ({len(kept)} un-suppressed; {suppressed} suppressed by ledger):")
        for f in sorted(kept, key=lambda x: (x.source, x.lineno, x.eq_raw)):
            print(f"  [-] {f.message()}")
    else:
        print(f"FLAGS: none un-suppressed ({suppressed} suppressed by ledger).")

    if kept and args.severity == "error":
        print(f"check-internal-eq-refs: FAIL ({len(kept)} un-suppressed flag(s)) "
              f"-- severity=error", file=sys.stderr)
        return 1

    status = "PASS" if not kept else f"ADVISORY ({len(kept)} flag(s), severity=warn)"
    print(f"check-internal-eq-refs: {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
