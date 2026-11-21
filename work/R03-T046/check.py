#!/usr/bin/env python3
"""R03-T046: Automated verification of failure diagnosis when resetting a commit.

Verifies:
1. Isolated temporary Git repository creation.
2. Reproduction of commits A, B, and C with branch `topic` at commit B:
   - A creates notes.txt with "alpha\\n"
   - B appends "beta\\n" to notes.txt
   - C adds todo.txt with "one\\n"
   - branch topic created at commit B
3. Violated precondition: passing a non-existent / invalid revision to `git reset`.
4. Meaningful Git state assertions:
   - Fact 1: Bad case fails with nonzero exit status (code 128) and ambiguous argument error.
   - Fact 2: Failed command leaves repository state completely untouched (HEAD remains at C).
   - Fact 3: Corrected command using authentic commit hash succeeds (exit code 0).
   - Fact 4: HEAD is updated to commit B.
   - Fact 5: Unstaged changes in working tree match changes since commit B.
   - Fact 6: Branch topic remains fixed and untouched at commit B.
5. Verifies reproducibility across two independent temporary directory runs.
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

    # Verify initial state
    expect(f"{prefix}: start HEAD is commit C", sha_c, sb.out("rev-parse", "HEAD"))
    expect(f"{prefix}: start branch topic is commit B", sha_b, sb.out("rev-parse", "topic"))
    expect(f"{prefix}: start working tree is clean", "", sb.out("status", "--porcelain"))

    # --- Step 1: The Violated Precondition (Bad Case) ---
    # Attempting to reset to a non-existent commit hash
    bad_hash = "badc0de" if pass_num == 1 else "deadbeef"
    bad_res = sb.git("reset", bad_hash, ok=None)

    # Meaningful Fact 1: Bad case fails with nonzero exit status
    expect(f"{prefix}: Fact 1a - bad reset exits non-zero", True, bad_res.returncode != 0)
    has_ambiguous = "ambiguous argument" in bad_res.stderr or "unknown revision" in bad_res.stderr
    expect(f"{prefix}: Fact 1b - error identifies ambiguous revision", True, has_ambiguous)

    # Meaningful Fact 2: Repository state left completely untouched
    expect(f"{prefix}: Fact 2a - HEAD still at commit C after failure", sha_c, sb.out("rev-parse", "HEAD"))
    expect(f"{prefix}: Fact 2b - working tree remains clean", "", sb.out("status", "--porcelain"))
    expect(f"{prefix}: Fact 2c - topic still at commit B", sha_b, sb.out("rev-parse", "topic"))

    # --- Step 2: The Smallest Correction (Repaired Case) ---
    # Query log to obtain valid commit hash for Commit B
    valid_hash = sha_b[:7]
    repaired_res = sb.git("reset", valid_hash)

    # Meaningful Fact 3: Repaired command succeeds (exit code 0)
    expect(f"{prefix}: Fact 3 - repaired reset exits 0", 0, repaired_res.returncode)

    # Meaningful Fact 4: HEAD moved to commit B
    expect(f"{prefix}: Fact 4 - HEAD updated to commit B", sha_b, sb.out("rev-parse", "HEAD"))

    # Meaningful Fact 5: Changes since commit B are unstaged in working tree
    status_after = sb.lines("status", "--porcelain")
    expect(f"{prefix}: Fact 5 - todo.txt is untracked", ["?? todo.txt"], status_after)
    expect(f"{prefix}: Fact 5b - todo.txt content preserved on disk", "one\n", (sb.work / "todo.txt").read_text())

    # Meaningful Fact 6: Branch topic remained completely unchanged
    expect(f"{prefix}: Fact 6 - topic still points to commit B", sha_b, sb.out("rev-parse", "topic"))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T046",
        "guide": "docs/additional-material/git_workflow_scenarios/resetting-a-commit.md",
        "author": f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>",
        "bad_commands": ["git reset badc0de", "git reset deadbeef"],
        "corrected_command": "git reset <valid_commithash>",
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
        with tempfile.TemporaryDirectory(prefix="r03-t046-run1-") as tmp1:
            verify_run(1, Path(tmp1))
        with tempfile.TemporaryDirectory(prefix="r03-t046-run2-") as tmp2:
            verify_run(2, Path(tmp2))
    finally:
        write_evidence()

    print(f"OK: All {len(RESULTS)} checks passed across both runs.")


if __name__ == "__main__":
    main()
