#!/usr/bin/env python3
"""Controls for `check-bytecode-freshness.py`.

Every test here forges the exact coincidence CPython cannot see: a `.pyc` whose
header records the source's CURRENT mtime and size while its bytecode is from a
different version of that source. Nothing about that is exotic -- a positive
control that swaps one character for another, reverted within the same second,
produces it by construction, and this repo produced it twice on 2026-08-22 by
two independent mechanisms (a control on `mtef_parser.py`, a container-snapshot
rollback on a module the gates import).
"""
from __future__ import annotations

import importlib.util
import os
import struct
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "viewer" / "tools" / "check-bytecode-freshness.py"

_GOOD = "VALUE = 11.0\n"
# Same byte count as _GOOD -- the property that defeats the size half of the check.
_BAD = "VALUE = 1.63\n"


def _run(*args):
    return subprocess.run([sys.executable, str(CHECKER), *map(str, args)],
                          capture_output=True, text=True)


def _compile_to_cache(src: Path) -> Path:
    """Write a `.pyc` for `src` exactly as an import would."""
    subprocess.run([sys.executable, "-c",
                    f"import sys; sys.path.insert(0, {str(src.parent)!r}); import {src.stem}"],
                   check=True, capture_output=True)
    return Path(importlib.util.cache_from_source(str(src)))


def _forge_header(src: Path, cache: Path) -> None:
    """Make the cache header claim the source's current mtime and size."""
    raw = bytearray(cache.read_bytes())
    st = os.stat(src)
    struct.pack_into("<II", raw, 8, int(st.st_mtime), st.st_size)
    cache.write_bytes(raw)


class TestStaleBytecodeIsDetected(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.src = self.dir / "victim.py"
        self.addCleanup(self._tmp.cleanup)

    def _make_stale(self) -> Path:
        """Correct source on disk, DIFFERENT bytecode in a header-valid cache."""
        self.src.write_text(_BAD, encoding="utf-8")
        cache = _compile_to_cache(self.src)
        self.src.write_text(_GOOD, encoding="utf-8")
        self.assertEqual(self.src.stat().st_size, len(_BAD),
                         "the control is only meaningful if the two sizes match")
        _forge_header(self.src, cache)
        return cache

    def test_cpython_itself_does_not_notice(self):
        """The premise. If CPython caught this, the tool would be pointless."""
        self._make_stale()
        out = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, {str(self.dir)!r}); "
             "import victim; print(victim.VALUE)"],
            capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(out, "1.63",
                         "CPython recompiled; the mtime+size hole this tool exists "
                         "for did not reproduce, so the tests below prove nothing")

    def test_the_checker_reports_it_and_exits_nonzero(self):
        cache = self._make_stale()
        r = _run(self.dir)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("STALE", r.stdout)
        self.assertIn(cache.name, r.stdout)

    def test_fix_removes_it_and_the_next_import_is_correct(self):
        cache = self._make_stale()
        r = _run(self.dir, "--fix")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(cache.exists(), "--fix left the stale cache in place")
        out = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, {str(self.dir)!r}); "
             "import victim; print(victim.VALUE)"],
            capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(out, "11.0")

    def test_a_matching_cache_is_not_reported(self):
        """The other half of a control: it must not cry wolf."""
        self.src.write_text(_GOOD, encoding="utf-8")
        _compile_to_cache(self.src)
        r = _run(self.dir)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("STALE", r.stdout)
        self.assertIn("match their source", r.stdout)

    def test_an_unchecked_hash_based_cache_is_reported(self):
        """CPython NEVER validates these -- strictly worse than the mtime hole."""
        self.src.write_text(_GOOD, encoding="utf-8")
        cache = _compile_to_cache(self.src)
        raw = bytearray(cache.read_bytes())
        struct.pack_into("<I", raw, 4, 0x1)   # hash-based, unchecked
        cache.write_bytes(raw)
        r = _run(self.dir)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("never validates", r.stdout)


class TestTheCheckerDoesNotCryWolf(unittest.TestCase):
    """A false positive is not a lesser failure: an oracle that cries wolf is switched off.

    The first run of this tool reported three stale caches, two of which were
    freshly written and identical. The cause: `marshal` rebuilds a `frozenset`
    with a different insertion order than the compiler produced, so two EQUAL
    sets `repr()` differently. `omml_converter._convert_function` holds a 30-name
    frozenset and tripped it.
    """

    def test_a_frozenset_constant_does_not_read_as_a_difference(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            src = d / "sets.py"
            src.write_text(textwrap.dedent("""
                def f(x):
                    return x in {'lg', 'arccos', 'dim', 'ker', 'gcd', 'cosh', 'log',
                                 'coth', 'lim', 'sup', 'tan', 'max', 'sin', 'arcsin',
                                 'sinh', 'cos', 'arctan', 'sec', 'tanh', 'deg', 'mod',
                                 'exp', 'cot', 'det', 'hom', 'ln', 'inf', 'arg',
                                 'csc', 'min'}
            """), encoding="utf-8")
            _compile_to_cache(src)
            r = _run(d)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertNotIn("STALE", r.stdout)


class TestTheCheckerReportsItsDenominator(unittest.TestCase):
    """`.claude/rules/campaign-lifecycle.md`: a gate prints what it read of what it
    was named, and REFUSEs rather than passing when it has no denominator."""

    def test_a_missing_path_refuses_rather_than_passing(self):
        r = _run(ROOT / "no-such-directory-here")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("REFUSE", r.stderr)

    def test_a_directory_with_no_python_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "notes.txt").write_text("hi", encoding="utf-8")
            r = _run(td)
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("REFUSE", r.stderr)

    def test_no_caches_at_all_passes_but_says_so(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "m.py").write_text("X = 1\n", encoding="utf-8")
            r = _run(td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("0 cache files present", r.stdout)
            self.assertIn("nothing can be stale", r.stdout)

    def test_the_repo_is_clean_right_now(self):
        r = _run(ROOT)
        self.assertEqual(r.returncode, 0,
                         "a stale cache is present in the working tree; the "
                         "interpreter is running code that is not on disk:\n"
                         + r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
