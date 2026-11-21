#!/usr/bin/env python3
"""R03-T049: Automated verification of prediction-and-verification exercise for reverting a commit.

Verifies:
1. Isolated temporary Git repository creation.
2. Reproduction of commits A, B, and C with branch `topic` at commit B:
   - A creates notes.txt with "alpha\\n"
   - B appends "beta\\n" to notes.txt
   - C adds todo.txt with "one\\n"
   - branch topic created at commit B
3. Execution of `git revert --no-edit <commit_c>`:
   - Fact 1: Reverting creates a new forward commit D on main (history is [D, C, B, A]).
   - Fact 2: Commit C remains preserved as the direct parent of commit D.
   - Fact 3: Tree of commit D contains notes.txt but omits todo.txt.
   - Fact 4: File todo.txt is deleted from the working directory on disk.
   - Fact 5: File notes.txt is preserved on disk with content "alpha\\nbeta\\n".
   - Fact 6: Working tree is completely clean after revert.
   - Fact 7: Branch topic remains completely unaffected at commit B.
4. Verifies reproducibility across two independent temporary directory runs.
"""

import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

AUTHOR_NAME = "Course Student"
AUTHOR_EMAIL = "student@example.invalid"

COMMANDS = []
RESULTS = []


def expect(label, expected, actual):
    ok = expected == actual
    RESULTS.append({"check": label, "expected": expected, "actual": actual, "ok": ok})
    if not ok:
        raise AssertionError("%s: expected %r, got %r" % (label, expected, actual))


class Sandbox:
    """Working repo isolated from user/system git configuration."""

    def __init__(self, root: Path):
        self.root = root
        self.work = self.root / "repo"
        self.home = self.root / "home"
        self.work.mkdir(parents=True)
        self.home.mkdir(parents=True)

    def env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "HOME": str(self.home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": AUTHOR_NAME,
            "GIT_AUTHOR_EMAIL": AUTHOR_EMAIL,
            "GIT_COMMITTER_NAME": AUTHOR_NAME,
            "GIT_COMMITTER_EMAIL": AUTHOR_EMAIL,
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        })
        return env

    def git(self, *args, ok=(0,)):
        p = subprocess.run(["git", *args], cwd=self.work, env=self.env(),
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


def build_scenario(root: Path):
    """Sets up local repo with A, B, C, branch topic at B."""
    sb = Sandbox(root)
    sb.git("init", "-q", "-b", "main")

    # Commit A: create notes.txt with "alpha\n"
    notes = sb.work / "notes.txt"
    notes.write_text("alpha\n")
    sb.git("add", "notes.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit A: create notes.txt")
    sha_a = sb.out("rev-parse", "HEAD")

    # Commit B: append "beta\n" to notes.txt
    with open(notes, "a") as f:
        f.write("beta\n")
    sb.git("add", "notes.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit B: append beta to notes.txt")
    sha_b = sb.out("rev-parse", "HEAD")

    # Branch topic at Commit B
    sb.git("branch", "topic", sha_b)

    # Commit C: create todo.txt with "one\n"
    todo = sb.work / "todo.txt"
    todo.write_text("one\n")
    sb.git("add", "todo.txt")
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit C: add todo.txt")
    sha_c = sb.out("rev-parse", "HEAD")

    return sb, sha_a, sha_b, sha_c


def verify_run(pass_num: int, tmp_path: Path):
    prefix = f"run{pass_num}"
    sb, sha_a, sha_b, sha_c = build_scenario(tmp_path)

    # Initial state verification
    expect(f"{prefix}: start HEAD is commit C", sha_c, sb.out("rev-parse", "HEAD"))
    expect(f"{prefix}: start branch topic is commit B", sha_b, sb.out("rev-parse", "topic"))
    expect(f"{prefix}: start todo.txt exists on disk", True, (sb.work / "todo.txt").is_file())

    # Execute git revert on commit C
    revert_proc = sb.git("revert", "--no-edit", sha_c)
    expect(f"{prefix}: git revert exits 0", 0, revert_proc.returncode)

    sha_d = sb.out("rev-parse", "HEAD")

    # Meaningful Fact 1: Reverting creates a new forward commit D
    expect(f"{prefix}: Fact 1a - commit D is distinct from C", False, sha_d == sha_c)
    history = sb.lines("rev-list", "main")
    expect(f"{prefix}: Fact 1b - main history is [D, C, B, A]", [sha_d, sha_c, sha_b, sha_a], history)

    # Meaningful Fact 2: Commit C is preserved as direct parent of commit D
    expect(f"{prefix}: Fact 2 - parent of D is commit C", sha_c, sb.out("rev-parse", "HEAD~1"))

    # Meaningful Fact 3: Tree of commit D contains only notes.txt (todo.txt object is removed)
    tree_files = sb.lines("ls-tree", "--name-only", "HEAD")
    expect(f"{prefix}: Fact 3 - commit D tree contains only notes.txt", ["notes.txt"], tree_files)

    # Meaningful Fact 4: todo.txt was deleted from the disk
    expect(f"{prefix}: Fact 4 - todo.txt deleted from disk", False, (sb.work / "todo.txt").exists())

    # Meaningful Fact 5: notes.txt content preserved
    expect(f"{prefix}: Fact 5 - notes.txt content matches", "alpha\nbeta\n", (sb.work / "notes.txt").read_text())

    # Meaningful Fact 6: Working tree is clean
    expect(f"{prefix}: Fact 6 - working tree status is clean", "", sb.out("status", "--porcelain"))

    # Meaningful Fact 7: Branch topic remained completely untouched at commit B
    expect(f"{prefix}: Fact 7 - branch topic still points to commit B", sha_b, sb.out("rev-parse", "topic"))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T049",
        "guide": "docs/additional-material/git_workflow_scenarios/reverting-a-commit.md",
        "author": f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
        "operation": "git revert --no-edit <commit_c>",
        "predicted_states": [
            "commit graph: new forward commit D added, C preserved",
            "tree: todo.txt deleted from tree, notes.txt preserved",
            "working tree: todo.txt removed from disk, working tree clean",
            "other branches: topic untouched at commit B"
        ],
        "passes": ["run1 (independent repo 1)", "run2 (independent repo 2)"]
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
        with tempfile.TemporaryDirectory(prefix="r03-t049-run1-") as tmp1:
            verify_run(1, Path(tmp1))
        with tempfile.TemporaryDirectory(prefix="r03-t049-run2-") as tmp2:
            verify_run(2, Path(tmp2))
    finally:
        write_evidence()

    print(f"OK: All {len(RESULTS)} checks passed across both runs.")


if __name__ == "__main__":
    main()
