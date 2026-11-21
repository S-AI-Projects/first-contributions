#!/usr/bin/env python3
"""R03-T045: Automated verification of path quoting and `--` handling in rebase workflows.

Verifies:
1. Isolated temporary Git repository creation.
2. Reproduction of commits A, B, and C with branch `topic` at commit B:
   - A creates notes.txt with "alpha\\n"
   - B appends "beta\\n" to notes.txt
   - C adds todo.txt with "one\\n"
   - branch topic created at commit B
3. Exercising workflow with "release notes.txt" and directory "sample data":
   - Fact 1: Unquoted path `git add release notes.txt` fails with error.
   - Fact 2: Quoted paths `git add "release notes.txt" "sample data/data.txt"` succeed.
   - Fact 3: Rebase of `topic` onto `main` succeeds and creates linear history [topic_tip, C, B, A].
   - Fact 4: Working tree contains files from both main and topic.
   - Fact 5: `git checkout -- "release notes.txt"` resolves path ambiguity and restores file content.
   - Fact 6: Branch main remains completely fixed at commit C.
   - Fact 7: Working tree is clean.
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

    # Switch to topic
    sb.git("switch", "topic")
    expect(f"{prefix}: switched to branch topic", "refs/heads/topic", sb.out("symbolic-ref", "HEAD"))

    # Create files with spaces in name and directory
    rel_notes = sb.work / "release notes.txt"
    sample_dir = sb.work / "sample data"
    sample_dir.mkdir(parents=True)
    sample_file = sample_dir / "data.txt"

    rel_notes.write_text("notes for release\n")
    sample_file.write_text("sample data payload\n")

    # Fact 1: Unquoted path fails because shell/git treats "release" and "notes.txt" as 2 files
    unquoted_res = sb.git("add", "release", "notes.txt", ok=None)
    expect(f"{prefix}: Fact 1 - unquoted add fails", True, unquoted_res.returncode != 0)
    expect(f"{prefix}: Fact 1b - error mentions pathspec 'release'", True, "release" in unquoted_res.stderr)

    # Fact 2: Quoted paths successfully stage both files
    sb.git("add", "release notes.txt", "sample data/data.txt")
    staged_files = sb.lines("diff", "--cached", "--name-only")
    expect(f"{prefix}: Fact 2 - staged files include 'release notes.txt'", True, "release notes.txt" in staged_files)
    expect(f"{prefix}: Fact 2b - staged files include 'sample data/data.txt'", True, "sample data/data.txt" in staged_files)

    # Commit on topic
    sb.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Add release notes and sample data")
    sha_topic_pre = sb.out("rev-parse", "HEAD")

    # Fact 3: Rebase topic onto main succeeds
    sb.git("rebase", "main")
    sha_topic_post = sb.out("rev-parse", "HEAD")
    history_after = sb.lines("rev-list", "HEAD")
    expect(f"{prefix}: Fact 3a - rebase creates new commit", False, sha_topic_post == sha_topic_pre)
    expect(f"{prefix}: Fact 3b - history length on topic is 4", 4, len(history_after))
    expect(f"{prefix}: Fact 3c - commit C is direct parent of topic tip", sha_c, sb.out("rev-parse", "HEAD~1"))

    # Fact 4: Working tree contains files from main and topic
    expect(f"{prefix}: Fact 4a - todo.txt from main exists", True, (sb.work / "todo.txt").is_file())
    expect(f"{prefix}: Fact 4b - release notes.txt exists", True, rel_notes.is_file())
    expect(f"{prefix}: Fact 4c - sample data/data.txt exists", True, sample_file.is_file())

    # Fact 5: Ambiguity resolution with `--`
    # Mutate release notes.txt and restore via `git checkout -- "release notes.txt"`
    with open(rel_notes, "a") as f:
        f.write("accidental line\n")
    expect(f"{prefix}: file modified", "notes for release\naccidental line\n", rel_notes.read_text())

    sb.git("checkout", "--", "release notes.txt")
    expect(f"{prefix}: Fact 5 - checkout -- restores clean file content", "notes for release\n", rel_notes.read_text())

    # Fact 6: Branch main remained unchanged at commit C
    expect(f"{prefix}: Fact 6 - branch main still points to commit C", sha_c, sb.out("rev-parse", "refs/heads/main"))

    # Fact 7: Working tree is clean
    expect(f"{prefix}: Fact 7 - working tree is clean", "", sb.out("status", "--porcelain"))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T045",
        "guide": "docs/additional-material/git_workflow_scenarios/rebase-vs-merge.md",
        "author": f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
        "paths_with_spaces": ["release notes.txt", "sample data/data.txt"],
        "commands": ["git switch topic", "git rebase main", "git checkout -- <path>"],
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
        with tempfile.TemporaryDirectory(prefix="r03-t045-run1-") as tmp1:
            verify_run(1, Path(tmp1))
        with tempfile.TemporaryDirectory(prefix="r03-t045-run2-") as tmp2:
            verify_run(2, Path(tmp2))
    finally:
        write_evidence()

    print(f"OK: All {len(RESULTS)} checks passed across both runs.")


if __name__ == "__main__":
    main()
