#!/usr/bin/env python3
"""Guide test for docs/additional-material/git_workflow_scenarios/gitflow.md

Checks the guide's plain-git way of creating the develop branch:

    git branch develop
    git push -u origin develop

Run it from the root of the repository:

    python3 tests/guides/test_gitflow_develop_branch.py

The test never touches your own repository.  It builds a temporary repository with a
`main` branch (commits A, B, C), a branch `topic` at B, and a second, bare repository
that acts as `origin` (reached through a file:// URL).  Both are deleted afterwards,
also when a test fails.  `git flow init` is not run: it needs the separate git-flow
extension, which is not part of git.

For demonstration, GUIDE_TEST_OMIT=push (or =branch) leaves that command out of the
sequence; the test then fails, which shows that it really checks the command.

Needs: git >= 2.28 (init -b) and Python 3.8+.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

NAME = "Course Student"
EMAIL = "student@example.invalid"
TMP_PREFIX = "gitflow-guide-test-"


class ChildFailure(RuntimeError):
    """A git child process exited with a status the test did not expect."""

    def __init__(self, command, returncode, stderr):
        super().__init__("%s exited with %d: %s" % (command, returncode, stderr.strip()))
        self.command = command
        self.returncode = returncode


class Sandbox:
    """Working repository + bare 'origin', both inside one temporary directory."""

    def __init__(self, root):
        self.root = Path(root)
        self.work = self.root / "work"
        self.remote = self.root / "origin.git"
        self.home = self.root / "home"
        for d in (self.work, self.home, self.root / "xdg"):
            d.mkdir()

    def env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.root / "xdg"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": NAME, "GIT_AUTHOR_EMAIL": EMAIL,
            "GIT_COMMITTER_NAME": NAME, "GIT_COMMITTER_EMAIL": EMAIL,
            "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0", "GIT_EDITOR": "false", "LC_ALL": "C",
        })
        return env

    def git(self, *args, cwd=None, ok=(0,)):
        """Run git; a status outside `ok` raises ChildFailure instead of being ignored."""
        p = subprocess.run(["git", *args], cwd=cwd or self.work, env=self.env(),
                           capture_output=True, text=True)
        if p.returncode not in ok:
            raise ChildFailure("git " + " ".join(args), p.returncode, p.stderr)
        return p

    def out(self, *args, cwd=None):
        return self.git(*args, cwd=cwd).stdout.strip()

    def refs(self, cwd=None):
        rows = self.out("for-each-ref", "--format=%(refname) %(objectname)", cwd=cwd).splitlines()
        return dict(r.split(" ", 1) for r in rows)

    def commit(self, name, text, message, append=False):
        with open(self.work / name, "a" if append else "w") as f:
            f.write(text)
        self.git("add", name)
        self.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
        return self.out("rev-parse", "HEAD")


def build_sandbox(root):
    """main = A-B-C, topic = B, origin (bare, file:// URL) already holds main."""
    sb = Sandbox(root)
    sb.git("init", "-q", "-b", "main")
    sb.a = sb.commit("notes.txt", "alpha\n", "A: create notes.txt")
    sb.b = sb.commit("notes.txt", "beta\n", "B: append beta", append=True)
    sb.c = sb.commit("todo.txt", "one\n", "C: add todo.txt")
    sb.git("branch", "topic", sb.b)
    sb.git("init", "--bare", "-q", "-b", "main", str(sb.remote), cwd=sb.root)
    sb.git("remote", "add", "origin", sb.remote.resolve().as_uri())
    sb.git("push", "-q", "origin", "main")
    return sb


def run_guide_sequence(root, omit=(), start="main"):
    """The guide's commands, with `start` checked out.  `omit` leaves commands out on purpose."""
    sb = build_sandbox(root)
    if start != "main":
        sb.git("checkout", "-q", start)
    sb.start = start
    sb.before = sb.refs()
    if "branch" not in omit:
        sb.git("branch", "develop")                   # guide, step 1
    if "push" not in omit:
        sb.git("push", "-u", "origin", "develop")     # guide, step 2
    return sb


class GitflowDevelopBranchTest(unittest.TestCase):
    def fresh_dir(self):
        tmp = tempfile.TemporaryDirectory(prefix=TMP_PREFIX)
        self.addCleanup(tmp.cleanup)
        return tmp.name

    def check_published(self, sb, tip):
        """State after `git branch develop` + `git push -u origin develop`."""
        local = sb.refs()
        self.assertEqual(tip, local.get("refs/heads/develop"), "develop is at the expected commit")
        self.assertEqual(sb.start, sb.out("rev-parse", "--abbrev-ref", "HEAD"),
                         "git branch does not switch branches")
        for ref in ("refs/heads/main", "refs/heads/topic"):
            self.assertEqual(sb.before[ref], local[ref], ref + " did not move")
        self.assertEqual({"refs/heads/main": sb.c, "refs/heads/develop": tip}, sb.refs(cwd=sb.remote),
                         "origin has main and develop, and nothing else")
        self.assertEqual("origin", sb.out("config", "branch.develop.remote"))
        self.assertEqual("refs/heads/develop", sb.out("config", "branch.develop.merge"))
        self.assertEqual("origin/develop", sb.out("rev-parse", "--abbrev-ref", "develop@{upstream}"))
        self.assertEqual(tip, local.get("refs/remotes/origin/develop"), "remote-tracking ref is updated")
        self.assertEqual("0\t0", sb.out("rev-list", "--left-right", "--count", "develop...origin/develop"))

    def test_guide_sequence_publishes_develop_from_main(self):
        omit = set(filter(None, os.environ.get("GUIDE_TEST_OMIT", "").split(",")))
        sb = run_guide_sequence(self.fresh_dir(), omit=omit)
        self.check_published(sb, sb.c)
        self.assertEqual(sb.out("rev-parse", "main"), sb.out("rev-parse", "develop"),
                         "develop starts at the tip of main")

    def test_develop_starts_from_the_checked_out_branch(self):
        sb = run_guide_sequence(self.fresh_dir(), start="topic")
        self.check_published(sb, sb.b)
        self.assertNotEqual(sb.out("rev-parse", "main"), sb.out("rev-parse", "develop"),
                            "run from topic, develop does not start at main")

    def test_omitting_the_push_makes_the_check_fail(self):
        with self.assertRaises(AssertionError):
            sb = run_guide_sequence(self.fresh_dir(), omit={"push"})
            self.check_published(sb, sb.c)

    def test_omitting_the_branch_command_propagates_the_git_failure(self):
        with self.assertRaises(ChildFailure) as caught:
            run_guide_sequence(self.fresh_dir(), omit={"branch"})
        self.assertNotEqual(0, caught.exception.returncode)
        self.assertIn("push", caught.exception.command)

    def test_temporary_directory_is_removed_even_after_a_failure(self):
        paths = []
        for omit in (set(), {"branch"}):
            try:
                with tempfile.TemporaryDirectory(prefix=TMP_PREFIX) as tmp:
                    paths.append(Path(tmp))
                    run_guide_sequence(tmp, omit=omit)
            except ChildFailure:
                pass
        self.assertEqual(2, len(paths))
        for p in paths:
            self.assertFalse(p.exists(), "%s was not cleaned up" % p)


if __name__ == "__main__":
    unittest.main(verbosity=2)
