#!/usr/bin/env python3
"""check-value-ledger.py -- the T7 self-consistency gate (restatement drift).

Four of the seventeen defects measured on `surveys/adc-calibration` (2026-07-28)
were derivable from the document alone: a formula refuted by its own sanity
anchor two sentences away, a sign contradicting the section that set it, a claim
contradicting its own preceding paragraph, and a matrix cell inverting the
threshold it derived from.  Nothing in the survey's gates looked for that.

This tool owns one tractable slice of it: **restatement drift**.  A survey
derives a number once and restates it many times — the §11 matrix, the §12
tables, the §15 Q&A and the executive summary all quote §5–§8.  When the
derivation is corrected, the restatements go stale silently.

Two modes, mirroring the repo's existing eq/ref marker discipline:

  *Ledger mode* (authoritative).  The site that derives a value declares it:

      <!-- val:dwa-osr4 = 10.01 dB -->

  and every restatement references it:

      <!-- val:dwa-osr4 -->10.01 dB

  The tool checks each restatement carries the declared value.  Opt-in, so it
  has no false positives, and it makes drift structurally impossible.

  *Survey mode* (advisory, `--survey`).  For values not yet in the ledger:
  find numeric literals that recur across files with a shared context word and
  DIFFERENT values — candidates to annotate.  Advisory only, because a number
  legitimately differs between operating points and the tool cannot know which.

Usage:
    check-value-ledger.py <path>...              # ledger mode
    check-value-ledger.py <path>... --survey     # + drift candidates
    check-value-ledger.py <path>... --severity=error|warn|off

Exit 1 only at `error`, and only for ledger-mode mismatches — survey mode never
blocks, because a heuristic must not gate a push.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

DECL_RE = re.compile(r"<!--\s*val:([A-Za-z0-9._-]+)\s*=\s*(.+?)\s*-->")
# The restatement text is captured up to the next HTML comment or end of line.
# The cap was 40 chars, which clipped a formula-valued restatement mid-symbol
# and made the literal comparison below unusable; 160 spans any real one.
REF_RE = re.compile(r"<!--\s*val:([A-Za-z0-9._-]+)\s*-->\s*([^\s<][^<\n]{0,160})")
# Numbers in a survey are routinely MATH-DELIMITED -- `$150$ dB`,
# `$\approx 60.6$~dB`, `$1.5\,\mathrm{ms}$` -- so a number and its unit are
# separated not by plain whitespace but by a closing `$`, a LaTeX thin space,
# or a tilde, and the unit itself may be wrapped in `\mathrm{...}`.
#
# The original pattern required `\d+\s*UNIT` and so matched only the bare
# `150 dB` form. That made the gate STRUCTURALLY BLIND to the corpus's
# dominant number form: `ledger_pass` skips the comparison outright when
# either side yields no match (`if not got or not want_n: continue`), so a
# marker on `$150$ dB` was accepted and never checked. The gate reported
# clean because it could not read the numbers, not because they agreed --
# exactly the vacuous-pass failure the ledger exists to prevent.
# See bugs/2026-07-31-value-ledger-blind-to-math-delimited-numbers.
_NUM = r"-?\d+(?:\.\d+)?(?:\s*[x×]\s*10\^?\{?-?\d+\}?)?"
_SEP = r"[\s$~]*(?:\\[,;:!]|\\quad|\\qquad)?[\s$~]*"
_UNIT_OPEN = r"(?:\\(?:mathrm|mathsf|text|textrm)\s*\{\s*)?"
NUM_UNIT_RE = re.compile(
    r"(?<![\w.])(" + _NUM + r")" + _SEP + _UNIT_OPEN +
    r"(dBc|dBFS|dB|fs|ps|ns|µs|us|ms|s|GHz|MHz|kHz|Hz|GS/s|MS/s|bits?|LSB|%)(?![\w])"
)
CODE_FENCE_RE = re.compile(r"^\s*```")
STOP = {"the", "a", "an", "of", "is", "at", "in", "to", "and", "for", "with", "that",
        "it", "its", "this", "as", "on", "by", "be", "are", "from", "than", "so"}


def load_severity(explicit, root):
    if explicit:
        return explicit
    f = root / ".claude" / "value-ledger-severity"
    if f.exists():
        v = f.read_text(encoding="utf-8").strip().lower()
        if v in ("off", "warn", "error"):
            return v
    return "warn"


def iter_md(paths):
    """Every markdown file under `paths`, RECURSIVELY for directories.

    This used to be a non-recursive `glob("*.md")`, and the pre-push gate
    invokes the tool as `check-value-ledger.py surveys/`. Under that pairing
    the gate saw only the 12 flat single-file surveys sitting directly in
    `surveys/` and NONE of the multi-file survey directories -- so it read
    zero declarations, found zero drift, and reported clean without ever
    opening the documents the ledger exists to police. A green gate must
    mean "looked and found nothing", never "did not look".
    """
    out = []
    for p in paths:
        q = pathlib.Path(p)
        if q.is_dir():
            out.extend(sorted(q.rglob("*.md")))
        elif q.suffix == ".md":
            out.append(q)
    return out


def live_lines(path):
    lines = path.read_text(encoding="utf-8").split("\n")
    inside, out = False, []
    for i, ln in enumerate(lines):
        if CODE_FENCE_RE.match(ln):
            inside = not inside
            continue
        if not inside:
            out.append((i + 1, ln))
    return out


def norm(v: str) -> str:
    """Normalise a value string so '10.01 dB' == '10.01dB'.

    Also strips the math/LaTeX scaffolding a survey wraps numbers in -- `$`,
    `~`, `\\,`-family thin spaces and a `\\mathrm{...}` unit wrapper -- so
    that `$150$ dB` and `150 dB` compare equal.
    """
    v = re.sub(r"\\(?:mathrm|mathsf|text|textrm)\s*\{\s*([^}]*)\}", r"\1", v)
    v = re.sub(r"\\(?:[,;:!]|quad|qquad)", "", v)
    v = v.replace("$", "").replace("~", "")
    return re.sub(r"\s+", "", v).lower().replace("×", "x")


def num_unit(s):
    """The (number, unit) pair of the first number+unit in `s`, normalised.

    Comparing the captured GROUPS rather than the raw matched span keeps the
    separator out of the comparison entirely, so `150 dB` (a declaration) and
    `$150$ dB` (its restatement) agree without relying on `norm` to have
    stripped every possible delimiter.
    """
    m = NUM_UNIT_RE.search(s)
    return None if not m else (norm(m.group(1)), norm(m.group(2)))


def ledger_pass(files):
    decls, refs, errs = {}, [], []
    for f in files:
        for lineno, ln in live_lines(f):
            for m in DECL_RE.finditer(ln):
                key, val = m.group(1), m.group(2)
                if key in decls and norm(decls[key][0]) != norm(val):
                    errs.append((f, lineno, key,
                                 f"re-declared as '{val}', already declared "
                                 f"'{decls[key][0]}' at {decls[key][1]}:{decls[key][2]}"))
                else:
                    decls[key] = (val, f.name, lineno)
            for m in REF_RE.finditer(ln):
                if DECL_RE.match(ln[m.start():]):
                    continue
                refs.append((f, lineno, m.group(1), m.group(2)))

    for f, lineno, key, shown in refs:
        if key not in decls:
            errs.append((f, lineno, key, "reference to an undeclared value"))
            continue
        want = decls[key][0]
        where = f"{decls[key][1]}:{decls[key][2]}"
        got_nu, want_nu = num_unit(shown), num_unit(want)
        if got_nu and want_nu:
            if got_nu != want_nu:
                errs.append((f, lineno, key,
                             f"restated as '{got_nu[0]} {got_nu[1]}' but declared "
                             f"'{want_nu[0]} {want_nu[1]}' at {where}"))
            continue
        # Neither side (or only one) yields a number+unit -- the declared value
        # is a FORMULA, e.g. `SNR_MF = 2|a'|^2 E_s/N_0`, whose restatements
        # drift in shape rather than magnitude. Falling through to `continue`
        # here is what made a marker decoration; compare the text instead.
        # Containment in EITHER direction is the tolerant-but-real test: a
        # restatement legitimately carries surrounding context ("...=2|a'|^2
        # E_s/N_0 of §1.2"), and REF_RE may clip a long one, but a restatement
        # that dropped the |a'|^2 factor contains neither and is caught.
        w, g = norm(want), norm(shown)
        if w and g and w not in g and g not in w:
            errs.append((f, lineno, key,
                         f"restated as '{shown.strip()}' but declared "
                         f"'{want}' at {where}"))
    return decls, refs, errs


def survey_pass(files):
    """Advisory: numeric literals recurring across files with a shared context
    word but different values.

    Precision is the whole problem here.  A generic context word ('about',
    'above', 'error') co-occurs with dozens of unrelated quantities, so keying on
    it produces noise indistinguishable from signal.  The filter that works is
    *rarity*: a word appearing a handful of times corpus-wide and attached to two
    different values is a plausible restatement; a word appearing everywhere is
    not.  This still over-reports and is advisory for that reason.
    """
    freq = collections.Counter()
    for f in files:
        for _, ln in live_lines(f):
            for w in re.sub(r"<!--.*?-->", "", ln).split():
                w = w.lower().strip("*_`().,;:")
                if len(w) > 3 and w.isalpha():
                    freq[w] += 1
    idx = collections.defaultdict(set)
    for f in files:
        for lineno, ln in live_lines(f):
            plain = re.sub(r"<!--.*?-->", "", ln)
            for m in NUM_UNIT_RE.finditer(plain):
                lo = max(0, m.start() - 60)
                ctx = {w.lower().strip("*_`().,;:")
                       for w in plain[lo:m.start()].split()}
                ctx = {w for w in ctx
                       if len(w) > 3 and w not in STOP and w.isalpha()
                       and 2 <= freq[w] <= 12}   # rare enough to be distinctive
                for w in ctx:
                    idx[(w, m.group(2))].add((norm(m.group(1)), f.name, lineno))
    out = []
    for (word, unit), vals in sorted(idx.items()):
        distinct = {v[0] for v in vals}
        files_seen = {v[1] for v in vals}
        if len(distinct) > 1 and len(files_seen) > 1 and len(distinct) <= 3:
            out.append((word, unit, sorted(vals)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--survey", action="store_true")
    ap.add_argument("--severity", choices=["off", "warn", "error"])
    a = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parents[2]
    sev = load_severity(a.severity, root)
    if sev == "off":
        print("[value-ledger] off")
        return 0

    files = iter_md(a.paths)
    if not files:
        print("[value-ledger] refusing to report clean: no markdown in scope", file=sys.stderr)
        return 2

    decls, refs, errs = ledger_pass(files)
    for f, lineno, key, why in errs:
        print(f"{f}:{lineno}: [{'ERROR' if sev == 'error' else 'warn'}] "
              f"VALUE-DRIFT val:{key} -- {why}")

    if a.survey:
        cands = survey_pass(files)
        if cands:
            print(f"\n[value-ledger] {len(cands)} cross-file drift candidate(s) "
                  f"(advisory -- annotate the real ones with val: markers):")
            for word, unit, vals in cands[:40]:
                joined = ", ".join(f"{v}{unit} @{fn}:{ln}" for v, fn, ln in vals)
                print(f"  '{word}' + {unit}: {joined}")

    print(f"\n[value-ledger] {len(files)} file(s), {len(decls)} declared value(s), "
          f"{len(refs)} restatement(s), {len(errs)} drift error(s), severity={sev}")
    return 1 if (errs and sev == "error") else 0


if __name__ == "__main__":
    sys.exit(main())
