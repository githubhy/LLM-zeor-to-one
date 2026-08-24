#!/usr/bin/env python3
"""Forbidden-phrasing gate — enforces .claude/rules/calibration-residuals.md.

That rule shipped with NO gate: a document on the honour system.
Nothing stopped the next session writing "brackets the reference". This is the
missing enforcement.

REPO-WIDE by design, not campaign-scoped. The rule is domain-agnostic — a
dishonest attribution is dishonest whether or not it lives inside a campaign. It
fired in five unrelated domains upstream before the rule was written, which is why it
is scoped repo-wide here rather than to any one survey.

What it flags: a forbidden phrasing used to ASSERT AGREEMENT with an external
reference. The check is deliberately narrow — it fires only when a forbidden
phrase sits near reference/residual vocabulary, because "matches" is a perfectly
good English word and a linter that cries wolf gets bypassed.

  "brackets the reference"      -> closes X of the Y gap at the representative
                                   point; Z remains
  "agrees with" / "matches"     -> the signed delta, the percentage, and the CI
  "qualitative match"           -> a numeric gate, or "not yet gated - lead only"
  "confirmed" (positive attrib) -> "partial root-cause - dominant driver is X;
                                   residual UNCLOSED"

Escape hatch: append  <!-- phrasing-ok: <reason> -->  on the same line. It is
recorded, greppable, and a reviewer can audit every one.

Severity: .claude/campaign-phrasing-severity (off|warn|error, default warn).
Rolls out warn -> error exactly like bare-refs and crosslink.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEV_FILE = ROOT / ".claude/campaign-phrasing-severity"
DEFAULT_SCAN = ["reports", "docs", "surveys", "campaigns", "wikis"]

# The forbidden phrasings, from the rule's own table.
#
# BOUNDED-GAP MATCHING, and why. The first draft of this gate MISSED the single most
# important phrase in its own history — "bracketing the 195 ns reference", an upstream
# headline overclaim that shipped and had to be retracted. Two reasons: the gerund
# ("bracketing", not "brackets"), and the intervening "195 ns" between "the" and
# "reference". A positive-control test caught it. So every pattern is now
# <claim-verb> ... up to GAP non-sentence chars ... <reference-noun>.
REFNOUN = (r"(reference|ref\b|curve|target|published|anchor|baseline|leaderboard|"
           r"model[-\s]?card|paper|benchmark)")
GAP = r"[^.;!?\n]{0,45}?"   # stay inside one sentence

PATTERNS = [
    (re.compile(rf"\bbracket(s|ed|ing)?\b{GAP}\b{REFNOUN}", re.I),
     "PH-BRACKET",
     'state how much of the gap the cause closes at the representative operating point, and what remains'),
    (re.compile(r"\bqualitativ(e|ely)\s+(match|agree|consistent|agreement)", re.I),
     "PH-QUALITATIVE",
     'a "qualitative match" is a misread waiting to happen — give a numeric gate, or call it a LEAD'),
    (re.compile(rf"\b(agrees?|agreement|agreeing)\b{GAP}\b{REFNOUN}", re.I),
     "PH-AGREES", "give the signed delta, the percentage, and the CI"),
    (re.compile(rf"\b(matches|matching|is\s+close\s+to|closely\s+match\w*|in\s+line\s+with)\b{GAP}\b{REFNOUN}", re.I),
     "PH-MATCHES", "give the signed delta, the percentage, and the CI"),
    (re.compile(r"\bresidual\s+is\s+confirmed\b|\bconfirm(s|ed|ing)?\s+(the\s+)?(attribution|root[- ]cause)", re.I),
     "PH-CONFIRMED",
     'for a positive attribution write "partial root-cause — dominant driver is X; residual UNCLOSED"'),
    # `.claude/rules/calibration-residuals.md`'s forbidden table lists "X under-performs Y"
    # and the gate long had no pattern for it. The upstream instance: an independent
    # implementation described as "under-realizing" the reference, carried with a flattering-
    # range delta, caught only by an adversarial panel.
    #
    # The verb PRESUMES the reference is right and the sim is deficient, which is the arbitration
    # check 4 forbids: a lower value can be a metric-basis difference, not an under-realization.
    (re.compile(r"\b(under|over)[- ]realiz(e|es|ed|ing|ation)\b", re.I),
     "PH-REALIZES",
     'names a verdict the comparison has not earned — a low value may be a metric-basis difference; '
     'write "the X-vs-Y gap is partly a basis difference; the reference aligns with the ... basis"'),
]
# Only fire near reference/residual vocabulary — a narrow gate is a gate people keep.
CONTEXT = re.compile(
    r"\b(residual|reference|calibrat|baseline|benchmark|harness|leaderboard|"
    r"reproduc|envelope|attribut|root[- ]cause|gap)\b", re.I)
OK_RE = re.compile(r"<!--\s*phrasing-ok:", re.I)
FENCE_RE = re.compile(r"^\s*(```|~~~)")

# Idioms that collide with the patterns but are not agreement claims. Measured, not
# guessed: the first corpus run scored ~40% precision, and a gate people learn to
# ignore has stopped gating (cf. todos/2026-07-10-lint-gates-scan-scratch-evidence-ledgers).
#   - "exact match" / "string|fuzzy|pattern matching" : core EVAL-SCORING terms, not claims
#   - "Bracketed reference"                : the BARE-REF LINT syntax, not a claim
#   - "inter-annotator/inter-rater agreement" : a metric name, not an agreement claim
#   - matches-…/matching-…                 : hyphenated anchors + HTML comments
EXCLUDE_LINE = re.compile(
    r"exact[-\s]?match|(string|fuzzy|pattern|substring|regex|bipartite)[-\s]?match\w*|"
    r"matching\s+scheme|bracket(ed|ing)?\s+(syntax|form|ref\b)|"
    r"bracketed\s+reference|inter[-\s]?(annotator|rater)|<!--|-->|"
    r"match(es|ing)-|agreement\s+(wording|text|reached|rate|score)|"
    # Named terms and non-measurement senses. Upstream measured these on a triage of 19
    # standing findings, 15 of which were false; the LLM-domain equivalents are:
    #   "matching no published"   -> a CITATION TITLE that matches nothing, not a measurement
    #   "pinned to a matching (revision|checkpoint|commit)" -> traceability, not agreement
    #   "matches the gold/reference answer" -> EXACT-MATCH SCORING, a scorer's rule
    r"matching\s+no\s+published|pinned\s+to\s+a\s+matching|"
    r"a\s+matching\s+(revision|checkpoint|commit|config)|"
    r"match\w*\s+the\s+(gold|reference|target|expected)\s+"
    r"(answer|completion|string|output|label)", re.I)

# A claim that ALREADY CARRIES ITS TOLERANCE is the honest form the rule asks for, so
# firing on it trains the reader to ignore the gate. The discriminator is a TOLERANCE
# PREPOSITION before the quantity -- not the mere presence of a number.
#
# That distinction is load-bearing and nearly went the other way: "bracketing the 195 ns
# reference" -- the overclaim this whole gate exists for -- CONTAINS a number and a unit.
# Suppressing on "a number appears nearby" would have silenced the gate's own positive
# control. "matches the reference within 0.4 points (CI <= 0.2)" states a delta; "bracketing
# the 195 ns reference" states the reference's value and no delta at all.
QUANTIFIED = re.compile(
    r"(within|to\s+within|by|of)\s*[\u00b1+-]?\s*\d"      # "to within 0.4 points"
    r"|[\u00b1]\s*\d|\bCI\b|\bci95\b|\d\s*(%|percent)"   # "+-0.3", "CI", "4 %"
    r"|\d\s*e\s*[+-]?\s*\d"                              # "1e-9", "0.00e+00"
    r"|machine\s+epsilon|bit-exact|byte-identical|\bEXACT\b",  # exactness IS a tolerance
    re.I)

# A gap that crosses a contrastive conjunction has left the claim and joined the next one.
# Measured: "The local file content matches the topic but the references.md ..." was read as
# "matches ... the reference", which is two unrelated clauses stitched together.
GAP_BREAK = re.compile(r"\b(but|however|whereas|although|though)\b", re.I)

# "matching arXiv:2203.15556" names a DOCUMENT, not a measurement -- there is no delta to
# state because nothing numeric was compared. Same for a DOI, a model revision, or a
# harness release tag.
TDOC_REF = re.compile(
    r"\barxiv:\s*\d{4}\.\d{4,5}|\bdoi:\s*10\.\d{4,9}/|"
    r"\bv\d+\.\d+(\.\d+)?\b|\b[0-9a-f]{7,40}\b", re.I)

# A claim inside ~~strikethrough~~ is a claim the document has WITHDRAWN. Two of the 19 were
# reports correctly recording their own retraction, in the exact words the rule forbids --
# which is the behaviour the rule wants, flagged as if it were the violation.
STRIKE = re.compile(r"~~.+?~~", re.S)
# A sentence terminator is followed by whitespace or end-of-line -- otherwise the "."
# in "TS 38.212" or "V19.3" splits a sentence and truncates the tolerance window.
SENT_END = re.compile(r"[.!?](?=\s|$)")

# A markdown TABLE HEADER is a column label, not a claim: "| W | modulus | BER | agreement
# with the float reference |" names what the column holds; the numbers are in the rows
# below it, which is the honest form. Detected structurally -- the next line is the
# |---|---| separator -- rather than by guessing at the text.
TABLE_SEP = re.compile(r"^\s*\|[\s:|-]+\|\s*$")

# Directories whose prose is not a claim surface: agent evidence ledgers, archived
# copies, and the design specs that necessarily QUOTE the forbidden forms.
SKIP_DIRS = ("_scratch/", "surveys/archive/", "docs/superpowers/")


def severity() -> str:
    if SEV_FILE.exists():
        s = SEV_FILE.read_text(encoding="utf-8").strip()
        if s in ("off", "warn", "error"):
            return s
    return "warn"


def scan_file(p: Path) -> list[tuple[int, str, str, str]]:
    out = []
    in_fence = False
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return out
    for i, line in enumerate(lines, 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or OK_RE.search(line):
            continue
        if EXCLUDE_LINE.search(line):
            continue
        # The rule file itself and this tool's own docs quote the forbidden forms.
        if not CONTEXT.search(line):
            continue
        # A markdown table HEADER row (next line is the |---| separator) labels a column.
        if line.lstrip().startswith("|") and i < len(lines) and TABLE_SEP.match(lines[i]):
            continue
        # A withdrawn claim is not a live one. Blank the strikethrough so the surrounding
        # prose is still scanned.
        probe = STRIKE.sub(lambda mm: " " * len(mm.group(0)), line)
        for rx, code, fix in PATTERNS:
            m = rx.search(probe)
            if not m:
                continue
            span = m.group(0)
            if GAP_BREAK.search(span):
                continue          # the match crossed into the next clause
            if TDOC_REF.search(probe[m.start():m.end() + 12]):
                continue          # "matching arXiv:2203.15556" -- a doc id, not a measurement
            # Does the sentence CONTAINING the match state its tolerance? BOTH directions:
            # "equivalence tests (1e-9...1e-12; n_iter EXACT), and the (R,Z) grid matching
            # the reference goldens" puts the tolerance BEFORE the claim, and a
            # forward-only scan called that a violation. The bound is the sentence, not the
            # line: a later sentence's number says nothing about this claim.
            head = probe[:m.start()]
            cut = max((m2.start() for m2 in SENT_END.finditer(head)), default=-1)
            if cut >= 0:
                head = head[cut + 1:]
            else:
                # The sentence STARTED on an earlier line. Markdown soft-wraps, so a
                # line-bounded scan reads a wrapped sentence as if it began mid-clause
                # and misses a tolerance stated a line or two up. Walk back through the
                # same paragraph (blank line / fence ends it) to the previous terminator.
                prefix = []
                j = i - 2                       # 0-based index of the preceding line
                while j >= 0 and len(prefix) < 6:
                    prev = lines[j]
                    if not prev.strip() or FENCE_RE.match(prev):
                        break
                    prev = STRIKE.sub(lambda mm: " " * len(mm.group(0)), prev)
                    k = max((m2.start() for m2 in SENT_END.finditer(prev)), default=-1)
                    if k >= 0:
                        prefix.append(prev[k + 1:])
                        break
                    prefix.append(prev)
                    j -= 1
                head = " ".join(reversed(prefix)) + " " + head
            tail = probe[m.start():]
            end = SENT_END.search(tail)
            sentence = head + (tail[:end.start()] if end else tail)
            if QUANTIFIED.search(sentence):
                continue          # already in the honest form the rule asks for
            out.append((i, code, span.strip(), fix))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Forbidden-phrasing gate (calibration-residuals rule).")
    ap.add_argument("paths", nargs="*", help=f"default: {' '.join(DEFAULT_SCAN)}")
    ap.add_argument("--severity", choices=("off", "warn", "error"))
    a = ap.parse_args()

    sev = a.severity or severity()
    if sev == "off":
        print("[phrasing] off")
        return 0

    targets = [ROOT / p for p in (a.paths or DEFAULT_SCAN)]
    files: list[Path] = []
    for t in targets:
        if t.is_file() and t.suffix == ".md":
            files.append(t)
        elif t.is_dir():
            files.extend(sorted(t.rglob("*.md")))

    # The rule and its own tests legitimately quote every forbidden form.
    skip = {ROOT / ".claude/rules/calibration-residuals.md"}
    files = [f for f in files if f not in skip]
    if not a.paths:  # only prune on a corpus scan; an explicit path is always honoured
        files = [f for f in files if not any(d in str(f) for d in SKIP_DIRS)]

    hits = 0
    for f in files:
        for ln, code, frag, fix in scan_file(f):
            hits += 1
            try:
                rel = f.relative_to(ROOT)
            except ValueError:  # a path outside the repo (ad-hoc scan / self-test)
                rel = f
            print(f"[phrasing] {code} {rel}:{ln}\n            {frag!r} — {fix}")

    if not hits:
        print(f"[phrasing] clean — {len(files)} file(s)")
        return 0

    print(f"[phrasing] {hits} finding(s) in {len(files)} file(s) "
          f"(escape hatch: `<!-- phrasing-ok: reason -->`)")
    if sev == "error":
        return 1
    print("[phrasing] advisory (severity=warn) — not blocking")
    return 0


if __name__ == "__main__":
    sys.exit(main())
