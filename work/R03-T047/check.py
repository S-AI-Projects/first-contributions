#!/usr/bin/env python3
"""R03-T047: Automated verification of prerequisite clarification for resetting a commit.

Verifies:
1. Isolated temporary Git repository creation with local configuration.
2. Verification of all documented prerequisites:
   - Repository state: verified inside working tree.
   - Active branch: verified on branch main.
   - Staging/working tree: verified clean before operation.
   - Valid target commit: verified commit B exists in log.
   - Local configuration: verified local user identity.
3. Execution of `git reset <commit_b>`:
   - Fact 1: HEAD and refs/heads/main move from commit C to commit B.
   - Fact 2: Commit history on main contains [B, A].
   - Fact 3: Changes from commit C (todo.txt) are unstaged and preserved on disk.
   - Fact 4: Working tree files match expected content.
   - Fact 5: Branch topic remains completely unaffected at commit B.
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
    """Sets up local repo with A, B, C, branch topic at B, with local config."""
    sb = Sandbox(root)
    sb.git("init", "-q", "-b", "main")

    # Set local repository configuration
    sb.git("config", "--local", "user.name", AUTHOR_NAME)
    sb.git("config", "--local", "user.email", AUTHOR_EMAIL)

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

    # --- Verify All Documented Prerequisites ---
    # Prerequisite 1: Repository state
    expect(f"{prefix}: Prereq 1 - inside work tree", "true", sb.out("rev-parse", "--is-inside-work-tree"))

    # Prerequisite 2: Active branch
    expect(f"{prefix}: Prereq 2 - current branch is main", "main", sb.out("branch", "--show-current"))

    # Prerequisite 3: Working tree is clean before reset
    expect(f"{prefix}: Prereq 3 - working tree clean", "", sb.out("status", "--porcelain"))

    # Prerequisite 4: Target commit exists in history
    rev_list_before = sb.lines("rev-list", "main")
    expect(f"{prefix}: Prereq 4 - commit B exists in rev-list", True, sha_b in rev_list_before)

    # Prerequisite 5: Local config identity is set
    expect(f"{prefix}: Prereq 5 - local user.name is Course Student", AUTHOR_NAME,
           sb.out("config", "--local", "user.name"))

    # --- Execute git reset to Commit B ---
    reset_proc = sb.git("reset", sha_b)
    expect(f"{prefix}: git reset commit_b exits 0", 0, reset_proc.returncode)

    # --- Assert Meaningful State Facts After Reset ---
    # Meaningful Fact 1: HEAD ref moved from commit C to commit B
    expect(f"{prefix}: Fact 1 - HEAD points to commit B", sha_b, sb.out("rev-parse", "HEAD"))
    expect(f"{prefix}: Fact 1b - refs/heads/main points to commit B", sha_b, sb.out("rev-parse", "refs/heads/main"))

    # Meaningful Fact 2: Commit history on main is now [B, A]
    rev_list_after = sb.lines("rev-list", "main")
    expect(f"{prefix}: Fact 2 - main history contains [B, A]", [sha_b, sha_a], rev_list_after)

    # Meaningful Fact 3: Changes from commit C (todo.txt) are unstaged/untracked in working tree
    status_after = sb.lines("status", "--porcelain")
    expect(f"{prefix}: Fact 3 - todo.txt is untracked", ["?? todo.txt"], status_after)

    # Meaningful Fact 4: Working tree file contents match expected state
    expect(f"{prefix}: Fact 4a - todo.txt content preserved", "one\n", (sb.work / "todo.txt").read_text())
    expect(f"{prefix}: Fact 4b - notes.txt content preserved", "alpha\nbeta\n", (sb.work / "notes.txt").read_text())

    # Meaningful Fact 5: Branch topic is completely unaffected and still points to commit B
    expect(f"{prefix}: Fact 5 - branch topic still points to commit B", sha_b, sb.out("rev-parse", "topic"))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T047",
        "guide": "docs/additional-material/git_workflow_scenarios/resetting-a-commit.md",
        "author": f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
        "prerequisites_checked": [
            "repository state (inside work tree)",
            "active branch (main)",
            "working tree cleanliness (clean)",
            "target commit existence (sha_b in rev-list)",
            "local repository configuration (user.name/email)"
        ],
        "operation": "git reset <commit_b>",
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
        with tempfile.TemporaryDirectory(prefix="r03-t047-run1-") as tmp1:
            verify_run(1, Path(tmp1))
        with tempfile.TemporaryDirectory(prefix="r03-t047-run2-") as tmp2:
            verify_run(2, Path(tmp2))
    finally:
        write_evidence()

    print(f"OK: All {len(RESULTS)} checks passed across both runs.")


if __name__ == "__main__":
    main()
