#!/usr/bin/env python3
"""R03-T058: resolving-merge-conflicts guide - making the prerequisites visible.

Run from the repository root:  python3 work/R03-T058/check.py

Builds a throw-away repository (no remote is needed: a merge is local).  The setup is the
guide section's example, run line by line through the shell:

    main  = A --- B --- C --- E        (E changes line 2 of notes.txt)
    topic = A --- B --- D              (D changes line 2 of notes.txt differently)

`git merge topic` on main then stops with a conflict, and the guide's own commands finish it:
git status, (edit the file), git add, git commit -m "Resolved merge conflicts".

Each prerequisite is asserted:  clean start and current branch, merge in progress (MERGE_HEAD,
unmerged index entries, `UU` status), conflict markers present and gone, resolved file staged,
and the configured name/email.  Two prerequisites are violated on purpose to show what
happens: committing before `git add`, and committing without a name/email.

Configuration is per-test and local: HOME and XDG_CONFIG_HOME point into the temporary
directory and the identity is set with `git config` in the temporary repository, so the
user's own git configuration is neither read nor changed (asserted).  Every assertion goes
through expect(), which records expected-vs-actual and raises AssertionError (non-zero
exit) on mismatch.  Evidence files are written next to this script even when a check fails.

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
MSG = {"A": "A: create notes.txt", "B": "B: append beta", "C": "C: add todo.txt",
       "D": "D: change line 2 on topic", "E": "E: change line 2 on main"}
MERGE_MESSAGE = "Resolved merge conflicts"

# The setup example from the guide section, one command per line.  "Your Name" and
# "you@example.com" are the placeholders shown in the guide; the check fills in its own.
SETUP = [
    "git init -b main",
    'git config user.name "Your Name"',
    'git config user.email "you@example.com"',
    "printf 'alpha\\n' > notes.txt",
    "git add notes.txt",
    'git commit -m "%s"' % MSG["A"],
    "printf 'beta\\n' >> notes.txt",
    'git commit -am "%s"' % MSG["B"],
    "printf 'one\\n' > todo.txt",
    "git add todo.txt",
    'git commit -m "%s"' % MSG["C"],
    "git branch topic HEAD~1",
    "git switch topic",
    "printf 'alpha\\nbeta from topic\\n' > notes.txt",
    'git commit -am "%s"' % MSG["D"],
    "git switch main",
    "printf 'alpha\\nbeta from main\\n' > notes.txt",
    'git commit -am "%s"' % MSG["E"],
]
MERGE = "git merge topic"
CONFLICTED = "alpha\n<<<<<<< HEAD\nbeta from main\n=======\nbeta from topic\n>>>>>>> topic\n"
RESOLVED = "alpha\nbeta from main and topic\n"

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

    def env(self):
        # No GIT_AUTHOR_* / GIT_COMMITTER_* here: the identity comes from the repository's
        # own config, which is one of the prerequisites being demonstrated.
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "HOME": str(self.home), "XDG_CONFIG_HOME": str(self.root / "xdg"),
            "GIT_CONFIG_NOSYSTEM": "1",
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

    def refs(self):
        rows = self.lines("for-each-ref", "--format=%(refname) %(objectname)")
        return dict(r.split(" ", 1) for r in rows)

    def merge_head(self):
        p = self.git("rev-parse", "-q", "--verify", "MERGE_HEAD", ok=None)
        return p.stdout.strip() if p.returncode == 0 else None

    def unmerged(self):
        """(stage, blob id, path) for every unmerged index entry."""
        rows = []
        for line in self.lines("ls-files", "-u"):
            meta, path = line.split("\t")
            _mode, blob, stage = meta.split(" ")
            rows.append((int(stage), blob, path))
        return rows

    def read(self, name):
        return (self.path / name).read_text()

    def write(self, name, text):
        (self.path / name).write_text(text)


def scenario(tmp):
    repo = Repo(tmp)
    for command in SETUP:
        repo.sh(command.replace("Your Name", NAME).replace("you@example.com", EMAIL))

    toplevel = Path(repo.out("rev-parse", "--show-toplevel")).resolve()
    expect("commands run only inside the temp repo", True,
           str(toplevel).startswith(str(Path(tmp).resolve())))

    ids = {"A": repo.out("rev-parse", "topic~2"), "B": repo.out("rev-parse", "topic~1"),
           "C": repo.out("rev-parse", "main~1"), "D": repo.out("rev-parse", "topic"),
           "E": repo.out("rev-parse", "main")}
    blob = {k: repo.out("rev-parse", ids[k] + ":notes.txt") for k in "BDE"}

    # --- prerequisites before the merge: repository state, branch, clean tree, config ----
    expect("start: current branch is main", "main", repo.out("symbolic-ref", "--short", "HEAD"))
    expect("start: main is E, C, B, A", [MSG["E"], MSG["C"], MSG["B"], MSG["A"]],
           repo.lines("log", "main", "--format=%s"))
    expect("start: topic is D, B, A", [MSG["D"], MSG["B"], MSG["A"]],
           repo.lines("log", "topic", "--format=%s"))
    expect("start: authors are Course Student", [NAME + " <" + EMAIL + ">"] * 4,
           repo.lines("log", "main", "--format=%an <%ae>"))
    expect("start: the working tree is clean", "", repo.git("status", "--porcelain").stdout)
    expect("start: git status says so in words", True,
           "nothing to commit, working tree clean" in repo.git("status").stdout)
    expect("start: name and email come from the repository's own config",
           [NAME, EMAIL], [repo.out("config", "--local", "--get", "user.name"),
                           repo.out("config", "--local", "--get", "user.email")])
    expect("start: no merge is in progress", None, repo.merge_head())
    before = repo.refs()

    # --- the merge stops on a conflict --------------------------------------------------
    p = repo.sh(MERGE, ok=None)
    expect("merge: git merge topic exits with status 1", 1, p.returncode)
    expect("merge: git reports a content conflict in notes.txt", True,
           "CONFLICT (content): Merge conflict in notes.txt" in p.stdout)
    status = repo.git("status").stdout
    expect("conflict: git status names the current branch", True, "On branch main" in status)
    expect("conflict: git status says there are unmerged paths", True,
           "You have unmerged paths" in status and "both modified:" in status and "notes.txt" in status)
    expect("conflict: git status --short shows UU for notes.txt only", ["UU notes.txt"],
           repo.lines("status", "--short"))
    expect("conflict: MERGE_HEAD is D, the tip of topic", ids["D"], repo.merge_head())
    expect("conflict: no commit was made, main is still E", ids["E"], repo.out("rev-parse", "main"))
    expect("conflict: the index holds three versions of notes.txt (base B, ours E, theirs D)",
           [(1, blob["B"], "notes.txt"), (2, blob["E"], "notes.txt"), (3, blob["D"], "notes.txt")],
           repo.unmerged())
    expect("conflict: notes.txt contains the conflict markers", CONFLICTED, repo.read("notes.txt"))
    expect("conflict: todo.txt was not touched", "one\n", repo.read("todo.txt"))
    p = repo.git("diff", "--check", ok=None)
    expect("conflict: git diff --check reports the leftover markers", True,
           p.returncode != 0 and "leftover conflict marker" in p.stdout)

    # --- violated prerequisite 1: commit before `git add` ------------------------------
    p = repo.sh('git commit -m "%s"' % MERGE_MESSAGE, ok=None)
    expect("commit before git add: fails", 128, p.returncode)
    expect("commit before git add: the complaint is about unmerged files", True,
           "unmerged" in p.stderr.lower())
    expect("commit before git add: nothing changed (still merging, still unmerged, main at E)",
           (ids["D"], 3, ids["E"]),
           (repo.merge_head(), len(repo.unmerged()), repo.out("rev-parse", "main")))

    # --- resolve: edit, then the guide's `git add` ---------------------------------------
    repo.write("notes.txt", RESOLVED)
    repo.sh("git add notes.txt")
    status = repo.git("status").stdout
    expect("resolved: no unmerged index entries are left", [], repo.unmerged())
    expect("resolved: git status --short shows the file as staged", ["M  notes.txt"],
           repo.lines("status", "--short"))
    expect("resolved: git status says all conflicts are fixed but the merge is not finished", True,
           "All conflicts fixed but you are still merging" in status)
    expect("resolved: no conflict markers are left, staged or unstaged", (0, 0),
           (repo.git("diff", "--check", ok=None).returncode,
            repo.git("diff", "--cached", "--check", ok=None).returncode))
    expect("resolved: still merging (MERGE_HEAD is D) and main is still E", (ids["D"], ids["E"]),
           (repo.merge_head(), repo.out("rev-parse", "main")))

    # --- violated prerequisite 2: no name/email configured ------------------------------
    repo.git("config", "user.useConfigOnly", "true")  # git may not guess a name/email
    repo.git("config", "--unset", "user.name")
    repo.git("config", "--unset", "user.email")
    p = repo.sh('git commit -m "%s"' % MERGE_MESSAGE, ok=None)
    expect("commit without name/email: fails", 128, p.returncode)
    expect("commit without name/email: the complaint is about the identity", True,
           any(s in p.stderr.lower() for s in ("who you are", "identity unknown", "no email was given")))
    expect("commit without name/email: the merge is still in progress, resolved file still staged",
           (ids["D"], ids["E"], ["M  notes.txt"]),
           (repo.merge_head(), repo.out("rev-parse", "main"), repo.lines("status", "--short")))
    repo.git("config", "user.name", NAME)
    repo.git("config", "user.email", EMAIL)

    # --- the guide's final command --------------------------------------------------------
    repo.sh('git commit -m "%s"' % MERGE_MESSAGE)
    merge = repo.out("rev-parse", "HEAD")
    expect("done: the merge commit has two parents, E then D", [merge, ids["E"], ids["D"]],
           repo.out("rev-list", "--parents", "-n", "1", "HEAD").split())
    expect("done: the commit message is the guide's", MERGE_MESSAGE, repo.out("log", "-1", "--format=%s"))
    expect("done: author is Course Student", NAME + " <" + EMAIL + ">",
           repo.out("log", "-1", "--format=%an <%ae>"))
    expect("done: MERGE_HEAD is gone, the working tree is clean", (None, ""),
           (repo.merge_head(), repo.git("status", "--porcelain").stdout))
    expect("done: notes.txt has the resolved content", RESOLVED, repo.read("notes.txt"))
    expect("done: the committed notes.txt is the resolved content", RESOLVED,
           repo.git("show", "HEAD:notes.txt").stdout)
    after = repo.refs()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    expect("done: only refs/heads/main changed; topic is still D", (["refs/heads/main"], ids["D"]),
           (changed, after["refs/heads/topic"]))
    expect("done: main is the merge commit", merge, after["refs/heads/main"])

    # --- the user's own git configuration was never involved ------------------------------
    expect("global config: user.name is not set", 1,
           repo.git("config", "--global", "--get", "user.name", ok=None).returncode)
    expect("global config: no .gitconfig was created in the temporary HOME", False,
           (repo.home / ".gitconfig").exists())


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T058",
        "guide": "docs/additional-material/git_workflow_scenarios/resolving-merge-conflicts.md",
        "guide_commands": ["git status", "git add", 'git commit -m "Resolved merge conflicts"'],
        "author": NAME + " <" + EMAIL + "> (set with git config in the temporary repository)",
        "commits": {"A": "create notes.txt 'alpha\\n'", "B": "append 'beta\\n' to notes.txt",
                    "C": "add todo.txt 'one\\n'", "D": "topic: line 2 of notes.txt changed",
                    "E": "main: line 2 of notes.txt changed differently"},
        "branches": {"main": "A-B-C-E (checked out)", "topic": "A-B-D (created at B)"},
        "remote": "none: a merge is local",
        "violated_on_purpose": ["commit before git add", "commit without name/email"],
        "setup_example": SETUP + [MERGE],
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
        with tempfile.TemporaryDirectory(prefix="r03-t058-") as tmp:
            scenario(Path(tmp))
    finally:
        write_evidence()
    print("OK: %d checks passed" % len(RESULTS))


if __name__ == "__main__":
    main()
