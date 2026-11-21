#!/usr/bin/env python3
"""Guide test for docs/additional-material/git_workflow_scenarios/undoing-a-commit.md

Checks the guide's commands for:
1. Unstaging a file using `git reset <file>`
2. Undoing the latest commit using `git reset --hard HEAD~1`

Run it from the root of the repository:
    python3 tests/guides/test_undoing_a_commit.py

Needs: git >= 2.28 and Python 3.8+.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

NAME = "Course Student"
EMAIL = "student@example.invalid"
TMP_PREFIX = "undoing-guide-test-"


class ChildFailure(RuntimeError):
    """Raised when a git child process exits with an unexpected code."""

    def __init__(self, command, returncode, stderr):
        super().__init__("%s exited with %d: %s" % (command, returncode, stderr.strip()))
        self.command = command
        self.returncode = returncode


class Sandbox:
    """Isolated working repository inside a temporary directory."""

    def __init__(self, root):
        self.root = Path(root)
        self.work = self.root / "work"
        self.home = self.root / "home"
        self.work.mkdir(parents=True)
        self.home.mkdir(parents=True)

    def env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "HOME": str(self.home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": NAME,
            "GIT_AUTHOR_EMAIL": EMAIL,
            "GIT_COMMITTER_NAME": NAME,
            "GIT_COMMITTER_EMAIL": EMAIL,
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        })
        return env

    def git(self, *args, ok=(0,)):
        p = subprocess.run(["git", *args], cwd=self.work, env=self.env(),
                           capture_output=True, text=True)
        if ok is not None and p.returncode not in ok:
            raise ChildFailure("git " + " ".join(args), p.returncode, p.stderr)
        return p

    def out(self, *args):
        return self.git(*args).stdout.strip()

    def lines(self, *args):
        return self.out(*args).splitlines()

    def refs(self):
        rows = self.lines("for-each-ref", "--format=%(refname) %(objectname)")
        return dict(r.split(" ", 1) for r in rows)


def build_sandbox(root):
    """Builds main = A-B-C, topic = B."""
    sb = Sandbox(root)
    sb.git("init", "-q", "-b", "main")

    # Commit A: create notes.txt
    notes = sb.work / "notes.txt"
    notes.write_text("alpha\n")
    sb.git("add", "notes.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit A: create notes.txt")
    sb.sha_a = sb.out("rev-parse", "HEAD")

    # Commit B: append beta to notes.txt
    with open(notes, "a") as f:
        f.write("beta\n")
    sb.git("add", "notes.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit B: append beta to notes.txt")
    sb.sha_b = sb.out("rev-parse", "HEAD")

    # Branch topic at Commit B
    sb.git("branch", "topic", sb.sha_b)

    # Commit C: create todo.txt
    todo = sb.work / "todo.txt"
    todo.write_text("one\n")
    sb.git("add", "todo.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit C: add todo.txt")
    sb.sha_c = sb.out("rev-parse", "HEAD")

    return sb


def run_guide_sequence(root, omit=()):
    """Executes git reset <file> to unstage and git reset --hard HEAD~1 to undo a commit."""
    sb = build_sandbox(root)

    # Stage two changes: notes.txt update and new draft.txt
    notes = sb.work / "notes.txt"
    with open(notes, "a") as f:
        f.write("extra\n")
    draft = sb.work / "draft.txt"
    draft.write_text("draft\n")

    sb.git("add", "notes.txt", "draft.txt")

    # Step 1: Unstage draft.txt using git reset draft.txt
    if "reset" not in omit and "unstage" not in omit:
        sb.git("reset", "draft.txt")

    # Step 2: Commit notes.txt as commit D
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit D: add extra notes")
    sb.sha_d = sb.out("rev-parse", "HEAD")

    # Step 3: Undo commit D using git reset --hard HEAD~1
    if "reset" not in omit and "hard" not in omit:
        sb.git("reset", "--hard", "HEAD~1")

    return sb


class UndoingACommitTest(unittest.TestCase):
    def fresh_dir(self):
        tmp = tempfile.TemporaryDirectory(prefix=TMP_PREFIX)
        self.addCleanup(tmp.cleanup)
        return tmp.name

    def test_guide_sequence_undoes_commit_and_unstages_file(self):
        omit = set(filter(None, os.environ.get("GUIDE_TEST_OMIT", "").split(",")))
        sb = run_guide_sequence(self.fresh_dir(), omit=omit)

        # 1. Assert HEAD is back at commit C
        self.assertEqual(sb.sha_c, sb.out("rev-parse", "HEAD"),
                         "HEAD is restored to pre-commit-D state (commit C)")

        # 2. Assert notes.txt content matches commit C
        self.assertEqual("alpha\nbeta\n", (sb.work / "notes.txt").read_text(),
                         "notes.txt content was rolled back to commit C")

        # 3. Assert draft.txt was untracked/unstaged
        status = sb.lines("status", "--porcelain")
        self.assertIn("?? draft.txt", status, "draft.txt remained untracked")

        # 4. Assert branch topic remained untouched at commit B
        self.assertEqual(sb.sha_b, sb.out("rev-parse", "topic"),
                         "branch topic remained untouched at commit B")

    def test_omitting_the_reset_command_makes_the_check_fail(self):
        with self.assertRaises(AssertionError):
            sb = run_guide_sequence(self.fresh_dir(), omit={"reset"})
            self.assertEqual(sb.sha_c, sb.out("rev-parse", "HEAD"))

    def test_child_failure_propagation(self):
        sb = build_sandbox(self.fresh_dir())
        with self.assertRaises(ChildFailure) as caught:
            sb.git("log", "nonexistent-branch-ref")
        self.assertNotEqual(0, caught.exception.returncode)

    def test_temporary_directory_is_removed_even_after_a_failure(self):
        paths = []
        try:
            with tempfile.TemporaryDirectory(prefix=TMP_PREFIX) as tmp:
                paths.append(Path(tmp))
                sb = Sandbox(tmp)
                sb.git("invalid-command")
        except ChildFailure:
            pass

        self.assertEqual(1, len(paths))
        self.assertFalse(paths[0].exists(), "temporary directory was cleaned up")


if __name__ == "__main__":
    unittest.main(verbosity=2)
