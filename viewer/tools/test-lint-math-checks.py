#!/usr/bin/env python3
"""Assertion tests for the lint-math symbol-declaration checks (#12, #13).

These checks are cheap to get subtly wrong -- #13 shipped on 2026-08-10 reading
an `aligned` block's alignment marker `&` as a symbol name
(`bugs/2026-08-10-lint-math-check13-aligned-ampersand`).  A fixture that is only
*described* in a bug record is not a regression test; this runs it.

Usage:
  python viewer/tools/test-lint-math-checks.py

Exits 0 on success, 1 on any failed expectation.
"""

import importlib.util
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
FIXTURES = TOOLS / 'fixtures'


def load_lint_math():
    """lint-math.py is not importable by name (hyphen), so load by path."""
    spec = importlib.util.spec_from_file_location(
        'lint_math', TOOLS / 'lint-math.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    lint = load_lint_math()
    failures = []

    # ── check #13 ──────────────────────────────────────────────────────
    fixture = FIXTURES / 'lint-math-check13.md'
    lines = fixture.read_text(encoding='utf-8').splitlines()
    issues = lint.check_duplicate_definitions(lines)

    if len(issues) != 1:
        failures.append(
            f'check #13: expected exactly 1 finding on {fixture.name}, '
            f'got {len(issues)}: {[i[2] for i in issues]}')
    else:
        message = issues[0][2]
        if '`\\gamma`' not in message:
            failures.append(
                f'check #13: finding should name the macro `\\gamma` with its '
                f'backslash intact, got: {message}')
        # The aligned-marker regression: a finding keyed on `&` means the
        # alignment marker was read as the symbol name.
        if '`&`' in message:
            failures.append(
                'check #13: alignment marker `&` read as a symbol name '
                '(bugs/2026-08-10-lint-math-check13-aligned-ampersand)')

    # ── check #12 ──────────────────────────────────────────────────────
    # The fixture is far below the tagged-equation threshold, so #12 must be
    # silent on it regardless of the configured severity.
    if lint.check_notation_table(lines, fixture):
        failures.append(
            'check #12: fired on a fixture with fewer than '
            f'{lint.NOTATION_MIN_TAGGED_EQS} tagged equations')

    for failure in failures:
        print(f'FAIL: {failure}')
    if failures:
        print(f'\n{len(failures)} failure(s)')
        return 1
    print('lint-math symbol checks: all expectations met '
          '(#13 fires once on the true positive, stays silent on the identical '
          'restatement, fenced code, and aligned markers; #12 silent below '
          'threshold)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
