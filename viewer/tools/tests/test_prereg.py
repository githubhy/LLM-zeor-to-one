#!/usr/bin/env python3
"""Tests for lib/prereg.py — the pre-registration commit-order verifier.

This is the HEART of the campaign harness: it is the only thing standing between a
"pre-registered hypothesis" and a post-hoc rationalisation. Until these tests
existed, the harness asserted `"positive-control": {"passed": true}` in a JSON file
and NOTHING verified it. A self-attested gate is not a gate.

The load-bearing case is `test_same_commit_fails`: if the registration and the result
land in one commit their order is unverifiable, which is exactly how the discipline
gets bypassed — including by an innocent `git add -A`.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import prereg  # noqa: E402

GOOD = """---
campaign: t
task: T1.1
tier: A
registered: 2026-07-12
status: registered
claimed_for: [UMa, UMi]
---

## Hypotheses
| id | hypothesis | prediction | threshold | falsifier |
|----|-----------|-----------|-----------|-----------|
| H1 | the release delta explains it | closes >= 6 dB | >= 6 dB | closes < 3 dB |
"""

NO_FALSIFIER = GOOD.replace("| closes < 3 dB |", "|  |")
NO_THRESHOLD = GOOD.replace("| >= 6 dB | closes < 3 dB |", "|  | closes < 3 dB |")


def git(d: Path, *a: str) -> str:
    # prereg.git_env() -- not a local copy. The scrub is the thing under test, so
    # a second definition here could drift from the library's and still pass.
    return subprocess.run(["git", "-C", str(d), *a], capture_output=True,
                          text=True, check=True,
                          env=prereg.git_env()).stdout.strip()


class TmpRepo:
    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        git(self.d, "init", "-q")
        git(self.d, "config", "user.email", "t@t")
        git(self.d, "config", "user.name", "t")
        return self

    def __exit__(self, *a):
        self.tmp.cleanup()

    def write(self, rel: str, text: str) -> Path:
        p = self.d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def commit(self, msg: str):
        git(self.d, "add", "-A")
        git(self.d, "commit", "-q", "-m", msg)


def codes(findings) -> set:
    return {f.code for f in findings}


class TestContent(unittest.TestCase):
    def test_good_prereg_passes(self):
        with TmpRepo() as r:
            p = r.write("pre-registration.md", GOOD)
            self.assertEqual(prereg.validate_content(prereg.parse(p)), [])

    def test_missing_falsifier_fails(self):
        """A pre-registration you cannot fail is not a pre-registration."""
        with TmpRepo() as r:
            p = r.write("pre-registration.md", NO_FALSIFIER)
            self.assertIn("PR-FALSIFIER", codes(prereg.validate_content(prereg.parse(p))))

    def test_missing_threshold_fails(self):
        with TmpRepo() as r:
            p = r.write("pre-registration.md", NO_THRESHOLD)
            self.assertIn("PR-THRESH", codes(prereg.validate_content(prereg.parse(p))))

    def test_no_hypotheses_table_fails(self):
        with TmpRepo() as r:
            p = r.write("pre-registration.md", "---\ncampaign: t\ntask: T\ntier: A\n"
                                               "registered: x\nstatus: registered\n---\n\nprose only\n")
            self.assertIn("PR-NOHYP", codes(prereg.validate_content(prereg.parse(p))))

    def test_claimed_for_parses(self):
        with TmpRepo() as r:
            p = r.write("pre-registration.md", GOOD)
            self.assertEqual(prereg.parse(p).frontmatter["claimed_for"], ["UMa", "UMi"])


class TestCommitOrder(unittest.TestCase):
    def test_prereg_before_result_passes(self):
        with TmpRepo() as r:
            p = r.write("pre-registration.md", GOOD)
            r.commit("register")
            res = r.write("result.json", "{}")
            r.commit("result")
            self.assertEqual(codes(prereg.verify(r.d, p, [res])), set())

    def test_same_commit_fails(self):
        """THE load-bearing case. One commit => the order is unverifiable, so the
        registration proves nothing. This is how the discipline gets bypassed."""
        with TmpRepo() as r:
            p = r.write("pre-registration.md", GOOD)
            res = r.write("result.json", "{}")
            r.commit("both at once")
            self.assertIn("PR-SAMECOMMIT", codes(prereg.verify(r.d, p, [res])))

    def test_result_before_prereg_fails(self):
        with TmpRepo() as r:
            res = r.write("result.json", "{}")
            r.commit("result first")
            p = r.write("pre-registration.md", GOOD)
            r.commit("register after the fact")
            self.assertIn("PR-ORDER", codes(prereg.verify(r.d, p, [res])))

    def test_uncommitted_prereg_with_committed_result_fails(self):
        with TmpRepo() as r:
            res = r.write("result.json", "{}")
            r.commit("result")
            p = r.write("pre-registration.md", GOOD)  # never committed
            self.assertIn("PR-UNCOMMITTED", codes(prereg.verify(r.d, p, [res])))

    def test_silent_post_hoc_threshold_edit_fails(self):
        """Moving the goalposts after seeing the data, with no visible amendment."""
        with TmpRepo() as r:
            p = r.write("pre-registration.md", GOOD)
            r.commit("register")
            res = r.write("result.json", "{}")
            r.commit("result")
            r.write("pre-registration.md", GOOD.replace(">= 6 dB", ">= 1 dB"))
            r.commit("quietly relax the threshold")
            self.assertIn("PR-SILENT-EDIT", codes(prereg.verify(r.d, p, [res])))

    def test_visible_amendment_is_warn_not_error(self):
        with TmpRepo() as r:
            p = r.write("pre-registration.md", GOOD)
            r.commit("register")
            res = r.write("result.json", "{}")
            r.commit("result")
            r.write("pre-registration.md",
                    GOOD.replace(">= 6 dB", ">= 1 dB") +
                    "\n## Amendment\nThreshold relaxed because X; see review.\n")
            r.commit("amend, visibly")
            f = prereg.verify(r.d, p, [res])
            self.assertIn("PR-AMENDED", codes(f))
            self.assertNotIn("PR-SILENT-EDIT", codes(f))
            self.assertTrue(all(x.level != "error" for x in f))

    def test_nothing_committed_is_not_an_error(self):
        with TmpRepo() as r:
            p = r.write("pre-registration.md", GOOD)
            res = r.write("result.json", "{}")
            self.assertTrue(all(x.level != "error" for x in prereg.verify(r.d, p, [res])))


class TestShallowClone(unittest.TestCase):
    """A shallow clone has no clock, and reading its absence as disorder CONVICTS.

    The pre-registration mechanism rests on git being a tamper-evident clock
    (`.claude/rules/campaign-execution.md`). At a shallow GRAFT BOUNDARY that clock stops:
    `--diff-filter=A` attributes every pre-existing path to the boundary commit, so a
    correctly-ordered pair reads as SAME-COMMIT, and no ancestry question can cross it.

    Measured 2026-08-23: `actions/checkout@v4` defaults to `fetch-depth: 1`, and CI reported
    16 campaign errors against a tree that reports 6 with history — 11 fabricated, comprising
    every PR-SAMECOMMIT and every phase-3/4 CM-MEASUREFIRST.

    RED-first (`[opt:PLAN-REDFIRST]`). The discriminating input is
    `test_a_correctly_ordered_pair_is_not_convicted_in_a_depth_1_clone`: a repo where the
    pre-registration provably precedes the result, cloned at depth 1. The pre-fix
    implementation reports PR-SAMECOMMIT — a hard error, on impeccable history.
    """

    def _ordered_repo(self, r):
        """prereg in commit 1, result in commit 2 — unambiguously correct order."""
        pr = r.write("t/pre-registration.md", GOOD)
        r.commit("register")
        res = r.write("t/result.json", '{"x": 1}\n')
        r.commit("measure")
        return pr, res

    def test_the_ordered_pair_passes_with_full_history(self):
        """Control: with history, the same repo is clean. Without this the test below
        could pass for the wrong reason."""
        with TmpRepo() as r:
            pr, res = self._ordered_repo(r)
            self.assertEqual(codes(prereg.verify(r.d, pr, [res])), set())
            self.assertEqual(prereg.boundary_shas(r.d), frozenset())

    def test_a_correctly_ordered_pair_is_not_convicted_in_a_depth_1_clone(self):
        with TmpRepo() as r:
            self._ordered_repo(r)
            with tempfile.TemporaryDirectory() as td:
                sc = Path(td) / "shallow"
                git(r.d, "clone", "--depth", "1", "-q", f"file://{r.d}", str(sc))
                found = codes(prereg.verify(sc, sc / "t/pre-registration.md",
                                            [sc / "t/result.json"]))
                self.assertNotIn("PR-SAMECOMMIT", found,
                                 "a depth-1 clone must not fabricate a same-commit verdict")
                self.assertNotIn("PR-ORDER", found)
                self.assertIn("PR-NOHISTORY", found, "it must REFUSE, not silently pass")

    def test_the_refusal_is_its_own_level_not_an_error(self):
        """REFUSE is distinct from FAIL: one has no verdict, the other has a bad one."""
        with TmpRepo() as r:
            self._ordered_repo(r)
            with tempfile.TemporaryDirectory() as td:
                sc = Path(td) / "shallow"
                git(r.d, "clone", "--depth", "1", "-q", f"file://{r.d}", str(sc))
                fs = prereg.verify(sc, sc / "t/pre-registration.md", [sc / "t/result.json"])
                levels = {f.level for f in fs if f.code == "PR-NOHISTORY"}
                self.assertEqual(levels, {"refuse"})

    def test_the_boundary_set_is_read_from_the_clone(self):
        with TmpRepo() as r:
            self._ordered_repo(r)
            with tempfile.TemporaryDirectory() as td:
                sc = Path(td) / "shallow"
                git(r.d, "clone", "--depth", "1", "-q", f"file://{r.d}", str(sc))
                b = prereg.boundary_shas(sc)
                self.assertTrue(b, "a depth-1 clone must report a graft boundary")
                head = git(sc, "rev-parse", "HEAD")
                self.assertIn(head, b, "in a depth-1 clone HEAD itself is the boundary")
                self.assertTrue(prereg.is_boundary(sc, head))

    def test_repo_level_shallowness_is_NOT_the_predicate(self):
        """A deep-but-shallow clone still answers most questions, and must keep doing so.

        This repo is itself shallow (875 commits, 39 boundaries) while answering almost
        every ancestry question correctly. Refusing on `--is-shallow-repository` would throw
        away every real finding it can still make.
        """
        with TmpRepo() as r:
            self._ordered_repo(r)
            r.write("t/extra.json", "{}\n")
            r.commit("third")
            with tempfile.TemporaryDirectory() as td:
                sc = Path(td) / "shallow"
                git(r.d, "clone", "--depth", "2", "-q", f"file://{r.d}", str(sc))
                self.assertEqual(git(sc, "rev-parse", "--is-shallow-repository"), "true")
                # The pair added in the two most recent commits is still orderable.
                self.assertNotIn(
                    "PR-NOHISTORY",
                    codes(prereg.verify(sc, sc / "t/result.json", [sc / "t/extra.json"])),
                    "a shallow clone that CAN order these commits must give the verdict")

    def test_an_uncommitted_prereg_beside_committed_results_still_errors(self):
        """The refusal must not become a blanket amnesty: this failure needs no clock."""
        with TmpRepo() as r:
            res = r.write("t/result.json", "{}\n")
            r.commit("measure")
            pr = r.write("t/pre-registration.md", GOOD)   # never committed
            self.assertIn("PR-UNCOMMITTED", codes(prereg.verify(r.d, pr, [res])))


class TestGitEnvIsolation(unittest.TestCase):
    """A git hook exports GIT_DIR, and GIT_DIR OUTRANKS `-C <dir>`.

    So an inherited environment silently redirects every `git -C fixture` call at
    the REAL repository. That is not hypothetical: it is how the pre-push gate came
    to commit test fixtures onto the branch it was validating, burying the pushed
    commit under six of them (bugs/2026-08-22-prereg-tests-mutate-the-real-repo-
    under-a-git-hook). The suite passed by hand and corrupted the repo under the
    gate -- the only context that triggers it is the one meant to protect the push.

    Both halves below are load-bearing. Asserting only that the fixture works would
    miss the corruption, which is the damaging half.
    """

    def test_ambient_git_dir_does_not_capture_fixture_commits(self):
        with TmpRepo() as ambient, TmpRepo() as fixture:
            ambient.write("seed.txt", "seed")
            ambient.commit("seed")
            before = git(ambient.d, "rev-parse", "HEAD")

            old = os.environ.get("GIT_DIR")
            os.environ["GIT_DIR"] = str(ambient.d / ".git")
            try:
                fixture.write("pre-registration.md", GOOD)
                fixture.commit("register")
            finally:
                if old is None:
                    os.environ.pop("GIT_DIR", None)
                else:
                    os.environ["GIT_DIR"] = old

            self.assertEqual(before, git(ambient.d, "rev-parse", "HEAD"),
                             "fixture commits leaked into the ambient repository")
            self.assertEqual(git(fixture.d, "log", "--format=%s"), "register",
                             "the fixture commit did not land in the fixture")

    def test_library_reads_the_root_it_is_given_not_the_ambient_repo(self):
        with TmpRepo() as ambient, TmpRepo() as fixture:
            ambient.write("seed.txt", "seed")
            ambient.commit("seed")

            p = fixture.write("pre-registration.md", GOOD)
            fixture.commit("register")

            old = os.environ.get("GIT_DIR")
            os.environ["GIT_DIR"] = str(ambient.d / ".git")
            try:
                found = prereg.add_commit(fixture.d, p)
            finally:
                if old is None:
                    os.environ.pop("GIT_DIR", None)
                else:
                    os.environ["GIT_DIR"] = old

            self.assertIsNotNone(
                found,
                "add_commit consulted the ambient repo instead of the root it was given")


if __name__ == "__main__":
    unittest.main(verbosity=2)
