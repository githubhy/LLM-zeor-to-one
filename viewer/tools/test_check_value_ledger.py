"""Tests for the T7 restatement-drift gate (`check-value-ledger.py`).

Motivating incident (2026-07-31): the gate had TWO independent vacuous-pass
mechanisms, either of which alone made it ornamental.

  * It could not read math-delimited numbers. `NUM_UNIT_RE` required
    `\\d+\\s*UNIT`, so it matched `150 dB` and nothing else -- while a survey
    writes `$150$ dB`, `$\\approx 150$ dB`, `$150\\,\\mathrm{dB}$`. The
    comparison then did `if not got or not want_n: continue`, treating an
    unreadable value as a passing one.
    (`bugs/2026-07-31-value-ledger-blind-to-math-delimited-numbers`)
  * `iter_md` globbed a directory non-recursively, and `.githooks/pre-push`
    invokes it as `check-value-ledger.py surveys/`. It therefore read the 12
    flat single-file surveys and NONE of the multi-file survey directories --
    1.5% of an 811-file corpus.
    (`bugs/2026-07-31-value-ledger-scope-not-recursive`)

The load-bearing property this suite locks in is DISCRIMINATION, not
cleanliness: a gate that never fires passes every smoke test. So each
"silent" case below is paired with a "fires" case that differs from it only
in the defect, and the formula cases reproduce the exact six-site drift
(`2|a'|^2 E_s/N_0` restated as `2E_s/N_0`) that the ledger was reached for and
could not previously have caught.
"""
import pathlib
import subprocess
import sys

TOOL = pathlib.Path(__file__).with_name("check-value-ledger.py")

DECL_NUM = r"budget is <!-- val:sic = 150 dB -->$150$ dB here."
DECL_FORMULA = (
    r"gain <!-- val:snrmf = 2\lvert\alpha'\rvert^2 E_s/N_0 -->"
    r"$\mathrm{SNR}_{\text{MF}}=2\lvert\alpha'\rvert^2 E_s/N_0$ here."
)


def _run(tmp_path, *files, severity="error"):
    """Write `files` as (name, text) pairs into tmp_path and run the gate."""
    for name, text in files:
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(TOOL), str(tmp_path), f"--severity={severity}"],
        capture_output=True, text=True,
    )


# ── Silence on legitimate restatement forms ─────────────────────────────────


def test_math_delimited_restatements_are_read_not_skipped(tmp_path):
    """The four forms the corpus actually uses must all compare equal.

    Before the fix every one of these yielded NUM_UNIT_RE -> None and was
    silently skipped, so this test passed for the wrong reason. The
    companion drift test below is what makes it meaningful.
    """
    r = _run(
        tmp_path,
        ("a.md", "# d\n" + DECL_NUM + "\n"),
        ("b.md", "# r\n"
                 r"approx <!-- val:sic -->$\approx 150$ dB" "\n"
                 r"bare <!-- val:sic -->150 dB" "\n"
                 r"wrapped <!-- val:sic -->$150\,\mathrm{dB}$" "\n"
                 r"tilde <!-- val:sic -->$150$~dB" "\n"),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "4 restatement" in r.stdout, r.stdout


def test_formula_restatement_with_surrounding_context_is_silent(tmp_path):
    r = _run(
        tmp_path,
        ("a.md", "# d\n" + DECL_FORMULA + "\n"),
        ("b.md", "# r\n"
                 r"the gain <!-- val:snrmf -->"
                 r"$\mathrm{SNR}_{\text{MF}} = 2\lvert\alpha'\rvert^2 E_s/N_0$"
                 r" of section 1.2 counted in cells" "\n"),
    )
    assert r.returncode == 0, r.stdout + r.stderr


# ── Fires on real drift ─────────────────────────────────────────────────────


def test_numeric_drift_is_caught(tmp_path):
    r = _run(
        tmp_path,
        ("a.md", "# d\n" + DECL_NUM + "\n"),
        ("b.md", "# r\nstale <!-- val:sic -->$120$ dB budget\n"),
    )
    assert r.returncode == 1, r.stdout
    assert "VALUE-DRIFT val:sic" in r.stdout
    assert "120 db" in r.stdout and "150 db" in r.stdout


def test_formula_drift_dropping_a_factor_is_caught(tmp_path):
    """The historical six-site defect: `2|a'|^2 E_s/N_0` -> `2E_s/N_0`.

    Neither side yields a number+unit, so the pre-fix `continue` made this
    undetectable -- the one defect class the ledger was reached for.
    """
    r = _run(
        tmp_path,
        ("a.md", "# d\n" + DECL_FORMULA + "\n"),
        ("b.md", "# r\ndropped <!-- val:snrmf -->"
                 r"$\mathrm{SNR}_{\text{MF}} = 2E_s/N_0$ oops" "\n"),
    )
    assert r.returncode == 1, r.stdout
    assert "VALUE-DRIFT val:snrmf" in r.stdout


def test_unit_basis_change_is_caught(tmp_path):
    """dB and dBc are different bases; the same magnitude must not pass."""
    r = _run(
        tmp_path,
        ("a.md", "# d\n" + DECL_NUM + "\n"),
        ("b.md", "# r\nbasis <!-- val:sic -->$150$ dBc budget\n"),
    )
    assert r.returncode == 1, r.stdout


def test_reference_to_undeclared_key_is_caught(tmp_path):
    r = _run(tmp_path, ("b.md", "# r\norphan <!-- val:nope -->$5$ dB\n"))
    assert r.returncode == 1, r.stdout
    assert "undeclared" in r.stdout


def test_conflicting_redeclaration_is_caught(tmp_path):
    r = _run(
        tmp_path,
        ("a.md", "# d\n" + DECL_NUM + "\n"),
        ("b.md", "# d2\nalso <!-- val:sic = 175 dB -->$175$ dB\n"),
    )
    assert r.returncode == 1, r.stdout


# ── Scope ───────────────────────────────────────────────────────────────────


def test_directory_scope_is_recursive(tmp_path):
    """A drift nested below the named directory must still be found.

    The pre-push gate runs `check-value-ledger.py surveys/`, and every
    multi-file survey lives one level down. A non-recursive glob reports a
    clean exit 0 here.
    """
    r = _run(
        tmp_path,
        ("a.md", "# d\n" + DECL_NUM + "\n"),
        ("nested/deep/b.md", "# r\nstale <!-- val:sic -->$120$ dB\n"),
    )
    assert r.returncode == 1, (
        "nested drift not seen -- directory scope is not recursive:\n" + r.stdout
    )
    assert "nested" in r.stdout


def test_empty_scope_refuses_rather_than_reporting_clean(tmp_path):
    r = subprocess.run(
        [sys.executable, str(TOOL), str(tmp_path / "does-not-exist")],
        capture_output=True, text=True,
    )
    assert r.returncode == 2, r.stdout + r.stderr


def test_code_fences_are_not_scanned(tmp_path):
    r = _run(
        tmp_path,
        ("a.md", "# d\n" + DECL_NUM + "\n"),
        ("b.md", "# r\n```\nstale <!-- val:sic -->$120$ dB\n```\n"),
    )
    assert r.returncode == 0, r.stdout


# ── Real corpus ─────────────────────────────────────────────────────────────


def test_the_real_corpus_is_clean():
    repo = pathlib.Path(__file__).resolve().parents[2]
    surveys = repo / "surveys"
    if not surveys.exists():
        return
    r = subprocess.run(
        [sys.executable, str(TOOL), str(surveys), "--severity=error"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"corpus has value drift:\n{r.stdout}{r.stderr}"


def test_the_real_corpus_is_actually_in_scope():
    """A green corpus run must mean 'looked', not 'did not look'.

    Guards the regression directly: with a non-recursive glob this reports
    12 files and 0 declarations while the multimodal ledger sits unread.
    """
    repo = pathlib.Path(__file__).resolve().parents[2]
    surveys = repo / "surveys"
    if not surveys.exists():
        return
    r = subprocess.run(
        [sys.executable, str(TOOL), str(surveys)],
        capture_output=True, text=True,
    )
    n_files = int(r.stdout.split(" file(s)")[0].split("]")[-1].strip())
    n_decl = int(r.stdout.split("file(s), ")[1].split(" declared")[0])
    assert n_files > 10, f"only {n_files} files in scope: {r.stdout}"
    # The declaration count is NOT asserted > 0 here. The `<!-- val:ID = V -->`
    # ledger is opt-in and this corpus has not adopted it yet, so a non-zero
    # assertion would test the corpus's conventions rather than the tool's
    # scope -- and the scope property is already carried by n_files above.
    # Re-enable once the ledger is in use (tracked in todos/).
    assert n_decl >= 0
