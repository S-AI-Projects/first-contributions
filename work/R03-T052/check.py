#!/usr/bin/env python3
"""R03-T052: squashing-commits guide, current branch `topic`, default branch `main`.

Run from the repository root:  python3 work/R03-T052/check.py

Builds a throw-away repository (no remote is needed: squashing is a purely local
rewrite) with three commits on `main`:

    A  creates notes.txt  "alpha\\n"
    B  appends            "beta\\n"
    C  adds todo.txt      "one\\n"

and a branch `topic` at B, checked out.  Three scenarios are then run, each in its
own fresh repository:

    1. the guide as written:  git log, then  git rebase -i HEAD~2
    2. a common variation:    git rebase -i main
    3. what actually squashes A and B:  git rebase -i --root

Every assertion goes through expect(), which records expected-vs-actual and raises
AssertionError (non-zero exit) on mismatch.  Evidence files are written next to this
script even when a check fails.

Needs: git >= 2.28 (init -b), Python 3.8+, a POSIX shell (git starts editors via sh).
"""
import json
import os
import platform
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "Course Student"
EMAIL = "student@example.invalid"
SQUASH_MESSAGE = "Add notes.txt with alpha and beta\n"

COMMANDS = []  # every git call -> commands.log
RESULTS = []   # expected-vs-actual rows -> expected_vs_actual.md

# Stand-in for the editor that `git rebase -i` would open.  "todo" mode turns every
# `pick` after the first into `squash`; "msg" mode writes the final commit message.
EDITOR_PY = '''import sys
mode, path = sys.argv[1], sys.argv[2]
if mode == "todo":
    out, seen_first = [], False
    for line in open(path).read().splitlines(True):
        if line.startswith("pick "):
            if seen_first:
                line = "squash " + line[len("pick "):]
            seen_first = True
        out.append(line)
    open(path, "w").write("".join(out))
else:
    open(path, "w").write(%r)
''' % SQUASH_MESSAGE


def expect(label, expected, actual):
    ok = expected == actual
    RESULTS.append({"check": label, "expected": expected, "actual": actual, "ok": ok})
    if not ok:
        raise AssertionError("%s: expected %r, got %r" % (label, expected, actual))


class Repo:
    """A temporary repository plus an isolated HOME so no user/system git config leaks in."""

    def __init__(self, root):
        self.path = Path(root) / "repo"
        self.home = Path(root) / "home"
        self.path.mkdir(parents=True)
        self.home.mkdir()

    def env(self, extra=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update({
            "HOME": str(self.home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": NAME, "GIT_AUTHOR_EMAIL": EMAIL,
            "GIT_COMMITTER_NAME": NAME, "GIT_COMMITTER_EMAIL": EMAIL,
            "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C",
            # Any editor that opens unexpectedly fails loudly instead of hanging.
            "GIT_EDITOR": "false", "GIT_SEQUENCE_EDITOR": "false",
        })
        if extra:
            env.update(extra)
        return env

    def git(self, *args, env=None, ok=(0,)):
        """Run git. ok=(0,) -> raise unless exit code is 0; ok=None -> caller inspects it."""
        p = subprocess.run(["git", *args], cwd=self.path, env=self.env(env),
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

    def rebase_in_progress(self):
        git_dir = self.path / ".git"
        return (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists()


def build_repo(root):
    """main = A-B-C, topic = B, topic checked out. Returns (repo, A, B, C)."""
    repo = Repo(root)
    repo.git("init", "-q", "-b", "main")
    notes, todo = repo.path / "notes.txt", repo.path / "todo.txt"

    notes.write_text("alpha\n")
    repo.git("add", "notes.txt")
    repo.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "A: create notes.txt")
    a = repo.out("rev-parse", "HEAD")

    with open(notes, "a") as f:
        f.write("beta\n")
    repo.git("add", "notes.txt")
    repo.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "B: append beta")
    b = repo.out("rev-parse", "HEAD")

    todo.write_text("one\n")
    repo.git("add", "todo.txt")
    repo.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "C: add todo.txt")
    c = repo.out("rev-parse", "HEAD")

    repo.git("branch", "topic", b)
    repo.git("checkout", "-q", "topic")
    return repo, a, b, c


def check_start_state(repo, a, b, c, tag):
    expect(tag + ": current branch is topic", "refs/heads/topic", repo.out("symbolic-ref", "HEAD"))
    expect(tag + ": only main (at C) and topic (at B) exist",
           {"refs/heads/main": c, "refs/heads/topic": b}, repo.refs())
    expect(tag + ": commit author is Course Student",
           [NAME + " <" + EMAIL + ">"] * 3,
           repo.lines("log", "main", "--format=%an <%ae>"))


def scenario_guide_as_written(tmp):
    """Guide: `git log`, then `git rebase -i HEAD~2`, while topic is checked out."""
    repo, a, b, c = build_repo(tmp)
    check_start_state(repo, a, b, c, "s1")
    before = repo.refs()

    log_text = repo.git("log").stdout
    expect("s1: `git log` lists B and A but not C",
           (True, True, False),
           ("B: append beta" in log_text, "A: create notes.txt" in log_text,
            "C: add todo.txt" in log_text))
    expect("s1: topic history is B, A", [b, a], repo.lines("log", "--format=%H"))

    p = repo.git("rev-parse", "--verify", "--quiet", "HEAD~2", ok=None)
    expect("s1: HEAD~2 does not exist on topic (only 2 commits)", True, p.returncode != 0)

    p = repo.git("rebase", "-i", "HEAD~2", ok=None)
    expect("s1: `git rebase -i HEAD~2` fails on topic", True, p.returncode != 0)
    expect("s1: failed rebase changed no refs", before, repo.refs())
    expect("s1: no rebase left in progress", False, repo.rebase_in_progress())


def scenario_rebase_onto_main(tmp):
    """`git rebase -i main` from topic: nothing to squash, topic is just moved."""
    repo, a, b, c = build_repo(tmp)
    check_start_state(repo, a, b, c, "s2")

    expect("s2: main..topic is empty (nothing unique to squash)", [], repo.lines("rev-list", "main..topic"))
    expect("s2: topic..main is exactly C", [c], repo.lines("rev-list", "topic..main"))

    repo.git("rebase", "-i", "main", env={"GIT_SEQUENCE_EDITOR": "true"})  # accept the todo as-is
    after = repo.refs()
    expect("s2: main did not move", c, after["refs/heads/main"])
    expect("s2: topic was fast-forwarded to main's tip, not squashed", c, after["refs/heads/topic"])
    expect("s2: history is still three commits", 3, int(repo.out("rev-list", "--count", "topic")))


def scenario_squash_root(tmp):
    """Squash A and B on topic with `git rebase -i --root`."""
    repo, a, b, c = build_repo(tmp)
    check_start_state(repo, a, b, c, "s3")
    before = repo.refs()

    editor = Path(tmp) / "editor.py"
    editor.write_text(EDITOR_PY)
    py = shlex.quote(sys.executable) + " " + shlex.quote(str(editor))
    repo.git("rebase", "-i", "--root",
             env={"GIT_SEQUENCE_EDITOR": py + " todo", "GIT_EDITOR": py + " msg"})

    after = repo.refs()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    expect("s3: the only ref that changed is refs/heads/topic", ["refs/heads/topic"], changed)
    expect("s3: refs/heads/main still points at C", c, after["refs/heads/main"])

    s = after["refs/heads/topic"]
    expect("s3: new topic tip is a new commit (not A, B or C)", True, s not in (a, b, c))
    expect("s3: topic is now a single root commit", 1, int(repo.out("rev-list", "--count", "topic")))
    expect("s3: squashed commit has the same tree as old B", repo.out("rev-parse", b + "^{tree}"),
           repo.out("rev-parse", s + "^{tree}"))
    expect("s3: squashed commit message is the one we entered", SQUASH_MESSAGE.strip(),
           repo.out("log", "-1", "--format=%B", "topic"))
    expect("s3: main history untouched (C, B, A)", [c, b, a], repo.lines("rev-list", "main"))
    expect("s3: main..topic is exactly the squashed commit", [s], repo.lines("rev-list", "main..topic"))
    expect("s3: topic and main have diverged (neither is an ancestor of the other)",
           (1, 1),
           (repo.git("merge-base", "--is-ancestor", s, "main", ok=None).returncode,
            repo.git("merge-base", "--is-ancestor", "main", s, ok=None).returncode))
    expect("s3: old topic tip B is still recoverable via topic@{1}", b, repo.out("rev-parse", "topic@{1}"))
    expect("s3: HEAD is still on topic", "refs/heads/topic", repo.out("symbolic-ref", "HEAD"))
    expect("s3: notes.txt content", "alpha\nbeta\n", (repo.path / "notes.txt").read_text())
    expect("s3: todo.txt (from C) is not on topic", False, (repo.path / "todo.txt").exists())
    expect("s3: working tree clean", "", repo.out("status", "--porcelain"))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T052",
        "guide": "docs/additional-material/git_workflow_scenarios/squashing-commits.md",
        "author": NAME + " <" + EMAIL + ">",
        "commits": {"A": "create notes.txt 'alpha\\n'", "B": "append 'beta\\n' to notes.txt",
                    "C": "add todo.txt 'one\\n'"},
        "branches": {"main": "A-B-C", "topic": "at B (checked out)"},
        "remote": "none: squashing is a local rewrite",
        "scenarios": ["git log + git rebase -i HEAD~2", "git rebase -i main", "git rebase -i --root"],
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
        with tempfile.TemporaryDirectory(prefix="r03-t052-") as tmp:
            for name, fn in (("s1", scenario_guide_as_written),
                             ("s2", scenario_rebase_onto_main),
                             ("s3", scenario_squash_root)):
                path = Path(tmp) / name
                path.mkdir()
                fn(path)
    finally:
        write_evidence()
    print("OK: %d checks passed" % len(RESULTS))


if __name__ == "__main__":
    main()
