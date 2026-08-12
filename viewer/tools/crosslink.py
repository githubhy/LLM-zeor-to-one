#!/usr/bin/env python3
"""crosslink.py — cheap, pre-filtered cross-link proposer for the survey corpus.

Motivation
----------
The 2026-06-23 cross-link sweep cost ~11.5M tokens / 217 sonnet agents to
land 131 links (~87k tokens/link) because it handed *candidate discovery*,
*judgment*, AND *application* all to agents — and the apply agents silently
failed to persist on the stricter files (field-notes/2026-06-23-workflow-apply-
persistence.md). Three of those four jobs are deterministic. This tool does the
deterministic 90% in code and reserves the model for the irreducible semantic
judgment, on a pre-filtered shortlist, in batches.

The cheap pipeline (≈20-40x fewer tokens for the same links):

    1. extract     (code)  parse every section: heading, body, existing links
    2. candidates  (code)  TF-IDF cosine pre-filter -> ranked shortlist, with
                           link syntax + dedup key precomputed, grouped into
                           small agent batches
    3. <judge>     (agent) ONE batched agent per ~15 candidates returns only
                           {id -> keep, anchor_phrase, confidence}. Link syntax
                           and dedup are NOT the agent's job.
    4. apply       (code)  idempotent normalize-with-map insertion of approved
                           links; verify against the filesystem, then lint.

Stages 1, 2, 4 are this script. Stage 3 is a tiny workflow (see the
`viewer/tools/crosslink.README.md` driver). The agent only ever sees short
snippets and returns a few tokens per candidate.

Link convention (keyed on the TARGET's corpus, matching the existing 131 links):
  * target is a survey section  -> secxref marker + § glyph:
        <!-- secxref:D.3.1 -->[§D.3.1](appendix-d.md#sec-D.3.1)
  * target is a wiki section     -> plain relative link, descriptive text, no §:
        [softmax derivation](../../wikis/foo.md#sec-4)

Pure stdlib. Corpus is inferred from path (surveys/** -> survey, wikis/** ->
wiki). Anchors are the canonical `sec-<num>` scheme shared by both corpora.

Usage
-----
    python viewer/tools/crosslink.py extract \
        surveys/llms-for-coding wikis/llr-preprocessing-factor-space.md ... \
        --out temp/xlink-index.json

    python viewer/tools/crosslink.py candidates \
        --index temp/xlink-index.json --out temp/xlink-cands.json \
        --per-source 3 --max-candidates 60 --min-score 0.10 --batch 15

    # (run the batched judge agent over temp/xlink-cands.json -> decisions.json)

    python viewer/tools/crosslink.py apply \
        --candidates temp/xlink-cands.json --decisions temp/xlink-dec.json \
        [--dry-run]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import posixpath
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path as _Path

# mdctx — the shared "which bytes may I rewrite?" map. `apply` once inserted a link
# *inside* an inline `$...$` span (llms-for-coding/implementation.md:399, commit 035dcd70),
# a live KaTeX parse error. Insertion points are now nudged out of math/code/links,
# and refused inside fences, HTML comments and frontmatter.
_MDCTX_SPEC = importlib.util.spec_from_file_location(
    "mdctx", _Path(__file__).parent / "mdctx.py")
mdctx = importlib.util.module_from_spec(_MDCTX_SPEC)
_MDCTX_SPEC.loader.exec_module(mdctx)
from pathlib import Path
from typing import NamedTuple

# UTF-8 stdout/stderr guard (the § glyph etc. must not crash on a non-UTF-8
# console/pipe — GBK/CP936 crash class, bug 2026-06-22-01). Mirrors
# renumber-sections.py / validate-refs.py.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# -- Canonical patterns (mirrors viewer/tools/renumber-sections.py) ----------

# The section-number grammar lives in exactly one place. Hand-copying it is what
# produced bugs/2026-07-09-13 (this module's copy was dotted-only, so flat-numbered
# wikis yielded ZERO sections and `check` printed a false "no gaps") and -04
# (renumber-sections' copies were dotted-only, so 131 flat secxref markers were
# never validated — 35 of them dead links). See viewer/tools/heading_grammar.py.
#
# Loaded by path: this module is itself loaded by path from the tests, and the
# tools directory is not a package.
_HG_SPEC = importlib.util.spec_from_file_location(
    "heading_grammar", Path(__file__).with_name("heading_grammar.py")
)
heading_grammar = importlib.util.module_from_spec(_HG_SPEC)
_HG_SPEC.loader.exec_module(heading_grammar)

match_heading = heading_grammar.match_heading
SEC_ANCHOR_RE = heading_grammar.SEC_ANCHOR_RE
HEADING_RE = heading_grammar.HEADING_RE

LINK_TARGET_RE = re.compile(r"\]\(([^)]+)\)")
FENCE_RE = re.compile(r"^\s*```")


SKIP_BASENAMES = {"index.md", "references.md"}


_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def resolve_target(src_dir: str, fpart: str) -> str:
    """Resolve a markdown link's file part against the SOURCE file's directory.

    Returns a repo-relative, forward-slashed, normalized path -- the identity key for a
    file. `../../wikis/foo.md` from `surveys/a/b.md` becomes `wikis/foo.md`.

    An absolute URL (`https://...`) or an absolute path is returned unchanged: it can
    never match a corpus section, which is the correct outcome. Returning the basename
    instead -- what this code used to do -- silently fused every same-named file in the
    corpus into one. bugs/2026-07-10-18.
    """
    fpart = fpart.strip()
    if not fpart or _SCHEME_RE.match(fpart) or fpart.startswith("/"):
        return fpart
    return posixpath.normpath(posixpath.join(src_dir, fpart)) if src_dir else \
        posixpath.normpath(fpart)


def disp(path: str) -> str:
    """Short display name that still distinguishes same-named files across surveys.

    `os.path.basename` printed `fundamentals.md -> fundamentals.md` for a gap between two
    different surveys -- unreadable, and the surface symptom of bugs/2026-07-10-18.
    """
    parts = path.replace("\\", "/").split("/")
    return "/".join(parts[-2:]) if len(parts) > 1 else parts[-1]


def corpus_of(path: str) -> str:
    p = path.replace("\\", "/")
    if "/wikis/" in p or p.startswith("wikis/"):
        return "wiki"
    return "survey"


# -- Tokenization / digest ---------------------------------------------------

_STOP = set("""
a an the of to in on for and or but if then else as at by from with within into
onto is are was were be been being this that these those it its their there here
we our you your they them he she his her i me my mine ours yours
which who whom whose what when where why how all any each few more most other some
such no nor not only own same so than too very can will just should now also
one two three first second figure table equation eq section appendix see e.g i.e
where which given using used use thus hence therefore however because while via
between among across over under above below up down out off again further both
do does did done has have had having would could may might must shall let
case via per vs etc cf ie eg
""".split())

_TOKEN_RE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")


def _strip_noise(text: str) -> str:
    """Remove code, math, comments, tags, link URLs, emphasis — keep prose."""
    out_lines = []
    in_fence = False
    for line in text.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out_lines.append(line)
    s = "\n".join(out_lines)
    s = re.sub(r"\$\$.*?\$\$", " ", s, flags=re.S)   # display math
    s = re.sub(r"\$[^$]*\$", " ", s)                 # inline math
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)    # comments
    # Nav chrome, before the generic tag-strip: the tags go but the WORDS stay,
    # so `back` and `toc` entered the vector of every container section and
    # helped two unrelated surveys score cosine 1.000 (bugs/2026-07-09-11).
    s = re.sub(r"<div[^>]*>\s*<a[^>]*#toc[^>]*>.*?</a>\s*</div>", " ", s,
               flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)                   # html tags
    s = re.sub(r"[↑←⬅→]?\s*back to toc", " ", s, flags=re.I)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r" \1 ", s)  # links -> keep text
    s = s.replace("**", " ").replace("==", " ").replace("`", " ").replace("*", " ")
    return s


def tokenize(text: str) -> list[str]:
    s = _strip_noise(text).lower()
    raw = [t for t in _TOKEN_RE.findall(s) if len(t) >= 3 and t not in _STOP]
    toks = list(raw)
    # bigrams of adjacent kept unigrams capture "gradient descent", "layer norm"
    for a, b in zip(raw, raw[1:]):
        toks.append(a + "_" + b)
    return toks


# -- Section extraction ------------------------------------------------------

def descendants_of(heads, h_idx):
    """Indices of the sections nested under `heads[h_idx]`, in document order.

    A section j is a descendant of i when it follows i and every heading between
    them is deeper than i. Scanning stops at the first heading at i's level or
    shallower -- that is i's sibling, not its child.
    """
    level = heads[h_idx][4]
    out = []
    for j in range(h_idx + 1, len(heads)):
        if heads[j][4] <= level:
            break
        out.append(j)
    return out


def extract_file(path: str, roll_up: bool = True) -> list[dict]:
    """Parse one markdown file into a list of section dicts.

    `roll_up` (default on) folds each section's descendant text into its VECTOR.
    A container -- a heading immediately followed by its own first subsection --
    otherwise has an empty body, so its vector is its title alone and two
    unrelated surveys whose containers share a conventional title ("State of the
    Art and Current Practice") score cosine exactly 1.000. That is a degenerate
    vector, not a similarity (bugs/2026-07-09-11).

    Only `tokens` changes. Deliberately left alone:

      * `snippet` / `has_prose` -- computed from the section's OWN body, because
        `apply` places a link by locating a verbatim substring of the source's
        own prose. A container is a bad vector and a good link TARGET; rolling
        up must not make it look like a viable link SOURCE.
      * `existing` -- own body only. A parent must not inherit its children's
        outbound links, or file-scoped dedup silently widens.

    Each section is tokenized separately and the token LISTS are concatenated,
    never the texts: `tokenize` emits adjacent-pair bigrams, so joining bodies
    first would mint a bigram straddling the seam between a parent's last word
    and a child's first.

    idf is then computed over the rolled documents (`build_vectors` sees these
    tokens), so a leaf's terms also count toward its ancestors' document
    frequency. That is self-consistent -- the documents are the sections as
    represented -- but it is a choice, and it shifts every idf weight in the
    corpus. See todos/2026-07-09-container-vector-rollup.md.
    """
    text = Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    rel = path.replace("\\", "/")
    base = os.path.basename(rel)
    corpus = corpus_of(rel)
    here = posixpath.dirname(rel)

    # Find heading line indices + their section number / title / anchor / level.
    heads = []  # (line_idx, sec_num, title, anchor_id_or_None, level)
    for i, line in enumerate(lines):
        m = match_heading(line)
        if not m:
            continue
        am = SEC_ANCHOR_RE.search(line)
        anchor = am.group(1) if am else None
        heads.append((i, m.group("num"), m.group("title").strip(), anchor,
                      len(m.group("hashes"))))

    # Own tokens + own snippet per section, before any roll-up.
    own_tokens, own_snippets = [], []
    for h_idx, (line_i, _sec, title, _anchor, _lvl) in enumerate(heads):
        end = heads[h_idx + 1][0] if h_idx + 1 < len(heads) else len(lines)
        own_body = "\n".join(lines[line_i + 1:end])
        own_tokens.append(tokenize(title + " " + own_body))
        own_snippets.append(first_paragraph(own_body))

    sections = []
    for h_idx, (line_i, sec_num, title, anchor, _lvl) in enumerate(heads):
        end = heads[h_idx + 1][0] if h_idx + 1 < len(heads) else len(lines)
        body = "\n".join(lines[line_i + 1:end])

        tokens = list(own_tokens[h_idx])
        preview = own_snippets[h_idx]
        if roll_up:
            for j in descendants_of(heads, h_idx):
                tokens.extend(own_tokens[j])
            # A container has no prose of its own, so a judge shown only its own
            # snippet is shown NOTHING and must decide blind. Borrow the first
            # prose-bearing descendant's opening paragraph as a read-only preview.
            # This is display-side only: `snippet` and `has_prose` stay own-body,
            # because `apply` must locate the anchor phrase in the SOURCE's own
            # text. A container is a bad source and a good target; `preview` lets
            # it be judged as the target it is.
            if not preview.strip():
                for j in descendants_of(heads, h_idx):
                    if own_snippets[j].strip():
                        preview = own_snippets[j]
                        break
        # Existing outbound links in this section: set of (repo-relative path, anchor).
        #
        # NOT the basename. Four surveys in one corpus group carry a `fundamentals.md`;
        # keying on the basename made them one file, so cross-file pairs between them
        # were skipped as "same-file", `file_existing` merged unrelated files' links,
        # and `pair_key` collided in the rejection ledger. bugs/2026-07-10-18.
        existing = set()
        for tgt in LINK_TARGET_RE.findall(lines[line_i] + "\n" + body):
            tgt = tgt.strip()
            if tgt.startswith("#"):
                existing.add((rel, tgt[1:]))
            elif "#" in tgt:
                fpart, apart = tgt.split("#", 1)
                existing.add((resolve_target(here, fpart), apart))
        # first paragraph snippet (for the agent; kept short)
        snippet = first_paragraph(body)
        sections.append({
            "file": rel,
            # `path` is IDENTITY (repo-relative, forward-slashed). `base` is a DISPLAY
            # name and a tier hint only -- never compare two sections by it.
            "path": rel,
            "base": base,
            "corpus": corpus,
            "sec": sec_num,
            "title": title,
            "anchor": anchor,                       # None if heading lacks sec-anchor
            "tokens": tokens,                       # rolled-up; see docstring
            "snippet": snippet,
            # `apply` places a link by locating `anchor_phrase`, a verbatim
            # substring of the SOURCE section's prose. A container heading --
            # one immediately followed by its own first subsection -- has no
            # prose, so it can never host a link. This is an invariant, not a
            # heuristic: 231 of 3128 sections, and 63% of >=0.30 candidates,
            # had such a source. See bugs/2026-07-09-11.
            "has_prose": bool(snippet.strip()),
            # Display-only: the section's own opening paragraph, or -- for a
            # container -- its first prose-bearing descendant's. Never used for
            # has_prose or for anchor-phrase placement. See extract_file docstring.
            "preview": preview,
            "existing": sorted(existing),
        })
    return sections


def first_paragraph(body: str, limit: int = 320) -> str:
    s = _strip_noise(body).strip()
    s = re.sub(r"\s+", " ", s)
    # take up to the first sentence-ish boundary past a reasonable length
    if len(s) <= limit:
        return s
    cut = s.rfind(". ", 0, limit)
    if cut > 80:
        return s[: cut + 1]
    # No sentence boundary in range -- fall back to the last WORD boundary, never a
    # hard mid-word cut. `_anchor_suggestion` draws its default anchor from the tail
    # of this snippet; a partial trailing word ("...frequencies wit") made
    # find_insertion_point skip the anchor (todos/2026-07-11-anchor-suggestion-word-boundary).
    wcut = s.rfind(" ", 0, limit)
    return s[:wcut] if wcut > 0 else s[:limit]


def expand_paths(args_paths: list[str]) -> list[str]:
    out = []
    for a in args_paths:
        p = Path(a)
        if p.is_dir():
            for f in sorted(p.glob("*.md")):
                # `_`-prefixed files are briefs/scratch (e.g. `_brief.md`),
                # not corpus sections — same spirit as the `_scratch/` dir.
                if (f.name in SKIP_BASENAMES or f.name.endswith(".index.md")
                        or f.name.startswith("_")):
                    continue
                out.append(str(f))
        elif p.is_file():
            out.append(str(p))
        else:
            print(f"warning: path not found: {a}", file=sys.stderr)
    return out


# -- TF-IDF cosine pre-filter ------------------------------------------------

def build_vectors(sections: list[dict]):
    N = len(sections)
    df = Counter()
    for s in sections:
        for t in set(s["tokens"]):
            df[t] += 1
    idf = {t: math.log((N + 1) / (d + 1)) + 1.0 for t, d in df.items()}
    vecs = []
    for s in sections:
        tf = Counter(s["tokens"])
        v = {}
        for t, c in tf.items():
            v[t] = (1.0 + math.log(c)) * idf[t]
        norm = math.sqrt(sum(w * w for w in v.values())) or 1.0
        vecs.append({t: w / norm for t, w in v.items()})
    return vecs, idf


def cosine(a: dict, b: dict) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b.get(t, 0.0) for t, w in a.items())


# -- Link-syntax + dedup (owned by the script, not the agent) ----------------

def survey_dir_of(path: str) -> str | None:
    """The `surveys/<dir>` that owns `path`, or None.

    None for a wiki and for a top-level single-file survey (`surveys/foo.md`) —
    neither has an `order.json`, so neither can host a resolvable `secxref`.
    """
    p = path.replace("\\", "/")
    if not p.startswith("surveys/"):
        return None
    rest = p[len("surveys/"):]
    return f"surveys/{rest.split('/')[0]}" if "/" in rest else None


def make_link(src: dict, dst: dict) -> tuple[str, str]:
    """Return (link_markdown, dedup_target) for a src->dst cross-link.

    dedup_target is the `relpath#anchor` string used for idempotency.

    Syntax is keyed on whether the target is reachable through the SOURCE's own
    `order.json` — that is what `renumber-sections.py` uses to resolve a
    `secxref` (it builds {sec_num: file} from `<source survey dir>/order.json`).

      * same survey directory -> `secxref` marker + `§` glyph
      * anything else (wiki target, wiki source, a DIFFERENT survey, or a
        single-file survey with no order.json) -> plain relative link with
        descriptive text and NO `§` glyph

    Emitting a `secxref` across surveys would orphan or mis-resolve (the marker
    keys on the wrong `order.json`), and a visible `§` in the link text trips the
    bare-ref gate. See `.claude/rules/cross-linking.md` (directional syntax
    convention) and bug 2026-07-09-14.
    """
    rel = os.path.relpath(dst["file"], start=os.path.dirname(src["file"]))
    rel = rel.replace("\\", "/")
    anchor = dst["anchor"]  # e.g. "sec-D.3.1"
    dedup = f"{rel}#{anchor}"
    sec = dst["sec"]
    sdir = survey_dir_of(src["file"])
    same_survey = (dst["corpus"] == "survey" and src["corpus"] == "survey"
                   and sdir is not None and sdir == survey_dir_of(dst["file"]))
    if same_survey:
        link = f"<!-- secxref:{sec} -->[§{sec}]({dedup})"
    else:
        text = short_text(dst["title"])
        link = f"[{text}]({dedup})"
    return link, dedup


def link_text_of(title: str) -> str:
    """Sanitize a heading title for use as visible markdown link text.

    A heading's title is not link text. Corpus titles legitimately contain HTML
    comments, nested markdown links, and section glyphs -- e.g.

        CORESET Structure (TS 38.213 <!-- secref:10.1 -->[§10.1](#sec-10.1))

    Slicing that to six words yields `[CORESET Structure (TS 38.213 <!-- secref:10.1](url)`:
    a broken link with a dangling comment, which `apply` would have written into a
    survey verbatim. Three hazards, all removed here:

      * HTML comments -- corrupt the link and re-inject a stale secref marker;
      * `[` / `]`     -- unbalance the link text;
      * `§`           -- a glyph in visible link text trips the bare-ref gate
                         (`.claude/rules/cross-linking.md`), which is the entire
                         reason a cross-corpus link is a plain link to begin with.
    """
    t = re.sub(r"<!--.*?-->", " ", title, flags=re.S)     # comments
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)        # nested links -> text
    t = t.replace("§", " ").replace("[", " ").replace("]", " ")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\(\s+", "(", t)          # "( TS" -> "(TS"
    t = re.sub(r"\s+\)", ")", t)          # "7.4.1.3 )" -> "7.4.1.3)"
    # a lone '(' left by truncation would swallow the rest of the line
    return t.rstrip(" (")


def short_text(title: str, words: int = 6) -> str:
    t = re.sub(r"\s+", " ", link_text_of(title)).strip().rstrip(".")
    parts = t.split(" ")
    return " ".join(parts[:words]).rstrip(" (")


def tier_of(corpus: str, base: str) -> int:
    """Derivation tier: higher = more derivation-like (better link target).
    survey body = 1, survey appendix = 2, wiki = 3. Used to pick the
    assertion->derivation direction when a pair is symmetric."""
    if corpus == "wiki":
        return 3
    if base.startswith("appendix-"):
        return 2
    return 1


def generate_candidates(sections, per_source, min_score, keep_symmetric,
                        source_bases=None, file_scoped=False, rejected=None):
    """Core pre-filter shared by `candidates` and `check`.

    Returns a score-sorted list of candidate dicts (no id/batch assignment, no
    max cap). `source_bases`, if given, restricts source endpoints to those
    repo-relative file PATHS (used by `check --changed`). `file_scoped` dedups a target
    already linked anywhere in the source *file* (what `apply` would skip),
    not just in the source section — used by `check` so its report matches
    what `apply` would actually add.

    `rejected` is a set of `pair_key`s a judge has already dismissed. Without
    it, `check` re-reports every candidate the judge rejected, forever — which
    makes the `warn -> error` rollout unreachable (a rejected pair is not a
    fixable gap). The count of suppressed pairs is always reported; it is never
    a silent filter.
    """
    rejected = rejected or set()
    n_suppressed = 0
    vecs, _ = build_vectors(sections)
    linkable = [i for i, s in enumerate(sections) if s["anchor"]]

    # Inverted index over LINKABLE targets. Cosine of L2-normalized sparse
    # vectors is the sum over shared terms, so accumulating each source's terms
    # against the postings yields the identical score in ~sum_t df_t^2 work
    # instead of O(n^2 * terms). At corpus scale (900 sections/group, ~220
    # terms each) this is the difference between a 20 s and a sub-second gate.
    postings = defaultdict(list)
    for j in linkable:
        for t, w in vecs[j].items():
            postings[t].append((j, w))

    # Outbound links per FILE. Always built: needed for the reverse-direction
    # test below even when the forward test is section-scoped.
    file_existing = defaultdict(set)
    for s in sections:
        file_existing[s["path"]].update((b, a) for b, a in s["existing"])

    cands = []
    for i, src in enumerate(sections):
        if source_bases is not None and src["path"] not in source_bases:
            continue
        existing = set(file_existing[src["path"]]) if file_scoped \
            else {(b, a) for b, a in src["existing"]}
        acc = defaultdict(float)
        for t, w in vecs[i].items():
            for j, wj in postings.get(t, ()):
                acc[j] += w * wj
        scored = []
        for j, sc in acc.items():
            if j == i or sc < min_score:
                continue
            dst = sections[j]
            if dst["path"] == src["path"]:
                continue  # cross-file only -- by PATH, not basename (bugs/2026-07-10-18)
            # dedup against existing outbound links (section- or file-scoped)
            if (dst["path"], dst["anchor"]) in existing:
                continue
            # ...and against the REVERSE link: if the target file already links
            # back to this source section, the pair is connected. Without this,
            # every link you add is re-reported forever in the opposite
            # direction (bug 2026-07-09-15).
            if src["anchor"] and (src["path"], src["anchor"]) in file_existing[dst["path"]]:
                continue
            scored.append((sc, j))
        scored.sort(reverse=True)

        # Apply the rejection ledger BEFORE the per-source cap, not after. A
        # rejected pair used to consume a top-k slot, so dismissing it never
        # surfaced the next-best target and the gate could not be cleared by its
        # own pipeline (bugs/2026-07-09-07).
        kept = []
        for sc, j in scored:
            dst = sections[j]
            # Path-keyed, so `fundamentals.md#1.2` in two surveys are two pairs, not one.
            # Rejecting one used to suppress the other. Migrated by
            # viewer/tools/migrate-rejection-ledger.py (bugs/2026-07-10-18).
            pk = "|".join(sorted([f"{src['path']}#{src['sec']}",
                                  f"{dst['path']}#{dst['sec']}"]))
            if pk in rejected:
                n_suppressed += 1
                continue
            kept.append((sc, j, pk))
            if len(kept) >= per_source:
                break

        for sc, j, pk in kept:
            dst = sections[j]
            link_md, dedup = make_link(src, dst)
            cands.append({
                "score": round(sc, 4),
                "pair_key": pk,
                "_st": tier_of(src["corpus"], src["base"]),
                "_dt": tier_of(dst["corpus"], dst["base"]),
                "_sp": 1 if src.get("has_prose", True) else 0,
                "source": {"file": src["file"], "sec": src["sec"],
                           "title": src["title"], "snippet": src["snippet"]},
                # The TARGET is shown to the judge via `preview`, so a container
                # target is legible instead of blank. The SOURCE keeps its own
                # `snippet`: `apply` must find the anchor phrase in that text.
                "target": {"file": dst["file"], "sec": dst["sec"],
                           "title": dst["title"],
                           "snippet": dst.get("preview") or dst["snippet"],
                           "corpus": dst["corpus"]},
                "link_markdown": link_md,
                "dedup_target": dedup,
            })

    if n_suppressed:
        print(f"[crosslink] {n_suppressed} candidate(s) suppressed by the rejection "
              f"ledger (judged not worth linking).", file=sys.stderr)

    if not keep_symmetric:
        # collapse each unordered pair to its assertion->derivation direction:
        # prefer larger (dst_tier - src_tier), then higher score, then a
        # deterministic source-key tiebreak.
        best = {}
        for c in cands:
            k = c["pair_key"]
            # A direction whose source has no prose can never be applied, so it
            # loses to the reverse direction outright -- ahead of tier and score.
            # Skipping prose-less sources at generation time instead would delete
            # the pair entirely, losing the legitimate reverse proposal: the
            # tiebreak below is lexicographic on the source path, so `t.md#8`
            # (a container) beats `c.md#3.1` and would have won. bugs/2026-07-09-11.
            key = (c["_sp"], c["_dt"] - c["_st"], c["score"],
                   f"{c['source']['file']}#{c['source']['sec']}")
            cur = best.get(k)
            if cur is None or key > cur[0]:
                best[k] = (key, c)
        cands = [v[1] for v in best.values()]

    # Enforce the invariant AFTER collapse: whatever direction survived, a source
    # with no prose cannot host a link. Both-sides-prose-less pairs (the cosine
    # 1.000 `## N. State of the Art` twins) drop out here.
    n_before = len(cands)
    cands = [c for c in cands if c["_sp"]]
    n_dropped = n_before - len(cands)
    if n_dropped:
        print(f"[crosslink] {n_dropped} candidate(s) dropped: the source section "
              f"has no prose, so no anchor phrase could be placed there.",
              file=sys.stderr)

    for c in cands:
        del c["_st"], c["_dt"], c["_sp"]
    cands.sort(key=lambda c: c["score"], reverse=True)
    return cands


# -- One planner, two callers ------------------------------------------------
#
# `check` (the gate) and `candidates` (the pipeline that clears it) used to build
# their candidate sets with different parameters: per-source 2 vs 3, file-scoped
# vs section-scoped dedup. Each proposed pairs the other never saw, so at
# --severity=error a divergent pair blocked every push and /cross-link could not
# clear it -- the operator had to hand-write a pair_key rejection. One rule, two
# implementations, drifted. bugs/2026-07-09-07.
#
# There is now exactly one planner. Both commands build a GapConfig and call it.

# H-3, from measurement, not convention. `decisions/2026-07-10-03` (+ its per_source
# amendment) and `decisions/2026-07-10-06`.
#
# per_source = 1, NOT 3: at every deployment budget the top-1 cap DOMINATES top-3 on
#   author-link recall -- `K=1, t=0.11` emits 624 pairs at recall 0.175 while `K=3,
#   t=0.12` emits 690 at 0.159. `K = 3` never wins anywhere. Precision is non-inferior
#   (judge keep rate by within-source rank: 0.288 / 0.209 / 0.182, trend p = 0.10).
#   The 3 was inherited, never tested, until method-search Candidate 01 tested it.
#
# min_score = 0.20, NOT 0.12: tokens per accepted link are minimised there (12.2K, vs
#   19.9K at 0.12 and 33.6K at 0.05) and it yields ~93 candidate pairs corpus-wide --
#   a list a human reads in an hour. Precision saturates at 0.417 [0.301, 0.543] no
#   matter what, so buying volume buys rejects.
DEFAULT_PER_SOURCE = 1
DEFAULT_MIN_SCORE = 0.20
DEFAULT_MAX_CANDIDATES = 60


class GapConfig(NamedTuple):
    per_source: int = DEFAULT_PER_SOURCE
    min_score: float = DEFAULT_MIN_SCORE
    max_candidates: int = DEFAULT_MAX_CANDIDATES
    keep_symmetric: bool = False
    # File-scoped dedup is the link-spam guard `apply` already enforces, so
    # `check`'s gap report equals what `apply` would actually add -- the claim
    # .claude/rules/cross-linking.md makes and previously could not keep.
    file_scoped: bool = True
    source_bases: frozenset | None = None
    rejected: frozenset = frozenset()


def gap_config_from_args(args, **override) -> GapConfig:
    """Build the planner config from either subcommand's parsed args."""
    cfg = GapConfig(
        per_source=args.per_source,
        min_score=args.min_score,
        max_candidates=args.max_candidates,
        keep_symmetric=getattr(args, "keep_symmetric", False),
        rejected=frozenset(
            set() if getattr(args, "ignore_rejections", False)
            else load_rejections(getattr(args, "rejections", DEFAULT_REJECTIONS))),
    )
    return cfg._replace(**override) if override else cfg


def plan_gaps(sections, cfg: GapConfig):
    """The single source of truth for 'what are the cross-link gaps?'.

    Returns (capped_candidates, n_found). `n_found` is pre-cap, so no caller can
    let a truncation read as 'that is all there is'.
    """
    cands = generate_candidates(
        sections, cfg.per_source, cfg.min_score, cfg.keep_symmetric,
        source_bases=cfg.source_bases, file_scoped=cfg.file_scoped,
        rejected=set(cfg.rejected))
    n_found = len(cands)
    return cands[: cfg.max_candidates], n_found


def parse_paths(paths: list[str]):
    """Parse files -> (sections, empty_paths, unanchored_paths).

    `empty_paths` are scoped files that yielded ZERO sections: they are absent
    from the TF-IDF index entirely — neither link source nor link target — so no
    gap involving them is expressible and `check` would report a false "no gaps".
    These must never be silent (bug 2026-07-09-13).

    `unanchored_paths` yielded sections but carry no `sec-` anchor on any of
    them: usable as a link *source*, never as a link *target*.
    """
    sections, empty, unanchored = [], [], []
    for p in paths:
        secs = extract_file(p)
        if not secs:
            empty.append(p)
            continue
        if not any(s["anchor"] for s in secs):
            unanchored.append(p)
        sections.extend(secs)
    return sections, empty, unanchored


def warn_coverage(empty: list[str], unanchored: list[str]) -> None:
    """Report scoped-but-invisible files. Silence here is the bug."""
    for p in empty:
        print(f"[crosslink] WARNING: 0 sections from {p} — invisible to the "
              f"index (no heading matched); it can neither propose nor receive "
              f"a link.", file=sys.stderr)
    for p in unanchored:
        print(f"[crosslink] note: {p} has sections but no sec-anchor — usable "
              f"as a link source, never as a link target.", file=sys.stderr)


def load_or_build_index(args):
    """Return the section list, from --index, --cache, or a fresh corpus parse."""
    if getattr(args, "index", None):
        return json.loads(Path(args.index).read_text(encoding="utf-8"))["sections"]
    cache = getattr(args, "cache", None)
    if cache and Path(cache).exists() and not getattr(args, "refresh_cache", False):
        return json.loads(Path(cache).read_text(encoding="utf-8"))["sections"]
    sections, empty, unanchored = parse_paths(expand_paths(args.paths))
    warn_coverage(empty, unanchored)
    if cache:
        Path(cache).write_text(
            json.dumps({"sections": sections}, indent=2, ensure_ascii=False),
            encoding="utf-8")
    return sections


DEFAULT_REJECTIONS = ".claude/crosslink-rejected.json"


def load_rejections(path: str | None) -> set:
    """Read the judged-and-rejected `pair_key` ledger.

    A rejected pair is NOT an unfixed gap — a judge looked at it and decided the
    link was not worth having. Without this, `check` re-reports it forever and
    `--severity=error` can never be reached. Keyed on `pair_key`
    (`base#sec|base#sec`, direction-independent), so a pair stays rejected even
    if the assertion->derivation direction flips.

    Caveat: the key does not capture section *content*. If a section is
    substantially rewritten, its old rejection still applies. Re-judge with
    `--ignore-rejections` after a large rewrite.
    """
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        return set()
    data = json.loads(p.read_text(encoding="utf-8"))
    return {r["pair_key"] for r in data.get("rejected", [])}


def _append_rejections(out_path: str, by_id: dict, ids: list[str], note: str) -> int:
    """Append pair_keys to the rejection ledger (idempotent). One writer, two callers:
    `reject_cmd` (judge path) and `apply_cmd`'s from-review reject branch."""
    out = Path(out_path)
    existing = []
    if out.exists():
        existing = json.loads(out.read_text(encoding="utf-8")).get("rejected", [])
    seen = {r["pair_key"] for r in existing}
    added = 0
    for cid in ids:
        c = by_id.get(cid)
        if not c or c["pair_key"] in seen:
            continue
        existing.append({"pair_key": c["pair_key"], "score": c["score"], "note": note})
        seen.add(c["pair_key"])
        added += 1
    existing.sort(key=lambda r: r["pair_key"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"rejected": existing}, indent=1, ensure_ascii=True),
                   encoding="utf-8")
    return added


def reject_cmd(args):
    """Append judge-rejected pairs to the rejection ledger (idempotent)."""
    cdata = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in cdata["candidates"]}
    decisions = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    if isinstance(decisions, dict):
        decisions = decisions.get("decisions", [])
    ids = [d["id"] for d in decisions if not d.get("keep")]
    added = _append_rejections(args.out, by_id, ids, args.note)
    print(f"rejection ledger: +{added} -> {args.out}", file=sys.stderr)
    return 0


GROUP_RE = re.compile(r"^\[([A-Za-z0-9][\w.-]*)\]\s*$")


def load_scope(path: str) -> dict[str, list[str]]:
    """Parse `.claude/crosslink-scope` into ordered named corpus groups.

    Format (backward compatible): a `[group-name]` header opens a group; every
    following path line belongs to it. Lines before the first header land in a
    group named `default`, so a flat legacy scope file parses as one group.

    Each group is an INDEPENDENT TF-IDF corpus: a candidate never spans two
    groups. That is the whole point — it keeps unrelated surveys from proposing
    links at each other while letting each corpus be checked on its own terms.
    """
    groups: dict[str, list[str]] = {}
    cur = "default"
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = GROUP_RE.match(line)
        if m:
            cur = m.group(1)
            groups.setdefault(cur, [])
            continue
        groups.setdefault(cur, []).append(line)
    return {k: v for k, v in groups.items() if v}


def git_changed_md(since=None):
    """Return a set of changed .md files as repo-relative, forward-slashed PATHS.

    Paths, not basenames: `generate_candidates` filters sources on `src["path"]`, and a
    basename would both under-match (never equal a path) and over-match (every
    `fundamentals.md` in the corpus). bugs/2026-07-10-18.
    """
    import subprocess
    bases = set()
    cmds = []
    if since:
        cmds.append(["git", "diff", "--name-only", since])
    else:
        cmds.append(["git", "diff", "--name-only", "HEAD"])
        cmds.append(["git", "ls-files", "--others", "--exclude-standard"])
    for cmd in cmds:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 check=False).stdout
        except OSError:
            continue
        for line in out.splitlines():
            line = line.strip()
            if line.endswith(".md"):
                bases.add(line.replace("\\", "/"))
    return bases


# -- The Stage-3 judge contract, owned by the tool (bugs/2026-07-10-16, -06) -----
#
# Two defects lived in prose (the README's Stage-3 prompt) where no test could hold
# them: the prompt named "an LLM inference survey" though the corpus is five groups, and
# the workflow handed the agent the whole candidate dict -- score, pair_key,
# link_markdown -- so the judge read the cosine it exists to be an independent check
# ON. Both now live here.

JUDGE_PROMPT = (
    "You are judging proposed cross-links for {corpus}. For each candidate you get a "
    "SOURCE section snippet and a TARGET section snippet. Keep a link only if the TARGET "
    "genuinely derives, grounds, proves, or materially extends the specific claim in the "
    "SOURCE (assertion -> derivation), and the link is non-redundant and high-value. "
    "Reject vague topical overlap. For each kept candidate, return anchor_phrase: a "
    "verbatim substring (<= 12 words) copied from the SOURCE snippet, ending at the exact "
    "assertion the link should attach to. Do NOT choose link syntax or paths -- that is "
    "handled downstream. Return one object per candidate id."
)

# Default corpus noun. Neutral by design: the rubric is corpus-independent (assertion ->
# derivation), and naming a specific corpus invites the topical priors the rubric rejects.
DEFAULT_JUDGE_CORPUS = "a technical survey corpus"

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "keep": {"type": "boolean"},
                    "confidence": {"type": "number"},
                    "anchor_phrase": {"type": "string"},
                },
                "required": ["id", "keep", "anchor_phrase"],
            },
        },
    },
    "required": ["decisions"],
}

# The ONLY fields a judge may see. Everything else -- score above all, but also
# pair_key / link_markdown / dedup_target / corpus -- is withheld: a judge that can read
# the cosine cannot be an independent check on it (bugs/2026-07-10-17).
_JUDGE_VIEW_KEYS = ("file", "sec", "title", "snippet")


def judge_view(c: dict) -> dict:
    """Blinded projection of a candidate for the Stage-3 judge."""
    return {"id": c["id"],
            "source": {k: c["source"].get(k) for k in _JUDGE_VIEW_KEYS},
            "target": {k: c["target"].get(k) for k in _JUDGE_VIEW_KEYS}}


def assert_judge_view_blind(views: list[dict]) -> None:
    """Refuse to emit a judge payload that leaks the score (or any other lever).

    A whitelist assert with the failure mode named: if a future refactor lets `score`
    back into the view, this fires rather than silently voiding the next measurement.
    """
    blob = json.dumps(views)
    leaked = [k for k in ("score", "pair_key", "link_markdown", "dedup_target",
                          "corpus", "_st", "_dt", "_sp")
              if f'"{k}"' in blob]
    if leaked:
        raise AssertionError(f"judge_view leaks {leaked} to the judge (bugs/2026-07-10-17)")


def judge_prompt_cmd(args):
    """Print the canonical Stage-3 judge prompt (and schema). One source of truth."""
    print(JUDGE_PROMPT.format(corpus=args.corpus))
    if args.schema:
        print("\n--- JUDGE_SCHEMA ---")
        print(json.dumps(JUDGE_SCHEMA, indent=2))
    return 0


def candidates_cmd(args):
    sections = json.loads(Path(args.index).read_text(encoding="utf-8"))["sections"]
    # Suppress ledger-rejected pairs HERE, not just in `check`. Otherwise every
    # sweep re-proposes pairs a judge already dismissed, and the agent bill is
    # paid again for the same answer.
    cands, n_found = plan_gaps(sections, gap_config_from_args(args))
    if n_found > len(cands):
        print(f"[crosslink] showing top {len(cands)} of {n_found} candidates "
              f"(--max-candidates); {n_found - len(cands)} not judged. Raise the "
              f"cap or the gate will still report them.", file=sys.stderr)
    for n, c in enumerate(cands, 1):
        c["id"] = f"C{n:03d}"

    # group into agent batches
    batches = [cands[k:k + args.batch] for k in range(0, len(cands), args.batch)]
    # Blinded per-candidate view for the escape-hatch judge (bugs/2026-07-10-17).
    # The full record stays for `apply`/`review`; the judge is handed `judge_view` only.
    views = [judge_view(c) for c in cands]
    assert_judge_view_blind(views)
    out = {"candidates": cands, "judge_view": views,
           "batches": [[c["id"] for c in b] for b in batches],
           "n_candidates": len(cands), "n_batches": len(batches)}
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False),
                              encoding="utf-8")

    print(f"{len(cands)} candidates in {len(batches)} batches -> {args.out}",
          file=sys.stderr)
    print("\nTop candidates:", file=sys.stderr)
    for c in cands[:15]:
        s, t = c["source"], c["target"]
        sb = disp(s["file"])
        tb = disp(t["file"])
        print(f"  {c['id']} {c['score']:.3f}  {sb} §{s['sec']}"
              f"  ->  {tb} §{t['sec']} ({t['corpus']})", file=sys.stderr)


def check_cmd(args):
    """Gap detector for the lint/gen gates. Reports unlinked high-cosine
    candidates; NEVER writes. Exit code keyed on --severity:
      off  -> exit 0, silent
      warn -> exit 0, print residual gaps (advisory)
      error-> exit 1 if any residual gap scores >= --block-score
    """
    if args.severity == "off":
        return 0
    if not args.paths and not args.index and not args.cache and not args.scope_file:
        print("[crosslink] ERROR: check needs a corpus — pass paths, --index, "
              "--cache, or --scope-file. Refusing to report 'no gaps' over an "
              "empty corpus.", file=sys.stderr)
        return 2

    source_bases = None
    if args.changed or args.since:
        source_bases = git_changed_md(args.since)
        if not source_bases:
            print("[crosslink] no changed .md files; no gaps to check.",
                  file=sys.stderr)
            return 0

    if args.scope_file:
        groups = load_scope(args.scope_file)
        if not groups:
            print(f"[crosslink] ERROR: no corpus paths in {args.scope_file}.",
                  file=sys.stderr)
            return 2
    else:
        groups = {"default": list(args.paths)}

    rejected = set() if args.ignore_rejections else load_rejections(args.rejections)

    all_gaps, rc = [], 0
    for name, paths in groups.items():
        if args.index or args.cache:
            sections = load_or_build_index(args)
        else:
            sections, empty, unanchored = parse_paths(expand_paths(paths))
            warn_coverage(empty, unanchored)
        if not sections:
            print(f"[crosslink] ERROR: group '{name}' parsed to 0 sections — "
                  f"every scoped path is invisible. Not reporting 'no gaps'.",
                  file=sys.stderr)
            rc = max(rc, 2)
            continue

        cfg = gap_config_from_args(
            args, source_bases=source_bases,
            rejected=frozenset(rejected))
        cands, n_found = plan_gaps(sections, cfg)
        if n_found > len(cands):
            # Never let a cap read as "that's all there is" (no silent caps).
            print(f"[crosslink] group '{name}': showing top {len(cands)} of "
                  f"{n_found} gaps (--max-candidates); "
                  f"{n_found - len(cands)} not shown.", file=sys.stderr)
        for c in cands:
            c["group"] = name
        all_gaps.extend(cands)

        if not args.json:
            label = f"group '{name}'" if args.scope_file else "corpus"
            if cands:
                scope = "changed-file " if source_bases is not None else ""
                print(f"[crosslink] {label}: {len(cands)} unlinked {scope}"
                      f"cross-link candidate(s) (>= cosine {args.min_score}; "
                      f"advisory, not blocking):", file=sys.stderr)
                for c in cands:
                    s, t = c["source"], c["target"]
                    print(f"    {c['score']:.3f}  {disp(s['file'])} "
                          f"{s['sec']}  ->  {disp(t['file'])} "
                          f"{t['sec']} ({t['corpus']})", file=sys.stderr)
            else:
                print(f"[crosslink] {label}: no cross-link gaps.", file=sys.stderr)

        if args.severity == "error":
            blocking = [c for c in cands if c["score"] >= args.block_score]
            if blocking:
                print(f"[crosslink] BLOCKED - group '{name}': {len(blocking)} "
                      f"obvious cross-link gap(s) at or above cosine "
                      f"{args.block_score}. Add the link or run /cross-link.",
                      file=sys.stderr)
                rc = max(rc, 1)

    if args.json:
        print(json.dumps({"gaps": all_gaps, "n": len(all_gaps)},
                         indent=2, ensure_ascii=False))
    elif all_gaps:
        print("    Clear with: /cross-link  (or crosslink.py candidates|apply)",
              file=sys.stderr)
    return rc


# -- normalize-with-map matcher (reused from the 2026-06-23 recovery applier) -

_EMPH = ("**", "==")


def normalize_with_map(s: str):
    """Return (norm, idx_map): norm is s with comments/<a> tags/emphasis removed
    and whitespace collapsed; idx_map[k] = original index of norm[k]."""
    norm_chars = []
    idx_map = []
    i, n = 0, len(s)
    prev_space = True  # collapse leading space
    while i < n:
        # HTML comment
        if s.startswith("<!--", i):
            end = s.find("-->", i)
            i = end + 3 if end != -1 else n
            continue
        # <a ...> or </a>
        if s.startswith("<a", i) or s.startswith("</a", i):
            end = s.find(">", i)
            i = end + 1 if end != -1 else n
            continue
        # emphasis runs
        matched = False
        for e in _EMPH:
            if s.startswith(e, i):
                i += len(e)
                matched = True
                break
        if matched:
            continue
        ch = s[i]
        if ch in "*`":
            i += 1
            continue
        if ch.isspace():
            if not prev_space:
                norm_chars.append(" ")
                idx_map.append(i)
                prev_space = True
            i += 1
            continue
        norm_chars.append(ch)
        idx_map.append(i)
        prev_space = False
        i += 1
    return "".join(norm_chars), idx_map


def find_insertion_point(text: str, quote: str):
    """Return original-text index just after `quote` (render-normalized match),
    or None. Falls back to the quote's final sentence."""
    ntext, imap = normalize_with_map(text)
    nquote, _ = normalize_with_map(quote)
    nquote = nquote.strip()
    if not nquote:
        return None

    def _safe(pos_end):
        ip = imap[pos_end - 1] + 1
        # Refuse an insertion that lands in the MIDDLE of a word: a truncated
        # anchor ("wit"/"refer"/"SN") matches inside "with"/"references.md"/"SNR"
        # and inserting there splits the token (and corrupts a markdown link URL).
        # Skip instead — the reviewer repoints the anchor — rather than silently
        # corrupt the source. (bug 2026-07-11-03)
        if 0 < ip < len(text) and text[ip - 1].isalnum() and text[ip].isalnum():
            return None
        return ip

    pos = ntext.find(nquote)
    if pos == -1:
        # prefix fallback: last sentence of the quote
        tail = re.split(r"(?<=[.;:])\s+", nquote)[-1]
        if len(tail) >= 12:
            pos = ntext.find(tail)
            if pos != -1:
                return _safe(pos + len(tail))
        return None
    return _safe(pos + len(nquote))


DEFAULT_MERGE_LEDGER = ".claude/crosslink-merge-candidates.json"

# The review sheet's machine-readable per-candidate marker. `review` writes it; `apply
# --from-review` reads it. The visible checkbox line is parsed separately.
REVIEW_MARK_RE = re.compile(r"<!--\s*xlink\s+(\S+)\s+pair_key=(.+?)\s*-->")
REVIEW_ANCHOR_RE = re.compile(r"\*\*Anchor\*\*[^:`]*:\s*`([^`]*)`")
REVIEW_BOX_RE = re.compile(r"\[([ xX])\]\s*(link|merge|reject)")


def _anchor_suggestion(snippet: str, words: int = 10) -> str:
    """A verbatim tail of the source snippet, offered as the default link anchor.

    A human edits it to move the link; `apply` locates it in the file via the same
    normalize-with-map matcher the judge path uses. It is a substring of the section's
    own prose, so it is always locatable.
    """
    s = re.sub(r"\s+", " ", (snippet or "")).strip().rstrip(".")
    parts = s.split(" ")
    return " ".join(parts[-words:])


def review_cmd(args):
    """Emit the shortlist as a human review sheet: one block per pair, three boxes.

    This is the DEFAULT path (plan 2026-07-10-crosslink-detector-only): the tool
    proposes, a person decides, `apply --from-review` writes. The `merge` box is the
    action for a structural twin -- a duplication to fix, not a link to add -- which
    the judge path could only ever record as a lossy `reject`.
    """
    cands = json.loads(Path(args.candidates).read_text(encoding="utf-8"))["candidates"]
    lines = [
        "# Cross-link review sheet",
        "",
        f"{len(cands)} candidate pair(s). For each: check exactly one box.",
        "",
        "- **link** — a genuine cross-reference; `apply --from-review` inserts it at the Anchor.",
        "- **merge** — the two sections say the same thing; a duplication to fix, not a link "
        "(recorded to the merge ledger, nothing written).",
        "- **reject** — neither; recorded to the rejection ledger so the gate stops reporting it.",
        "",
        "Edit the **Anchor** to move where a kept link attaches (it must stay a verbatim "
        "substring of the source).",
        "",
        "---",
        "",
    ]
    for c in cands:
        s, t = c["source"], c["target"]
        lines += [
            f"<!-- xlink {c['id']} pair_key={c['pair_key']} -->",
            f"### {c['id']} · cosine {c['score']:.3f}",
            f"- **Source** — `{s['file']}` §{s['sec']} — {s.get('title','')}",
            f"  > {(s.get('snippet') or '').strip()[:400]}",
            f"- **Target** — `{t['file']}` §{t['sec']} — {t.get('title','')}",
            f"  > {(t.get('snippet') or '').strip()[:400]}",
            f"- **Would insert**: `{c['link_markdown']}`",
            f"- **Anchor** (edit to move the link): `{_anchor_suggestion(s.get('snippet',''))}`",
            "- **Decision**: [ ] link  [ ] merge  [ ] reject",
            "",
        ]
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"review sheet: {len(cands)} pair(s) -> {args.out}\n"
          f"Check one box per block, then: crosslink.py apply --candidates {args.candidates} "
          f"--from-review {args.out} --reviewed-by <you>", file=sys.stderr)
    return 0


def parse_review(path: str) -> list[dict]:
    """Parse a checked review sheet into decisions. Each block yields at most one.

    A block with zero boxes checked is 'undecided' and skipped (reported). A block with
    more than one is an error -- refuse rather than guess.
    """
    text = Path(path).read_text(encoding="utf-8")
    blocks = re.split(r"(?=<!--\s*xlink\s)", text)
    out, undecided, ambiguous = [], [], []
    for b in blocks:
        m = REVIEW_MARK_RE.search(b)
        if not m:
            continue
        cid, pk = m.group(1), m.group(2)
        checked = [kind for box, kind in REVIEW_BOX_RE.findall(b) if box in "xX"]
        if not checked:
            undecided.append(cid)
            continue
        if len(checked) > 1:
            ambiguous.append((cid, checked))
            continue
        am = REVIEW_ANCHOR_RE.search(b)
        out.append({"id": cid, "pair_key": pk, "decision": checked[0],
                    "anchor_phrase": (am.group(1).strip() if am else "")})
    if undecided:
        print(f"[crosslink] {len(undecided)} block(s) undecided (no box checked), skipped: "
              f"{', '.join(undecided[:8])}", file=sys.stderr)
    if ambiguous:
        raise SystemExit(f"[crosslink] {len(ambiguous)} block(s) have >1 box checked; "
                         f"refusing to guess: {ambiguous[:5]}")
    return out


def _record_merge_candidates(ledger_path: str, cands_by_id: dict, ids: list[str],
                             reviewed_by: str) -> int:
    """Append merge candidates to their OWN ledger (never the rejection ledger).

    A structural twin is a documentation defect to fix, not a link that was rejected;
    conflating the two loses the finding (plan Task 2).
    """
    p = Path(ledger_path)
    existing = []
    if p.exists():
        existing = json.loads(p.read_text(encoding="utf-8")).get("merge_candidates", [])
    seen = {m["pair_key"] for m in existing}
    added = 0
    for cid in ids:
        c = cands_by_id.get(cid)
        if not c or c["pair_key"] in seen:
            continue
        existing.append({"pair_key": c["pair_key"], "score": c["score"],
                         "source": c["source"]["file"], "source_sec": c["source"]["sec"],
                         "target": c["target"]["file"], "target_sec": c["target"]["sec"],
                         "reviewed_by": reviewed_by})
        seen.add(c["pair_key"])
        added += 1
    existing.sort(key=lambda m: m["pair_key"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"merge_candidates": existing}, indent=1, ensure_ascii=True),
                 encoding="utf-8")
    return added


def apply_cmd(args):
    cdata = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in cdata["candidates"]}

    # -- Provenance guard (plan 2026-07-10-crosslink-detector-only, Task 2/4).
    # `apply` writes into the corpus, and links it writes become "author" links to the
    # next recall measurement (bugs/2026-07-10-19). So it must never be driven by an
    # agent's decision file silently: a human takes responsibility, by review sheet or by
    # naming themselves. An unattributed --decisions file is refused.
    merge_ids, reject_ids = [], []
    if not args.from_review and not args.decisions:
        print("[crosslink] apply needs either --from-review <sheet> (the default path) "
              "or --decisions <json>.", file=sys.stderr)
        return 2
    if getattr(args, "from_review", None):
        reviewed_by = args.reviewed_by or "unknown (from review sheet)"
        parsed = parse_review(args.from_review)
        decisions = [{"id": d["id"], "keep": True, "anchor_phrase": d["anchor_phrase"]}
                     for d in parsed if d["decision"] == "link"]
        merge_ids = [d["id"] for d in parsed if d["decision"] == "merge"]
        reject_ids = [d["id"] for d in parsed if d["decision"] == "reject"]
    else:
        raw = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
        obj = raw if isinstance(raw, dict) else {"decisions": raw}
        reviewed_by = args.reviewed_by or obj.get("reviewed_by")
        if not reviewed_by:
            print("[crosslink] REFUSED: --decisions carries no human provenance.\n"
                  "  `apply` will not write links from an unattributed (agent) decision "
                  "file — its output becomes ground truth for the recall measurement "
                  "(bugs/2026-07-10-19).\n"
                  "  Use `crosslink.py review` + `apply --from-review`, or pass "
                  "`--reviewed-by <you>` to take responsibility for these decisions.",
                  file=sys.stderr)
            return 2
        decisions = obj.get("decisions", [])

    # group approved insertions per file
    per_file = defaultdict(list)
    skipped, kept = [], 0
    for d in decisions:
        if not d.get("keep"):
            continue
        c = by_id.get(d["id"])
        if not c:
            print(f"warning: decision for unknown id {d.get('id')}", file=sys.stderr)
            continue
        kept += 1
        per_file[c["source"]["file"]].append({
            "id": c["id"],
            "phrase": d.get("anchor_phrase", "").strip(),
            "link": c["link_markdown"],
            "dedup": c["dedup_target"],
        })

    total_applied = 0
    for fpath, items in per_file.items():
        text = Path(fpath).read_text(encoding="utf-8")
        # sort insertions by position descending so earlier offsets stay valid
        planned = []
        # Span classification (origin/main): which byte ranges are prose vs math /
        # code / link / fence / comment, so an insertion point can be nudged out of
        # a non-prose span (or refused inside a fence, comment, or frontmatter).
        _spans = mdctx.classify(text)
        _prose = mdctx.writable_mask(text)
        # Idempotency must compare PARSED link destinations, never a substring.
        # Anchors are dotted, so `a.md#sec-4` is a substring of `a.md#sec-4.2`:
        # a plain `in text` test silently drops every link to an ANCESTOR section
        # whose descendant is already linked -- i.e. exactly the container targets
        # the vector roll-up exists to make reachable -- and reports the loss as
        # "already-present". `generate_candidates` dedups on parsed (base, anchor)
        # tuples, so `check` proposed pairs `apply` then refused: the check/apply
        # divergence of bugs/2026-07-09-07, reopened in the apply direction.
        # See bugs/2026-07-10-15.
        # ...and compare them RESOLVED, not as raw relative strings: `../a/x.md#s` and
        # `x.md#s` can name the same target from different spellings (bugs/2026-07-10-18).
        here = posixpath.dirname(fpath.replace("\\", "/"))

        def _canon(t: str) -> str:
            t = t.strip()
            if "#" not in t or t.startswith("#"):
                return t
            f, a = t.split("#", 1)
            return f"{resolve_target(here, f)}#{a}"

        existing_targets = {_canon(t) for t in LINK_TARGET_RE.findall(text)}
        for it in items:
            if _canon(it["dedup"]) in existing_targets:
                skipped.append((it["id"], "already-present"))
                continue
            ip = find_insertion_point(text, it["phrase"]) if it["phrase"] else None
            if ip is None:
                skipped.append((it["id"], "phrase-not-found"))
                continue
            # The anchor phrase is matched against RENDER-NORMALIZED text, so its end can
            # map back inside an inline `$...$`, a code span, or a link destination. Nudge
            # out to just after the enclosing span; refuse entirely inside a fence, an HTML
            # comment or frontmatter (nothing should be linked out of those).
            nip = mdctx.advance_to_prose(text, _spans, _prose, ip)
            if nip is None:
                skipped.append((it["id"], f"non-prose-context:{mdctx.kind_at(_spans, ip)}"))
                continue
            ip = nip
            planned.append((ip, it))
            # Dedup planned-vs-planned, not only planned-vs-pre-existing: two
            # candidates in one run whose sources sit in the SAME file and point
            # at the SAME target would both pass the pre-run snapshot check and
            # double-link the target, violating the "at most once per file"
            # invariant. Seeding the set as we plan keeps apply idempotent within
            # a single run too (bugs/2026-07-11-01).
            existing_targets.add(_canon(it["dedup"]))
        planned.sort(key=lambda x: x[0], reverse=True)
        for ip, it in planned:
            ins = f" ({it['link']})"
            text = text[:ip] + ins + text[ip:]
            total_applied += 1
            print(f"  apply {it['id']}: {disp(fpath)} <- {it['dedup']}",
                  file=sys.stderr)
        if planned and not args.dry_run:
            Path(fpath).write_text(text, encoding="utf-8")

    print(f"\napplied {total_applied}/{kept} kept "
          f"({len(skipped)} skipped){' [DRY-RUN]' if args.dry_run else ''} "
          f"— reviewed_by: {reviewed_by}", file=sys.stderr)
    for cid, why in skipped:
        print(f"  skip {cid}: {why}", file=sys.stderr)

    # Route the review sheet's non-link outcomes (from-review only).
    if merge_ids and not args.dry_run:
        n = _record_merge_candidates(args.merge_ledger, by_id, merge_ids, reviewed_by)
        print(f"merge ledger: +{n} ({len(merge_ids)} marked) -> {args.merge_ledger}",
              file=sys.stderr)
    elif merge_ids:
        print(f"  [DRY-RUN] {len(merge_ids)} merge candidate(s) not recorded",
              file=sys.stderr)
    if reject_ids and not args.dry_run:
        # A human reject IS a ledger entry: the gate must stop reporting it. Reuse the
        # same pair_key ledger the judge path writes, tagged with who rejected it.
        _append_rejections(args.rejections, by_id, reject_ids,
                           f"human review ({reviewed_by})")
        print(f"rejection ledger: +{len(reject_ids)} human reject(s) -> {args.rejections}",
              file=sys.stderr)
    elif reject_ids:
        print(f"  [DRY-RUN] {len(reject_ids)} reject(s) not recorded", file=sys.stderr)


def extract_cmd(args):
    paths = expand_paths(args.paths)
    sections, empty, unanchored = parse_paths(paths)
    warn_coverage(empty, unanchored)
    Path(args.out).write_text(
        json.dumps({"sections": sections}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    n_anchored = sum(1 for s in sections if s["anchor"])
    print(f"{len(sections)} sections ({n_anchored} linkable) from "
          f"{len(paths) - len(empty)}/{len(paths)} files -> {args.out}",
          file=sys.stderr)
    if empty and getattr(args, "strict", False):
        print(f"[crosslink] BLOCKED - {len(empty)} scoped file(s) contributed "
              f"0 sections.", file=sys.stderr)
        return 1
    return 0


DEFAULT_KEEPOUT = ".claude/crosslink-keepout"
DEFAULT_COVERAGE_SEVERITY = ".claude/crosslink-coverage-severity"
DEFAULT_REACH_KEEPOUT = ".claude/reachability-keepout"


def _norm(p: str) -> str:
    return p.replace("\\", "/")


def content_files(roots=("surveys", "wikis")) -> set:
    """Every .md that COULD be a corpus source/target: single-file surveys, each
    multi-file survey's top-level chapters, and wikis. `_`-prefixed and index/references
    files are excluded by `expand_paths`; sub-dirs (method-search, _scratch) are not
    descended, so they are naturally out."""
    files = {_norm(f) for f in expand_paths(list(roots))}
    for root in roots:
        rp = Path(root)
        if not rp.is_dir():
            continue
        for d in sorted(rp.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                files.update(_norm(f) for f in expand_paths([str(d)]))
    return files


def _read_keepout(path: str) -> set:
    """Deliberately-excluded files, expanded from the keep-out list (paths or dirs)."""
    p = Path(path)
    if not p.exists():
        return set()
    entries = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()
               if ln.strip() and not ln.strip().startswith("#")]
    return {_norm(f) for f in expand_paths(entries)}


def coverage_cmd(args):
    """Report every survey/wiki that is neither in a corpus group nor a declared keep-out.

    A cross-link *detector* that silently does not scan a document reports "no gaps" for
    a corpus it never looked at — the false-green class of bugs/2026-07-09-13. This makes
    non-coverage loud. Advisory by default; blocks at `error`. Roadmap H-5.

    Coverage is TWO conditions, not one. Group membership is necessary and NOT
    sufficient: a file can be in a group, pass this gate, and still contribute ZERO
    sections — parsed, invisible to the index, unable to propose or receive a link,
    with `check` truthfully reporting "no gaps" for it. That held for 13 files until
    2026-07-26 while this gate printed "0 UNCOVERED" at `error` severity. The
    zero-section condition was reported by `warn_coverage` as an advisory WARNING
    only, and `extract --strict` (which does exit 1 on it) was wired into no gate.
    So the strictly worse failure was the quieter one. Both are checked here now."""
    universe = content_files()
    groups = load_scope(args.scope_file)
    covered = set()
    for paths in groups.values():
        covered.update(_norm(f) for f in expand_paths(paths))
    keepout = _read_keepout(args.keepout)

    orphans = sorted(universe - covered - keepout)
    both = sorted(covered & keepout)
    # keepout entries that no longer name a real content file (stale exclusions)
    stale_keepout = sorted(keepout - universe)

    # Scoped-but-invisible: in a group, but no heading matched, so zero sections.
    scoped = sorted(covered - keepout)
    _, empty, _unanchored = parse_paths(scoped)
    invisible = sorted(_norm(p) for p in empty)

    for f in orphans:
        print(f"[crosslink] UNCOVERED: {f} — in no corpus group and not a declared "
              f"keep-out. Add it to a group in {args.scope_file}, or to {args.keepout}.",
              file=sys.stderr)
    for f in both:
        print(f"[crosslink] CONFLICT: {f} is both grouped and kept-out.", file=sys.stderr)
    for f in stale_keepout:
        print(f"[crosslink] note: keep-out entry {f} names no content file (stale?).",
              file=sys.stderr)
    for f in invisible:
        print(f"[crosslink] INVISIBLE: {f} — in a corpus group but contributes 0 "
              f"sections (no heading matched), so it can neither propose nor receive "
              f"a link and 'no gaps' is meaningless for it. Give its headings a "
              f"section number + sec-anchor, or declare it in {args.keepout}.",
              file=sys.stderr)

    print(f"[crosslink] coverage: {len(covered)} grouped, {len(keepout)} kept-out, "
          f"{len(orphans)} UNCOVERED, {len(invisible)} INVISIBLE "
          f"of {len(universe)} content files.", file=sys.stderr)

    if args.severity == "off":
        return 0
    problems = bool(orphans or both or invisible)
    if problems and args.severity == "error":
        return 1
    return 0


_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
_MD_LINK_RE = re.compile(r"\]\(\s*([^)\s]+)")


def _reader_facing_links(path: str) -> set:
    """Repo-relative .md targets a READER can actually follow out of `path`.

    HTML comments are stripped FIRST, and that is the whole point: a mention inside
    `<!-- ... -->` is invisible in the rendered page. `ici-aware-bem-derivation.md` was
    named four times in `equalization-detection.md` and every one sat inside a KEEP
    comment warning "do not renumber, you will stale the wiki" — the survey tracked the
    wiki as a *fragility hazard* and never once offered a reader a way to it.
    """
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    out = set()
    for target in _MD_LINK_RE.findall(_HTML_COMMENT_RE.sub("", text)):
        target = target.split("#", 1)[0].strip()
        if not target.endswith(".md") or "://" in target:
            continue
        try:
            rel = (p.parent / target).resolve().relative_to(Path.cwd().resolve())
        except (ValueError, OSError):
            continue
        out.add(_norm(str(rel)))
    return out


def _md_under(root: str) -> set:
    """Every reader-facing .md under `root` (skipping `_`-prefixed scratch dirs)."""
    return {_norm(str(p)) for p in Path(root).rglob("*.md")
            if not any(part.startswith("_") for part in p.parts)}


def reach_cmd(args):
    """Report every wiki UNREACHABLE from the survey corpus by reader-facing links.

    A derivation wiki no survey links to is invisible: the reader who meets the claim
    never learns the proof exists. This is one-way BY CONSTRUCTION, not by accident —
    the reference-implementation-study G0 gate requires the wiki to cite the SURVEY
    (provenance), and nothing requires the survey to cite the WIKI. So the obligation
    has no owner in the survey->wiki direction, and it failed identically for all three
    2026-07-08 ICI wikis (BEM, banded-MMSE, SIC).

    `crosslink check` structurally CANNOT catch this: it scores unlinked *pairs* with
    symmetric dedup, so a pair linked in one direction is closed (bugs/2026-07-09-15 —
    making that dedup directional would re-introduce the reverse-duplicate spam it fixed).
    Reachability is a different question, and it needs a different check.

    Reachability is transitive from `surveys/`: a wiki linked only from another *reachable*
    wiki is reachable (a hub wiki is legitimate); a wiki linked only from an orphan is not.
    Process/harness wikis with no survey host are declared in the keep-out file.
    """
    wikis = {f for f in _md_under("wikis") if Path(f).parent.name == "wikis"}
    keepout = _read_keepout(args.keepout)

    reachable, frontier = set(), list(_md_under("surveys"))
    while frontier:                       # BFS from the corpus entry points
        for tgt in _reader_facing_links(frontier.pop()):
            if tgt in wikis and tgt not in reachable:
                reachable.add(tgt)
                frontier.append(tgt)

    orphans = sorted(wikis - reachable - keepout)
    stale = sorted(keepout - wikis)

    for f in orphans:
        print(f"[crosslink] UNREACHABLE: {f} — no reader-facing link from any survey "
              f"(mentions inside HTML comments do not count). Link it from the section "
              f"it supports, or declare it in {args.keepout}.", file=sys.stderr)
    for f in stale:
        print(f"[crosslink] note: keep-out entry {f} names no wiki (stale?).",
              file=sys.stderr)
    print(f"[crosslink] reach: {len(reachable)} reachable, {len(keepout)} declared "
          f"standalone, {len(orphans)} UNREACHABLE of {len(wikis)} wikis.", file=sys.stderr)

    if args.severity == "off":
        return 0
    if orphans and args.severity == "error":
        return 1
    return 0


def groups_cmd(args):
    """List corpus groups, or print one group's paths (for /cross-link scoping)."""
    groups = load_scope(args.scope_file)
    if args.group:
        if args.group not in groups:
            print(f"[crosslink] unknown group '{args.group}'. Known: "
                  f"{', '.join(groups)}", file=sys.stderr)
            return 2
        print(" ".join(groups[args.group]))
        return 0
    for name, paths in groups.items():
        print(f"{name}\t{len(paths)} path(s)")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("groups", help="list corpus groups / a group's paths")
    g.add_argument("--scope-file", default=".claude/crosslink-scope")
    g.add_argument("--group", help="print just this group's paths, space-joined")
    g.set_defaults(func=groups_cmd)

    cov = sub.add_parser("coverage", help="report surveys/wikis in no group and not "
                                          "a declared keep-out (H-5; anti-false-green)")
    cov.add_argument("--scope-file", default=".claude/crosslink-scope")
    cov.add_argument("--keepout", default=DEFAULT_KEEPOUT)
    cov.add_argument("--severity", choices=["off", "warn", "error"], default="warn")
    cov.set_defaults(func=coverage_cmd)

    rc = sub.add_parser("reach", help="report wikis unreachable from the survey corpus "
                                      "by reader-facing links (orphaned derivations)")
    rc.add_argument("--keepout", default=DEFAULT_REACH_KEEPOUT)
    rc.add_argument("--severity", choices=["off", "warn", "error"], default="warn")
    rc.set_defaults(func=reach_cmd)

    jp = sub.add_parser("judge-prompt", help="print the canonical Stage-3 judge prompt "
                                             "(one source of truth; bugs/2026-07-10-16)")
    jp.add_argument("--corpus", default=DEFAULT_JUDGE_CORPUS,
                    help="corpus noun for the prompt (default: neutral)")
    jp.add_argument("--schema", action="store_true", help="also print JUDGE_SCHEMA")
    jp.set_defaults(func=judge_prompt_cmd)

    e = sub.add_parser("extract", help="parse sections -> index.json")
    e.add_argument("paths", nargs="+", help="files or dirs (surveys/wikis)")
    e.add_argument("--out", required=True)
    e.add_argument("--strict", action="store_true",
                   help="exit 1 if any scoped file contributes 0 sections")
    e.set_defaults(func=extract_cmd)

    c = sub.add_parser("candidates", help="TF-IDF pre-filter -> candidates.json")
    c.add_argument("--index", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--per-source", type=int, default=DEFAULT_PER_SOURCE)
    c.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES)
    c.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    c.add_argument("--batch", type=int, default=15)
    c.add_argument("--keep-symmetric", action="store_true",
                   help="keep both directions of a pair (default: collapse to "
                        "the assertion->derivation direction)")
    c.add_argument("--rejections", default=DEFAULT_REJECTIONS,
                   help="pair-key ledger of judged-and-rejected candidates")
    c.add_argument("--ignore-rejections", action="store_true",
                   help="re-propose ledger-rejected pairs (use after a large "
                        "rewrite, when section content has changed)")
    c.set_defaults(func=candidates_cmd)

    v = sub.add_parser("review", help="emit the shortlist as a human review sheet "
                                      "(link/merge/reject) — the default apply path")
    v.add_argument("--candidates", required=True)
    v.add_argument("--out", required=True)
    v.set_defaults(func=review_cmd)

    a = sub.add_parser("apply", help="apply HUMAN-reviewed decisions (refuses an "
                                     "unattributed/agent decision file)")
    a.add_argument("--candidates", required=True)
    a.add_argument("--decisions", help="JSON decisions; requires human provenance "
                                       "(a reviewed_by field or --reviewed-by)")
    a.add_argument("--from-review", help="a checked review sheet from `review` "
                                         "(implies human provenance)")
    a.add_argument("--reviewed-by", help="who reviewed these — recorded, and satisfies "
                                         "the provenance guard for a --decisions file")
    a.add_argument("--merge-ledger", default=DEFAULT_MERGE_LEDGER,
                   help=f"where `merge` outcomes are recorded (default: {DEFAULT_MERGE_LEDGER})")
    a.add_argument("--rejections", default=DEFAULT_REJECTIONS,
                   help="where `reject` outcomes are recorded (the pair-key ledger)")
    a.add_argument("--dry-run", action="store_true")
    a.set_defaults(func=apply_cmd)

    k = sub.add_parser("check", help="gap detector for the gates (reports, "
                                     "never writes)")
    k.add_argument("paths", nargs="*", help="corpus files/dirs (if no --index)")
    k.add_argument("--scope-file", help="named-group scope file (e.g. "
                                        ".claude/crosslink-scope); each [group] "
                                        "is an independent TF-IDF corpus")
    k.add_argument("--index", help="prebuilt index.json (else parse paths)")
    k.add_argument("--cache", help="persist/load the parsed index here")
    k.add_argument("--refresh-cache", action="store_true")
    k.add_argument("--changed", action="store_true",
                   help="restrict source endpoint to working-tree changed .md")
    k.add_argument("--since", help="restrict source endpoint to .md changed "
                                   "since this git ref")
    k.add_argument("--severity", choices=["off", "warn", "error"], default="warn")
    k.add_argument("--per-source", type=int, default=DEFAULT_PER_SOURCE)
    k.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES)
    k.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    k.add_argument("--block-score", type=float, default=0.30,
                   help="error severity blocks only gaps at/above this cosine")
    k.add_argument("--keep-symmetric", action="store_true")
    k.add_argument("--json", action="store_true")
    k.add_argument("--rejections", default=DEFAULT_REJECTIONS,
                   help="judged-and-rejected pair ledger (default: "
                        f"{DEFAULT_REJECTIONS})")
    k.add_argument("--ignore-rejections", action="store_true",
                   help="re-report pairs a judge previously rejected")
    k.set_defaults(func=check_cmd)

    r = sub.add_parser("reject", help="append judge-rejected pairs to the ledger")
    r.add_argument("--candidates", required=True)
    r.add_argument("--decisions", required=True)
    r.add_argument("--out", default=DEFAULT_REJECTIONS)
    r.add_argument("--note", default="", help="why (e.g. 'judged 2026-07-09')")
    r.set_defaults(func=reject_cmd)

    return ap


def main():
    args = build_parser().parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
