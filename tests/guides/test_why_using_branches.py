#!/usr/bin/env python3
"""
Integration test suite for:
docs/additional-material/git_workflow_scenarios/why-using-branches.md

Verifies:
1. git branch my-new-branch
2. git checkout my-new-branch
3. git checkout -b my-new-branch
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

NAME = "Course Student"
EMAIL = "student@example.invalid"

def run_git(args, cwd, env=None):
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed with code {res.returncode}: {res.stderr.strip()}")
    return res.stdout.strip()

def run_test():
    with tempfile.TemporaryDirectory(prefix="why-branches-test-") as tmpdir:
        repo = Path(tmpdir)

        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": NAME,
            "GIT_AUTHOR_EMAIL": EMAIL,
            "GIT_COMMITTER_NAME": NAME,
            "GIT_COMMITTER_EMAIL": EMAIL,
            "LC_ALL": "C",
        })

        # Initialize base fixture
        run_git(["init", "-b", "main"], cwd=repo, env=env)
        run_git(["config", "user.name", NAME], cwd=repo, env=env)
        run_git(["config", "user.email", EMAIL], cwd=repo, env=env)

        # Commit A: creates notes.txt with "alpha\n"
        (repo / "notes.txt").write_text("alpha\n", encoding="utf-8")
        run_git(["add", "notes.txt"], cwd=repo, env=env)
        run_git(["commit", "-m", "A: add notes"], cwd=repo, env=env)
        commit_a = run_git(["rev-parse", "HEAD"], cwd=repo, env=env)

        # Commit B: appends "beta\n"
        with open(repo / "notes.txt", "a", encoding="utf-8") as f:
            f.write("beta\n")
        run_git(["add", "notes.txt"], cwd=repo, env=env)
        run_git(["commit", "-m", "B: append notes"], cwd=repo, env=env)
        commit_b = run_git(["rev-parse", "HEAD"], cwd=repo, env=env)

        # Branch topic at Commit B
        run_git(["branch", "topic", commit_b], cwd=repo, env=env)

        # Commit C: adds todo.txt with "one\n"
        (repo / "todo.txt").write_text("one\n", encoding="utf-8")
        run_git(["add", "todo.txt"], cwd=repo, env=env)
        run_git(["commit", "-m", "C: add todo"], cwd=repo, env=env)
        commit_c = run_git(["rev-parse", "HEAD"], cwd=repo, env=env)

        # Step 1: git branch my-new-branch
        run_git(["branch", "my-new-branch"], cwd=repo, env=env)
        assert run_git(["rev-parse", "refs/heads/my-new-branch"], cwd=repo, env=env) == commit_c
        assert run_git(["symbolic-ref", "--short", "HEAD"], cwd=repo, env=env) == "main"

        # Step 2: git checkout my-new-branch (unless deliberately omitted)
        if os.environ.get("OMIT_BRANCH_SWITCH") != "1":
            run_git(["checkout", "my-new-branch"], cwd=repo, env=env)
        
        active_branch = run_git(["symbolic-ref", "--short", "HEAD"], cwd=repo, env=env)
        assert active_branch == "my-new-branch", f"Decisive command failed: active branch is '{active_branch}', expected 'my-new-branch'"

        # Step 3: git checkout -b my-other-branch (verifying shortcut)
        run_git(["checkout", "-b", "my-other-branch"], cwd=repo, env=env)
        assert run_git(["symbolic-ref", "--short", "HEAD"], cwd=repo, env=env) == "my-other-branch"
        assert run_git(["rev-parse", "refs/heads/my-other-branch"], cwd=repo, env=env) == commit_c

        # Verify topic ref remained invariant at Commit B
        assert run_git(["rev-parse", "refs/heads/topic"], cwd=repo, env=env) == commit_b
        assert run_git(["rev-parse", "refs/heads/main"], cwd=repo, env=env) == commit_c

    print("ALL INTEGRATION TESTS PASSED.")

if __name__ == "__main__":
    run_test()
