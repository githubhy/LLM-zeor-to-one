#!/usr/bin/env python3
"""check-citation-sources.py -- enforce the references.md <-> download/ invariant.

Every numbered reference entry in a references file must end with a source
tag declaring where the acquired source is:

    (local: download/<file>)    full text held in the repo
    (spec: docs/specs/<path>)   a standard held in the repo spec mirror
    (web)                       a live web resource (the citation is the page)
    (abstract-only)             full text genuinely not held

See `.claude/rules/citation-integrity.md` for the convention. This checker
flags any untagged reference entry and any `local:` / `spec:` tag whose file
is missing from disk -- an error of the same class as a `lint-math`
violation.

With `--identity` it additionally runs two ADVISORY (warn-only, never
error) checks that a presence check structurally cannot catch:

  * a weak IDENTITY check -- for each existing `local:`/`spec:` source it
    extracts the document's first-page text and warns when NONE of the
    entry's distinctive tokens (author surnames / title words) appear, i.e.
    the file on disk is probably the WRONG document (bug 2026-05-31-02: two
    subagent-acquired PDFs were the wrong documents under correct filenames);
  * an INVERSE-STALENESS check -- for each `(web)`/`(abstract-only)` weak
    entry it scans `download/` for a filename matching the entry's tokens and
    warns when a plausible file IS present, i.e. a held source is still
    under-tagged as not-held (the 2026-07-24 RMB / Goldsmith / Sesia
    recurrence, N=3).

Warnings never change the exit code; `--identity` is purely diagnostic.

Usage:
    python viewer/tools/check-citation-sources.py FILE [FILE ...] [--identity]

`--check` is accepted and ignored (the checker is always read-only), so the
tool can be invoked with the same flag convention as the renumber scripts.

Exit code 0 if every entry is tagged and every local:/spec: file exists; 1
if any error is found; 2 on a usage error.
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# repo root: <root>/viewer/tools/check-citation-sources.py -> parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]

# a reference entry is a top-level numbered list item. Two list styles are
# accepted: "12. Author, ..." (plain ordered list) and "[12] Author, ..."
# (bracket-numbered with a preceding <!-- bib:N --> marker).
ENTRY_RE = re.compile(r'^(?:(\d+)\.|\[(\d+)\])\s+(.*\S)\s*$')

# the source tag is the final parenthetical on the entry line
TAG_RE = re.compile(
    r'\((local|spec|web|abstract-only)\b\s*:?\s*([^)]*)\)\s*$'
)

KINDS = ('local', 'spec', 'web', 'abstract-only')

# words that appear in almost every citation and so carry no identity signal.
_STOPWORDS = {
    'the', 'and', 'for', 'under', 'with', 'from', 'into', 'over', 'its',
    'are', 'was', 'via', 'ieee', 'acm', 'transactions', 'transaction',
    'journal', 'proceedings', 'conference', 'symposium', 'workshop',
    'letters', 'magazine', 'volume', 'vol', 'no', 'pno', 'page', 'pages',
    'university', 'press', 'arxiv', 'technical', 'report', 'edition',
    'using', 'based', 'toward', 'towards', 'analysis', 'approach',
    'performance', 'evaluation', 'communications', 'communication',
    'language', 'models', 'model', 'neural', 'networks', 'network',
    'international', 'available',
}


_BOLD_LEAD_RE = re.compile(r'^\*\*(.+?)\*\*', re.S)
_TITLE_RE = re.compile(r'["“][^"”“]{6,}["”]')
_DOI_RE = re.compile(r'\b10\.\d{4,9}/\S+')
# standards numbering: IETF (RFC 8259), W3C/IETF drafts, IEEE (Std 754),
# ITU-T (Rec. P.863), and the archive IDs PMC/PMID.
_SPECNUM_RE = re.compile(
    r'\b(?:TR|TS|TP|RP|SP|S[1-6]|R[1-5])[\s‑-]?\d'
    r'|\bITU[\s‑-]?[TR]\b'
    r'|\bIEEE\s+Std\b'
    r'|\bPM(?:C|ID)\s?\d',
    re.I,
)
_URL_RE = re.compile(r'https?://\S+|\]\(\s*https?://')


def _has_author(body):
    """True if the entry's leading bold field names anybody at all.

    An entry opens '**Surname, A., and Other, B. (2019).**' or
    '**MCP Specification 2025-06-18.**'. Strip the parenthesised
    date and punctuation; what should remain is a name or an
    organisation. '**(2024).**' leaves nothing, which is the defect.
    Entries with no bold lead at all are left to the other checks.
    """
    m = _BOLD_LEAD_RE.match(body)
    if not m:
        return True                       # not this check's business
    lead = re.sub(r'\([^)]*\)', ' ', m.group(1))     # drop (2024), (NeurIPS, ...)
    lead = re.sub(r'[*_`]', ' ', lead)               # drop nested emphasis
    return re.search(r'[A-Za-z]{2,}', lead) is not None


def _has_identifier(body):
    """True if the entry names a document at all.

    A source tag records where a document is *held*; it does not record
    that the entry identifies one. An entry naming no title and no
    identifier points at nothing and can be neither acquired nor checked.

    SCOPE -- this check applies ONLY to the bold-lead citation style,
    `**Author (Year).** "Title." *Venue*.`, because that style itself
    declares a delimited author field followed by a delimited title
    field: a bold-lead entry with no title is a defect in the style's
    own terms. The corpus also uses a plain style,
    `[9] H. L. Van Trees, Detection, Estimation, and Modulation Theory,
    Wiley, 1971`, whose title carries no quotes and no italics and is
    separated from the author by nothing but a comma. There the title is
    not machine-locatable at all, so the check has no purchase and
    ABSTAINS rather than firing on 19 correctly-cited books (measured
    across the corpus, 2026-07-30). A gate that fires on correct input is
    worse than no gate.

    Within the bold-lead style, "names a document" is still generous --
    any ONE of these suffices:
      * a quoted title  -- "Some Paper Title"      (papers)
      * an italic title -- *Some Book Title*       (books, standards)
      * an identifier   -- arXiv / DOI / spec or Tdoc / standard number
      * a URL or markdown link                     (web-form entries)
    """
    lead = _BOLD_LEAD_RE.match(body)
    if not lead:
        return True                       # plain style -- not this check's business
    # The bold lead is the author/organisation field; a title inside it
    # would be a style error, so look for the title AFTER it.
    rest = body[lead.end():]
    italic = re.search(r'(?<!\*)\*(?!\*)([^*]{6,})\*(?!\*)|_([^_]{6,})_', rest)
    return bool(
        _TITLE_RE.search(body)
        or italic
        or _ARXIV_RE.search(body)
        or _DOI_RE.search(body)
        or _SPECNUM_RE.search(body)
        or _URL_RE.search(body)
    )


def _distinctive_tokens(body):
    """Capitalised alphabetic words (>=4 chars) from the head of an entry,
    minus venue/stopwords -- the author surnames + distinctive title words
    that a correct source's first page should contain."""
    # strip the trailing source tag + any [link] before tokenising
    head = TAG_RE.sub('', body)
    head = re.sub(r'\[[^\]]*\]\([^)]*\)', ' ', head)   # markdown links
    head = re.sub(r'\[[^\]]*\]', ' ', head)            # bare [http...] refs
    toks = []
    for w in re.findall(r"[A-Z][A-Za-zÀ-ɏ'’-]{3,}", head):
        lw = w.lower().strip("'’-")
        if lw and lw not in _STOPWORDS:
            toks.append(lw)
    # de-dup, preserve order
    seen = set()
    out = []
    for t in toks:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _author_tokens(body):
    """Tokens from the AUTHOR block only -- the text before the first title
    quote. Used for the inverse-staleness filename match so a shared TITLE word
    (e.g. 'learning') cannot collide with a title-first filename like
    `learning-to-link-milne-witten`; only a real author surname matches."""
    head = TAG_RE.sub('', body)
    head = re.sub(r'\[[^\]]*\]\([^)]*\)', ' ', head)
    head = re.sub(r'\[[^\]]*\]', ' ', head)
    author_block = re.split(r'["“”]', head, maxsplit=1)[0]
    out = []
    seen = set()
    for w in re.findall(r"[A-Z][A-Za-zÀ-ɏ'’-]{3,}", author_block):
        lw = w.lower().strip("'’-")
        if lw and lw not in _STOPWORDS and lw not in seen:
            seen.add(lw)
            out.append(lw)
    return out


_ARXIV_RE = re.compile(r'arxiv\s*:?\s*\d{4}\.\d{4,5}(v\d+)?', re.I)
_PAGES_RE = re.compile(r'\bpp?\.\s*\d+\s*[-\u2010-\u2015]\s*\d+')
_YEAR_RE = re.compile(r'\b(19[0-9]{2}|20[0-9]{2})\b')
# Years within this many of a declared year count as a match (draft /
# submission / reprint drift). Calibrated on the live corpus 2026-07-27.
_YEAR_TOL = 3


def _entry_years(body):
    """Years declared by a reference entry.

    arXiv identifiers (`arXiv:2009.05553`) and page ranges (`pp. 1990-2000`)
    are stripped first: both can present 4-digit runs that look like years and
    would otherwise make the check hunt for a year the document never claimed.
    An entry may legitimately declare more than one year -- a preprint posted
    one year and published the next -- and any single match is enough.
    """
    head = TAG_RE.sub('', body)
    head = _ARXIV_RE.sub(' ', head)
    head = _PAGES_RE.sub(' ', head)
    return {m.group(0) for m in _YEAR_RE.finditer(head)}


def _doc_years(doc):
    """Years appearing in the extracted head of the held document."""
    return {m.group(0) for m in _YEAR_RE.finditer(doc)} if doc else set()


def _entry_volume(body):
    """The volume number an entry declares, if any."""
    m = re.search(r'\bvol(?:ume)?\.?\s*(\d{1,4})\b', TAG_RE.sub('', body), re.I)
    return m.group(1) if m else None


def _doc_states_any_volume(doc):
    """Whether the document's head uses a `vol <number>` convention at all."""
    return re.search(r'\bvol(?:ume)?\.?\s*\d{1,4}\b', doc, re.I) is not None


def _doc_has_volume(doc, vol):
    """Whether the document's head carries `vol <n>` for the declared number.

    Matched only adjacent to a `vol`/`volume` keyword -- a bare integer occurs
    everywhere on a title page and would carry no signal.
    """
    return re.search(r'vol(?:ume)?\.?\s*' + re.escape(vol) + r'\b', doc, re.I) is not None


_EXTRACT_SKIPS = []


def _extract_doc_text(path, max_chars=20000):
    """Return up to max_chars of lowercased text from a source file, or None
    if it cannot be read. PDFs go through pdftotext (UTF-8, errors ignored --
    the Windows GBK-codec trap); text files (spec .txt/.md) are read directly.
    """
    p = Path(path)
    if not p.is_file():
        return None
    suffix = p.suffix.lower()
    if suffix not in ('.pdf', '.txt', '.md', '.tex'):
        return None   # .zip/.docx/... -- no cheap text extraction, skip the check
    if suffix == '.pdf':
        tmp = None
        try:
            fd, tmp = tempfile.mkstemp(suffix='.txt')
            os.close(fd)
            subprocess.run(
                ['pdftotext', '-enc', 'UTF-8', '-f', '1', '-l', '3',
                 str(p), tmp],
                timeout=60, check=False,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            data = Path(tmp).read_bytes()
        except FileNotFoundError:
            data = None   # pdftotext absent -> try the pymupdf fallback below
        except Exception:
            data = None
        finally:
            if tmp and os.path.exists(tmp):
                os.remove(tmp)
        if data:
            return data.decode('utf-8', 'ignore')[:max_chars].lower()
        # Fallback: pymupdf, so a container without poppler-utils still gets a
        # real check instead of a silent pass (see _EXTRACT_SKIPS below).
        try:
            import fitz
            doc = fitz.open(str(p))
            txt = ''.join(doc[i].get_text() for i in range(min(3, doc.page_count)))
            doc.close()
            return txt[:max_chars].lower() if txt.strip() else None
        except Exception:
            return None
    # non-PDF: read directly, tolerating encoding noise
    try:
        return p.read_text(encoding='utf-8', errors='ignore')[:max_chars].lower()
    except Exception:
        return None


_DOWNLOAD_CACHE = None
_DOWNLOAD_LEAD = None


def _download_names():
    """Lowercased filenames under download/ (cached)."""
    global _DOWNLOAD_CACHE
    if _DOWNLOAD_CACHE is None:
        d = REPO_ROOT / 'download'
        _DOWNLOAD_CACHE = (
            [f.name.lower() for f in d.iterdir() if f.is_file()]
            if d.is_dir() else []
        )
    return _DOWNLOAD_CACHE


def _download_lead_index():
    """{leading-token -> [filenames]} keyed on each download file's FIRST
    alphabetic token. The repo names sources `<first-author-surname>-<...>`,
    so the leading token is the first-author surname -- a precise identity
    key. Matching an entry's surname against this (rather than any shared
    common word against any substring) is what keeps the inverse-staleness
    check from firing on `attention` / `detection` collisions."""
    global _DOWNLOAD_LEAD
    if _DOWNLOAD_LEAD is None:
        idx = {}
        for n in _download_names():
            m = re.match(r'[^a-z]*([a-z]{4,})', n)   # first alpha run, >=4 chars
            if m:
                idx.setdefault(m.group(1), []).append(n)
        _DOWNLOAD_LEAD = idx
    return _DOWNLOAD_LEAD


_INDEX_PATHS = None


def _index_paths():
    """Repo-relative POSIX paths of every git-TRACKED file (memoized).

    Used by `--index` mode. Returns None if git is unavailable or errors, which
    callers treat as "fall back to the filesystem" -- never as "everything is
    missing" (a gate must not fail closed on a broken git invocation, nor pass
    silently; falling back to the on-disk check preserves the old behaviour)."""
    global _INDEX_PATHS
    if _INDEX_PATHS is None:
        try:
            out = subprocess.run(
                ['git', '-C', str(REPO_ROOT), 'ls-files', '-z'],
                capture_output=True, check=True, timeout=60,
            ).stdout.decode('utf-8', 'replace')
            _INDEX_PATHS = {p for p in out.split('\0') if p}
        except (OSError, subprocess.SubprocessError):
            _INDEX_PATHS = False          # sentinel: unavailable
    return _INDEX_PATHS or None


def _source_exists(arg, target, use_index):
    """Does the source a `local:`/`spec:` tag names actually exist?

    Default (filesystem): the path is a file in the working tree.

    `--index` (`use_index=True`): the path is TRACKED IN GIT. This is both the
    CI-compatible check -- validate.yml sparse-checkouts away the ~1 GB download/
    mirror, so the working tree has no PDFs to stat -- and the semantically
    stronger one: the references.md <-> download/ invariant is a property of the
    REPOSITORY, not of one clone's disk. An untracked local PDF satisfies the
    filesystem check while being missing for every other reader; index mode
    catches that. Falls back to the filesystem check if git is unavailable."""
    if use_index:
        idx = _index_paths()
        if idx is not None:
            return arg.replace('\\', '/').lstrip('./') in idx
    return target.is_file()


def check_file(path, do_identity=False, use_index=False):
    """Return (errors, warnings, counts) for one references file.

    errors:   list of (lineno, ref-number, message)   -- exit-code affecting
    warnings: list of (lineno, ref-number, message)   -- advisory only
    counts:   dict kind -> int for the tagged entries
    """
    errors = []
    warnings = []
    counts = {k: 0 for k in KINDS}
    text = Path(path).read_text(encoding='utf-8')
    for lineno, line in enumerate(text.splitlines(), 1):
        m = ENTRY_RE.match(line)
        if not m:
            continue
        num, body = (m.group(1) or m.group(2)), m.group(3)

        # --- IDENTITY-BEARING FIELDS -------------------------------------
        # Two pure-syntax checks that no other gate makes. Both were earned
        # from real defects in a multimodal survey (2026-07-30):
        #   * ref [54] read literally '**(2024).**' -- an empty author field --
        #     and carried a title matching no published work. The empty author
        #     alone would have flagged it.
        #   * ref [55] named neither a title nor any identifier, so it
        #     identified no document and could be neither acquired nor
        #     verified, yet it carried a valid (abstract-only) tag and passed.
        # A source tag says WHERE a document is held; these say WHETHER the
        # entry names a document at all. See
        # bugs/2026-07-30-ref54-title-matches-no-published-work.
        if not _has_author(body):
            errors.append(
                (lineno, num,
                 'author field is empty -- the entry names no author '
                 '(an entry beginning "**(YEAR).**" identifies nobody)')
            )
        if not _has_identifier(body):
            errors.append(
                (lineno, num,
                 'entry names neither a quoted title nor any identifier '
                 '(arXiv / DOI / spec or Tdoc number) -- it identifies no '
                 'document and cannot be acquired or verified')
            )

        tag = TAG_RE.search(body)
        if not tag:
            errors.append(
                (lineno, num,
                 'untagged -- no (local:/spec:/web/abstract-only) source tag')
            )
            continue
        kind, arg = tag.group(1), tag.group(2).strip()
        counts[kind] += 1
        if kind in ('local', 'spec'):
            if not arg:
                errors.append((lineno, num, f'{kind}: tag carries no path'))
                continue
            target = (REPO_ROOT / arg).resolve()
            if not _source_exists(arg, target, use_index):
                where = 'not tracked in git' if use_index else 'file not found'
                errors.append(
                    (lineno, num, f'{kind}: {where}: {arg}')
                )
                continue
            if do_identity:
                toks = _distinctive_tokens(body)
                doc = _extract_doc_text(target)
                if doc is None:
                    _EXTRACT_SKIPS.append(arg)
                if doc is not None and toks and not any(t in doc for t in toks):
                    warnings.append(
                        (lineno, num,
                         f'{kind}: IDENTITY -- none of the entry tokens '
                         f'{toks[:6]} appear in the first pages of {arg}; '
                         f'the held file may be the WRONG document')
                    )
                # Token presence needs the named and held works to be
                # lexically DISJOINT, so it is blind to the likeliest
                # mislabel of all: another work by the same author on the
                # same subject (bugs/2026-07-27-identity-check-blind-to-
                # same-author-mislabel -- a Gray 1990 entry tagged at the
                # Gray & Neuhoff 1998 paper passes every token). Year and
                # volume are already in the extracted text and DO separate
                # such a pair.
                if doc is not None:
                    # Tolerance, not equality. A held PDF very often carries a
                    # submission/received/draft year rather than the published
                    # one (Cooley-Tukey 1965 prints 1964; the Tse & Viswanath
                    # 2005 book circulates as a 2004 draft), so demanding an
                    # exact match produced a ~8% warn rate on the live corpus --
                    # noise, not signal. A mislabel that swaps one work for
                    # another by the same author is normally years apart, which
                    # this still catches; a swap inside the window is not
                    # detectable this way and is a stated limit of the check.
                    # `spec:` sources are formal specifications identified by
                    # spec name + VERSION, not by year: the cited year is the
                    # version's release date while the .txt head carries
                    # unrelated dates. A systematic false-positive class, so
                    # the year test does not apply to them.
                    e_years = _entry_years(body) if kind != 'spec' else set()
                    d_years = _doc_years(doc)
                    near = any(abs(int(e) - int(d)) <= _YEAR_TOL
                               for e in e_years for d in d_years)
                    if e_years and d_years and not near:
                        warnings.append(
                            (lineno, num,
                             f'{kind}: IDENTITY(year) -- entry declares '
                             f'{sorted(e_years)} but the first pages of {arg} '
                             f'carry {sorted(d_years)[:6]} (none within '
                             f'{_YEAR_TOL}y); the held file may be a DIFFERENT '
                             f'work by the same author')
                        )
                    vol = _entry_volume(body)
                    # Only meaningful if the document uses a `vol <n>`
                    # convention AT ALL. A substring test for 'vol' matches
                    # "revolution"; and venues like MDPI print no volume
                    # keyword, while a glyph-mangled scan can render the
                    # number unreadable. In both cases absence is a property
                    # of the document, not evidence of a mislabel.
                    if vol and _doc_states_any_volume(doc) and not _doc_has_volume(doc, vol):
                        warnings.append(
                            (lineno, num,
                             f'{kind}: IDENTITY(volume) -- entry declares vol. '
                             f'{vol}, not found in the first pages of {arg}')
                        )
        elif do_identity and kind in ('web', 'abstract-only'):
            toks = {t for t in _author_tokens(body) if len(t) >= 4}
            lead = _download_lead_index()
            hits = []
            for t in toks:
                hits.extend(lead.get(t, []))
            if hits:
                warnings.append(
                    (lineno, num,
                     f'{kind}: INVERSE-STALENESS -- a download/ file is named '
                     f'for an author of this entry ({sorted(set(hits))[:2]}); '
                     f'it may be a held source still tagged not-held -- verify '
                     f'+ upgrade to (local:)')
                )
    return errors, warnings, counts


def main(argv):
    do_identity = '--identity' in argv
    use_index = '--index' in argv
    files = [a for a in argv[1:] if not a.startswith('--')]
    if not files:
        print('usage: check-citation-sources.py FILE [FILE ...] [--identity] [--index]',
              file=sys.stderr)
        return 2

    total_err = 0
    total_warn = 0
    total_entries = 0
    for f in files:
        errors, warnings, counts = check_file(f, do_identity=do_identity, use_index=use_index)
        tagged = sum(counts.values())
        n = tagged + len([e for e in errors if 'untagged' in e[2]])
        total_entries += n
        total_err += len(errors)
        total_warn += len(warnings)
        for lineno, num, msg in errors:
            print(f'{f}:{lineno}: ERROR: [{num}] {msg}')
        for lineno, num, msg in warnings:
            print(f'{f}:{lineno}: WARN: [{num}] {msg}')
        strong = counts['local'] + counts['spec']
        weak = counts['web'] + counts['abstract-only']
        print(
            f'{f}: {n} entries -- '
            f'{strong} strong (local {counts["local"]} / spec {counts["spec"]}), '
            f'{weak} weak (web {counts["web"]} / abstract-only {counts["abstract-only"]}), '
            f'{len(errors)} error(s)'
            + (f', {len(warnings)} warn(s)' if do_identity else '')
        )

    print(f'\n{len(files)} file(s) scanned, {total_entries} entries, '
          f'{total_err} error(s)'
          + (f', {total_warn} warn(s)' if do_identity else ''))
    if do_identity and _EXTRACT_SKIPS:
        # Coverage is never silent: a source whose text could not be extracted
        # was NOT checked, and a run that says nothing about it would let
        # "did not look" read exactly like "looked and found nothing".
        uniq = sorted(set(_EXTRACT_SKIPS))
        print(f'NOTE: identity check could not read {len(uniq)} source(s) -- '
              f'NOT verified: {uniq[:4]}{" ..." if len(uniq) > 4 else ""}')
        print('      (install poppler-utils for pdftotext, or `pip install pymupdf`)')
    return 1 if total_err else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
