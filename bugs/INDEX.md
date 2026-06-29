# Bugs Index

| date | id | title | severity | status | hook |
|---|---|---|---|---|---|
| 2026-06-29 | 2026-06-29-01 | §A.19 worked example used the row/data-matrix convention, clashing with §A.1's column convention | med | fixed | numbers right but X∈R^{T×d}/W_Q∈R^{d×d_k} clashed with §A.1's column form and made "W_OV=W_O W_V" dimensionally false; rewrote §A.19 + Fig A.12 to column convention (same values, transposed) |
| 2026-06-28 | 2026-06-28-01 | Relative asset links (link to figures/*.svg) 404 in viewer SPA — href not rewritten to doc dir | med | fixed | viewer rewrote img src but not a[href]; figures/*.svg link resolved to root /figures/ → 404; fixRelativePaths now rewrites asset hrefs too |
| 2026-06-13 | 2026-06-13-01 | Magicoder base HumanEval figure misattributed (WizardCoder-CL's 48.2 used for Code Llama-Python-7B) | med | fixed | citation-audit caught wrong base value in LLMs-for-code §8; fixed 48.2→37.8 |
| 2026-06-17 | 2026-06-17-01 | serve.js /api/md/<empty-or-dir> crashes the whole server process (unhandled EISDIR) | med | open | one malformed GET kills the dev server; upstream defect, fix-location TBD |
| 2026-06-19 | 2026-06-19-01 | Highlighting a span that starts inside inline math and crosses a second math span highlights the whole paragraph | med | fixed | viewer routed multi-span start-in-katex selections to the whole-block sidecar; now routes to PLAIN_SPANNING_MATH for a precise inline highlight |
| 2026-06-20 | 2026-06-20-01 | Appendix E.5 over-attributed Llama-2-70B's 64-head count to the Llama-2 paper [63] | low | fixed | citation-audit caught H=64 not in [63]'s text (derived/config value); reworded to cite only the stated 8-KV-group GQA design; non-load-bearing |
