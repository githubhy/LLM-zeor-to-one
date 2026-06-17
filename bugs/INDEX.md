# Bugs Index

| date | id | title | severity | status | hook |
|---|---|---|---|---|---|
| 2026-06-13 | 2026-06-13-01 | Magicoder base HumanEval figure misattributed (WizardCoder-CL's 48.2 used for Code Llama-Python-7B) | med | fixed | citation-audit caught wrong base value in LLMs-for-code §8; fixed 48.2→37.8 |
| 2026-06-17 | 2026-06-17-01 | serve.js /api/md/<empty-or-dir> crashes the whole server process (unhandled EISDIR) | med | open | one malformed GET kills the dev server; upstream defect, fix-location TBD |
