#!/usr/bin/env python3
"""R03-T057: check-commit-log guide - `git log` compared with `git log --all`.

Run from the repository root:  python3 work/R03-T057/check.py

The example from the guide section is built with its exact command lines (run through
the shell) in three temporary repositories (no remote is needed: the log is local):

    main  = A --- B --- C          (A creates notes.txt, B appends, C adds todo.txt)
    topic = B                      (checked out, except in repository 3)

Commit dates are fixed per commit, so repositories 1 and 2 are byte-for-byte equivalent
(same commit ids).  Then:

    repository 1:  git log ...           (history of the checked-out branch)
    repository 2:  git log --all ...     (history of every ref)
    repository 3:  both, after `git switch main`

Facts asserted: what each command lists; WHY they differ (which refs contain C, whether C
is an ancestor of HEAD); that neither command changes refs, HEAD, index, status or
working-tree files; that the two repositories end in identical states.

Every assertion goes through expect(), which records expected-vs-actual and raises
AssertionError (non-zero exit) on mismatch.  Evidence files are written next to this
script even when a check fails.

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

    def listing(self, command):
        return self.sh(command).stdout.splitlines()

    def refs(self):
        rows = self.lines("for-each-ref", "--format=%(refname) %(objectname)")
        return dict(r.split(" ", 1) for r in rows)

    def snapshot(self):
        """Everything a read-only command must leave alone."""
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


def check_fixture(repo, ids, label):
    expect(label + ": topic is checked out", "refs/heads/topic", repo.out("symbolic-ref", "HEAD"))
    expect(label + ": main at C, topic at B",
           {"refs/heads/main": ids["C"], "refs/heads/topic": ids["B"]}, repo.refs())
    expect(label + ": history of main is C, B, A", [MSG_C, MSG_B, MSG_A],
           repo.lines("log", "main", "--format=%s"))
    expect(label + ": author is Course Student", [NAME + " <" + EMAIL + ">"] * 3,
           repo.lines("log", "main", "--format=%an <%ae>"))
    expect(label + ": the working tree has notes.txt only (todo.txt is not on topic)",
           {"notes.txt": "alpha\nbeta\n"}, repo.snapshot()["files"])


def scenario(tmp):
    # --- repository 1: `git log` on topic ---------------------------------------------
    (tmp / "r1").mkdir()
    repo1, ids1 = build_fixture(tmp / "r1")
    check_fixture(repo1, ids1, "fixture 1")
    before1 = repo1.snapshot()
    expect("git log: lists the commits reachable from the checked-out branch (B, A)",
           [MSG_B, MSG_A], repo1.listing("git log --format=%s"))
    expect("git log -- todo.txt: lists nothing (todo.txt has no history on topic)",
           [], repo1.listing("git log --format=%s -- todo.txt"))
    after1 = repo1.snapshot()
    expect("git log: refs, HEAD, index, status and files are unchanged", before1, after1)

    # --- repository 2: `git log --all`, an equivalent fixture --------------------------
    (tmp / "r2").mkdir()
    repo2, ids2 = build_fixture(tmp / "r2")
    check_fixture(repo2, ids2, "fixture 2")
    expect("fixtures 1 and 2 have the same commit ids", ids1, ids2)
    before2 = repo2.snapshot()
    expect("fixtures 1 and 2 start in the same state", before1, before2)

    expect("git log --all: lists the commits reachable from every ref (C, B, A)",
           [MSG_C, MSG_B, MSG_A], repo2.listing("git log --format=%s --all"))
    expect("git log --all -- todo.txt: lists C",
           [MSG_C], repo2.listing("git log --format=%s --all -- todo.txt"))
    expect("git log --all -- notes.txt: the file name restricts the commits (C is skipped)",
           [MSG_B, MSG_A], repo2.listing("git log --format=%s --all -- notes.txt"))
    after2 = repo2.snapshot()
    expect("git log --all: refs, HEAD, index, status and files are unchanged", before2, after2)
    expect("both workflows end in the same state", after1, after2)

    # --- why they differ: refs -----------------------------------------------------------
    expect("C is contained in refs/heads/main only", ["refs/heads/main"],
           repo2.lines("for-each-ref", "--contains", ids2["C"], "--format=%(refname)"))
    expect("B is contained in main and topic", ["refs/heads/main", "refs/heads/topic"],
           repo2.lines("for-each-ref", "--contains", ids2["B"], "--format=%(refname)"))
    expect("C is not an ancestor of HEAD (topic)", 1,
           repo2.git("merge-base", "--is-ancestor", ids2["C"], "HEAD", ok=None).returncode)
    expect("C is an ancestor of main", 0,
           repo2.git("merge-base", "--is-ancestor", ids2["C"], "main", ok=None).returncode)

    # --- the guide's literal form `git log --all <filename>` ----------------------------
    p = repo2.sh("git log --all todo.txt", ok=None)
    expect("git log --all todo.txt fails while todo.txt is not in the working tree", 128, p.returncode)
    expect("the failure is the filename-or-revision ambiguity", True,
           "ambiguous argument 'todo.txt'" in p.stderr)

    # --- repository 3: after `git switch main` the two commands agree -------------------
    (tmp / "r3").mkdir()
    repo3, ids3 = build_fixture(tmp / "r3")
    repo3.sh("git switch main")
    plain = repo3.listing("git log --format=%s")
    expect("on main: git log lists C, B, A", [MSG_C, MSG_B, MSG_A], plain)
    expect("on main: git log --all lists the same", plain, repo3.listing("git log --format=%s --all"))
    expect("on main: git log --all todo.txt works without -- (the file exists)", [MSG_C],
           repo3.listing("git log --format=%s --all todo.txt"))
    expect("on main: topic is contained in main, so --all adds nothing", 0,
           repo3.git("merge-base", "--is-ancestor", "topic", "main", ok=None).returncode)


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T057",
        "guide": "docs/additional-material/git_workflow_scenarios/check-commit-log.md",
        "compared": ["git log", "git log --all"],
        "author": NAME + " <" + EMAIL + ">",
        "commits": {"A": "create notes.txt 'alpha\\n'", "B": "append 'beta\\n' to notes.txt",
                    "C": "add todo.txt 'one\\n'"},
        "branches": {"main": "A-B-C", "topic": "at B, checked out"},
        "remote": "none: the log is local",
        "commit_dates": ["2026-01-01T12:00:00+0000", "2026-01-02T12:00:00+0000",
                         "2026-01-03T12:00:00+0000"],
        "example": EXAMPLE,
    }
    (HERE / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")

    rows = ["| check | expected | actual | ok |", "|---|---|---|---|"]
    for r in RESULTS:
        text = lambda v: json.dumps(v).replace("|", "\\|")
        rows.append("| %s | `%s` | `%s` | %s |" % (
            r["check"], text(r["expected"]), text(r["actual"]), "yes" if r["ok"] else "NO"))
    (HERE / "expected_vs_actual.md").write_text("\n".join(rows) + "\n")

    log = []
    for c in COMMANDS:
        log.append("$ %s\n[exit %d]\n%s%s" % (c["cmd"], c["returncode"], c["stdout"], c["stderr"]))
    (HERE / "commands.log").write_text("\n".join(log))


def main():
    try:
        with tempfile.TemporaryDirectory(prefix="r03-t057-") as tmp:
            scenario(Path(tmp))
    finally:
        write_evidence()
    print("OK: %d checks passed" % len(RESULTS))


if __name__ == "__main__":
    main()
