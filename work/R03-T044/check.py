#!/usr/bin/env python3
"""R03-T044: Automated verification of git config command comparison (global vs local).

Verifies:
1. Isolated temporary environment with custom HOME (~/.gitconfig).
2. Global configuration:
   - git config --global user.name "Course Student"
   - git config --global user.email "student@example.invalid"
3. Initial repository fixture with commits A, B, and C with branch `topic` at commit B.
4. Comparison of two workflows:
   - Workflow 1: Committing using global identity.
   - Workflow 2: Overriding identity locally with git config --local and committing.
5. Meaningful Git state assertions:
   - Fact 1: Commit created under Workflow 1 records global author and committer identity.
   - Fact 2: Local .git/config contains no user section when using global config.
   - Fact 3: Commit created under Workflow 2 records local author and committer identity.
   - Fact 4: Global ~/.gitconfig remains unchanged after local configuration.
   - Fact 5: A separate repository under the same environment uses the global identity,
             proving that local config is strictly scoped.
   - Fact 6: Branch topic at commit B remains fixed and untouched.
6. Verifies reproducibility across two independent temporary directory runs.
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

GLOBAL_NAME = "Course Student"
GLOBAL_EMAIL = "student@example.invalid"
LOCAL_NAME = "Project Contributor"
LOCAL_EMAIL = "contributor@project.invalid"

COMMANDS = []
RESULTS = []


def expect(label, expected, actual):
    ok = expected == actual
    RESULTS.append({"check": label, "expected": expected, "actual": actual, "ok": ok})
    if not ok:
        raise AssertionError("%s: expected %r, got %r" % (label, expected, actual))


class TestEnvironment:
    """Isolated environment with its own HOME directory (~/.gitconfig)."""

    def __init__(self, root: Path):
        self.root = root
        self.home = self.root / "home"
        self.repo1 = self.root / "repo1"
        self.repo2 = self.root / "repo2"
        self.home.mkdir(parents=True)
        self.repo1.mkdir(parents=True)
        self.repo2.mkdir(parents=True)

    def env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "HOME": str(self.home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        })
        return env

    def git(self, cwd, *args, ok=(0,)):
        p = subprocess.run(["git", *args], cwd=cwd, env=self.env(),
                           capture_output=True, text=True)
        COMMANDS.append({"cmd": f"git (cwd={cwd.name}) " + " ".join(args),
                         "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
        if ok is not None and p.returncode not in ok:
            raise RuntimeError("git %s failed (%d): %s" % (" ".join(args), p.returncode, p.stderr))
        return p

    def out(self, cwd, *args):
        return self.git(cwd, *args).stdout.strip()


def build_fixture(env: TestEnvironment):
    """Initializes global config and repo1 with A, B, C, branch topic at B."""
    # 1. Set global configuration
    env.git(env.repo1, "config", "--global", "user.name", GLOBAL_NAME)
    env.git(env.repo1, "config", "--global", "user.email", GLOBAL_EMAIL)

    # 2. Init repo1 with branch main
    env.git(env.repo1, "init", "-q", "-b", "main")

    # Commit A: create notes.txt with "alpha\n"
    notes = env.repo1 / "notes.txt"
    notes.write_text("alpha\n")
    env.git(env.repo1, "add", "notes.txt")
    env.git(env.repo1, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit A: create notes.txt")
    sha_a = env.out(env.repo1, "rev-parse", "HEAD")

    # Commit B: append "beta\n" to notes.txt
    with open(notes, "a") as f:
        f.write("beta\n")
    env.git(env.repo1, "add", "notes.txt")
    env.git(env.repo1, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit B: append beta to notes.txt")
    sha_b = env.out(env.repo1, "rev-parse", "HEAD")

    # Branch topic at Commit B
    env.git(env.repo1, "branch", "topic", sha_b)

    # Commit C: create todo.txt with "one\n"
    todo = env.repo1 / "todo.txt"
    todo.write_text("one\n")
    env.git(env.repo1, "add", "todo.txt")
    env.git(env.repo1, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Commit C: add todo.txt")
    sha_c = env.out(env.repo1, "rev-parse", "HEAD")

    return sha_a, sha_b, sha_c


def verify_run(pass_num: int, tmp_path: Path):
    prefix = f"run{pass_num}"
    env = TestEnvironment(tmp_path)
    sha_a, sha_b, sha_c = build_fixture(env)

    # --- Workflow 1: Committing with Global Configuration ---
    item1 = env.repo1 / "item1.txt"
    item1.write_text("item1\n")
    env.git(env.repo1, "add", "item1.txt")
    env.git(env.repo1, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Workflow 1: global config commit")
    sha_w1 = env.out(env.repo1, "rev-parse", "HEAD")

    # Meaningful Fact 1: Commit metadata matches global identity
    author_w1 = env.out(env.repo1, "log", "-1", "--format=%an <%ae>", sha_w1)
    committer_w1 = env.out(env.repo1, "log", "-1", "--format=%cn <%ce>", sha_w1)
    expect(f"{prefix}: Fact 1a - Workflow 1 author is global identity", f"{GLOBAL_NAME} <{GLOBAL_EMAIL}>", author_w1)
    expect(f"{prefix}: Fact 1b - Workflow 1 committer is global identity", f"{GLOBAL_NAME} <{GLOBAL_EMAIL}>", committer_w1)

    # Meaningful Fact 2: Local config has no user section yet
    local_config_w1 = env.git(env.repo1, "config", "--local", "--get", "user.name", ok=None)
    expect(f"{prefix}: Fact 2 - repo1 local config has no user.name", 1, local_config_w1.returncode)

    # --- Workflow 2: Overriding Identity with Local Configuration ---
    env.git(env.repo1, "config", "--local", "user.name", LOCAL_NAME)
    env.git(env.repo1, "config", "--local", "user.email", LOCAL_EMAIL)

    item2 = env.repo1 / "item2.txt"
    item2.write_text("item2\n")
    env.git(env.repo1, "add", "item2.txt")
    env.git(env.repo1, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Workflow 2: local config commit")
    sha_w2 = env.out(env.repo1, "rev-parse", "HEAD")

    # Meaningful Fact 3: Commit metadata matches local identity override
    author_w2 = env.out(env.repo1, "log", "-1", "--format=%an <%ae>", sha_w2)
    committer_w2 = env.out(env.repo1, "log", "-1", "--format=%cn <%ce>", sha_w2)
    expect(f"{prefix}: Fact 3a - Workflow 2 author is local identity", f"{LOCAL_NAME} <{LOCAL_EMAIL}>", author_w2)
    expect(f"{prefix}: Fact 3b - Workflow 2 committer is local identity", f"{LOCAL_NAME} <{LOCAL_EMAIL}>", committer_w2)

    # Meaningful Fact 4: Global config in ~/.gitconfig remained untouched
    global_name_val = env.out(env.repo1, "config", "--global", "user.name")
    global_email_val = env.out(env.repo1, "config", "--global", "user.email")
    expect(f"{prefix}: Fact 4a - global user.name is still Course Student", GLOBAL_NAME, global_name_val)
    expect(f"{prefix}: Fact 4b - global user.email is still student@example.invalid", GLOBAL_EMAIL, global_email_val)

    # --- Cross-Repository Isolation Verification ---
    # Init repo2 in the same environment and verify it uses global identity
    env.git(env.repo2, "init", "-q", "-b", "main")
    file_r2 = env.repo2 / "sample.txt"
    file_r2.write_text("sample\n")
    env.git(env.repo2, "add", "sample.txt")
    env.git(env.repo2, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Repo 2 commit")
    author_r2 = env.out(env.repo2, "log", "-1", "--format=%an <%ae>")

    # Meaningful Fact 5: repo2 uses global identity (local override in repo1 did not leak)
    expect(f"{prefix}: Fact 5 - repo2 uses global identity", f"{GLOBAL_NAME} <{GLOBAL_EMAIL}>", author_r2)

    # Meaningful Fact 6: Branch topic in repo1 is unchanged at commit B
    expect(f"{prefix}: Fact 6 - topic in repo1 points to commit B", sha_b, env.out(env.repo1, "rev-parse", "topic"))


def write_evidence():
    versions = [
        subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "Python " + platform.python_version(),
        "Platform " + platform.platform(),
    ]
    (HERE / "versions.txt").write_text("\n".join(versions) + "\n")

    inputs = {
        "task": "R03-T044",
        "guide": "docs/additional-material/git_workflow_scenarios/configuring-git.md",
        "author_global": f"{GLOBAL_NAME} <{GLOBAL_EMAIL}>",
        "author_local": f"{LOCAL_NAME} <{LOCAL_EMAIL}>",
        "comparison": "git config --global vs git config --local",
        "passes": ["run1 (independent environment 1)", "run2 (independent environment 2)"]
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
        with tempfile.TemporaryDirectory(prefix="r03-t044-run1-") as tmp1:
            verify_run(1, Path(tmp1))
        with tempfile.TemporaryDirectory(prefix="r03-t044-run2-") as tmp2:
            verify_run(2, Path(tmp2))
    finally:
        write_evidence()

    print(f"OK: All {len(RESULTS)} checks passed across both runs.")


if __name__ == "__main__":
    main()
