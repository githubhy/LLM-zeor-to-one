"""Tests for renumber-equations.py's cross-file marker-kind check.

`bugs/2026-08-02-cross-file-eq-refs-marked-same-file` fixed 19 cross-file
equation references written with the same-file `<!-- ref: -->` marker. Eighteen
were caught by the orphan check only because they were *also* unlinked (bare
`(6)`). The nineteenth carried a perfectly valid link and no gate saw it:

    <!-- ref:2.5-9 -->[(20)](fundamentals.md#eq-20)

`REF_MARKER` requires `(#eq-N)` or a bare `(N)`, so it does not match; and
`propagate_xrefs` keys on `xref:`, so it is never renumbered either. The link is
right today and goes stale the moment the target file renumbers.

The check added for `todos/2026-08-02-crossfile-ref-marker-latent-staleness` is a
**marker-kind** check: a `ref:` pointing into a sibling file is wrong regardless
of whether its number currently happens to be correct. These tests pin that the
check fires on the correct-link case -- which is the whole point, and the one a
link-correctness check structurally cannot catch.
"""

import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parent / 'renumber-equations.py'

TARGET = """<!-- sec:2 -->
## 2. Target

<a id="eq-1"></a><!-- eq:2.1-1 -->
$$
a = b . \\tag{1}
$$
"""


def run(path):
    p = subprocess.run(
        [sys.executable, str(TOOL), '--check', str(path)],
        capture_output=True, text=True,
    )
    return p.returncode, p.stdout + p.stderr


def make(tmp_path, source_body):
    (tmp_path / 'fundamentals.md').write_text(TARGET, encoding='utf-8')
    src = tmp_path / 'method.md'
    src.write_text(source_body, encoding='utf-8')
    return src


def test_crossfile_ref_with_a_CORRECT_link_is_reported(tmp_path):
    """The blind-spot case: right file, right anchor, right number, wrong marker."""
    src = make(tmp_path, '# 3. Method\n\nAs <!-- ref:2.1-1 -->[(1)](fundamentals.md#eq-1) shows.\n')
    rc, out = run(src)
    assert rc == 1, f'a mis-marked cross-file ref with a valid link passed: {out}'
    assert 'instead of' in out and 'xref:2.1-1' in out, out


def test_canonical_xref_form_is_accepted(tmp_path):
    """The correct form must stay green -- the check must not fire on it."""
    src = make(tmp_path, '# 3. Method\n\nAs [(1)](fundamentals.md#eq-1) <!-- xref:2.1-1 --> shows.\n')
    rc, out = run(src)
    assert rc == 0, f'canonical xref form was rejected: {out}'


def test_same_file_ref_is_untouched(tmp_path):
    """A genuine same-file ref: must not be swept up by the new check."""
    src = tmp_path / 'solo.md'
    src.write_text(
        '# 2. Solo\n\n'
        '<a id="eq-1"></a><!-- eq:2.1-1 -->\n$$\na = b . \\tag{1}\n$$\n\n'
        'As <!-- ref:2.1-1 -->[(1)](#eq-1) shows.\n',
        encoding='utf-8')
    rc, out = run(src)
    assert rc == 0, f'a legitimate same-file ref was flagged: {out}'
    assert 'instead of' not in out, out
