#!/usr/bin/env python3
"""R03-T053: check-commit-log guide - recover a commit hidden from `git log` by a mistake.

Run from the repository root:  python3 work/R03-T053/check.py

Builds a throw-away repository (no remote is needed: the reflog is local) with three
commits on `main`:

    A  creates notes.txt  "alpha\\n"
    B  appends            "beta\\n"
    C  adds todo.txt      "one\\n"

and a branch `topic` at B.  `main` is checked out.  The scenario:

    1. read the log with the guide's commands (git log -n 2, git log --all -- <file>)
    2. leave an UNCOMMITTED edit in notes.txt
    3. mistake: `git reset --hard <B>` on main  -> C disappears from git log
    4. find C again in the reflog and `git reset --hard <C>`
    5. verify the tree hash and file contents, and that the uncommitted edit stayed lost

All destructive commands run only inside the temporary repository (asserted).
Every assertion goes through expect(), which records expected-vs-actual and raises
AssertionError (non-zero exit) on mismatch.  Evidence files are written next to this
script even when a check fails.

Needs: git >= 2.28 (init -b) and Python 3.8+.
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

COMMANDS = []  # every git call -> commands.log
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

    def git(self, *args, ok=(0,)):
        """Run git. ok=(0,) -> raise unless exit code is 0; ok=None -> caller inspects it."""
        p = subprocess.run(["git", *args], cwd=self.path, env=self.env(),
                           capture_output=True, text=True)
        COMMANDS.append({"cmd": "git " + " ".join(args), "returncode": p.returncode,
                         "stdout": p.stdout, "stderr": p.stderr})
        if ok is not None and p.returncode not in ok:
            raise RuntimeError("git %s failed (%d): %s" % (" ".join(args), p.returncode, p.stderr))
        return p

    def out(self, *args):
        return self.git(*args).stdout.strip()

    def lines(self, *args):
        return self.out(*args).splitlines()

    def refs(self):
        rows = self.lines("for-each-ref", "--format=%(refname) %(objectname)")
        return dict(r.split(" ", 1) for r in rows)

    def read(self, name):
        return (self.path / name).read_text()

    def commit_file(self, name, text, message, append=False):
        with open(self.path / name, "a" if append else "w") as f:
            f.write(text)
        self.git("add", name)
        self.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
        return self.out("rev-parse", "HEAD")


def main_scenario(tmp):
    repo = Repo(tmp)
    repo.git("init", "-q", "-b", "main")
    a = repo.commit_file("notes.txt", "alpha\n", "A: create notes.txt")
    b = repo.commit_file("notes.txt", "beta\n", "B: append beta", append=True)
    c = repo.commit_file("todo.txt", "one\n", "C: add todo.txt")
    repo.git("branch", "topic", b)
    tree_c = repo.out("rev-parse", c + "^{tree}")
    start_refs = repo.refs()

    # Safety: every destructive command below runs in the temporary repository only.
    toplevel = Path(repo.out("rev-parse", "--show-toplevel")).resolve()
    expect("destructive commands run only inside the temp repo", True,
           str(toplevel).startswith(str(Path(tmp).resolve())))

    expect("start: main is checked out", "refs/heads/main", repo.out("symbolic-ref", "HEAD"))
    expect("start: main at C, topic at B", {"refs/heads/main": c, "refs/heads/topic": b}, start_refs)
    expect("start: author is Course Student", [NAME + " <" + EMAIL + ">"] * 3,
           repo.lines("log", "--format=%an <%ae>"))

    # 1. The guide's commands.
    expect("guide: `git log -n 2` lists C then B", [c, b], repo.lines("log", "-n", "2", "--format=%H"))
    expect("guide: `git log --all -- todo.txt` lists C", [c],
           repo.lines("log", "--all", "--format=%H", "--", "todo.txt"))

    # 2. An uncommitted edit (will NOT be recoverable).
    with open(repo.path / "notes.txt", "a") as f:
        f.write("gamma\n")
    expect("uncommitted edit is present", " M notes.txt\n", repo.git("status", "--porcelain").stdout)

    # 3. The mistake: the id of B is taken from `git log -n 2`, then main is reset to it.
    b_from_log = repo.lines("log", "-n", "2", "--format=%H")[1]
    repo.git("reset", "--hard", b_from_log)
    expect("mistake: main now points at B", b, repo.refs()["refs/heads/main"])
    expect("mistake: topic did not move", b, repo.refs()["refs/heads/topic"])
    expect("mistake: HEAD is still on main", "refs/heads/main", repo.out("symbolic-ref", "HEAD"))
    expect("mistake: git log lists only B, A", [b, a], repo.lines("log", "--format=%H"))
    expect("mistake: even `git log --all` no longer lists C", [b, a],
           repo.lines("log", "--all", "--format=%H"))
    expect("mistake: todo.txt is gone from the working tree", False, (repo.path / "todo.txt").exists())
    expect("mistake: the commit object still exists", 0, repo.git("cat-file", "-e", c).returncode)

    # 4. Recovery: find C in the reflog (do not reuse the saved id), then move main back.
    reflog = [r.split("\t", 1) for r in repo.lines("reflog", "show", "--format=%H%x09%gs", "HEAD")]
    found = [sha for sha, subject in reflog if "C: add todo.txt" in subject]
    expect("recovery point: the reflog has exactly one entry for C, with C's id", [c], found)
    expect("recovery point: main@{1} is also C", c, repo.out("rev-parse", "main@{1}"))
    repo.git("reset", "--hard", found[0])

    # 5. Verification.
    expect("recovered: main points at C again", c, repo.refs()["refs/heads/main"])
    expect("recovered: tree hash equals the saved tree hash of C", tree_c,
           repo.out("rev-parse", "main^{tree}"))
    expect("recovered: git log lists C, B, A", [c, b, a], repo.lines("log", "--format=%H"))
    expect("recovered: notes.txt content", "alpha\nbeta\n", repo.read("notes.txt"))
    expect("recovered: todo.txt content", "one\n", repo.read("todo.txt"))
    expect("recovered: working tree clean", "", repo.out("status", "--porcelain"))
    expect("recovered: all refs are back where they started", start_refs, repo.refs())
    expect("NOT recoverable: the uncommitted 'gamma' edit stays lost", False,
           "gamma" in repo.read("notes.txt"))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T053",
        "guide": "docs/additional-material/git_workflow_scenarios/check-commit-log.md",
        "author": NAME + " <" + EMAIL + ">",
        "commits": {"A": "create notes.txt 'alpha\\n'", "B": "append 'beta\\n' to notes.txt",
                    "C": "add todo.txt 'one\\n'"},
        "branches": {"main": "A-B-C (checked out)", "topic": "at B"},
        "remote": "none: the reflog is local",
        "mistake": "git reset --hard <B>, with an uncommitted edit in notes.txt",
        "recovery": "git reflog -> git reset --hard <C>",
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
        with tempfile.TemporaryDirectory(prefix="r03-t053-") as tmp:
            main_scenario(tmp)
    finally:
        write_evidence()
    print("OK: %d checks passed" % len(RESULTS))


if __name__ == "__main__":
    main()
