#!/usr/bin/env python3
"""Render a verified module leaf-tree into a conformant capability-tree survey.

Usage: render_module.py <units.json> <meta.json>   -> full module .md on stdout

units.json : [{unit, data, verification}]  (the workflow result.units)
meta.json  : {title, slug, coverage, cite_sentence, order:[keys],
              titles:{key:label}, references:[full tagged bib line, ...]}
Discipline: no '§' on external clauses (use 'cl.'), no ordered lists, ✅/⚠️/❌.
"""
import json, sys, re

GLYPH = {'present': '✅', 'partial': '⚠️', 'absent': '❌'}

def esc(s):
    if s is None: return ''
    s = str(s).replace('|', '\\|').replace('\n', ' ').strip().replace('§', 'cl. ')
    # neutralize external (paper) equation refs so the same-doc bare-ref
    # validator doesn't read them as internal eq cross-references
    s = re.sub(r'\bEq\.?\s*\(([^)]*)\)', r'eq \1', s)
    return s

def _esc_emphasis(text):
    """Escape markdown emphasis/mark delimiters in a PLAIN-text (non-code)
    segment so literal code tokens render verbatim. Without this, the data's
    `__init__` renders as bold "init", `*args` as an italic, and `e==0` as a
    ==mark==-stripped "e0" (markdown-it strong/em + the texmath/mark rules)."""
    return (text.replace('*', '\\*').replace('_', '\\_').replace('==', '\\=\\='))

def esc_md(s):
    """esc() + neutralize markdown emphasis OUTSIDE backtick code spans, so
    literal code tokens (dunders, *args, e==0, n*m) survive rendering while
    the data's own `inline code` spans are left intact. Use for every plain-text
    cell (summary/role/step/detail/why/what); code() stays raw (backticks already
    shield it)."""
    s = esc(s)
    parts = re.split(r'(`[^`]*`)', s)
    return ''.join(p if p.startswith('`') else _esc_emphasis(p) for p in parts)

def code(s):
    s = esc(s); return f'`{s}`' if s else '—'

def main():
    units_path, meta_path = sys.argv[1], sys.argv[2]
    units_list = [u for u in json.load(open(units_path)) if u]
    units = {u['unit']: u for u in units_list}
    meta = json.load(open(meta_path))
    order = [k for k in meta['order'] if k in units]
    titles = meta.get('titles', {})
    T = lambda k: titles.get(k, k.replace('-', ' ').title())
    slug = meta['slug']
    # Optional explorer cross-links: emit "Open in explorer" per class ONLY when
    # the meta opts in (`meta.explorer` truthy) — i.e. the survey ships the
    # interactive explorer (build_explorer_data.py + viewer/explorer.html). The
    # node id `{slug}:{ci}` MUST match build_explorer_data.py's class counter,
    # which numbers in UNITS-FILE order (not meta order; the two diverge for e.g.
    # fec), so we key the map by object identity over units_list.
    EXPLORER = meta.get('explorer')
    cls_ci = {}
    if EXPLORER:
        _ci = 0
        for u in units_list:
            for cls in u['data'].get('classes', []):
                cls_ci[id(cls)] = _ci
                _ci += 1
    missing_why = []   # partial/absent steps lacking a rationale (quality gate)
    out = []; P = out.append

    # ---- counts + rollup ----
    counts = {}; rollup = []; tot = {'present':0,'partial':0,'absent':0}
    for key in order:
        d = units[key]['data']; c = {'present':0,'partial':0,'absent':0}
        for cls in d.get('classes', []):
            for proc in cls.get('procedures', []):
                for st in proc.get('steps', []):
                    s = st.get('status','present'); c[s]=c.get(s,0)+1; tot[s]=tot.get(s,0)+1
                    if s in ('partial','absent'):
                        if not (st.get('why') or '').strip():
                            missing_why.append(f'{key} · {cls["name"]} · {st["step"]} [{s}]')
                        rollup.append((key, cls['name'], proc['name'], st['step'], s, st.get('detail',''), st.get('why','')))
            for a in cls.get('classLevelAbsent', []):
                rollup.append((key, cls['name'], '(class)', a['what'], 'absent', '', a.get('why','')))
        for a in d.get('moduleLevelAbsent', []):
            rollup.append((key, '(subtree)', '', a['what'], 'absent', '', a.get('why','')))
        counts[key] = c

    # ---- preamble ----
    P(f'# {meta["title"]}\n')
    P(f'> **What this is.** An exhaustive, **step-level in/out-of-the-box** map of {meta["coverage"]}, drilled module → class → procedure → **step** (a step = the finest named operation that could independently be present, absent, or carry variants).' + (f' Part of the `{meta["survey"]}` survey.' if meta.get('survey') else ''))
    P('>')
    P(f'> **How it was produced.** One decomposition agent per subtree read the actual source to algorithm-step granularity; an adversarial verifier re-opened the cited `path:line` for every absent/partial leaf. {tot["present"]+tot["partial"]+tot["absent"]} step-leaves, {tot["partial"]+tot["absent"]} partial/absent. {meta.get("cite_sentence","")}')
    P('>')
    P(f'> **Coverage.** {", ".join(T(k) for k in order)}.\n')
    P('---\n')

    # ---- 1 legend ----
    P('<!-- sec:1 -->\n## 1 How to read this tree\n')
    P('| Glyph | Status | Meaning |\n|---|---|---|')
    P('| ✅ | In | implemented; *Detail* gives variants/extent |')
    P('| ⚠️ | Partial | implemented with a material restriction or approximation |')
    P('| ❌ | Out | not implemented — *Why* gives the reason |\n')
    P('Every leaf is backed by `path:line` evidence (strong `local:` evidence per `.claude/rules/citation-integrity.md`).\n')

    # ---- 2 matrix ----
    P('<!-- sec:2 -->\n## 2 Subtree summary matrix\n')
    P('| Subtree | ✅ In | ⚠️ Partial | ❌ Out | Classes |\n|---|---|---|---|---|')
    for key in order:
        c = counts[key]; d = units[key]['data']
        cls_names = ', '.join('`%s`' % cc['name'] for cc in d.get('classes', []))
        P(f'| **{T(key)}** | {c["present"]} | {c["partial"]} | {c["absent"]} | {cls_names} |')
    P(f'| **TOTAL** | {tot["present"]} | {tot["partial"]} | {tot["absent"]} | |')
    P('')

    # ---- per-unit ----
    sec = 3
    for key in order:
        d = units[key]['data']
        P(f'<!-- sec:{sec} -->\n## {sec} {T(key)}\n')
        P(esc_md(d.get('summary','')) + '\n')
        for cls in d.get('classes', []):
            P(f'### `{cls["name"]}`\n')
            P(f'*{esc_md(cls.get("role",""))}*  —  {code(cls.get("file",""))}\n')
            if EXPLORER:
                P(f'[Open `{cls["name"]}` in the explorer ↗](/explorer.html?node={slug}:{cls_ci[id(cls)]})\n')
            for proc in cls.get('procedures', []):
                P(f'**Procedure — {esc_md(proc["name"])}**\n')
                P('| Step | | Detail | Evidence |\n|---|---|---|---|')
                for st in proc.get('steps', []):
                    det = esc_md(st.get('detail',''))
                    if st.get('status') in ('partial','absent') and st.get('why'):
                        det = (det + ' — _why:_ ' + esc_md(st['why'])).strip(' —')
                    P(f'| {esc_md(st["step"])} | {GLYPH.get(st.get("status"),"")} | {det} | {code(st.get("evidence",""))} |')
                P('')
            for a in cls.get('classLevelAbsent', []):
                pass
            cla = cls.get('classLevelAbsent', [])
            if cla:
                P('**Not in the box (class):**\n')
                for a in cla:
                    ev = (' (' + esc_md(a['evidence']) + ')') if a.get('evidence') else ''
                    P(f'- ❌ {esc_md(a["what"])} — {esc_md(a.get("why",""))}{ev}')
                P('')
        mla = d.get('moduleLevelAbsent', [])
        if mla:
            P(f'**Not in the box ({T(key)} subtree):**\n')
            for a in mla:
                ev = (' (' + esc_md(a['evidence']) + ')') if a.get('evidence') else ''
                P(f'- ❌ {esc_md(a["what"])} — {esc_md(a.get("why",""))}{ev}')
            P('')
        sec += 1

    # ---- roll-up ----
    P(f'<!-- sec:{sec} -->\n## {sec} Roll-up — everything not fully in the box\n')
    P('| Subtree | Where | Item | | Why |\n|---|---|---|---|---|')
    for (key, cls, proc, step, status, detail, why) in rollup:
        where = esc_md(cls) + (f' · {esc_md(proc)}' if proc and proc not in ('(class)','') else '')
        item = esc_md(step) + ((' — ' + esc_md(detail)) if detail else '')
        P(f'| {T(key)} | {where} | {item} | {GLYPH[status]} | {esc_md(why)} |')
    sec += 1

    # ---- references ----
    P(f'<!-- sec:{sec} -->\n## {sec} References\n')
    P('In-repo code is cited inline by `path:line` (strong `local:` evidence). External standards:\n')
    for i, ref in enumerate(meta.get('references', []), 1):
        if i > 1: P('')   # blank line between entries, else CommonMark merges them into one run-together paragraph
        P(f'<!-- bib:{i} -->')
        P(ref)
    # quality gate: a partial/absent leaf must carry a `why` (the IS-vs-ISN'T
    # disclosure). leaf.schema.json now requires it; this catches legacy data.
    if missing_why:
        sys.stderr.write(f'WARNING: {len(missing_why)} partial/absent step(s) with no `why` '
                         'rationale (required by schema/leaf.schema.json + phase-2):\n')
        for m in missing_why[:20]:
            sys.stderr.write(f'  - {m}\n')
    print('\n'.join(out))

if __name__ == '__main__':
    main()
