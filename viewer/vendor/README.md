# vendor/

Vendored client-side libraries. All files fetched from jsDelivr on 2026-06-07.
No CDN dependency at runtime — these files are served directly from this directory.

## Files

| File | npm package | Version |
|---|---|---|
| `katex.min.js` | katex | 0.16.21 |
| `katex.min.css` | katex | 0.16.21 |
| `markdown-it.min.js` | markdown-it | 14.1.0 |
| `texmath.min.js` | markdown-it-texmath | 1.0.0 |
| `texmath.min.css` | markdown-it-texmath | 1.0.0 |
| `markdown-it-mark.min.js` | markdown-it-mark | 4.0.0 |
| `markdown-it-footnote.min.js` | markdown-it-footnote | 4.0.0 |
| `mermaid.min.js` | mermaid | 11.4.1 |

## KaTeX fonts (`fonts/`)

20 `.woff2` font files. The exact set was derived from the `url(fonts/...)` references
in `katex.min.css` (extracted via `grep -oE 'KaTeX_[A-Za-z0-9]+-[A-Za-z]+\.woff2'`),
then each file was fetched from:

```
https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/fonts/<filename>
```

The CSS uses relative `fonts/` paths, which resolve correctly because `katex.min.css`
sits alongside the `fonts/` directory within `vendor/`.

## Integrity verification

Run `npm run check-vendor` (from `viewer/`) to confirm all required files are present
and non-empty.
