from leafkey import leaf_key, iter_step_leaves, iter_module_leaves


def test_leaf_key_format():
    assert leaf_key("client", "Session", "request", "follow redirects") \
        == "client :: Session :: request :: follow redirects"


def test_iter_step_leaves():
    data = {"classes": [{"name": "C", "procedures": [
        {"name": "P", "steps": [
            {"step": "s1", "status": "present", "evidence": "f.py:1"},
            {"step": "s2", "status": "absent", "evidence": "", "why": "x"}]}]}]}
    assert list(iter_step_leaves(data)) == [
        ("C", "P", "s1", "present", "f.py:1"),
        ("C", "P", "s2", "absent", "")]


def test_iter_module_leaves_flattens_units():
    units = [{"unit": "u1", "data": {"classes": [{"name": "A", "procedures": [
                {"name": "P", "steps": [{"step": "s", "status": "present", "evidence": "a.py:2"}]}]}]}},
             {"unit": "u2", "data": {"classes": []}}]
    assert list(iter_module_leaves(units)) == [("A", "P", "s", "present", "a.py:2")]
