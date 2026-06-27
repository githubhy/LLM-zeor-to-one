"""Canonical leaf identity used by update_diff.py (Phase 5 splice + changelog).

A "leaf" is one step in a procedure of a class within a module. Its identity is
the semantic name-path (module, class, procedure, step) — stable across source
reordering, unlike the positional {slug}:{ci} explorer node id.
"""


def leaf_key(module, cls, proc, step):
    return f"{module} :: {cls} :: {proc} :: {step}"


def iter_step_leaves(unit_data):
    """Yield (cls, proc, step, status, evidence) for one unit's `data` object."""
    for cls in unit_data.get("classes", []):
        cname = cls.get("name", "")
        for proc in cls.get("procedures", []):
            pname = proc.get("name", "")
            for st in proc.get("steps", []):
                yield (cname, pname, st.get("step", ""),
                       st.get("status", "present"), st.get("evidence", ""))


def iter_module_leaves(units_list):
    """Yield (cls, proc, step, status, evidence) across a whole *.units.json
    (a list of {unit, data, ...} objects)."""
    for u in units_list:
        if not u:
            continue
        yield from iter_step_leaves(u.get("data", {}))
