"""Regression tests for link-references.py on bracketed-citation surveys.

`todos/2026-07-07-link-references-bracketed-citation-surveys` reported that
link-references.py hard-errored on ~14 corpus surveys that use bracketed-name
citations (`# References` H1 with `## Standards` / `## Academic` subsections)
rather than a numbered `[N]` system, because `find_bib_file` looked for a
`## References` H2 specifically.

That was fixed by widening `find_refs_section` to match a References heading at
ANY ATX level, not by adding a special case. These tests pin that behaviour so
it cannot regress -- and, critically, pin the case a naive "just don't error
when there's no heading" guard would have masked:

    markers present + heading absent  ->  MUST still exit 1

An H1 bibliography and a missing bibliography are different states. The first is
a legitimate survey style; the second is a broken citation graph. A guard keyed
on "no References heading" alone cannot tell them apart, which is why the fix
belongs in heading detection rather than in an error suppressor.
"""

import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parent / 'link-references.py'


def run(survey_dir):
    p = subprocess.run(
        [sys.executable, str(TOOL), str(survey_dir), '--check'],
        capture_output=True, text=True,
    )
    return p.returncode, p.stdout + p.stderr


def write(d, name, text):
    (d / name).write_text(text, encoding='utf-8')


def test_h1_bibliography_is_accepted(tmp_path):
    """The bracketed-citation style: `# References` H1 with `##` subsections.

    This is the shape of the 13 affected surveys. It must NOT error.
    """
    write(tmp_path, 'index.md', '# 1. Intro\n\nAs Smith (2020) shows, the loss is 3 dB.\n')
    write(tmp_path, 'references.md',
          '# References\n\n## Academic\n\n**Smith, J. (2020).** "A Paper." (web)\n')
    rc, out = run(tmp_path)
    assert rc == 0, f'H1 bibliography rejected: {out}'


def test_h2_bibliography_is_accepted(tmp_path):
    """The numbered-bib style still works -- the widening broke nothing."""
    write(tmp_path, 'index.md',
          '# 1. Intro\n\nAs shown in <!-- cite:1 --> [[1]](references.md#ref-1).\n')
    write(tmp_path, 'references.md',
          '## References\n\n<a id="ref-1"></a><!-- bib:1 -->\n[1] A. Author. "T."\n')
    rc, out = run(tmp_path)
    assert rc == 0, out


def test_markers_without_any_heading_still_errors(tmp_path):
    """Load-bearing: a cite marker with NO bibliography anywhere is broken.

    The citation points at an anchor nothing defines. Any future attempt to
    silence the bracketed-citation false alarm by suppressing the
    missing-heading error must keep this red.
    """
    write(tmp_path, 'index.md',
          '# 1. Intro\n\nAs shown in <!-- cite:3 -->[[3]](#ref-3) the loss is 3 dB.\n')
    write(tmp_path, 'notes.md', '# 2. Notes\n\nNo bibliography here.\n')
    rc, out = run(tmp_path)
    assert rc == 1, f'a broken citation graph was accepted: {out}'
    assert 'References heading' in out, out


def test_bib_marker_without_any_heading_still_errors(tmp_path):
    """Sibling of the above, from the bibliography side."""
    write(tmp_path, 'index.md', '# 1. Intro\n\nProse.\n')
    write(tmp_path, 'refs.md', '<a id="ref-1"></a><!-- bib:1 -->\n[1] A. Author. "T."\n')
    rc, out = run(tmp_path)
    assert rc == 1, f'a bib marker with no heading was accepted: {out}'
