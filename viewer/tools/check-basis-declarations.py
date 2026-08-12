#!/usr/bin/env python3
"""check-basis-declarations.py -- the [opt:MATH-BASIS] gate.

A quantity that can be measured on more than one basis must say which basis it is
on, at the point of use.  Metric-basis conflation is a leading silent defect
class in LLM writing -- a scaling-law N that does not say whether embeddings are
counted, a loss in bits quoted beside one in nats -- and
`.claude/rules/calibration-residuals.md` check 4 already forbade every one of
them: it owns the moment of *attribution*, and nothing owned the moment of
*authoring*.  This checker owns that moment.

It is deliberately a LOW-RECALL, HIGH-PRECISION gate.  It does not try to
understand the mathematics; it looks for basis-bearing symbols and asks whether a
declaration is in scope.  A gate that cries wolf gets switched off, and a gate
that is switched off finds nothing.

Scope of a declaration is the enclosing numbered section: declare `N` as
non-embedding in section 6.4 and every use of `N` inside 6.4 is satisfied.  A
survey-wide declaration (the notation contract, conventionally section 1.4) covers
every file in the survey.

Usage:
    check-basis-declarations.py <path>...            # files or survey dirs
    check-basis-declarations.py <path> --severity=error|warn|off
    check-basis-declarations.py <path> --list-registry

Severity resolves from, in order: --severity, `.claude/math-basis-severity`,
then the default `warn`.  Exit 1 only at `error`.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

# --------------------------------------------------------------------------
# The registry.  Each entry: the symbol as it appears in inline math, the axis
# it is ambiguous on, and the vocabulary that resolves it.  Every entry here was
# earned by an actual measured defect or is a direct sibling of one -- this is
# not a list of everything that could conceivably be ambiguous.
# --------------------------------------------------------------------------
REGISTRY: dict[str, dict] = {
    "N": {
        "axis": "parameter-count-basis",
        "why": "non-embedding vs total parameters -- the scaling-law literature is split "
               "(Kaplan et al. fit non-embedding N, Chinchilla fits total), and the gap is "
               "large enough at small scale to change a fitted exponent",
        # Fires only where N is USED as a parameter count. N-as-sample-count is a
        # different quantity sharing the glyph; the notation contract owns that
        # collision, not this gate. Precision over recall: a noisy gate gets ignored.
        "context": r"parameter|weight|model size|scal|compute budget|\bFLOP",
        "resolvers": [
            r"non[- ]embedding", r"embedding parameter", r"total parameter",
            r"including embedding", r"excluding embedding", r"parameter count",
        ],
    },
    "D": {
        "axis": "token-count-basis",
        "why": "unique tokens in the corpus vs tokens SEEN during training -- they differ "
               "by the epoch count, so a multi-epoch run reports two different D for one dataset",
        "context": r"token|corpus|dataset|epoch|training data",
        "resolvers": [
            r"unique token", r"tokens seen", r"token[- ]seen", r"single epoch", r"one epoch",
            r"epoch", r"deduplicat", r"distinct token", r"training token",
        ],
    },
    "B": {
        "axis": "batch-basis",
        "why": "batch size in SEQUENCES vs in TOKENS -- they differ by the sequence length, "
               "so a batch-size-vs-loss claim is unreadable without the basis",
        "context": r"batch|step|gradient|throughput",
        "resolvers": [
            r"in tokens", r"token batch", r"sequences per", r"in sequences",
            r"batch of \$?\d+\$? sequence", r"tokens per (?:step|batch)", r"sequence length",
        ],
    },
    r"\\mathrm\{pass\}@k": {
        "axis": "sampling-basis",
        "why": "pass@k over k INDEPENDENT samples vs a single greedy sample -- pass@k is "
               "systematically higher because one success among k is forgiven",
        "context": r"pass@|sample|greedy|temperature|unbiased estimator",
        "resolvers": [
            r"unbiased estimator", r"\bn\s*=\s*\d+", r"greedy", r"single sample",
            r"independent sample", r"samples per (?:problem|task)",
        ],
    },
}

# A loss / entropy / perplexity figure must say which log base it is on.
# The direct analogue of a dB figure needing its reference: bits (log2) and nats
# (ln) differ by ln 2 = 0.693, which silently rescales every scaling-law fit.
LOSS_UNIT_RE = re.compile(
    r"(?<![A-Za-z])(-?\d+(?:\.\d+)?)\s*(?:bits?|nats?)(?![A-Za-z/])|"
    r"(?<![A-Za-z])(?:loss|cross[- ]entropy|perplexity|entropy)\s+of\s+(-?\d+(?:\.\d+)?)",
    re.I,
)
LOSS_UNIT_RESOLVERS = re.compile(
    r"\bbits?\b|\bnats?\b|\blog_?2\b|\blog2\b|natural log|\bln\b|base[- ]2|base 2|"
    r"per token|per byte|per character|per word|bits/token|nats/token|"
    r"\bBPB\b|\bBPC\b|perplexity|\bppl\b", re.I)

SEC_RE = re.compile(r"^<!--\s*sec:([0-9A-Za-z.]+)\s*-->")
CODE_FENCE_RE = re.compile(r"^\s*```")
# A declaration is any sentence naming the symbol AND a resolver near it.
DECL_WINDOW = 400  # characters around the symbol in which a resolver counts


def load_severity(explicit: str | None, root: pathlib.Path) -> str:
    """Global severity, from --severity or `.claude/math-basis-severity`.

    Defaults to `warn`.  Promoting the GLOBAL setting to `error` would block
    pushes on surveys nobody has reviewed yet, which is how a gate gets switched
    off; a survey earns `error` individually once its backlog is zero, via
    `.claude/math-basis-strict` (one survey path per line).
    """
    if explicit:
        return explicit
    f = root / ".claude" / "math-basis-severity"
    if f.exists():
        v = f.read_text(encoding="utf-8").strip().lower()
        if v in ("off", "warn", "error"):
            return v
    return "warn"


def strict_paths(root: pathlib.Path) -> list[str]:
    """Surveys that have cleared their backlog and opted in to `error`."""
    f = root / ".claude" / "math-basis-strict"
    if not f.exists():
        return []
    return [ln.strip() for ln in f.read_text(encoding="utf-8").split("\n")
            if ln.strip() and not ln.startswith("#")]


SKIP_NAMES = {"references.md"}   # a bibliography quotes "bits"/"nats" inside paper titles


def iter_md(paths: list[str]) -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for p in paths:
        q = pathlib.Path(p)
        if q.is_dir():
            out.extend(sorted(x for x in q.glob("*.md") if x.name not in SKIP_NAMES))
        elif q.suffix == ".md":
            out.append(q)
    return out


def strip_fences(lines: list[str]) -> list[bool]:
    """Return a per-line mask: True where the line is inside a fenced block."""
    inside, mask = False, []
    for ln in lines:
        if CODE_FENCE_RE.match(ln):
            inside = not inside
            mask.append(True)
            continue
        mask.append(inside)
    return mask


def section_of(lines: list[str], idx: int) -> str:
    for k in range(idx, -1, -1):
        m = SEC_RE.match(lines[k])
        if m:
            return m.group(1)
    return "?"


def declared_in(text: str, resolvers: list[str]) -> bool:
    return any(re.search(r, text, re.I) for r in resolvers)


def check_file(path: pathlib.Path, global_decls: set[str]) -> list[tuple]:
    raw = path.read_text(encoding="utf-8")
    lines = raw.split("\n")
    fence = strip_fences(lines)
    findings: list[tuple] = []

    # Pass 1: which (section, symbol) pairs carry a declaration anywhere in the section?
    sec_text: dict[str, list[str]] = {}
    for i, ln in enumerate(lines):
        if fence[i]:
            continue
        sec_text.setdefault(section_of(lines, i), []).append(ln)
    sec_blob = {s: "\n".join(v) for s, v in sec_text.items()}

    seen: set[tuple[str, str]] = set()
    for i, ln in enumerate(lines):
        if fence[i] or ln.lstrip().startswith("<!--"):
            continue
        sec = section_of(lines, i)

        for sym, spec in REGISTRY.items():
            if sym in global_decls:
                continue
            pat = re.compile(r"\$[^$\n]*" + sym + r"(?![A-Za-z_{])[^$\n]*\$")
            if not pat.search(ln):
                continue
            ctx = spec.get("context")
            if ctx and not re.search(ctx, "\n".join(lines[max(0, i - 1):i + 2]), re.I):
                continue
            fctx = spec.get("file_context")
            if fctx and not re.search(fctx, raw, re.I):
                continue
            key = (sec, sym)
            if key in seen:
                continue
            blob = sec_blob.get(sec, "")
            if declared_in(blob, spec["resolvers"]):
                seen.add(key)
                continue
            # narrow window fallback: the paragraph itself
            lo = max(0, i - 2)
            win = "\n".join(lines[lo:i + 3])
            if declared_in(win, spec["resolvers"]):
                seen.add(key)
                continue
            seen.add(key)
            findings.append((path, i + 1, sec, sym.replace("\\\\", "\\"),
                             spec["axis"], spec["why"]))

        for m in LOSS_UNIT_RE.finditer(ln):
            lo = max(0, m.start() - DECL_WINDOW)
            hi = min(len(ln), m.end() + DECL_WINDOW)
            if LOSS_UNIT_RESOLVERS.search(ln[lo:hi]):
                continue
            key = (sec, "loss-unit@%d" % i)
            if key in seen:
                continue
            seen.add(key)
            findings.append((path, i + 1, sec, m.group(0), "loss-unit",
                             "a loss/entropy figure must name its log base (bits vs nats differ by ln 2)"))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--severity", choices=["off", "warn", "error"])
    ap.add_argument("--list-registry", action="store_true")
    a = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parents[2]
    if a.list_registry:
        for sym, spec in REGISTRY.items():
            print(f"{sym:24s} {spec['axis']:22s} {spec['why']}")
        return 0

    sev = load_severity(a.severity, root)
    if sev == "off":
        print("[basis] off")
        return 0

    files = iter_md(a.paths)
    if not files:
        print("[basis] refusing to report clean: no markdown files in scope", file=sys.stderr)
        return 2

    # A survey-wide notation contract (conventionally §1.4) declares for every file.
    global_decls: set[str] = set()
    for f in files:
        if f.name in ("index.md",):
            blob = f.read_text(encoding="utf-8")
            for sym, spec in REGISTRY.items():
                if re.search(r"\bbasis\b", blob, re.I) and declared_in(blob, spec["resolvers"]):
                    global_decls.add(sym)

    findings: list[tuple] = []
    for f in files:
        findings.extend(check_file(f, global_decls))

    strict = strict_paths(root)
    n_strict_err = 0
    for path, line, sec, sym, axis, why in findings:
        is_strict = sev == "error" or any(str(path).startswith(s) for s in strict)
        if is_strict:
            n_strict_err += 1
        tag = "ERROR" if is_strict else "warn"
        print(f"{path}:{line}: [{tag}] BASIS-UNDECLARED §{sec} '{sym}' ({axis}) -- {why}")

    n = len(findings)
    print(f"\n[basis] {len(files)} file(s), {n} undeclared basis use(s), "
          f"{len(global_decls)} survey-wide declaration(s), severity={sev}"
          + (f", {len(strict)} strict path(s), {n_strict_err} blocking" if strict else ""))
    return 1 if n_strict_err else 0


if __name__ == "__main__":
    sys.exit(main())
