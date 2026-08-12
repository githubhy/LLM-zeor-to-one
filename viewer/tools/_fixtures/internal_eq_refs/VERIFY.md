# Verification note — `check-internal-eq-refs.py`

Bring-up and live-corpus verification of the deterministic §↔Eq consistency gate.
Tool: `viewer/tools/check-internal-eq-refs.py` (Tier-1 pre-filter for the `citation-audit`
skill's internal-reference mode). Date: 2026-07-21.

## What the gate checks (the only thing)

A `# survey-ref` / `% survey-ref` code comment often pairs a SECTION anchor with an inline
equation number. The gate flags a comment whose cited equation N does **not** live in the
cited section S of the named survey file — the "wrong-but-resolving" copy-paste defect. Every
pre-existing gate (`chk_eq_code_correspondence.py`, `chk_survey_traceability.py`) only checks
that the anchor *resolves*; none checks that the section and the equation number are mutually
consistent. That is the whole gap this fills.

- Plain-integer token `N` (`Eq. 15`, `eq 61`, `Eqs. (60)-(61)`): owning section resolved by
  opening the survey `.md`, finding `id="eq-N"`, and taking the nearest **preceding** heading
  anchor `id="sec-<num>"` (landmark/part anchors like `sec-D.10-part-a` are excluded).
- Section-scoped marker `X.Y-Z` (`Eq. D.4-2`, `Eq. D.3.8-1`): owning section is its prefix
  `X.Y`; no survey lookup needed.
- Consistency: passes if owning is dotted-prefix-consistent with ANY cited `#sec-S` on the
  comment ("D.3" ~ "D.3.7" ok; "D.3.6" vs "D.3.7" NOT; "G.9.1" vs "G.9.2" NOT).

Advisory by default (exit 0). `--severity error` → exit 1 on any un-suppressed flag. UTF-8 on
every read; deterministic (no RNG/clock — confirmed). Not wired into any git hook.

## 1. Self-contained fixture (REQUIRED)

Fixture survey `fix.md` (two sections, α/×/− non-ASCII glyphs on purpose so a bare `open()`
on a Windows/GBK box would crash): `eq-1` under `sec-1.1`, `eq-2` under `sec-1.2`.
Fixture code `fix_code.py`: one CONSISTENT ref (`#sec-1.2 (Eq. 2)`) and one INCONSISTENT ref
(`#sec-1.1 (Eq. 2)` — Eq. 2 is in 1.2).

Command:

```
python viewer/tools/check-internal-eq-refs.py \
    viewer/tools/_fixtures/internal_eq_refs/fix_code.py \
    --survey-root viewer/tools/_fixtures/internal_eq_refs --severity error
```

Output:

```
check-internal-eq-refs: FAIL (1 un-suppressed flag(s)) -- severity=error
check-internal-eq-refs: scanned 1 source file(s), 2 survey-ref line(s), 2 equation token(s) checked against survey sections.
FLAGS (1 un-suppressed; 0 suppressed by ledger):
  [-] viewer/tools/_fixtures/internal_eq_refs/fix_code.py:13 cites #sec-1.1 but Eq. 2 lives in section 1.2 of fix.md
EXIT=1
```

**PASS** — flags exactly the inconsistent ref (line 13), passes the consistent one (line 8).
Advisory default (no `--severity`) prints the same flag as a warning and exits **0**.

## 2. Real-corpus run

```
python viewer/tools/check-internal-eq-refs.py sim/llms-for-coding --survey-root surveys/llms-for-coding
```

Raw scan: 408 source files, 89 survey-ref lines, **28 equation tokens checked**. Two raw flags:

| # | Site | Cited | Eq. | Owns | Judgment |
|---|---|---|---|---|---|
| 1 | `common/density.py:912` | G.9.1 | 83 | G.9.2 | **legitimate cross-section reuse** → seeded to ledger |
| 2 | `decoders/ga_ms.py:136` | D.7.8 | 41 | D.7.7 | **true low-severity defect** → residual |

**Flag 1 — density.py:912 (legit reuse).** `quantize_nonuniform()` REALIZES the run-time
*apply* of Eq. 83, whose defining home is G.9.2 ("The R/C/Q split"). The multi-line survey-ref
(density.py:912–915) deliberately grounds the code site to G.9.1 (design-vs-run two-phase map,
the conceptual home of an apply) and G.9.3 (which names this function), and explicitly states
appendix-d D.7 is "NOT the equation home." Citing Eq. 83 from a G.9.1-anchored comment is
intentional, not a wrong-but-resolving copy-paste. → seeded to
`.claude/internal-eq-refs-rejected.json`.

**Flag 2 — ga_ms.py:136 (true defect, residual).** The GA-MS check-node density operator
equations are eq-43…48, **all in D.7.8** (eq-49 opens D.8). The comment's range label
"eqs 41-46" pulls in eq-41/42, which live in the **adjacent** D.7.7 (NMS scale-change-of-
variables) — unrelated to GA-MS's φ-domain derivation — and omits eq-47/48. The anchor D.7.8
and the upper endpoint Eq. 46 are correct; only the lower range bound is misattributed. This is
a genuine (if low-severity) §↔Eq imprecision the 2026-07-20 audit (which fixed the pde.py
Eq. 13/14 → 15/16 family) did not tighten. Kept as an un-suppressed residual, NOT seeded — a
minor real defect is not "legitimate reuse," and the ledger must not hide it. Recommended
follow-up for the corpus owner: tighten the label to `eqs 43-48` in `ga_ms.py:136` (the code is
untouched here — out of scope for the gate bring-up), or, if the loose softmax-family span is
deemed acceptable, add one ledger line.

After seeding the ledger with flag 1:

```
check-internal-eq-refs: scanned 408 source file(s), 89 survey-ref line(s), 28 equation token(s) checked ...
FLAGS (1 un-suppressed; 1 suppressed by ledger):
  [-] sim/llms-for-coding/kernels/flash_attn.py:136 cites #sec-d.7.8 but Eq. 41 lives in section d.7.7 of appendix-d.md
```

Residual = **1** (ga_ms.py:136). `--severity error` exits 1; default `warn` exits 0.

## 3. Reconstructed-defect confirmation

The real 19-site defect was pde.py-family survey-refs citing `#sec-D.3.7 (Eq. 13/14)` when
Eq. 13/14's tags live outside D.3.7 (eq-13 → D.3.6; the fix moved the citation to Eq. 15/16,
both genuinely in D.3.7). Reconstructed as a one-off input (real fixed files untouched):

```
# survey-ref: appendix-d.md#sec-D.3.7 (Eq. 13/14 prefix-suffix product & cost)   <- historical
# survey-ref: appendix-d.md#sec-D.3.7 (Eq. 15 prefix-suffix product; Eq. 16 ...)  <- current fix
```

Output (`--severity error`): 4 tokens checked (13, 14, 15, 16), **1 flag**:

```
  [-] ...reconstructed_defect.py:5 cites #sec-d.3.7 but Eq. 13 lives in section d.3.6 of appendix-d.md
EXIT=1
```

**Confirmed** — the gate would have caught the real defect: it flags Eq. 13 (owns D.3.6),
passes Eq. 14 (owns D.3.7), and passes the current fixed Eq. 15/16 form. This is the exact
class the gate exists to detect.

## Coverage-is-not-silent

The gate prints scanned-file / survey-ref-line / token-checked counts on every run, and a
`COVERAGE WARNING` naming any survey `.md` a plain-int eq lookup required but could not open —
so "0 flags" can never silently mean "looked at nothing." On the live corpus no survey file was
unreadable and 28 tokens were checked.

## Determinism

Two consecutive corpus runs produced byte-identical output; `check-internal-eq-refs.py` imports
no `time`/`random`/`datetime`/`default_rng` and reads every file with `encoding='utf-8'`.
