#!/usr/bin/env python3
"""oa_fetch.py — resolve a paper to an open-access PDF via a KEYLESS cascade, then optionally
download + validate it. Replaces the Anna's-Archive-only acquisition path of the source-fetch
skill (the Anna's Archive API key is no longer available).

Cascade (all keyless unless noted), tried in order, candidates accumulated + de-duplicated:
  1. Semantic Scholar  graph/v1/paper/search -> openAccessPdf.url (+ ArXiv externalId)
  2. OpenAlex          works?search=          -> best_oa_location.pdf_url / open_access.oa_url (+ DOI, arXiv)
  3. arXiv direct      arxiv.org/pdf/<id>     (rock-solid once an arXiv id is known)
  4. Crossref          works?query.bibliographic= -> DOI (for verification + Unpaywall)
  5. Unpaywall         v2/<DOI>?email=        -> best_oa_location.url_for_pdf   [needs UNPAYWALL_EMAIL]
  6. LibGen+           ads.php -> get.php?...&key=  -> download_url             [keyless; primary --book source]
  7. Anna's Archive    fast_download.json     -> download_url                   [needs ANNAS_SECRET_KEY; last resort]

LibGen+ and Anna's Archive auto-select a currently-UP mirror from open-slum.org (SLUM, the
Shadow Library Uptime Monitor); both are best-effort and gated behind the OA cascade above.

Usage:
  python oa_fetch.py "Author Title Year"                 # -> JSON: ranked PDF candidates w/ titles to verify
  python oa_fetch.py "doi:10.1109/JIOT.2024.3418675"
  python oa_fetch.py "arxiv:2203.11854"
  python oa_fetch.py "<query>" --download download/name.pdf   # resolve + download first VALID pdf (content-type+size)
  python oa_fetch.py "<query>" --book                    # books: keyless LibGen+ (then Anna's, if key); OA APIs are paper-centric

Stdlib only. Each source is best-effort: failures are caught and skipped, never fatal.
"""
import json, os, re, sys, urllib.request, urllib.parse
from pathlib import Path

def _load_env():
    """Populate env from repo-root .env for UNPAYWALL_EMAIL / ANNAS_SECRET_KEY if unset."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        env = parent / ".env"
        if env.is_file():
            for line in env.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
            break
_load_env()
EMAIL = os.environ.get("UNPAYWALL_EMAIL", "").strip()
ANNAS_KEY = os.environ.get("ANNAS_SECRET_KEY", "").strip()
ANNAS_MIRROR = os.environ.get("ANNAS_MIRROR", "").strip()   # optional explicit override
UA = f"source-fetch/2.0 (research; mailto:{EMAIL or 'anon@example.org'})"
# open-slum.org = SLUM (Shadow Library Uptime Monitor, an Uptime Kuma instance). Its public
# status-page API exposes each mirror's URL + live up/down, so the Anna's fallback can target
# a currently-UP mirror instead of a hardcoded domain (mirrors rotate / get blocked).
SLUM_API = "https://open-slum.org/api/status-page"
SLUM_SLUG = "slum"
ANNAS_STATIC_MIRRORS = ["https://annas-archive.gl", "https://annas-archive.vg",
                        "https://annas-archive.pk", "https://annas-archive.gd"]
LIBGEN_MIRROR = os.environ.get("LIBGEN_MIRROR", "").strip()   # optional explicit override
LIBGEN_STATIC_MIRRORS = ["https://libgen.bz", "https://libgen.gl", "https://libgen.la", "https://libgen.vg"]
BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

def _get(url, timeout=15, headers=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers
def _json(url, timeout=15):
    try:
        body, _ = _get(url, timeout); return json.loads(body)
    except Exception as e:
        return {"_error": str(e)}
def _q(s):
    return urllib.parse.quote(s)

def _arxiv_pdf(aid):
    aid = aid.replace("arxiv:", "").replace("arXiv:", "").strip()
    return f"https://arxiv.org/pdf/{aid}", aid

def from_semanticscholar(query):
    out = []
    d = _json(f"https://api.semanticscholar.org/graph/v1/paper/search?query={_q(query)}&limit=3"
              f"&fields=title,openAccessPdf,externalIds,year")
    for p in (d.get("data") or [])[:3]:
        oa = (p.get("openAccessPdf") or {}).get("url")
        ax = (p.get("externalIds") or {}).get("ArXiv")
        title = p.get("title")
        if oa: out.append({"pdf_url": oa, "source": "semanticscholar", "title": title,
                           "doi": (p.get("externalIds") or {}).get("DOI"), "arxiv_id": ax})
        elif ax:
            url, aid = _arxiv_pdf(ax)
            out.append({"pdf_url": url, "source": "s2->arxiv", "title": title, "arxiv_id": aid})
    return out

def from_openalex(query):
    out = []
    mail = f"&mailto={_q(EMAIL)}" if EMAIL else ""
    d = _json(f"https://api.openalex.org/works?search={_q(query)}&per_page=3{mail}")
    for w in (d.get("results") or [])[:3]:
        title = w.get("title"); doi = (w.get("doi") or "").replace("https://doi.org/", "") or None
        ax = None
        loc = w.get("primary_location") or {}
        if (loc.get("source") or {}).get("type") == "repository" and "arxiv" in (loc.get("landing_page_url") or "").lower():
            m = re.search(r'arxiv\.org/abs/([\w.\-/]+)', loc.get("landing_page_url",""))
            ax = m.group(1) if m else None
        pdf = (w.get("best_oa_location") or {}).get("pdf_url") or w.get("open_access", {}).get("oa_url")
        if pdf: out.append({"pdf_url": pdf, "source": "openalex", "title": title, "doi": doi, "arxiv_id": ax})
        elif ax:
            url, aid = _arxiv_pdf(ax); out.append({"pdf_url": url, "source": "openalex->arxiv", "title": title, "doi": doi, "arxiv_id": aid})
    return out

def from_crossref(query):
    d = _json(f"https://api.crossref.org/works?query.bibliographic={_q(query)}&rows=1&select=DOI,title")
    items = (d.get("message") or {}).get("items") or []
    if items:
        return items[0].get("DOI"), (items[0].get("title") or [""])[0]
    return None, None

def from_unpaywall(doi):
    if not EMAIL or not doi:
        return None
    d = _json(f"https://api.unpaywall.org/v2/{_q(doi)}?email={_q(EMAIL)}")
    if d.get("error"):
        return None
    loc = d.get("best_oa_location") or {}
    return loc.get("url_for_pdf") or loc.get("url")

_SLUM_SNAPSHOT = {}   # in-process memo: SLUM is queried at most once per process (config + heartbeat)

def _slum_snapshot():
    """Fetch SLUM's status-page config + heartbeat ONCE per process and memoize. Both shadow
    paths (LibGen + Anna's) filter the same snapshot, so this collapses what was 4 SLUM HTTP
    calls per resolve (2 per `live_mirrors`) down to 2, and avoids tripping SLUM's rate-limiter
    across a batch. Best-effort: caches ({}, {}) on any failure so callers degrade to statics."""
    if "data" not in _SLUM_SNAPSHOT:
        try:
            cfg = _json(f"{SLUM_API}/{SLUM_SLUG}")
            hb = (_json(f"{SLUM_API}/heartbeat/{SLUM_SLUG}") or {}).get("heartbeatList", {}) or {}
            _SLUM_SNAPSHOT["data"] = (cfg if isinstance(cfg, dict) else {}, hb)
        except Exception:
            _SLUM_SNAPSHOT["data"] = ({}, {})
    return _SLUM_SNAPSHOT["data"]

def live_mirrors(keyword):
    """UP mirror base URLs from the (memoized) open-slum.org snapshot whose monitor name contains
    <keyword> (e.g. 'anna', 'libgen'), ordered as listed. Best-effort -> [] on any failure."""
    try:
        cfg, hb = _slum_snapshot()
        up = []
        for g in cfg.get("publicGroupList", []):
            for m in g.get("monitorList", []):
                name = (m.get("name") or "").strip().lower()
                url = (m.get("url") or "").strip().rstrip("/")
                beats = hb.get(str(m.get("id")))
                if url and keyword in name and beats and beats[-1].get("status") == 1:
                    up.append(url)
        return up
    except Exception:
        return []

def _mirror_priority(explicit, keyword, static):
    """explicit override -> live (up) mirrors from SLUM -> static fallbacks, de-duplicated."""
    cands = ([explicit] if explicit else []) + live_mirrors(keyword) + static
    seen, ordered = set(), []
    for m in cands:
        m = (m or "").rstrip("/")
        if m and m not in seen:
            seen.add(m); ordered.append(m)
    return ordered

def annas_mirrors():  return _mirror_priority(ANNAS_MIRROR,  "anna",   ANNAS_STATIC_MIRRORS)
def libgen_mirrors(): return _mirror_priority(LIBGEN_MIRROR, "libgen", LIBGEN_STATIC_MIRRORS)

def from_libgen(query, book=False):
    """Keyless LibGen+ (libgen.li family) fallback: search -> md5 -> ads.php -> get.php?...&key=.
    The `key` is a per-request token scraped from the ads page (no user secret needed), so this
    runs ahead of the key-gated Anna's path and is the primary --book source. Best-effort per
    mirror (anti-bot / availability vary); the first mirror that yields a download link wins."""
    hdr = {"User-Agent": BROWSER_UA}
    for base in libgen_mirrors():
        try:
            body, _ = _get(f"{base}/index.php?req={_q(query)}&res=25&covers=on&filesuns=all",
                           timeout=25, headers=hdr)
            md5s = list(dict.fromkeys(re.findall(r'md5=([a-f0-9]{32})', body.decode("utf-8", "ignore"))))[:4]
        except Exception:
            continue
        out = []
        for md5 in md5s:
            try:
                ads, _ = _get(f"{base}/ads.php?md5={md5}", timeout=25,
                              headers={**hdr, "Referer": base + "/"})
            except Exception:
                continue
            m = re.search(r'get\.php\?md5=[a-f0-9]{32}&key=[A-Za-z0-9]+', ads.decode("utf-8", "ignore"))
            if m:
                out.append({"pdf_url": f"{base}/{m.group(0)}",
                            "source": f"libgen[{base.split('//')[-1]}]", "md5": md5})
        if out:
            return out
    return []

def from_annas(query, book=False):
    """Last-resort Anna's Archive path — only if ANNAS_SECRET_KEY is set. Tries mirrors in
    priority order (open-slum.org live status first); the first mirror that yields results wins."""
    if not ANNAS_KEY:
        return []
    content = "&content=book_any" if book else ""
    for base in annas_mirrors():
        try:
            body, _ = _get(f"{base}/search?q={_q(query)}{content}&ext=pdf")
            md5s = list(dict.fromkeys(re.findall(r'href="/md5/([a-f0-9]{32})"', body.decode("utf-8", "ignore"))))[:3]
        except Exception:
            continue
        out = []
        for md5 in md5s:
            api = _json(f"{base}/dyn/api/fast_download.json?md5={md5}&key={ANNAS_KEY}")
            url = api.get("download_url")
            if url:
                out.append({"pdf_url": url, "source": f"annas-archive[{base.split('//')[-1]}]", "md5": md5})
        if out:
            return out
    return []

def _dedupe(cands):
    """De-duplicate candidates by pdf_url, preserving order (= cascade priority)."""
    seen, ranked = set(), []
    for c in cands:
        u = c.get("pdf_url")
        if u and u not in seen:
            seen.add(u); ranked.append(c)
    return ranked

def resolve_oa(query):
    """Open-access cascade ONLY (papers): Semantic Scholar -> OpenAlex -> Crossref(->Unpaywall).
    Touches no shadow library and no SLUM. A `doi:` query skips the title APIs and goes to
    Unpaywall directly. Returns ranked candidates (possibly empty)."""
    cands = []
    doi = query.split("doi:", 1)[1].strip() if query.lower().startswith("doi:") else None
    if not doi:
        cands += from_semanticscholar(query)
        cands += from_openalex(query)
        doi, _ctitle = from_crossref(query)
    if doi:
        up = from_unpaywall(doi)
        if up: cands.append({"pdf_url": up, "source": "unpaywall", "doi": doi})
    return _dedupe(cands)

def resolve_shadow(query, book=False):
    """Shadow-library fallback ONLY: keyless LibGen+ then key-gated Anna's. This is the stage
    that queries SLUM (once, memoized) and searches mirrors — kept separate so callers can defer
    it until the OA cascade is exhausted (papers) and run it directly (books)."""
    return _dedupe(from_libgen(query, book=book) + from_annas(query, book=book))

def resolve(query, book=False):
    """Resolve to ranked PDF candidates. Short-circuits: an `arxiv:` query returns immediately;
    a paper returns the OA cascade and only falls through to the shadow libraries (and SLUM) if
    OA found nothing; a book goes straight to the shadow libraries (OA APIs are paper-centric).
    The `--download` path in main() adds a second lazy shadow attempt if OA candidates all fail
    validation, so the cross-source fallback is preserved without pinging SLUM on the happy path."""
    if query.lower().startswith("arxiv:"):
        url, aid = _arxiv_pdf(query); return [{"pdf_url": url, "source": "arxiv-direct", "arxiv_id": aid}]
    if book:                                   # OA APIs are paper-centric -> shadow libraries only
        return resolve_shadow(query, book=True)
    cands = resolve_oa(query)
    if not cands:                              # OA came up empty -> we genuinely need the shadow stage
        cands = resolve_shadow(query, book=False)
    return cands

def download(url, path):
    """Download + validate: must be a real PDF (content-type or %PDF magic) and >= 100 KB."""
    try:
        body, headers = _get(url, timeout=60)
    except Exception as e:
        return {"ok": False, "why": f"fetch failed: {e}"}
    ct = (headers.get("Content-Type") or "").lower()
    is_pdf = ("pdf" in ct) or body[:5] == b"%PDF-"
    if not is_pdf:
        return {"ok": False, "why": f"not a PDF (content-type={ct or '?'}, magic={body[:5]!r}) — likely an HTML landing page"}
    if len(body) < 100_000:
        return {"ok": False, "why": f"too small ({len(body)} bytes < 100 KB) — likely a stub"}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(body)
    return {"ok": True, "bytes": len(body), "path": path, "content_type": ct}

def main():
    args = [a for a in sys.argv[1:]]
    book = "--book" in args; args = [a for a in args if a != "--book"]
    dl = None
    if "--download" in args:
        i = args.index("--download"); dl = args[i+1]; del args[i:i+2]
    if not args:
        print("usage: oa_fetch.py \"<query|doi:..|arxiv:..>\" [--book] [--download path.pdf]", file=sys.stderr); return 2
    query = args[0]

    def _try(cands):
        for c in cands:
            res = download(c["pdf_url"], dl)
            print(json.dumps({"tried": c.get("source"), **res}), file=sys.stderr)
            if res.get("ok"):
                return True
        return False

    cands = resolve(query, book=book)
    print(json.dumps({"query": query, "email_configured": bool(EMAIL), "annas_fallback": bool(ANNAS_KEY),
                      "candidates": cands}, indent=2))
    if dl:
        if _try(cands):
            return 0
        # Lazy shadow fallback: if the candidates we just tried were OA-only (a paper whose OA
        # cascade succeeded but every OA URL failed validation), fall through to the shadow
        # libraries now — only then do we pay the SLUM query. Skip if shadow was already tried
        # (book path, or an OA-empty paper where resolve() already returned shadow candidates).
        tried_shadow = book or any((c.get("source") or "").startswith(("libgen", "annas")) for c in cands)
        if not tried_shadow and _try(resolve_shadow(query, book=False)):
            return 0
        print("all candidates failed validation", file=sys.stderr); return 1
    return 0 if cands else 1

if __name__ == "__main__":
    sys.exit(main())
