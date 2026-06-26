#!/usr/bin/env python3
"""crosslink.py — cheap, pre-filtered cross-link proposer for the survey corpus.

Motivation
----------
A prior all-agent cross-link sweep cost ~11.5M tokens / 217 sonnet agents to
land ~130 links (~87k tokens/link) because it handed *candidate discovery*,
*judgment*, AND *application* all to agents — and the apply agents silently
failed to persist on the stricter files. Three of those four jobs are
deterministic. This tool does the
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

Link convention (keyed on the TARGET's corpus):
  * target is a survey section  -> secxref marker + § glyph:
        <!-- secxref:D.3.1 -->[§D.3.1](appendix-d.md#sec-D.3.1)
  * target is a wiki section     -> plain relative link, descriptive text, no §:
        [softmax derivation](../../wikis/foo.md#sec-4)

Pure stdlib. Corpus is inferred from path (surveys/** -> survey, wikis/** ->
wiki). Anchors are the canonical `sec-<num>` scheme shared by both corpora.

Usage
-----
    python viewer/tools/crosslink.py extract \
        surveys/llms-for-coding surveys/attention-demo ... \
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
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# UTF-8 stdout/stderr guard (the § glyph etc. must not crash on a non-UTF-8
# console/pipe — GBK/CP936 crash class, bug 2026-06-22-01). Mirrors
# renumber-sections.py / validate-refs.py.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# -- Canonical patterns (mirrors viewer/tools/renumber-sections.py) ----------

HEADING_RE = re.compile(
    r'^(?:<a\s+id="[^"]*"></a>)?'
    r"(?P<hashes>#{2,6})\s+"
    r'(?:<a\s+id="[^"]*"></a>)?'
    r"(?P<num>[A-Z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*)"
    r"\s+(?P<title>.*)$"
)
SEC_ANCHOR_RE = re.compile(
    r'<a\s+id="(sec-[A-Za-z]?\d+(?:\.\d+)+(?:-[\w.\-]+)?|sec-[A-Z]\.\d+(?:\.\d+)*(?:-[\w.\-]+)?)"></a>'
)
LINK_TARGET_RE = re.compile(r"\]\(([^)]+)\)")
FENCE_RE = re.compile(r"^\s*```")

SKIP_BASENAMES = {"index.md", "references.md"}


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
    s = re.sub(r"<[^>]+>", " ", s)                   # html tags
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r" \1 ", s)  # links -> keep text
    s = s.replace("**", " ").replace("==", " ").replace("`", " ").replace("*", " ")
    return s


def tokenize(text: str) -> list[str]:
    s = _strip_noise(text).lower()
    raw = [t for t in _TOKEN_RE.findall(s) if len(t) >= 3 and t not in _STOP]
    toks = list(raw)
    # bigrams of adjacent kept unigrams capture "gradient descent", "scaling law"
    for a, b in zip(raw, raw[1:]):
        toks.append(a + "_" + b)
    return toks


# -- Section extraction ------------------------------------------------------

def extract_file(path: str) -> list[dict]:
    """Parse one markdown file into a list of section dicts."""
    text = Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    rel = path.replace("\\", "/")
    base = os.path.basename(rel)
    corpus = corpus_of(rel)

    # Find heading line indices + their section number / title / anchor.
    heads = []  # (line_idx, sec_num, title, anchor_id_or_None)
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if not m:
            continue
        am = SEC_ANCHOR_RE.search(line)
        anchor = am.group(1) if am else None
        heads.append((i, m.group("num"), m.group("title").strip(), anchor))

    sections = []
    for h_idx, (line_i, sec_num, title, anchor) in enumerate(heads):
        end = heads[h_idx + 1][0] if h_idx + 1 < len(heads) else len(lines)
        body = "\n".join(lines[line_i + 1:end])
        # existing outbound links in this section: set of (basename, anchor)
        existing = set()
        for tgt in LINK_TARGET_RE.findall(lines[line_i] + "\n" + body):
            tgt = tgt.strip()
            if tgt.startswith("#"):
                existing.add((base, tgt[1:]))
            elif "#" in tgt:
                fpart, apart = tgt.split("#", 1)
                existing.add((os.path.basename(fpart), apart))
        # first paragraph snippet (for the agent; kept short)
        snippet = first_paragraph(body)
        sections.append({
            "file": rel,
            "base": base,
            "corpus": corpus,
            "sec": sec_num,
            "title": title,
            "anchor": anchor,                       # None if heading lacks sec-anchor
            "tokens": tokenize(title + " " + body),
            "snippet": snippet,
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
    return s[: cut + 1] if cut > 80 else s[:limit]


def expand_paths(args_paths: list[str]) -> list[str]:
    out = []
    for a in args_paths:
        p = Path(a)
        if p.is_dir():
            for f in sorted(p.glob("*.md")):
                if f.name in SKIP_BASENAMES or f.name.endswith(".index.md"):
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

def make_link(src: dict, dst: dict) -> tuple[str, str]:
    """Return (link_markdown, dedup_target) for a src->dst cross-link.

    dedup_target is the `relpath#anchor` string used for idempotency.
    """
    rel = os.path.relpath(dst["file"], start=os.path.dirname(src["file"]))
    rel = rel.replace("\\", "/")
    anchor = dst["anchor"]  # e.g. "sec-D.3.1"
    dedup = f"{rel}#{anchor}"
    sec = dst["sec"]
    if dst["corpus"] == "survey":
        link = f"<!-- secxref:{sec} -->[§{sec}]({dedup})"
    else:
        text = short_text(dst["title"])
        link = f"[{text}]({dedup})"
    return link, dedup


def short_text(title: str, words: int = 6) -> str:
    t = re.sub(r"\s+", " ", title).strip().rstrip(".")
    parts = t.split(" ")
    return " ".join(parts[:words])


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
                        source_bases=None, file_scoped=False):
    """Core pre-filter shared by `candidates` and `check`.

    Returns a score-sorted list of candidate dicts (no id/batch assignment, no
    max cap). `source_bases`, if given, restricts source endpoints to those
    file basenames (used by `check --changed`). `file_scoped` dedups a target
    already linked anywhere in the source *file* (what `apply` would skip),
    not just in the source section — used by `check` so its report matches
    what `apply` would actually add.
    """
    vecs, _ = build_vectors(sections)
    linkable = [i for i, s in enumerate(sections) if s["anchor"]]

    file_existing = defaultdict(set)
    if file_scoped:
        for s in sections:
            file_existing[s["base"]].update((b, a) for b, a in s["existing"])

    cands = []
    for i, src in enumerate(sections):
        if source_bases is not None and src["base"] not in source_bases:
            continue
        existing = set(file_existing[src["base"]]) if file_scoped \
            else {(b, a) for b, a in src["existing"]}
        scored = []
        for j in linkable:
            if j == i:
                continue
            dst = sections[j]
            if dst["base"] == src["base"]:
                continue  # cross-file only
            # dedup against existing outbound links (section- or file-scoped)
            if (dst["base"], dst["anchor"]) in existing:
                continue
            sc = cosine(vecs[i], vecs[j])
            if sc >= min_score:
                scored.append((sc, j))
        scored.sort(reverse=True)
        for sc, j in scored[:per_source]:
            dst = sections[j]
            link_md, dedup = make_link(src, dst)
            cands.append({
                "score": round(sc, 4),
                "pair_key": "|".join(sorted([f"{src['base']}#{src['sec']}",
                                             f"{dst['base']}#{dst['sec']}"])),
                "_st": tier_of(src["corpus"], src["base"]),
                "_dt": tier_of(dst["corpus"], dst["base"]),
                "source": {"file": src["file"], "sec": src["sec"],
                           "title": src["title"], "snippet": src["snippet"]},
                "target": {"file": dst["file"], "sec": dst["sec"],
                           "title": dst["title"], "snippet": dst["snippet"],
                           "corpus": dst["corpus"]},
                "link_markdown": link_md,
                "dedup_target": dedup,
            })

    if not keep_symmetric:
        # collapse each unordered pair to its assertion->derivation direction:
        # prefer larger (dst_tier - src_tier), then higher score, then a
        # deterministic source-key tiebreak.
        best = {}
        for c in cands:
            k = c["pair_key"]
            key = (c["_dt"] - c["_st"], c["score"],
                   f"{c['source']['file']}#{c['source']['sec']}")
            cur = best.get(k)
            if cur is None or key > cur[0]:
                best[k] = (key, c)
        cands = [v[1] for v in best.values()]

    for c in cands:
        del c["_st"], c["_dt"]
    cands.sort(key=lambda c: c["score"], reverse=True)
    return cands


def load_or_build_index(args):
    """Return the section list, from --index, --cache, or a fresh corpus parse."""
    if getattr(args, "index", None):
        return json.loads(Path(args.index).read_text(encoding="utf-8"))["sections"]
    cache = getattr(args, "cache", None)
    if cache and Path(cache).exists() and not getattr(args, "refresh_cache", False):
        return json.loads(Path(cache).read_text(encoding="utf-8"))["sections"]
    sections = []
    for p in expand_paths(args.paths):
        sections.extend(extract_file(p))
    if cache:
        Path(cache).write_text(
            json.dumps({"sections": sections}, indent=2, ensure_ascii=False),
            encoding="utf-8")
    return sections


def git_changed_md(since=None):
    """Return a set of changed .md file basenames (working tree, or since REF)."""
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
                bases.add(os.path.basename(line))
    return bases


def candidates_cmd(args):
    sections = json.loads(Path(args.index).read_text(encoding="utf-8"))["sections"]
    cands = generate_candidates(sections, args.per_source, args.min_score,
                                args.keep_symmetric)
    cands = cands[: args.max_candidates]
    for n, c in enumerate(cands, 1):
        c["id"] = f"C{n:03d}"

    # group into agent batches
    batches = [cands[k:k + args.batch] for k in range(0, len(cands), args.batch)]
    out = {"candidates": cands,
           "batches": [[c["id"] for c in b] for b in batches],
           "n_candidates": len(cands), "n_batches": len(batches)}
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False),
                              encoding="utf-8")

    print(f"{len(cands)} candidates in {len(batches)} batches -> {args.out}",
          file=sys.stderr)
    print("\nTop candidates:", file=sys.stderr)
    for c in cands[:15]:
        s, t = c["source"], c["target"]
        sb = os.path.basename(s["file"])
        tb = os.path.basename(t["file"])
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
    sections = load_or_build_index(args)
    source_bases = None
    if args.changed or args.since:
        source_bases = git_changed_md(args.since)
        if not source_bases:
            if args.severity != "off":
                print("[crosslink] no changed .md files; no gaps to check.",
                      file=sys.stderr)
            return 0
    cands = generate_candidates(sections, args.per_source, args.min_score,
                                args.keep_symmetric, source_bases=source_bases,
                                file_scoped=True)
    cands = cands[: args.max_candidates]

    if args.json:
        print(json.dumps({"gaps": cands, "n": len(cands)},
                         indent=2, ensure_ascii=False))
    elif cands:
        scope = "changed-file " if source_bases is not None else ""
        print(f"[crosslink] {len(cands)} unlinked {scope}cross-link candidate(s) "
              f"(>= cosine {args.min_score}; advisory, not blocking):",
              file=sys.stderr)
        for c in cands:
            s, t = c["source"], c["target"]
            print(f"    {c['score']:.3f}  {os.path.basename(s['file'])} "
                  f"{s['sec']}  ->  {os.path.basename(t['file'])} {t['sec']} "
                  f"({t['corpus']})", file=sys.stderr)
        print("    Clear with: /cross-link  (or crosslink.py candidates|apply)",
              file=sys.stderr)
    else:
        print("[crosslink] no cross-link gaps.", file=sys.stderr)

    if args.severity == "error":
        blocking = [c for c in cands if c["score"] >= args.block_score]
        if blocking:
            print(f"[crosslink] BLOCKED - {len(blocking)} obvious cross-link "
                  f"gap(s) at or above cosine {args.block_score}. Add the link "
                  f"or run /cross-link.", file=sys.stderr)
            return 1
    return 0


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
    pos = ntext.find(nquote)
    if pos == -1:
        # prefix fallback: last sentence of the quote
        tail = re.split(r"(?<=[.;:])\s+", nquote)[-1]
        if len(tail) >= 12:
            pos = ntext.find(tail)
            if pos != -1:
                pos_end = pos + len(tail)
                return imap[pos_end - 1] + 1
        return None
    pos_end = pos + len(nquote)
    return imap[pos_end - 1] + 1


def apply_cmd(args):
    cdata = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in cdata["candidates"]}
    decisions = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    if isinstance(decisions, dict):
        decisions = decisions.get("decisions", [])

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
        for it in items:
            if it["dedup"] in text:
                skipped.append((it["id"], "already-present"))
                continue
            ip = find_insertion_point(text, it["phrase"]) if it["phrase"] else None
            if ip is None:
                skipped.append((it["id"], "phrase-not-found"))
                continue
            planned.append((ip, it))
        planned.sort(key=lambda x: x[0], reverse=True)
        for ip, it in planned:
            ins = f" ({it['link']})"
            text = text[:ip] + ins + text[ip:]
            total_applied += 1
            print(f"  apply {it['id']}: {os.path.basename(fpath)} <- {it['dedup']}",
                  file=sys.stderr)
        if planned and not args.dry_run:
            Path(fpath).write_text(text, encoding="utf-8")

    print(f"\napplied {total_applied}/{kept} kept "
          f"({len(skipped)} skipped){' [DRY-RUN]' if args.dry_run else ''}",
          file=sys.stderr)
    for cid, why in skipped:
        print(f"  skip {cid}: {why}", file=sys.stderr)


def extract_cmd(args):
    paths = expand_paths(args.paths)
    sections = []
    for p in paths:
        sections.extend(extract_file(p))
    Path(args.out).write_text(
        json.dumps({"sections": sections}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    n_anchored = sum(1 for s in sections if s["anchor"])
    print(f"{len(sections)} sections ({n_anchored} linkable) from "
          f"{len(paths)} files -> {args.out}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract", help="parse sections -> index.json")
    e.add_argument("paths", nargs="+", help="files or dirs (surveys/wikis)")
    e.add_argument("--out", required=True)
    e.set_defaults(func=extract_cmd)

    c = sub.add_parser("candidates", help="TF-IDF pre-filter -> candidates.json")
    c.add_argument("--index", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--per-source", type=int, default=3)
    c.add_argument("--max-candidates", type=int, default=60)
    c.add_argument("--min-score", type=float, default=0.10)
    c.add_argument("--batch", type=int, default=15)
    c.add_argument("--keep-symmetric", action="store_true",
                   help="keep both directions of a pair (default: collapse to "
                        "the assertion->derivation direction)")
    c.set_defaults(func=candidates_cmd)

    a = sub.add_parser("apply", help="idempotent apply of approved decisions")
    a.add_argument("--candidates", required=True)
    a.add_argument("--decisions", required=True)
    a.add_argument("--dry-run", action="store_true")
    a.set_defaults(func=apply_cmd)

    k = sub.add_parser("check", help="gap detector for the gates (reports, "
                                     "never writes)")
    k.add_argument("paths", nargs="*", help="corpus files/dirs (if no --index)")
    k.add_argument("--index", help="prebuilt index.json (else parse paths)")
    k.add_argument("--cache", help="persist/load the parsed index here")
    k.add_argument("--refresh-cache", action="store_true")
    k.add_argument("--changed", action="store_true",
                   help="restrict source endpoint to working-tree changed .md")
    k.add_argument("--since", help="restrict source endpoint to .md changed "
                                   "since this git ref")
    k.add_argument("--severity", choices=["off", "warn", "error"], default="warn")
    k.add_argument("--per-source", type=int, default=2)
    k.add_argument("--max-candidates", type=int, default=40)
    k.add_argument("--min-score", type=float, default=0.12)
    k.add_argument("--block-score", type=float, default=0.30,
                   help="error severity blocks only gaps at/above this cosine")
    k.add_argument("--keep-symmetric", action="store_true")
    k.add_argument("--json", action="store_true")
    k.set_defaults(func=check_cmd)

    args = ap.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
