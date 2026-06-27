#!/usr/bin/env python3
"""update_diff.py — splice re-decomposed subtree units into saved module data
and emit a leaf-level changelog of ✅/⚠️/❌ transitions.

Usage:
  update_diff.py --old <module>.units.json --new <redecomposed>.units.json \
                 [--out <merged.units.json>] [--changelog <changelog.md>]

--old : the saved full module data (list of {unit, data, verification}).
--new : a re-run subset (same shape) covering only the changed unit(s).
The named units in --new REPLACE their counterparts in --old (unmatched
units in --new are appended). Merged data -> --out (or stdout); the leaf-level
changelog for the replaced units -> --changelog (or stderr).

A "leaf key" is (unit, class, procedure, step). The changelog reports, per
replaced unit: status transitions (e.g. ❌→✅), added steps, removed steps,
and class/module-level absence changes — so a reviewer sees exactly what the
source change did to the capability surface.
"""
import argparse, json, sys

GLYPH = {'present': '✅', 'partial': '⚠️', 'absent': '❌'}


def leaves(unit_obj):
    """key -> status for every step leaf in one unit object."""
    out = {}
    d = unit_obj.get('data', {})
    for cls in d.get('classes', []):
        for proc in cls.get('procedures', []):
            for st in proc.get('steps', []):
                out[(cls.get('name', ''), proc.get('name', ''), st.get('step', ''))] = st.get('status', 'present')
    return out


def module_absent(unit_obj):
    d = unit_obj.get('data', {})
    s = {a.get('what', '') for a in d.get('moduleLevelAbsent', [])}
    for cls in d.get('classes', []):
        for a in cls.get('classLevelAbsent', []):
            s.add(f"{cls.get('name','')} :: {a.get('what','')}")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--old', required=True)
    ap.add_argument('--new', required=True)
    ap.add_argument('--out')
    ap.add_argument('--changelog')
    a = ap.parse_args()

    old = json.load(open(a.old))
    new = json.load(open(a.new))
    old_by = {u['unit']: u for u in old if u}
    new_by = {u['unit']: u for u in new if u}

    log = []
    for key, nu in new_by.items():
        ou = old_by.get(key)
        if ou is None:
            log.append(f"### {key}  (NEW unit)")
            log.append(f"- {len(leaves(nu))} leaves added.")
            continue
        ol, nl = leaves(ou), leaves(nu)
        changed = [(k, ol[k], nl[k]) for k in ol.keys() & nl.keys() if ol[k] != nl[k]]
        added = [k for k in nl.keys() - ol.keys()]
        removed = [k for k in ol.keys() - nl.keys()]
        oa, na = module_absent(ou), module_absent(nu)
        gained_support = oa - na    # was absent, now not listed
        new_gaps = na - oa
        if not (changed or added or removed or gained_support or new_gaps):
            log.append(f"### {key}  (no leaf changes)")
            continue
        log.append(f"### {key}")
        for (k, o, n) in sorted(changed):
            log.append(f"- {GLYPH.get(o,o)}→{GLYPH.get(n,n)}  {k[0]} · {k[1]} · {k[2]}")
        for k in sorted(added):
            log.append(f"- ＋ added step: {k[0]} · {k[1]} · {k[2]} ({GLYPH.get(nl[k],nl[k])})")
        for k in sorted(removed):
            log.append(f"- − removed step: {k[0]} · {k[1]} · {k[2]}")
        for g in sorted(gained_support):
            log.append(f"- ✅ no longer listed absent: {g}")
        for g in sorted(new_gaps):
            log.append(f"- ❌ newly listed absent: {g}")

    # splice: replace matched units in-place order, append unmatched
    merged = [new_by.get(u['unit'], u) for u in old if u]
    for key, nu in new_by.items():
        if key not in old_by:
            merged.append(nu)

    out_txt = json.dumps(merged, indent=1)
    if a.out:
        open(a.out, 'w').write(out_txt)
    else:
        print(out_txt)

    cl = "# Capability-tree update changelog\n\n" + ("\n".join(log) if log else "_no changes_") + "\n"
    if a.changelog:
        open(a.changelog, 'w').write(cl)
    else:
        sys.stderr.write(cl)


if __name__ == '__main__':
    main()
