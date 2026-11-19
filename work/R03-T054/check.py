#!/usr/bin/env python3
"""R03-T054: amending-a-commit guide - paths with spaces, quoting, and `--`.

Run from the repository root:  python3 work/R03-T054/check.py

Builds a throw-away repository (no remote is needed: amending is a local rewrite) with
three commits on `main`:

    A  creates notes.txt  "alpha\\n"
    B  appends            "beta\\n"
    C  adds todo.txt      "one\\n"

and a branch `topic` at B, which is checked out.  The scenario, using a file named
"release notes.txt" and a directory named "sample data":

    1. `git add release notes.txt`            -> shell splits the name, git refuses
    2. `git add -- "release notes.txt" ...`   -> quoted paths are staged, then committed (D)
    3. edit the file again, stage ONLY it, `git commit --amend --no-edit`  -> D is replaced
    4. `git log` with a path, and a file named like a branch (revision vs filename)

The exact command strings are run through the shell (sh -c), so the quoting shown in
the guide is what is really being tested.  Every assertion goes through expect(), which
records expected-vs-actual and raises AssertionError (non-zero exit) on mismatch.
Evidence files are written next to this script even when a check fails.

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
D_MESSAGE = "D: add release notes and sample data"

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

    def env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update({
            "HOME": str(self.home),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": NAME, "GIT_AUTHOR_EMAIL": EMAIL,
            "GIT_COMMITTER_NAME": NAME, "GIT_COMMITTER_EMAIL": EMAIL,
            "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C",
            "GIT_EDITOR": "false",  # an editor opening unexpectedly fails instead of hanging
        })
        return env

    def _run(self, cmd, label, shell, ok):
        p = subprocess.run(cmd, shell=shell, cwd=self.path, env=self.env(),
                           capture_output=True, text=True)
        COMMANDS.append({"cmd": label, "returncode": p.returncode,
                         "stdout": p.stdout, "stderr": p.stderr})
        if ok is not None and p.returncode not in ok:
            raise RuntimeError("%s failed (%d): %s" % (label, p.returncode, p.stderr))
        return p

    def git(self, *args, ok=(0,)):
        """Run git with an argument list. ok=None -> the caller inspects the exit code."""
        return self._run(["git", *args], "git " + " ".join(args), False, ok)

    def sh(self, command, ok=(0,)):
        """Run a command string through the shell, exactly as typed in a terminal."""
        return self._run(command, command, True, ok)

    def out(self, *args):
        return self.git(*args).stdout.strip()

    def lines(self, *args):
        return self.git(*args).stdout.splitlines()

    def names(self, *args):
        """Path list from a git command that was given -z (NUL separated, never quoted)."""
        return [n for n in self.git(*args).stdout.split("\0") if n]

    def refs(self):
        rows = self.lines("for-each-ref", "--format=%(refname) %(objectname)")
        return dict(r.split(" ", 1) for r in rows)

    def put(self, name, text, append=False):
        target = self.path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a" if append else "w") as f:
            f.write(text)

    def read(self, name):
        return (self.path / name).read_text()

    def commit_file(self, name, text, message, append=False):
        self.put(name, text, append)
        self.git("add", name)
        self.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
        return self.out("rev-parse", "HEAD")


def scenario(tmp):
    repo = Repo(tmp)
    repo.git("init", "-q", "-b", "main")
    a = repo.commit_file("notes.txt", "alpha\n", "A: create notes.txt")
    b = repo.commit_file("notes.txt", "beta\n", "B: append beta", append=True)
    c = repo.commit_file("todo.txt", "one\n", "C: add todo.txt")
    repo.git("branch", "topic", b)
    repo.git("checkout", "-q", "topic")

    # Safety: every command below runs in the temporary repository only.
    toplevel = Path(repo.out("rev-parse", "--show-toplevel")).resolve()
    expect("commands run only inside the temp repo", True,
           str(toplevel).startswith(str(Path(tmp).resolve())))
    expect("start: topic is checked out", "refs/heads/topic", repo.out("symbolic-ref", "HEAD"))
    expect("start: main at C, topic at B", {"refs/heads/main": c, "refs/heads/topic": b}, repo.refs())
    expect("start: author is Course Student", [NAME + " <" + EMAIL + ">"] * 3,
           repo.lines("log", "main", "--format=%an <%ae>"))

    repo.put("release notes.txt", "v1\n")
    repo.put("sample data/readings.csv", "x,y\n1,2\n")

    # 1. Unquoted names: the shell splits them into separate words.
    p = repo.sh("git add release notes.txt", ok=None)
    expect("unquoted file name: git add fails", True, p.returncode != 0)
    expect("unquoted file name: git looks for a file called 'release'", True,
           "pathspec 'release' did not match any files" in p.stderr)
    p = repo.sh("git add sample data", ok=None)
    expect("unquoted directory name: git looks for 'sample'", True,
           "pathspec 'sample' did not match any files" in p.stderr)
    expect("failed adds staged nothing", [], repo.names("diff", "--cached", "--name-only", "-z"))

    # 2. Quoted names, then the usual commit (this is commit D).
    repo.sh('git add -- "release notes.txt" "sample data"')
    expect("quoted paths: exactly the intended files are staged",
           ["release notes.txt", "sample data/readings.csv"],
           repo.names("diff", "--cached", "--name-only", "-z"))
    expect("git status --short shows the names in quotes (display only)",
           ['A  "release notes.txt"', 'A  "sample data/readings.csv"'],
           repo.lines("status", "--short"))
    repo.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", D_MESSAGE)
    d = repo.out("rev-parse", "HEAD")
    expect("D sits on top of B", b, repo.out("rev-parse", d + "^"))

    # 3. Forget a line: edit, stage ONLY that file, amend.
    repo.put("release notes.txt", "v2 line\n", append=True)
    repo.put("notes.txt", "gamma\n", append=True)  # an unrelated edit that must stay out
    repo.sh('git add -- "release notes.txt"')
    expect("only the intended file is staged",
           ["release notes.txt"], repo.names("diff", "--cached", "--name-only", "-z"))
    expect("git status --short: staged file quoted, unrelated edit unstaged",
           [' M notes.txt', 'M  "release notes.txt"'], repo.lines("status", "--short"))
    before = repo.refs()
    repo.sh("git commit --amend --no-edit")
    d2 = repo.out("rev-parse", "HEAD")
    after = repo.refs()

    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    expect("amend: the only ref that changed is refs/heads/topic", ["refs/heads/topic"], changed)
    expect("amend: main still points at C", c, after["refs/heads/main"])
    expect("amend: topic points at a new commit", True, d2 not in (b, c, d))
    expect("amend: the new commit has the same parent (B)", b, repo.out("rev-parse", d2 + "^"))
    expect("amend: the message was kept", D_MESSAGE, repo.out("log", "-1", "--format=%s"))
    expect("amend: release notes.txt in the new commit has both lines", "v1\nv2 line\n",
           repo.git("show", d2 + ":release notes.txt").stdout)
    expect("amend: the commit contains the two intended paths",
           ["release notes.txt", "sample data/readings.csv"],
           repo.names("show", "--name-only", "--format=", "-z", d2))
    expect("amend: unrelated notes.txt was not swept into the commit", "alpha\nbeta\n",
           repo.git("show", d2 + ":notes.txt").stdout)
    expect("amend: the unrelated edit is still there, unstaged", ["notes.txt"],
           repo.names("diff", "--name-only", "-z"))
    expect("amend: the old commit D is still reachable as topic@{1}", d, repo.out("rev-parse", "topic@{1}"))

    # 4. Paths in git log, and a file whose name is also a revision.
    by_path = repo.lines("log", "--format=%s", "--", "release notes.txt")
    expect("git log -- \"release notes.txt\" lists the commit that holds it", [D_MESSAGE], by_path)
    expect("quoted path also works without --, when it is not ambiguous", by_path,
           repo.sh('git log --format=%s "release notes.txt"').stdout.splitlines())

    repo.put("topic", "x\n")  # a file with the same name as the branch
    p = repo.sh("git log --oneline topic", ok=None)
    expect("file named like a branch: git log refuses to guess", True, p.returncode != 0)
    expect("ambiguity error text", True,
           "ambiguous argument 'topic': both revision and filename" in p.stderr
           and "Use '--' to separate paths from revisions" in p.stderr)
    expect("`git log topic --` means the branch", [D_MESSAGE, "B: append beta", "A: create notes.txt"],
           repo.sh("git log --format=%s topic --").stdout.splitlines())
    expect("`git log -- topic` means the file (no history)", [],
           repo.sh("git log --format=%s -- topic").stdout.splitlines())


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T054",
        "guide": "docs/additional-material/git_workflow_scenarios/amending-a-commit.md",
        "author": NAME + " <" + EMAIL + ">",
        "commits": {"A": "create notes.txt 'alpha\\n'", "B": "append 'beta\\n' to notes.txt",
                    "C": "add todo.txt 'one\\n'",
                    "D": "add 'release notes.txt' and 'sample data/readings.csv' on topic, then amend"},
        "branches": {"main": "A-B-C", "topic": "at B, checked out"},
        "remote": "none: amending is a local rewrite",
        "paths": ["release notes.txt", "sample data/readings.csv"],
    }
    (HERE / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")

    rows = ["| check | expected | actual | ok |", "|---|---|---|---|"]
    for r in RESULTS:
        rows.append("| %s | `%s` | `%s` | %s |" % (
            r["check"], json.dumps(r["expected"]), json.dumps(r["actual"]), "yes" if r["ok"] else "NO"))
    (HERE / "expected_vs_actual.md").write_text("\n".join(rows) + "\n")

    log = []
    for c in COMMANDS:
        log.append("$ %s\n[exit %d]\n%s%s" % (c["cmd"], c["returncode"], c["stdout"], c["stderr"]))
    (HERE / "commands.log").write_text("\n".join(log))


def main():
    try:
        with tempfile.TemporaryDirectory(prefix="r03-t054-") as tmp:
            scenario(tmp)
    finally:
        write_evidence()
    print("OK: %d checks passed" % len(RESULTS))


if __name__ == "__main__":
    main()
