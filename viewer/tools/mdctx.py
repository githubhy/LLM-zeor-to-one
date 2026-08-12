#!/usr/bin/env python3
"""mdctx — one shared answer to "which bytes of this markdown may a tool rewrite?"

Every marker/anchor tool in this repo re-derives, by regex, which byte ranges are prose
and which are comment / fence / math / code / link-destination.  Each got a different
subset right, and the three tools that *mutate* documents
(`renumber-sections`, `renumber-equations`, `renumber-paragraphs`) had no notion of it
at all.  That is the whole bug class:

  bugs/2026-07-09-04  `renumber-sections --init` promoted a bare `§4.8.1` inside an HTML
                      comment; the injected `-->` closed the comment and spilled its body
                      into the rendered page.  Every gate passed.
  (same class)        `renumber-sections --init` promoted a bare `§3.3.1` inside
                      `\text{}` in a `$$\begin{aligned}` block -> live KaTeX parse error.
  (same class)        `crosslink.py apply` inserted a link *inside* an inline `$...$` span
                      -> live KaTeX parse error.
  bugs/2026-05-06-01  `renumber-equations` needed a bespoke `==color: $$` special-case.

A rewriter's rule is now one predicate: **only rewrite where `writable`**.

Contexts recognised (everything else is PROSE):

    FRONTMATTER  leading `---` ... `---`
    FENCE        ``` / ~~~ fenced blocks, delimiters included
    COMMENT      <!-- ... --> (may span lines)
    DISPLAY_MATH $$ ... $$ blocks, incl. the project's `==color: $$` / `$$==` wrapper
                 and single-line `$$...$$`
    INLINE_CODE  `...`
    INLINE_MATH  $...$
    LINK_DEST    the `(...)` of a `[text](dest)` link

Usage:
    spans = classify(text)                 # sorted, non-overlapping, non-prose only
    mask  = writable_mask(text)            # bytearray; 1 = prose
    if is_writable(mask, a, b): ...
    new, n = sub_in_prose(pattern, repl, text)
    ip = advance_to_prose(text, spans, mask, ip)   # nudge an insertion point out of math

Kept dependency-free and offset-preserving on purpose: the corpus depends on byte-exact
round-tripping, so nothing here parses to an AST and re-renders.
"""
from __future__ import annotations

import re
from enum import Enum

__all__ = [
    "Ctx", "classify", "writable_mask", "is_writable",
    "sub_in_prose", "advance_to_prose", "kind_at",
]


class Ctx(Enum):
    FRONTMATTER = "frontmatter"
    FENCE = "fence"
    COMMENT = "comment"
    DISPLAY_MATH = "display_math"
    INLINE_CODE = "inline_code"
    INLINE_MATH = "inline_math"
    LINK_DEST = "link_dest"


# Contexts an insertion point may be nudged *out of* (the content is still text).
# A fence, a comment or frontmatter is a hard skip: nothing should be linked out of them.
_NUDGEABLE = {Ctx.INLINE_MATH, Ctx.DISPLAY_MATH, Ctx.INLINE_CODE, Ctx.LINK_DEST}

_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_INLINE_CODE = re.compile(r"`[^`\n]+`")
_INLINE_MATH = re.compile(r"(?<!\$)\$[^$\n]+?\$(?!\$)")
_LINK_DEST = re.compile(r"\]\([^)\n]*\)")

# Display math, line-oriented. The `==color:` prefix and `==` suffix are the project's
# highlight wrapper (viewer.js::shieldDisplayMath); renumber-equations models it as
# HIGHLIGHT_PREFIX. Modelled once, here.
_HL = r"(?:==\w+:\s*)?"
_DISP_OPEN = re.compile(rf"^\s*{_HL}\$\$\s*$")
_DISP_CLOSE = re.compile(r"^\s*\$\$(?:==)?\s*$")
_DISP_ONELINE = re.compile(rf"^\s*{_HL}\$\$.*\$\$(?:==)?\s*$")


def _line_spans(text: str):
    """(start, end_exclusive_including_newline) for every line."""
    out, i = [], 0
    for line in text.splitlines(keepends=True):
        out.append((i, i + len(line), line.rstrip("\r\n")))
        i += len(line)
    return out


def classify(text: str):
    """Return sorted, merged, non-overlapping (start, end, Ctx) for all NON-prose spans."""
    spans: list[tuple[int, int, Ctx]] = []
    lines = _line_spans(text)

    # --- frontmatter -------------------------------------------------------
    if lines and lines[0][2].strip() == "---":
        for s, e, raw in lines[1:]:
            if raw.strip() == "---":
                spans.append((0, e, Ctx.FRONTMATTER))
                break

    # --- fences and display math (line-oriented, mutually exclusive) --------
    in_fence = False
    fence_tok = ""
    in_disp = False
    disp_start = 0
    for s, e, raw in lines:
        if in_fence:
            spans.append((s, e, Ctx.FENCE))
            if raw.strip().startswith(fence_tok):
                in_fence = False
            continue
        if in_disp:
            if _DISP_CLOSE.match(raw):
                spans.append((disp_start, e, Ctx.DISPLAY_MATH))
                in_disp = False
            continue
        m = _FENCE.match(raw)
        if m:
            in_fence, fence_tok = True, m.group(1)
            spans.append((s, e, Ctx.FENCE))
            continue
        if _DISP_ONELINE.match(raw):
            spans.append((s, e, Ctx.DISPLAY_MATH))
            continue
        if _DISP_OPEN.match(raw):
            in_disp, disp_start = True, s
            continue
    if in_fence:                                    # unterminated fence -> to EOF
        spans.append((lines[-1][0], len(text), Ctx.FENCE))
    if in_disp:                                     # unterminated $$ -> to EOF
        spans.append((disp_start, len(text), Ctx.DISPLAY_MATH))

    # --- comments (may span lines; must beat the inline passes) -------------
    for m in _COMMENT.finditer(text):
        spans.append((m.start(), m.end(), Ctx.COMMENT))

    spans.sort()
    spans = _merge(spans)

    # --- inline passes, only where still prose -----------------------------
    mask = _mask_from(text, spans)
    for rx, kind in ((_INLINE_CODE, Ctx.INLINE_CODE),
                     (_INLINE_MATH, Ctx.INLINE_MATH),
                     (_LINK_DEST, Ctx.LINK_DEST)):
        found = []
        for m in rx.finditer(text):
            if all(mask[i] for i in range(m.start(), m.end())):
                found.append((m.start(), m.end(), kind))
        for s, e, k in found:
            for i in range(s, e):
                mask[i] = 0
        spans.extend(found)

    spans.sort()
    return spans


def _merge(spans):
    """Merge overlapping spans, keeping the FIRST (outermost) kind."""
    out = []
    for s, e, k in spans:
        if out and s <= out[-1][1]:
            ps, pe, pk = out[-1]
            out[-1] = (ps, max(pe, e), pk)
        else:
            out.append((s, e, k))
    return out


def _mask_from(text, spans):
    mask = bytearray(b"\x01" * len(text))
    for s, e, _ in spans:
        for i in range(s, min(e, len(text))):
            mask[i] = 0
    return mask


def writable_mask(text: str) -> bytearray:
    """1 where the byte is plain prose and a tool may rewrite it; 0 otherwise."""
    return _mask_from(text, classify(text))


def is_writable(mask: bytearray, start: int, end: int) -> bool:
    """True iff [start, end) lies wholly in prose."""
    if start < 0 or end > len(mask) or start >= end:
        return False
    return all(mask[i] for i in range(start, end))


def kind_at(spans, offset: int):
    for s, e, k in spans:
        if s <= offset < e:
            return k
    return None


def sub_in_prose(pattern, repl, text: str):
    """re.sub, but only for matches lying wholly in prose. Returns (new_text, n)."""
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    mask = writable_mask(text)
    edits = [m for m in pattern.finditer(text) if is_writable(mask, m.start(), m.end())]
    for m in reversed(edits):                       # right-to-left: earlier offsets stay valid
        text = text[:m.start()] + (repl(m) if callable(repl) else m.expand(repl)) + text[m.end():]
    return text, len(edits)


def advance_to_prose(text: str, spans, mask: bytearray, offset: int):
    """Nudge an insertion point out of a math/code/link span to just after it.

    Returns None when the offset sits in a context nothing should be inserted near
    (a fence, an HTML comment, frontmatter) — the caller should skip that insertion.
    """
    if offset >= len(mask) or mask[offset]:
        return offset
    k = kind_at(spans, offset)
    if k not in _NUDGEABLE:
        return None
    for s, e, kk in spans:
        if s <= offset < e and kk is k:
            return e
    return None
