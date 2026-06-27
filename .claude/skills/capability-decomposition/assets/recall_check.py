#!/usr/bin/env python3
"""Recall (completeness) check for capability-decomposition — source -> tree.

The Phase-2 verify stage checks PRECISION (are the marks the tree makes earned,
tree -> source). This is the complement: did the decomposition MISS any real
capability? It enumerates a module's public surface and reports which classes are
NOT represented in the decomposed units (the candidate-miss list to audit).

Usage:
    recall_check.py <source-dir> [<source-dir> ...] --units <module>_units.json

A class is "covered" if its name appears in a decomposed class name OR its file is
cited anywhere in the units. STRONG misses (file+name both absent) are whole
capabilities likely omitted; WEAK candidates (name absent, file cited) need a
per-item look — they are often folded into a sibling node or legitimately excluded
(abstract base, enum, dataclass, internal helper). Recall is SEARCH-BOUNDED: a
capability under different terminology can be invisible to both the tree and this
check; report coverage as agreement-at-this-depth, not a closed-world proof.
"""
import ast
import os
import json
import argparse
import re


def public_classes(roots):
    out = []
    for root in roots:
        for dp, _dirs, fns in os.walk(root):
            for fn in fns:
                if not fn.endswith('.py'):
                    continue
                p = os.path.join(dp, fn)
                try:
                    tree = ast.parse(open(p, encoding='utf-8').read())
                except Exception:
                    continue
                for n in tree.body:
                    if isinstance(n, ast.ClassDef) and not n.name.startswith('_'):
                        methods = [m.name for m in n.body
                                   if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                                   and not m.name.startswith('_')]
                        out.append({'name': n.name, 'file': p, 'line': n.lineno, 'methods': methods})
    return out


def tree_index(units_path):
    units = json.load(open(units_path))
    names, files = set(), set()
    for u in units:
        if not u:
            continue
        for c in u['data'].get('classes', []):
            for tok in re.findall(r'[A-Za-z_]\w+', c.get('name', '')):
                names.add(tok)
            evs = [c.get('file', '')]
            for proc in c.get('procedures', []):
                for st in proc.get('steps', []):
                    evs.append(st.get('evidence', ''))
            for a in c.get('classLevelAbsent', []):
                evs.append(a.get('evidence', ''))
            for ev in evs:
                for m in re.finditer(r'([\w./+-]+\.py)', ev or ''):
                    files.add(os.path.basename(m.group(1)))
    return names, files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('roots', nargs='+', help='source dir(s) for the module')
    ap.add_argument('--units', required=True, help='<module>_units.json (the decomposed data)')
    args = ap.parse_args()

    classes = public_classes(args.roots)
    names, files = tree_index(args.units)

    def cov(c):
        return (c['name'] in names, os.path.basename(c['file']) in files)

    name_hit = sum(1 for c in classes if cov(c)[0])
    file_hit = sum(1 for c in classes if cov(c)[1])
    strong = [c for c in classes if not cov(c)[0] and not cov(c)[1]]
    weak = [c for c in classes if not cov(c)[0] and cov(c)[1]]
    n = len(classes) or 1
    print(f'public classes: {len(classes)} | name-represented: {name_hit} ({100*name_hit//n}%) | '
          f'file-cited: {file_hit} ({100*file_hit//n}%)')
    print(f'STRONG miss candidates (file+name absent — likely omitted capabilities): {len(strong)}')
    for c in strong:
        print(f'  MISS  {c["name"]}  ({c["file"]}:{c["line"]})  methods={c["methods"][:6]}')
    print(f'WEAK candidates (name absent, file cited — audit each): {len(weak)}')
    for c in weak:
        print(f'  weak  {c["name"]}  ({c["file"]}:{c["line"]})')
    print('\nNext: audit each candidate against source — a substantive, user-facing capability '
          'with no tree node is a recall miss (add the leaf). Trivial accessors / abstract bases '
          '/ enums / dataclasses / framework overrides are legitimately excludable.')


if __name__ == '__main__':
    main()
