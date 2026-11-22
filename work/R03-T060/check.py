#!/usr/bin/env python3
"""R03-T060: installing-git-ubuntu guide - a complete, reproducible start-to-finish example.

Run from the repository root:  python3 work/R03-T060/check.py

The example from the guide section is run line by line through the shell, twice, in two
separate temporary directories (no remote is needed: configuration and commits are local):

    git --version
    git config --global user.name "Your Name"          <- the guide's command
    git config --global user.email "youremail@domain.com"
    git init -b main, three commits A, B, C on main, branch topic at B, topic checked out

Nothing outside the example is assumed: the folder starts empty and the (temporary) home
directory has no .gitconfig.  "Your Name" and "youremail@domain.com" are the placeholders
used by the guide; the check fills in Course Student <student@example.invalid>.  Every
command whose output the guide section shows (SHOW below) is run and its output is compared
with the text of the guide section.  Commit dates are fixed, so both runs must give the same
commit ids, refs, index, files, config file and outputs.

HOME and XDG_CONFIG_HOME point into the temporary directory, so `git config --global`
writes to a throw-away file; the user's own ~/.gitconfig is neither read nor changed (its
hash is compared before and after).  Every assertion goes through expect(), which records
expected-vs-actual and raises AssertionError (non-zero exit) on mismatch.  Evidence files
are written next to this script even when a check fails.

Needs: git >= 2.28 (init -b), Python 3.8+, a POSIX shell.
"""
import hashlib
import json
import os
import platform
import re
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "Course Student"
EMAIL = "student@example.invalid"
PLACEHOLDER_NAME, PLACEHOLDER_EMAIL = "Your Name", "youremail@domain.com"
MSG_A, MSG_B, MSG_C = "A: create notes.txt", "B: append beta", "C: add todo.txt"

# The commands of the guide section, one per line.
EXAMPLE = [
    "git --version",
    'git config --global user.name "Your Name"',
    'git config --global user.email "youremail@domain.com"',
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

AUTHOR = "Your Name <youremail@domain.com>"
# (command, output exactly as shown in the guide section)
SHOW = [
    ("git config --global user.name", "Your Name\n"),
    ("git config --global --list", "user.name=Your Name\nuser.email=youremail@domain.com\n"),
    ("cat ~/.gitconfig", "[user]\n\tname = Your Name\n\temail = youremail@domain.com\n"),
    ("git status", "On branch topic\nnothing to commit, working tree clean\n"),
    ("git branch", "  main\n* topic\n"),
    ("git log --format='%an <%ae>: %s'",
     "%s: %s\n%s: %s\n" % (AUTHOR, MSG_B, AUTHOR, MSG_A)),
    ("git log --format='%an <%ae>: %s' main",
     "%s: %s\n%s: %s\n%s: %s\n" % (AUTHOR, MSG_C, AUTHOR, MSG_B, AUTHOR, MSG_A)),
]

COMMANDS = []  # every command -> commands.log
RESULTS = []   # expected-vs-actual rows -> expected_vs_actual.md


def expect(label, expected, actual):
    ok = expected == actual
    RESULTS.append({"check": label, "expected": expected, "actual": actual, "ok": ok})
    if not ok:
        raise AssertionError("%s: expected %r, got %r" % (label, expected, actual))


def fill(text):
    """Replace the guide's placeholders by the identity used in the check."""
    return text.replace(PLACEHOLDER_NAME, NAME).replace(PLACEHOLDER_EMAIL, EMAIL)


def file_hash(path):
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


class Repo:
    """An empty folder plus a temporary HOME with no git configuration at all."""

    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / "repo"
        self.home = self.root / "home"
        self.path.mkdir(parents=True)
        self.home.mkdir()
        (self.root / "xdg").mkdir()

    def env(self, extra=None):
        # No GIT_AUTHOR_* / GIT_COMMITTER_* variables: the author must come from the
        # global config that the guide's `git config --global` commands write.
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.root / "xdg"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C",
            "GIT_EDITOR": "false",  # an editor opening unexpectedly fails instead of hanging
        })
        if extra:
            env.update(extra)
        return env

    def sh(self, command, ok=(0,), extra=None, cwd=None):
        """Run a command string through the shell, exactly as typed in a terminal."""
        p = subprocess.run(command, shell=True, cwd=cwd or self.path, env=self.env(extra),
                           capture_output=True, text=True)
        COMMANDS.append({"cmd": command, "returncode": p.returncode,
                         "stdout": p.stdout, "stderr": p.stderr})
        if ok is not None and p.returncode not in ok:
            raise RuntimeError("%s failed (%d): %s" % (command, p.returncode, p.stderr))
        return p

    def lines(self, command, **kw):
        return self.sh(command, **kw).stdout.splitlines()


def run_example(root, tag):
    """Run the whole guide example in `root`; returns everything that must be reproducible."""
    repo = Repo(root)
    toplevel_probe = repo.sh("git rev-parse --show-toplevel", ok=None)  # no repository yet
    expect(tag + ": the folder starts empty and is not inside a repository",
           ([], True), (os.listdir(repo.path), toplevel_probe.returncode != 0))
    expect(tag + ": the temporary home has no .gitconfig yet", False, (repo.home / ".gitconfig").exists())
    expect(tag + ": no user.name is configured before the guide's command", 1,
           repo.sh("git config user.name", ok=None).returncode)

    commit_no = 0
    for command in EXAMPLE:
        extra = None
        if command.startswith("git commit"):
            commit_no += 1
            date = "2026-01-%02dT12:00:00+0000" % commit_no
            extra = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        p = repo.sh(fill(command), extra=extra)
        if command == "git --version":
            expect(tag + ": git --version prints 'git version <number>'", True,
                   re.match(r"^git version \d+\.\d+", p.stdout) is not None)

    toplevel = Path(repo.sh("git rev-parse --show-toplevel").stdout.strip()).resolve()
    expect(tag + ": commands ran only inside the temp directory", True,
           str(toplevel).startswith(str(Path(root).resolve())))

    # The output the guide section shows, command by command.
    outputs = {}
    for command, shown in SHOW:
        out = repo.sh(command).stdout
        outputs[command] = out
        expect("%s: `%s` prints what the guide shows" % (tag, command), fill(shown), out)

    # What the global config did, and where the author comes from.
    outside = repo.lines("git config --list", cwd=repo.home)
    inside = repo.lines("git config --list")
    expect(tag + ": `git config --list` outside a repository is exactly the guide's two lines",
           ["user.name=" + NAME, "user.email=" + EMAIL], outside)
    expect(tag + ": inside a repository it lists the same two lines plus the repository's own settings",
           (True, True, True),
           ("user.name=" + NAME in inside and "user.email=" + EMAIL in inside,
            "core.bare=false" in inside, len(inside) > 2))
    expect(tag + ": the repository itself has no user.name (the author comes from the global config)", 1,
           repo.sh("git config --local user.name", ok=None).returncode)

    ids = {k: repo.sh("git rev-parse " + rev).stdout.strip()
           for k, rev in (("A", "topic~1"), ("B", "topic"), ("C", "main"))}
    refs = dict(r.split(" ", 1) for r in repo.lines("git for-each-ref --format='%(refname) %(objectname)'"))
    expect(tag + ": main is at C, topic is at B, nothing else",
           {"refs/heads/main": ids["C"], "refs/heads/topic": ids["B"]}, refs)
    expect(tag + ": HEAD is on topic", "refs/heads/topic",
           repo.sh("git symbolic-ref HEAD").stdout.strip())
    expect(tag + ": the index holds notes.txt only", ["notes.txt"], repo.lines("git ls-files"))
    expect(tag + ": notes.txt is 'alpha' and 'beta'; todo.txt is not on topic",
           ({"notes.txt": "alpha\nbeta\n"}),
           {p.name: p.read_text() for p in sorted(repo.path.iterdir()) if p.is_file()})
    expect(tag + ": the working tree is clean", "", repo.sh("git status --porcelain").stdout)

    return {
        "ids": ids, "refs": refs,
        "index": repo.sh("git ls-files --stage").stdout,
        "files": {p.name: p.read_text() for p in sorted(repo.path.iterdir()) if p.is_file()},
        "gitconfig": (repo.home / ".gitconfig").read_text(),
        "outputs": outputs,
    }


def scenario():
    real_home = os.path.expanduser("~")
    real_before = (file_hash(Path(real_home) / ".gitconfig"),
                   file_hash(Path(real_home) / ".config" / "git" / "config"))

    with tempfile.TemporaryDirectory(prefix="r03-t060-a-") as tmp1:
        first = run_example(tmp1, "run 1")
    with tempfile.TemporaryDirectory(prefix="r03-t060-b-") as tmp2:
        second = run_example(tmp2, "run 2")

    expect("the two runs used different temporary directories", True, tmp1 != tmp2)
    expect("both temporary directories were removed", (False, False),
           (Path(tmp1).exists(), Path(tmp2).exists()))
    expect("run 2 gives the same commit ids, refs, index, files, config file and outputs as run 1",
           first, second)
    expect("the global config file written by the guide's commands is the documented one",
           "[user]\n\tname = %s\n\temail = %s\n" % (NAME, EMAIL), first["gitconfig"])
    real_after = (file_hash(Path(real_home) / ".gitconfig"),
                  file_hash(Path(real_home) / ".config" / "git" / "config"))
    expect("your own global git configuration was not touched", real_before, real_after)


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T060",
        "guide": "docs/additional-material/git_workflow_scenarios/installing-git-ubuntu.md",
        "guide_commands": ["git --version", 'git config --global user.name "Your Name"'],
        "author": NAME + " <" + EMAIL + ">",
        "commits": {"A": "create notes.txt 'alpha\\n'", "B": "append 'beta\\n' to notes.txt",
                    "C": "add todo.txt 'one\\n'"},
        "branches": {"main": "A-B-C", "topic": "at B, checked out"},
        "remote": "none: configuration and commits are local",
        "commit_dates": ["2026-01-01T12:00:00+0000", "2026-01-02T12:00:00+0000",
                         "2026-01-03T12:00:00+0000"],
        "runs": "twice, in two separate temporary directories",
        "example": EXAMPLE,
        "shown_in_guide": [c for c, _ in SHOW],
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
        scenario()
    finally:
        write_evidence()
    print("OK: %d checks passed" % len(RESULTS))


if __name__ == "__main__":
    main()
