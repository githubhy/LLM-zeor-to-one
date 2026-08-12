#!/usr/bin/env python3
"""normalize-survey.py — the write-mode twin of check-survey.

check-survey.py *verifies* a survey's marker/anchor discipline (all `--check`);
this script *applies* it: it runs the renumber/link tools in the one correct
order, with the hard-won exceptions baked in, then runs the check suite and
reports. It exists because the fix-order is non-obvious and was, until now, a
per-survey gotcha reinvented by hand (53+ field-notes/bugs mention the
renumber/marker friction; the marker post-pass was reinvented ad hoc on the
2026-07-04 channel-estimation survey — see .claude/skill-options.json `SX-INIT`).

Order (each step feeds the next):
  1. renumber-sections <dir> --init   inject sec anchors + resolve/convert every
                                       BARE same-survey §X.Y to secref (same-file)
                                       or secxref (cross-file, via order.json).
  2. renumber-equations <file>         sequential \\tag{N} + eq anchors, per file.
  3. renumber-paragraphs <file> --init para anchors — SKIPPING references.md
                                       (init injects an inline anchor that pushes
                                       `[N]` off column 0 and breaks
                                       check-citation-sources; gotcha, deep-research-survey).
  4. link-references <file>            sync existing cite/bib markers (NO --init:
                                       --init is a one-time plain-[N]→marked
                                       migration, a citation-STYLE choice this
                                       tool must not force; pass --cite-init to opt in).
  5. check suite                       renumber --check (all), validate-refs,
                                       bare-refs --severity=error, check-citation-sources.

Cross-survey guard: any BARE §X.Y that survives step 1 points to a section NOT in
this survey (a different survey or an external spec) — renumber-sections can't
resolve it. Those are reported as `SX-DEGLYPH` candidates: de-glyph to a plain
relative link (different survey) or bracket-wrap (external spec); never leave bare.

Usage:
  normalize-survey.py <survey-dir> [--check-only] [--cite-init] [--quiet]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

# This script prints U+2713/U+2717/U+2192. On a Windows console defaulting to
# gbk/cp936 those raise UnicodeEncodeError *while reporting the result*, so a
# clean run dies at the summary line. Force utf-8 and degrade instead of raising.
# Must sit AFTER `import sys`, or the NameError is swallowed and this is dead code.
for _stream in ("stdout", "stderr"):
    try:
        getattr(sys, _stream).reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - a non-reconfigurable stream is fine
        pass

TOOLS = Path(__file__).resolve().parent


def _h(p: Path):
    try:
        return hashlib.sha1(p.read_bytes()).hexdigest()
    except OSError:
        return None


def _snap(files):
    return {p: _h(p) for p in files}


def _changed(before, files):
    """Return the list of files whose content changed vs the `before` snapshot."""
    return [p for p in files if _h(p) != before.get(p)]


def run(tool, *args, capture=True):
    # `text=True` alone decodes with the LOCALE codec (gbk on a zh Windows box),
    # and every check tool prints U+2713/U+2717. The decode then raises inside
    # subprocess.run, the exception is caught upstream, and the step is reported
    # as an ERROR that never happened. Pin utf-8 and never fail on a stray byte.
    # Same genus as bugs/2026-07-09-12 (read_text() without encoding).
    cmd = [sys.executable, str(TOOLS / tool), *args]
    r = subprocess.run(cmd, capture_output=capture, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def did_not_run(rc, out):
    """Return a reason string if a write-phase tool DID NOT RUN, else None.

    See `run_write` for the full rationale. Module-level and pure so the
    predicate is unit-testable without driving a whole survey:
    viewer/tools/test_normalize_survey_write_gate.py.

      rc == 0        -> ran fine
      rc == 1        -> ABSTAIN: a content-level signal these tools emit
                        routinely and benignly (every chapter file makes
                        link-references exit 1, "references section not found")
      rc >= 2        -> usage / environment error: the tool did not run
      traceback      -> crashed part-way through, at any exit code
    """
    if "Traceback (most recent call last)" in (out or ""):
        return "crashed"
    if rc >= 2:
        return f"exited {rc}"
    return None


def survey_files(d: Path):
    """File list from order.json if present, else *.md (excluding _scratch)."""
    order = d / "order.json"
    if order.is_file():
        try:
            names = json.loads(order.read_text())
            return [d / n for n in names if (d / n).is_file()]
        except Exception:
            pass
    return sorted(p for p in d.glob("*.md") if "_scratch" not in p.parts)


def main():
    ap = argparse.ArgumentParser(description="Normalize (write-mode) a survey's markers/anchors, then check.")
    ap.add_argument("dir", help="survey directory (containing order.json / *.md)")
    ap.add_argument("--check-only", action="store_true", help="skip the write steps; run only the check suite")
    ap.add_argument("--cite-init", action="store_true", help="also run link-references --init (plain-[N] → marked citation migration)")
    ap.add_argument("--quiet", action="store_true", help="only print the final summary + any errors")
    a = ap.parse_args()

    d = Path(a.dir)
    if not d.is_dir():
        print(f"error: {d} is not a directory", file=sys.stderr)
        return 2
    files = survey_files(d)
    if not files:
        print(f"error: no .md files found under {d}", file=sys.stderr)
        return 2

    def say(*x):
        if not a.quiet:
            print(*x)

    say(f"normalize-survey: {d}  ({len(files)} files)")
    changed = []
    write_failures = []

    def run_write(tool, *args):
        """Run a write-phase tool; record a DID-NOT-RUN exit as a hard failure.

        Change detection below is content-hash based, which is the right way to
        tell whether a tool EDITED anything -- but it cannot tell "nothing needed
        changing" apart from "the tool never ran". A write tool that dies on a
        missing dependency makes no change, so its exit status is the ONLY signal
        that the step was skipped.

        bugs/2026-08-02-normalize-survey-ignores-write-step-exit-codes: with
        markdown-it-py absent, renumber-paragraphs exits 2 without anchoring a
        single paragraph, and this driver reported "0 changed" then
        "RESULT: CLEAN" -- certifying 21 unanchored files as normalized.

        SCOPE -- why this is not `rc != 0`. In the write phase, exit 1 is a
        CONTENT-level signal these tools emit routinely and benignly: every
        chapter file makes link-references exit 1 with "references section not
        found", because only references.md has one. Treating rc != 0 as failure
        makes this driver report NOT CLEAN on every survey in the corpus -- a
        gate that fires on correct input, which is worse than no gate (the
        `_has_identifier` lesson, field-notes/2026-07-31-blind-gates.md).

        So the check abstains on exit 1 and fires only on the two states that
        unambiguously mean the tool did not do its job:
          * exit >= 2  -- usage / environment error (the repo-wide convention;
            renumber-paragraphs' ImportError is the only current instance)
          * a traceback in the output -- crashed part-way through

        KNOWN RESIDUAL: a tool that fails by exiting 1 with a clean message,
        indistinguishable from the benign case, is still not caught here. Fixing
        that needs distinct exit codes in the tools themselves, not a smarter
        predicate in the driver.
        """
        rc, out = run(tool, *args)
        why = did_not_run(rc, out)
        if why:
            tail = out.strip().splitlines()[-1] if out.strip() else "(no output)"
            write_failures.append(f"{tool} {why}: {tail}")
        return rc, out

    if not a.check_only:
        # change detection is content-hash based (accurate regardless of a tool's
        # stdout wording — e.g. re-slugging a paragraph anchor after a heading edit).
        # 1. sections (directory-level; resolves cross-file secxref via order.json)
        b = _snap(files)
        run_write("renumber-sections.py", str(d), "--init")
        c = _changed(b, files)
        if c:
            changed.append(f"sections: {len(c)} file(s) → {', '.join(p.name for p in c)}")
        say(f"  [1/5] renumber-sections --init      → {len(c)} changed")

        # 2. equations (per file)
        b = _snap(files)
        for f in files:
            run_write("renumber-equations.py", str(f))
        c = _changed(b, files)
        if c:
            changed.append(f"equations: {len(c)} file(s) → {', '.join(p.name for p in c)}")
        say(f"  [2/5] renumber-equations             → {len(c)} changed")

        # 3. paragraphs (per file, SKIP references.md — see module docstring)
        para_files = [f for f in files if f.name != "references.md"]
        b = _snap(para_files)
        for f in para_files:
            run_write("renumber-paragraphs.py", str(f), "--init")
        c = _changed(b, para_files)
        if c:
            changed.append(f"paragraphs: {len(c)} file(s) → {', '.join(p.name for p in c)}")
        say(f"  [3/5] renumber-paragraphs --init     → {len(c)} changed (references.md skipped)")

        # 4. link-references (sync-only unless --cite-init)
        lr_args = ["--init"] if a.cite_init else []
        b = _snap(files)
        for f in files:
            run_write("link-references.py", str(f), *lr_args)
        c = _changed(b, files)
        if c:
            changed.append(f"references/citations: {len(c)} file(s) → {', '.join(p.name for p in c)}")
        say(f"  [4/5] link-references {'--init' if a.cite_init else '(sync)'}"
            f"{'          ' if a.cite_init else '        '} → {len(c)} changed")
    else:
        say("  (--check-only: write steps skipped)")

    # 5. check suite
    say("  [5/5] check suite:")
    errors = []
    warns = []

    # A write step that never ran cannot have normalized anything -- surface it
    # BEFORE the checks, so a green check suite can never mask a skipped write.
    for f in dict.fromkeys(write_failures):
        errors.append(f"write step did not run -- {f}")

    rc, out = run("lint-math.py", str(d))
    tail = out.strip().splitlines()[-1] if out.strip() else ""
    say(f"        lint-math            {tail}")
    if "error" in tail and not tail.strip().startswith("0") and " 0 error" not in tail:
        errors.append("lint-math: " + tail)

    rc, out = run("validate-refs.py", str(d))
    ok = "0 error(s)" in out
    say(f"        validate-refs        {'OK' if ok else 'ERRORS'}")
    if not ok:
        errors.append("validate-refs: see `validate-refs.py " + str(d) + "`")

    rc, out = run("validate-refs.py", "--bare-refs-only", "--severity=error", str(d))
    bare = [ln for ln in out.splitlines() if "ERROR" in ln and "section-ref" in ln]
    say(f"        bare-refs (error)    {len(bare)} remaining")
    for ln in bare:
        # a bare §X.Y that survived --init is cross-survey or external → SX-DEGLYPH
        warns.append("SX-DEGLYPH candidate (de-glyph or bracket-wrap): " + ln.strip())
    if bare:
        errors.append(f"{len(bare)} bare section-ref(s) unresolved — see SX-DEGLYPH candidates below")

    ref = d / "references.md"
    if ref.is_file():
        rc, out = run("check-citation-sources.py", str(ref))
        tail = out.strip().splitlines()[-1] if out.strip() else ""
        say(f"        citation-sources     {tail}")
        if "error(s)" in tail and " 0 error" not in tail:
            errors.append("check-citation-sources: " + tail)

    # summary
    print()
    if changed and not a.check_only:
        print("changed:")
        for c in changed:
            print(f"  - {c}")
    if warns:
        print("SX-DEGLYPH candidates (bare §X.Y that --init could not resolve = cross-survey/external):")
        for w in warns:
            print(f"  ! {w}")
        print("  → de-glyph to a plain relative link (different survey) or bracket-wrap `[TS ... §X.Y]` (external spec).")
    if errors:
        print("RESULT: NOT CLEAN — fix:")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print("RESULT: CLEAN — survey normalized and all gates pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
