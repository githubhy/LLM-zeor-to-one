---
name: source-fetch
description: Acquire full-text papers and books as PDFs from open-access sources — Semantic Scholar, OpenAlex, arXiv, Crossref, and (optional) Unpaywall — via the keyless `oa_fetch.py` resolver, with keyless LibGen+ and an optional Anna's Archive as shadow-library fallbacks. Use when deep-research-survey Phase 3 needs full-text acquisition, or standalone when the user asks to download a specific paper or book.
---

# Source Fetch

## Overview

Resolve a paper to an **open-access PDF** through a keyless cascade and download it. The
acquisition spine is `oa_fetch.py` (stdlib-only), which tries, in priority order: Semantic
Scholar (`openAccessPdf`) → OpenAlex (`best_oa_location` / `oa_url`) → arXiv direct
(`arxiv.org/pdf/<id>`) → Crossref (title→DOI) → Unpaywall (DOI→OA PDF, if an email is
configured) → **LibGen+** (keyless shadow library; the `key` token is scraped per-request, so
no secret is needed — this is also the primary path for books) → Anna's Archive (only if a key
is configured; last resort). Both shadow-library fallbacks auto-select a currently-UP mirror
from **open-slum.org** — the Shadow Library Uptime Monitor — so a down/blocked mirror is
skipped. Every candidate is title-verified and every download is content-validated, so wrong or
paywalled hits are rejected.

**Open-access first (the shadow stage is deferred).** For a paper, the LibGen+/Anna's stage —
and its open-slum.org lookup — runs *only* if the OA cascade returns nothing, or if every OA
candidate fails download validation. Books skip the paper-centric OA APIs and go straight to the
shadow stage. So an openly-available paper never contacts a shadow library or SLUM, and when SLUM
*is* needed its status snapshot is fetched at most once per run (memoized — both the LibGen and
Anna's mirror lookups reuse it).

> History: this skill previously required the Anna's Archive API key (`fast_download.json`).
> That key is no longer available, so acquisition was reworked to be OA-first and keyless;
> Anna's Archive is now an optional, key-gated fallback only. (This is a rewrite of the
> acquisition path, not a default-off flag — the old default was broken.)

## Configuration

Read from `.env` in the repository root (all optional — the keyless cascade works with none):

| Variable | Purpose | Default |
|----------|---------|---------|
| `UNPAYWALL_EMAIL` | enables the Unpaywall DOI→OA step (must be a REAL email; a placeholder is rejected) | *(unset → Unpaywall skipped)* |
| `ANNAS_SECRET_KEY` | enables the Anna's Archive last-resort fallback | *(unset → fallback skipped)* |
| `ANNAS_MIRROR` | pin a specific Anna's Archive mirror base URL | *(unset → mirror auto-selected live via open-slum.org, then static fallbacks)* |
| `LIBGEN_MIRROR` | pin a specific LibGen+ (libgen.li-family) mirror base URL | *(unset → mirror auto-selected live via open-slum.org, then static fallbacks)* |
| `ANNAS_DOWNLOAD_PATH` | local download directory | `./download/` |

> **LibGen+ is keyless.** Unlike Anna's Archive, the LibGen+ path needs no API key — the
> `get.php?...&key=<token>` download key is a per-request token scraped from the book's
> `ads.php` page. It runs whenever the OA cascade comes up empty (papers) and is the primary
> book source. It is best-effort: mirrors apply anti-bot throttling, so a fetch may be skipped
> and the next mirror tried; download validation (below) rejects any non-PDF intermediate page.

> **Mirror selection (open-slum.org / SLUM).** When a shadow-library fallback runs,
> `oa_fetch.py` queries open-slum.org's status API for currently-UP mirrors — Anna's Archive
> (`annas-archive.gl/.vg/.pk/.gd`) for that path, LibGen+ (`libgen.bz/.la/.gl/.vg`) for the
> LibGen path — and tries them in listed order, falling back to a built-in static list if SLUM
> is unreachable. Set `ANNAS_MIRROR` / `LIBGEN_MIRROR` to override. (SLUM also monitors
> Z-Library and other mirrors, not wired in.)

`oa_fetch.py` auto-reads these from `.env`; you do not need to export them.

## Workflow

The resolver lives at `.claude/skills/source-fetch/oa_fetch.py`.

### Step 1 — Resolve candidates

Prefer a precise identifier when you have one (most reliable); fall back to a title query:

```bash
python .claude/skills/source-fetch/oa_fetch.py "arxiv:2203.11854"          # arXiv id (best)
python .claude/skills/source-fetch/oa_fetch.py "doi:10.1109/JIOT.2024.3418675"
python .claude/skills/source-fetch/oa_fetch.py "Author Title Year keywords"  # free-text (noisier)
```

It prints JSON: a `candidates` list (ranked by cascade priority), each with `pdf_url`,
`source`, and — for verification — `title`/`doi`/`arxiv_id`.

### Step 2 — Verify the candidate matches

Free-text title search is best-effort and returns *related* papers too. Compare each
candidate's `title`/`doi` against the expected author/title/year and **discard non-matches**
before downloading. An `arxiv:`/`doi:` query skips this ambiguity.

### Step 3 — Download + validate

Let the resolver download the first candidate that validates (content-type/`%PDF-` magic and
size >= 100 KB — rejects HTML landing pages and stubs):

```bash
python .claude/skills/source-fetch/oa_fetch.py "<query>" --download download/<filename>.pdf
```

Or download a specific verified `pdf_url` yourself and apply the same checks. **Filename
convention:** `<author>-<shorttitle>-<year>.pdf`, kebab-case, no spaces (e.g.
`harris-multirate-signal-processing-2004.pdf`).

### Step 4 — Confirm content

Extract the TOC / first-page text with pymupdf to confirm the content matches:

```bash
python -c "
import fitz
doc = fitz.open('download/<filename>.pdf')
toc = doc.get_toc()
print('\n'.join('  '*l + t + f' (p.{p})' for l,t,p in toc[:15]) if toc else doc[0].get_text()[:500])
doc.close()
"
```

If it does not match, delete and try the next candidate.

### Step 5 — Record / fall back

- Success → ledger entry: `[Author, Title, Year] (local: download/<filename>)`.
- All candidates fail → log in the evidence ledger Gaps column; fall back to abstract-level
  citation. (The resolver will already have tried keyless LibGen+, and Anna's Archive last if
  `ANNAS_SECRET_KEY` is set.)

## Books

The OA APIs are paper-centric, so `--book` skips them and goes straight to the shadow-library
fallbacks: **keyless LibGen+ first** (no key needed), then Anna's Archive if `ANNAS_SECRET_KEY`
is set. LibGen+ makes book acquisition work out of the box; if every mirror is blocked or the
title isn't held, flag the gap and fall back to an abstract-level citation.

```bash
python .claude/skills/source-fetch/oa_fetch.py "Vaidyanathan Multirate Systems" --book --download download/<filename>.pdf
```

## Rules

- **Format:** PDF only.
- **Prefer identifiers:** an `arxiv:`/`doi:` query is far more reliable than a title search.
- **Verify before trusting:** title-match each candidate (Step 2) AND content-validate every
  download (Steps 3–4). Never record a source you have not confirmed.
- **Budget:** ~50 downloads per day; track `Downloads: N/~50 used, holdback: H remaining`.
- **Holdback:** when called from `deep-research-survey`, reserve ~10–15 for synthesis-phase gaps.
- **Filenames:** `<author>-<shorttitle>-<year>.pdf`, kebab-case.
- **Size check:** reject files < 100 KB (the resolver enforces this on `--download`).
- **Ledger:** record each success as `(local: download/<filename>)`; log failures as gaps.

## Standalone Usage

```
/source-fetch Farrow continuously variable digital delay
/source-fetch arxiv:2203.11854
/source-fetch doi:10.1109/JIOT.2024.3418675
/source-fetch book: Vaidyanathan Multirate Systems
```

Run Steps 1–5, report the result, and place the file in the download directory.
