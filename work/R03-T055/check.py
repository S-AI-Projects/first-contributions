#!/usr/bin/env python3
"""R03-T055: configuring-git guide - `git commit` without a configured identity.

Run from the repository root:  python3 work/R03-T055/check.py

Builds throw-away repositories (no remote is needed: configuration is local) with three
commits on `main`:

    A  creates notes.txt  "alpha\\n"
    B  appends            "beta\\n"
    C  adds todo.txt      "one\\n"

and a branch `topic` at B, which is checked out.  A, B and C are made as
Course Student <student@example.invalid>, with the identity given through environment
variables.  After that the identity is taken away: no user.name / user.email in any
config file, none in the environment, and `user.useConfigOnly=true` so git may not
guess one from the operating-system account (some machines can guess, which is why the
guide's error does not appear for everybody).  A change to notes.txt is staged, and:

    1. `git commit -m ...` fails (violated precondition: git does not know who you are)
       - nonzero exit, no commit, no ref moved, the change is still staged
    2. correction A: `git config user.email/user.name` (this repository only), same commit
    3. correction B: `git -c user.name=... -c user.email=... commit` (this command only)
    4. correction C: `git config --global ...` (written to a temporary HOME), same commit

The checks look at exit codes and repository state, not at the exact wording of git's
message (only the keyword "who you are" / "identity unknown" is looked for).
HOME and XDG_CONFIG_HOME point into the temporary directory, so no real config file is
read or written.  Every assertion goes through expect(), which records expected-vs-actual
and raises AssertionError (non-zero exit) on mismatch.  Evidence files are written next to
this script even when a check fails.

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
IDENT = "%s <%s>" % (NAME, EMAIL)
D_MESSAGE = "D: add gamma"
COMMIT_CMD = 'git commit -m "%s"' % D_MESSAGE

COMMANDS = []  # every command -> commands.log
RESULTS = []   # expected-vs-actual rows -> expected_vs_actual.md


def expect(label, expected, actual):
    ok = expected == actual
    RESULTS.append({"check": label, "expected": expected, "actual": actual, "ok": ok})
    if not ok:
        raise AssertionError("%s: expected %r, got %r" % (label, expected, actual))


class Repo:
    """A temporary repository with its own HOME, so no real git config is read or written."""

    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / "repo"
        self.home = self.root / "home"
        self.path.mkdir(parents=True)
        self.home.mkdir()
        (self.root / "xdg").mkdir()

    def env(self, ident):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.root / "xdg"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C",
            "GIT_EDITOR": "false",  # an editor opening unexpectedly fails instead of hanging
        })
        if ident:  # identity through the environment, used only to build commits A, B, C
            env.update({"GIT_AUTHOR_NAME": NAME, "GIT_AUTHOR_EMAIL": EMAIL,
                        "GIT_COMMITTER_NAME": NAME, "GIT_COMMITTER_EMAIL": EMAIL})
        return env

    def _run(self, cmd, label, shell, ok, ident):
        p = subprocess.run(cmd, shell=shell, cwd=self.path, env=self.env(ident),
                           capture_output=True, text=True)
        COMMANDS.append({"cmd": label, "returncode": p.returncode,
                         "stdout": p.stdout, "stderr": p.stderr})
        if ok is not None and p.returncode not in ok:
            raise RuntimeError("%s failed (%d): %s" % (label, p.returncode, p.stderr))
        return p

    def git(self, *args, ok=(0,), ident=False):
        """Run git with an argument list. ok=None -> the caller inspects the exit code."""
        return self._run(["git", *args], "git " + " ".join(args), False, ok, ident)

    def sh(self, command, ok=(0,), ident=False):
        """Run a command string through the shell, exactly as typed in a terminal."""
        return self._run(command, command, True, ok, ident)

    def out(self, *args):
        return self.git(*args).stdout.strip()

    def lines(self, *args):
        return self.git(*args).stdout.splitlines()

    def refs(self):
        rows = self.lines("for-each-ref", "--format=%(refname) %(objectname)")
        return dict(r.split(" ", 1) for r in rows)

    def put(self, name, text, append=False):
        with open(self.path / name, "a" if append else "w") as f:
            f.write(text)

    def commit_file(self, name, text, message, append=False):
        self.put(name, text, append)
        self.git("add", name)
        self.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", message, ident=True)
        return self.out("rev-parse", "HEAD")


def make_broken(tmp):
    """A, B, C on main, topic at B (checked out), identity removed, a change staged."""
    repo = Repo(tmp)
    repo.git("init", "-q", "-b", "main")
    a = repo.commit_file("notes.txt", "alpha\n", "A: create notes.txt")
    b = repo.commit_file("notes.txt", "beta\n", "B: append beta", append=True)
    c = repo.commit_file("todo.txt", "one\n", "C: add todo.txt")
    repo.git("branch", "topic", b)
    repo.git("checkout", "-q", "topic")
    repo.git("config", "user.useConfigOnly", "true")  # git may not guess a name/email
    repo.put("notes.txt", "gamma\n", append=True)
    repo.git("add", "notes.txt")

    toplevel = Path(repo.out("rev-parse", "--show-toplevel")).resolve()
    expect("commands run only inside the temp repo", True,
           str(toplevel).startswith(str(Path(tmp).resolve())))
    return repo, a, b, c


def check_precondition_violated(repo, label):
    expect(label + ": user.name is not set anywhere", 1,
           repo.git("config", "--get", "user.name", ok=None).returncode)
    expect(label + ": user.email is not set anywhere", 1,
           repo.git("config", "--get", "user.email", ok=None).returncode)
    expect(label + ": git cannot determine an author identity", True,
           repo.git("var", "GIT_AUTHOR_IDENT", ok=None).returncode != 0)
    expect(label + ": the change is staged", ["M  notes.txt"], repo.lines("status", "--short"))


def check_commit_made(repo, label, b, c):
    d = repo.out("rev-parse", "HEAD")
    expect(label + ": the commit's parent is B", b, repo.out("rev-parse", d + "^"))
    expect(label + ": author is Course Student", IDENT, repo.out("log", "-1", "--format=%an <%ae>"))
    expect(label + ": message is " + D_MESSAGE, D_MESSAGE, repo.out("log", "-1", "--format=%s"))
    expect(label + ": the staged change is in the commit", "alpha\nbeta\ngamma\n",
           repo.git("show", d + ":notes.txt").stdout)
    refs = repo.refs()
    expect(label + ": topic moved to the new commit, main still at C",
           {"refs/heads/main": c, "refs/heads/topic": d}, refs)


def scenario_bad_then_repository_config(tmp):
    repo, a, b, c = make_broken(tmp)
    start = repo.refs()
    expect("start: main at C, topic at B", {"refs/heads/main": c, "refs/heads/topic": b}, start)
    expect("start: topic is checked out", "refs/heads/topic", repo.out("symbolic-ref", "HEAD"))
    expect("start: A, B, C were made by Course Student", [IDENT] * 3,
           repo.lines("log", "main", "--format=%an <%ae>"))
    check_precondition_violated(repo, "bad case")

    p = repo.sh(COMMIT_CMD, ok=None)
    expect("bad case: git commit exits with git's fatal-error status", 128, p.returncode)
    expect("bad case: the complaint is about the identity", True,
           "who you are" in p.stderr.lower() or "identity unknown" in p.stderr.lower())
    expect("bad case: no commit was made and no ref moved", start, repo.refs())
    expect("bad case: the change is still staged", ["M  notes.txt"], repo.lines("status", "--short"))

    # Correction A: the smallest persistent fix - this repository only (guide: omit --global).
    repo.sh('git config user.email "%s"' % EMAIL)
    repo.sh('git config user.name "%s"' % NAME)
    expect("repair A: git can now determine the author identity", True,
           repo.out("var", "GIT_AUTHOR_IDENT").startswith(IDENT))
    repo.sh(COMMIT_CMD)  # exactly the command that failed before
    check_commit_made(repo, "repair A", b, c)
    expect("repair A: the setting is stored in this repository", NAME,
           repo.out("config", "--local", "--get", "user.name"))
    expect("repair A: nothing was written to the global config", 1,
           repo.git("config", "--global", "--get", "user.name", ok=None).returncode)


def scenario_command_line_config(tmp):
    repo, a, b, c = make_broken(tmp)
    check_precondition_violated(repo, "-c case")
    repo.sh("git -c user.name='%s' -c user.email='%s' commit -m \"%s\"" % (NAME, EMAIL, D_MESSAGE))
    check_commit_made(repo, "repair B (-c)", b, c)
    expect("repair B (-c): nothing was saved to any config file", 1,
           repo.git("config", "--get", "user.name", ok=None).returncode)
    repo.put("notes.txt", "delta\n", append=True)
    repo.git("add", "notes.txt")
    p = repo.sh('git commit -m "E: add delta"', ok=None)
    expect("repair B (-c): the next plain git commit fails again", 128, p.returncode)


def scenario_global_config(tmp):
    repo, a, b, c = make_broken(tmp)
    check_precondition_violated(repo, "--global case")
    repo.sh('git config --global user.email "%s"' % EMAIL)
    repo.sh('git config --global user.name "%s"' % NAME)
    repo.sh(COMMIT_CMD)
    check_commit_made(repo, "repair C (--global)", b, c)
    origin = repo.out("config", "--global", "--show-origin", "--get", "user.name").split("\t")[0]
    expect("repair C (--global): written to the temporary HOME's .gitconfig, not a real one",
           (repo.home / ".gitconfig").resolve(), Path(origin[len("file:"):]).resolve())
    expect("repair C (--global): the repository's own config has no user.name", 1,
           repo.git("config", "--local", "--get", "user.name", ok=None).returncode)


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T055",
        "guide": "docs/additional-material/git_workflow_scenarios/configuring-git.md",
        "author_of_A_B_C": IDENT,
        "commits": {"A": "create notes.txt 'alpha\\n'", "B": "append 'beta\\n' to notes.txt",
                    "C": "add todo.txt 'one\\n'"},
        "branches": {"main": "A-B-C", "topic": "at B, checked out"},
        "remote": "none: configuration is local",
        "violated_precondition": "no user.name/user.email anywhere and user.useConfigOnly=true",
        "bad_command": COMMIT_CMD,
        "corrections": ["git config user.email/user.name (repository)",
                        "git -c user.name=... -c user.email=... commit (one command)",
                        "git config --global user.email/user.name (temporary HOME)"],
    }
    (HERE / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")

    rows = ["| check | expected | actual | ok |", "|---|---|---|---|"]
    for r in RESULTS:
        rows.append("| %s | `%s` | `%s` | %s |" % (
            r["check"], json.dumps(r["expected"], default=str), json.dumps(r["actual"], default=str),
            "yes" if r["ok"] else "NO"))
    (HERE / "expected_vs_actual.md").write_text("\n".join(rows) + "\n")

    log = []
    for c in COMMANDS:
        log.append("$ %s\n[exit %d]\n%s%s" % (c["cmd"], c["returncode"], c["stdout"], c["stderr"]))
    (HERE / "commands.log").write_text("\n".join(log))


def main():
    try:
        with tempfile.TemporaryDirectory(prefix="r03-t055-") as tmp:
            for name, fn in (("s1", scenario_bad_then_repository_config),
                             ("s2", scenario_command_line_config),
                             ("s3", scenario_global_config)):
                path = Path(tmp) / name
                path.mkdir()
                fn(path)
    finally:
        write_evidence()
    print("OK: %d checks passed" % len(RESULTS))


if __name__ == "__main__":
    main()
