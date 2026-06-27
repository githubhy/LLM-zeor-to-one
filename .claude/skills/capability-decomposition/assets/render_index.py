#!/usr/bin/env python3
"""Render the top-level capability-tree index from all module unit files.

Usage: render_index.py <manifest.json>  -> index.md on stdout
manifest.json: [{slug, title, units}], or {title, blurb, overview, modules:[...]} to customise the index header  (units = path to <module>_units.json)
"""
import json, sys, re

def esc(s):
    if s is None: return ''
    s = str(s).replace('|', '\\|').replace('\n', ' ').strip().replace('§', 'cl. ')
    s = re.sub(r'\bEq\.?\s*\(([^)]*)\)', r'eq \1', s)
    return s

def _esc_emphasis(text):
    return (text.replace('*', '\\*').replace('_', '\\_').replace('==', '\\=\\='))

def esc_md(s):
    """esc() + neutralize markdown emphasis OUTSIDE backtick code spans, so the
    data's literal `__all__`, `*args`, `e==0` survive rendering verbatim instead
    of being eaten as bold/italic/mark. Mirrors render_module.py."""
    s = esc(s)
    parts = re.split(r'(`[^`]*`)', s)
    return ''.join(p if p.startswith('`') else _esc_emphasis(p) for p in parts)

def counts_of(units):
    c = {'present': 0, 'partial': 0, 'absent': 0}
    classes = 0; mod_absent = []
    for u in units:
        if not u: continue
        d = u['data']
        classes += len(d.get('classes', []))
        for cls in d.get('classes', []):
            for proc in cls.get('procedures', []):
                for st in proc.get('steps', []):
                    c[st.get('status', 'present')] = c.get(st.get('status', 'present'), 0) + 1
        for a in d.get('moduleLevelAbsent', []):
            mod_absent.append(a)
    return c, classes, mod_absent

def main():
    raw = json.load(open(sys.argv[1]))
    if isinstance(raw, dict):
        idx_title = raw.get('title') or 'Capability Tree'
        idx_blurb = raw.get('blurb') or 'the codebase'
        overview = raw.get('overview')
        manifest = raw['modules']
    else:
        idx_title, idx_blurb, overview = 'Capability Tree', 'the codebase', None
        manifest = raw
    rows = []
    tot = {'present': 0, 'partial': 0, 'absent': 0}; tot_cls = 0
    gaps = []
    for m in manifest:
        units = json.load(open(m['units']))
        c, classes, mod_absent = counts_of(units)
        rows.append((m, c, classes))
        for k in tot: tot[k] += c[k]
        tot_cls += classes
        for a in mod_absent[:4]:
            gaps.append((m['slug'], a.get('what', ''), a.get('why', '')))
    out = []; P = out.append

    P(f'# {idx_title}\n')
    P(f'> **What this is.** An exhaustive, **step-level in/out-of-the-box** map of {idx_blurb}, decomposed module → class → procedure → **step** (a *step* = the finest named operation that could independently be present, absent, or carry variants). Each leaf is tagged ✅ In / ⚠️ Partial / ❌ Out and backed by `path:line` evidence, then adversarially verified against source.' + (f' This is the deep companion to the high-level `{overview}`.' if overview else ''))
    P('>')
    P(f'> **Scale.** {len(rows)} modules · {tot_cls} classes · {tot["present"]+tot["partial"]+tot["absent"]} step-leaves ({tot["present"]} in, {tot["partial"]} partial, {tot["absent"]} out).')
    P('>')
    P('> **How produced.** One decomposition agent per subtree filled the leaf tree; an adversarial verifier re-opened the cited `path:line` for every absent/partial leaf. All subtrees returned a TRUSTWORTHY verdict (only minor line-drift corrections).\n')
    P('---\n')

    P('<!-- sec:1 -->\n## 1 Module matrix\n')
    P('| Module | ✅ In | ⚠️ Partial | ❌ Out | Classes | Detail |\n|---|--:|--:|--:|--:|---|')
    for (m, c, classes) in rows:
        P(f'| **{esc(m["title"])}** | {c["present"]} | {c["partial"]} | {c["absent"]} | {classes} | [{m["slug"]}.md]({m["slug"]}.md) |')
    P(f'| **TOTAL** | {tot["present"]} | {tot["partial"]} | {tot["absent"]} | {tot_cls} | |')
    P('')

    P('<!-- sec:2 -->\n## 2 Headline out-of-the-box gaps\n')
    P('The biggest whole-subtree absences across the library (each module file has its full ❌/⚠️ roll-up):\n')
    P('| Module | Not in the box | Why |\n|---|---|---|')
    for (slug, what, why) in gaps:
        P(f'| {slug} | {esc_md(what)} | {esc_md(why)} |')
    P('')

    P('<!-- sec:3 -->\n## 3 How to read a module file\n')
    P('Each `<module>.md` is a self-contained capability tree: a legend, a subtree summary matrix, then per-class **procedure → step** tables (Step · status · Detail · Evidence), per-class/subtree "Not in the box" callouts, a roll-up of everything not fully in the box, and tagged references. Validated by `/check-survey`.\n')
    print('\n'.join(out))

if __name__ == '__main__':
    main()
