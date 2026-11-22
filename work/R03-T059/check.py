#!/usr/bin/env python3
"""R03-T059: resetting-a-branch guide - predict, run, explain.

Run from the repository root:  python3 work/R03-T059/check.py

The exercise from the guide section is built with its exact command lines (run through the
shell) in six temporary repositories (no remote is needed: reset is local):

    main  = A --- B --- C          (A creates notes.txt, B appends, C adds todo.txt)
    topic = B                      (checked out)

Commit dates are fixed per commit, so all six repositories are byte-for-byte equivalent
(same commit ids).  The exercise: reset `topic` so that it matches `main`.

    repository 1:  the guide's literal syntax  `git reset topic main --hard`  (and without --hard)
    repository 2:  git reset --soft main
    repository 3:  git reset main            (--mixed, the default)
    repository 4:  git reset --hard main
    repository 5:  git reset --hard main, with a staged edit and an untracked file present
    repository 6:  the alternative the guide mentions: delete topic, create it again from main

For the three modes the PREDICTIONS table below is written down first (it is the table in the
guide) and compared with what git really does: where refs/heads/topic points, what the index
holds, what the working tree holds, and what `git status --short` shows.

Every assertion goes through expect(), which records expected-vs-actual and raises
AssertionError (non-zero exit) on mismatch.  Evidence files are written next to this script
even when a check fails.

Needs: git >= 2.28 (init -b), Python 3.8+, a POSIX shell.
"""
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "Course Student"
EMAIL = "student@example.invalid"
MSG_A, MSG_B, MSG_C = "A: create notes.txt", "B: append beta", "C: add todo.txt"

# The reproducible example from the guide section, one command per line.
EXAMPLE = [
    "git init -b main",
    "printf 'alpha\\n' > notes.txt",
    "git add notes.txt",
    'git commit -m "%s"' % MSG_A,
    "printf 'beta\\n' >> notes.txt",
    'git commit -am "%s"' % MSG_B,
    "printf 'one\\n' > todo.txt",
    "git add todo.txt",
    'git commit -m "%s"' % MSG_C,
    "git branch topic HEAD~1",
    "git switch topic",
]

# Written down before running anything: after resetting topic (currently at B) to main (at C).
# In every mode topic moves to C, main does not move and HEAD stays on topic.
PREDICTIONS = {
    "--soft":  {"command": "git reset --soft main",
                "index": ["notes.txt"], "worktree": ["notes.txt"], "status": ["D  todo.txt"]},
    "--mixed": {"command": "git reset main",
                "index": ["notes.txt", "todo.txt"], "worktree": ["notes.txt"], "status": [" D todo.txt"]},
    "--hard":  {"command": "git reset --hard main",
                "index": ["notes.txt", "todo.txt"], "worktree": ["notes.txt", "todo.txt"], "status": []},
}

COMMANDS = []  # every command -> commands.log
RESULTS = []   # expected-vs-actual rows -> expected_vs_actual.md


def expect(label, expected, actual):
    ok = expected == actual
    RESULTS.append({"check": label, "expected": expected, "actual": actual, "ok": ok})
    if not ok:
        raise AssertionError("%s: expected %r, got %r" % (label, expected, actual))


class Repo:
    """A temporary repository plus an isolated HOME so no user/system git config leaks in."""

    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / "repo"
        self.home = self.root / "home"
        self.path.mkdir(parents=True)
        self.home.mkdir()
        (self.root / "xdg").mkdir()

    def env(self, extra=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.root / "xdg"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": NAME, "GIT_AUTHOR_EMAIL": EMAIL,
            "GIT_COMMITTER_NAME": NAME, "GIT_COMMITTER_EMAIL": EMAIL,
            "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C",
            "GIT_EDITOR": "false",  # an editor opening unexpectedly fails instead of hanging
        })
        if extra:
            env.update(extra)
        return env

    def _run(self, cmd, label, shell, ok, extra):
        p = subprocess.run(cmd, shell=shell, cwd=self.path, env=self.env(extra),
                           capture_output=True, text=True)
        COMMANDS.append({"cmd": label, "returncode": p.returncode,
                         "stdout": p.stdout, "stderr": p.stderr})
        if ok is not None and p.returncode not in ok:
            raise RuntimeError("%s failed (%d): %s" % (label, p.returncode, p.stderr))
        return p

    def git(self, *args, ok=(0,)):
        """Run git with an argument list. ok=None -> the caller inspects the exit code."""
        return self._run(["git", *args], "git " + " ".join(args), False, ok, None)

    def sh(self, command, ok=(0,), extra=None):
        """Run a command string through the shell, exactly as typed in a terminal."""
        return self._run(command, command, True, ok, extra)

    def out(self, *args):
        return self.git(*args).stdout.strip()

    def lines(self, *args):
        return self.git(*args).stdout.splitlines()

    def refs(self):
        rows = self.lines("for-each-ref", "--format=%(refname) %(objectname)")
        return dict(r.split(" ", 1) for r in rows)

    def worktree(self):
        return sorted(p.name for p in self.path.iterdir() if p.is_file())

    def snapshot(self):
        """Ref, index and working-tree state in one comparable value."""
        files = {p.name: p.read_text() for p in sorted(self.path.iterdir()) if p.is_file()}
        return {"head": self.out("symbolic-ref", "HEAD"), "refs": self.refs(),
                "index": self.git("ls-files", "--stage").stdout,
                "status": self.git("status", "--porcelain").stdout, "files": files}


def build_fixture(root):
    """Run the guide's example; each commit gets its own fixed date so ids are reproducible."""
    repo = Repo(root)
    n = 0
    for command in EXAMPLE:
        extra = None
        if command.startswith("git commit"):
            n += 1
            date = "2026-01-%02dT12:00:00+0000" % n
            extra = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        repo.sh(command, extra=extra)
    ids = {"A": repo.out("rev-parse", "topic~1"), "B": repo.out("rev-parse", "topic"),
           "C": repo.out("rev-parse", "main")}

    toplevel = Path(repo.out("rev-parse", "--show-toplevel")).resolve()
    expect("commands run only inside the temp repo", True,
           str(toplevel).startswith(str(Path(root).resolve())))
    return repo, ids


def fixture(tmp, name, reference=None):
    """A fixture plus the checks that make all fixtures equivalent to the first one."""
    (tmp / name).mkdir()
    repo, ids = build_fixture(tmp / name)
    expect(name + ": topic is checked out", "refs/heads/topic", repo.out("symbolic-ref", "HEAD"))
    expect(name + ": main at C, topic at B",
           {"refs/heads/main": ids["C"], "refs/heads/topic": ids["B"]}, repo.refs())
    expect(name + ": author is Course Student", [NAME + " <" + EMAIL + ">"] * 3,
           repo.lines("log", "main", "--format=%an <%ae>"))
    expect(name + ": the working tree has notes.txt only, the index too",
           (["notes.txt"], ["notes.txt"], ""),
           (repo.worktree(), repo.lines("ls-files"), repo.git("status", "--porcelain").stdout))
    snap = repo.snapshot()
    if reference is not None:
        expect(name + ": equivalent to the first fixture (same ids, same state)",
               reference, (ids, snap))
    return repo, ids, (ids, snap)


def check_reset_result(repo, ids, before, mode, label):
    """Refs, index, working tree and status after resetting topic to main in the given mode."""
    predicted = PREDICTIONS[mode]
    after = repo.refs()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    expect(label + ": the only ref that changed is refs/heads/topic", ["refs/heads/topic"], changed)
    expect(label + ": topic moved from B to C", (ids["B"], ids["C"]),
           (before["refs/heads/topic"], after["refs/heads/topic"]))
    expect(label + ": main did not move", ids["C"], after["refs/heads/main"])
    expect(label + ": HEAD is still on topic", "refs/heads/topic", repo.out("symbolic-ref", "HEAD"))
    expect(label + ": ORIG_HEAD remembers the old tip (B)", ids["B"], repo.out("rev-parse", "ORIG_HEAD"))
    expect(label + ": index, as predicted", predicted["index"], repo.lines("ls-files"))
    expect(label + ": working tree, as predicted", predicted["worktree"], repo.worktree())
    expect(label + ": git status --short, as predicted", predicted["status"], repo.lines("status", "--short"))


def scenario(tmp):
    # --- repository 1: the guide's literal syntax ---------------------------------------
    repo1, ids, reference = fixture(tmp, "r1")
    before_refs = repo1.refs()
    p = repo1.sh("git reset topic main --hard", ok=None)
    expect("literal `git reset topic main --hard` fails", 128, p.returncode)
    expect("the failure is about paths", True, "hard reset with paths" in p.stderr.lower())
    repo1.sh("git reset topic main", ok=None)
    expect("literal `git reset topic main` moves no branch (main is read as a path)",
           reference[1], repo1.snapshot())
    expect("the guide's syntax changed nothing: topic still at B, main at C", before_refs, repo1.refs())

    # --- repositories 2-4: the three modes, predicted first ------------------------------
    for name, mode in (("r2", "--soft"), ("r3", "--mixed"), ("r4", "--hard")):
        repo, ids_n, _ = fixture(tmp, name, reference)
        before = repo.refs()
        repo.sh(PREDICTIONS[mode]["command"])
        check_reset_result(repo, ids_n, before, mode, mode)
        if mode == "--hard":
            hard_snapshot = repo.snapshot()
            hard_repo = repo
        else:
            repo.sh("git reset --hard ORIG_HEAD")
            expect(mode + ": git reset --hard ORIG_HEAD goes back to the start (refs, index, working tree)",
                   reference[1], repo.snapshot())

    expect("--hard: the content of the working tree is C's", {"notes.txt": "alpha\nbeta\n", "todo.txt": "one\n"},
           hard_snapshot["files"])
    expect("--hard: the index matches C exactly (no difference to HEAD)", "",
           hard_repo.git("diff", "--cached", "--name-status").stdout)

    # --- repository 5: --hard with a staged edit and an untracked file ------------------------
    repo5, ids5, _ = fixture(tmp, "r5", reference)
    repo5.sh("printf 'scratch\\n' >> notes.txt")
    repo5.sh("git add notes.txt")
    repo5.sh("printf 'draft\\n' > untracked.txt")
    expect("r5: the staged edit and the untracked file are there before the reset",
           ["M  notes.txt", "?? untracked.txt"], repo5.lines("status", "--short"))
    repo5.sh("git reset --hard main")
    expect("r5: topic moved to C", ids5["C"], repo5.out("rev-parse", "topic"))
    expect("r5: the staged edit is gone, notes.txt is C's version", "alpha\nbeta\n",
           (repo5.path / "notes.txt").read_text())
    expect("r5: the index has no staged change left", "", repo5.git("diff", "--cached", "--name-status").stdout)
    expect("r5: the untracked file survived --hard", ["?? untracked.txt"], repo5.lines("status", "--short"))
    expect("r5: working tree now has C's files plus the untracked one",
           ["notes.txt", "todo.txt", "untracked.txt"], repo5.worktree())

    # --- repository 6: delete the branch and create it again from main ------------------------
    repo6, ids6, _ = fixture(tmp, "r6", reference)
    repo6.sh("git switch main")
    repo6.sh("git branch -D topic")
    repo6.sh("git switch -c topic main")
    expect("r6: same end state as the reset: topic at C, HEAD on topic",
           (ids6["C"], "refs/heads/topic"), (repo6.out("rev-parse", "topic"), repo6.out("symbolic-ref", "HEAD")))
    expect("r6: same index, working tree and status as git reset --hard main",
           (hard_snapshot["index"], hard_snapshot["status"], hard_snapshot["files"]),
           (repo6.git("ls-files", "--stage").stdout, repo6.git("status", "--porcelain").stdout,
            repo6.snapshot()["files"]))
    expect("r6: but the branch's old position is gone (no topic@{1})", True,
           repo6.git("rev-parse", "--verify", "-q", "topic@{1}", ok=None).returncode != 0)
    expect("reset keeps it: topic@{1} is B after git reset --hard main", ids["B"],
           hard_repo.out("rev-parse", "topic@{1}"))
    hard_repo.sh("git reset --hard ORIG_HEAD")
    expect("--hard: git reset --hard ORIG_HEAD goes back to the start (refs, index, working tree)",
           reference[1], hard_repo.snapshot())


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T059",
        "guide": "docs/additional-material/git_workflow_scenarios/resetting-a-branch.md",
        "operation": "git reset (--soft, --mixed, --hard) of topic to main",
        "author": NAME + " <" + EMAIL + ">",
        "commits": {"A": "create notes.txt 'alpha\\n'", "B": "append 'beta\\n' to notes.txt",
                    "C": "add todo.txt 'one\\n'"},
        "branches": {"main": "A-B-C", "topic": "at B, checked out"},
        "remote": "none: git reset is local",
        "commit_dates": ["2026-01-01T12:00:00+0000", "2026-01-02T12:00:00+0000",
                         "2026-01-03T12:00:00+0000"],
        "example": EXAMPLE,
        "predictions": PREDICTIONS,
    }
    (HERE / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")

    rows = ["| check | expected | actual | ok |", "|---|---|---|---|"]
    for r in RESULTS:
        text = lambda v: json.dumps(v, default=str).replace("|", "\\|")
        rows.append("| %s | `%s` | `%s` | %s |" % (
            r["check"], text(r["expected"]), text(r["actual"]), "yes" if r["ok"] else "NO"))
    (HERE / "expected_vs_actual.md").write_text("\n".join(rows) + "\n")

    log = []
    for c in COMMANDS:
        log.append("$ %s\n[exit %d]\n%s%s" % (c["cmd"], c["returncode"], c["stdout"], c["stderr"]))
    (HERE / "commands.log").write_text("\n".join(log))


def main():
    try:
        with tempfile.TemporaryDirectory(prefix="r03-t059-") as tmp:
            scenario(Path(tmp))
    finally:
        write_evidence()
    print("OK: %d checks passed" % len(RESULTS))


if __name__ == "__main__":
    main()
