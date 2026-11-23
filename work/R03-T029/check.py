#!/usr/bin/env python3
"""
Automated verification script for Task R03-T029:
State the missing setup explicitly: creating a gitignore file.

Verifies:
1. Target guide preserves all command anchors:
   - git config --global core.excludesfile ~/.gitignore_global
   - git rm --cached filename
   - git rm -r --cached .
2. Validates all documented preconditions:
   - Repository state: verified inside worktree.
   - Current branch: verified on branch main.
   - Worktree cleanliness: verified clean before untracking.
   - Excludes configuration: verifies core.excludesfile in isolated config.
3. Minimal setup demonstration:
   - Commits A, B, topic at B, Commit C on main.
   - .gitignore created with *.log; verify untracked log file is ignored.
   - git rm --cached todo.txt stages deletion while preserving file on disk.
   - Unrelated ref refs/heads/topic remains fixed at Commit B.
4. Per-test config is strictly local; user's global Git configuration is untouched.
5. Runs across 2 independent temporary repositories.
6. Exits non-zero on assertion failure.
"""

import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE_REL = "docs/additional-material/git_workflow_scenarios/creating-a-gitignore-file.md"
GUIDE_PATH = ROOT / GUIDE_REL
WORK_DIR = Path(__file__).resolve().parent

AUTHOR_NAME = "Course Student"
AUTHOR_EMAIL = "student@example.invalid"

def run_cmd(args, cwd, env=None, check=True):
    res = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=check
    )
    return res.stdout.strip()

def verify_guide():
    assert GUIDE_PATH.exists(), f"Guide file not found: {GUIDE_PATH}"
    content = GUIDE_PATH.read_text(encoding="utf-8")

    anchors = [
        "git config --global core.excludesfile ~/.gitignore_global",
        "git rm --cached filename",
        "git rm -r --cached ."
    ]
    for anchor in anchors:
        assert anchor in content, f"Missing anchor: {anchor}"

    assert "Prerequisites and Minimal Setup for .gitignore" in content, "Missing prerequisites section"
    assert "Precondition Checklist" in content, "Missing checklist table in guide"

def run_scenario(iteration: int):
    with tempfile.TemporaryDirectory(prefix=f"r03-t029-run{iteration}-") as tmpdir:
        repo = Path(tmpdir) / "repo"
        repo.mkdir()
        home = Path(tmpdir) / "home"
        home.mkdir()

        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "HOME": str(home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
            "GIT_AUTHOR_NAME": AUTHOR_NAME,
            "GIT_AUTHOR_EMAIL": AUTHOR_EMAIL,
            "GIT_COMMITTER_NAME": AUTHOR_NAME,
            "GIT_COMMITTER_EMAIL": AUTHOR_EMAIL,
            "LC_ALL": "C",
        })

        # Step 1: Initialize repository
        run_cmd(["git", "init", "-b", "main"], cwd=repo, env=env)
        run_cmd(["git", "config", "user.name", AUTHOR_NAME], cwd=repo, env=env)
        run_cmd(["git", "config", "user.email", AUTHOR_EMAIL], cwd=repo, env=env)

        # Commit A
        (repo / "notes.txt").write_text("alpha\n", encoding="utf-8")
        run_cmd(["git", "add", "notes.txt"], cwd=repo, env=env)
        run_cmd(["git", "commit", "-m", "A: add notes"], cwd=repo, env=env)
        commit_a = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)

        # Commit B
        with open(repo / "notes.txt", "a", encoding="utf-8") as f:
            f.write("beta\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo, env=env)
        run_cmd(["git", "commit", "-m", "B: append notes"], cwd=repo, env=env)
        commit_b = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)

        # Branch topic at Commit B
        run_cmd(["git", "branch", "topic", commit_b], cwd=repo, env=env)

        # Commit C on main
        (repo / "todo.txt").write_text("one\n", encoding="utf-8")
        run_cmd(["git", "add", "todo.txt"], cwd=repo, env=env)
        run_cmd(["git", "commit", "-m", "C: add todo"], cwd=repo, env=env)
        commit_c = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)

        # Precondition Checks:
        # Precondition 1: Repository state
        is_worktree = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo, env=env)
        # Precondition 2: Current branch
        current_branch = run_cmd(["git", "branch", "--show-current"], cwd=repo, env=env)
        # Precondition 3: Clean worktree before untracking
        clean_status = run_cmd(["git", "status", "--porcelain"], cwd=repo, env=env)
        # Precondition 4: Excludesfile configuration in isolated HOME
        run_cmd(["git", "config", "--global", "core.excludesfile", "~/.gitignore_global"], cwd=repo, env=env)
        excludes_cfg = run_cmd(["git", "config", "--get", "core.excludesfile"], cwd=repo, env=env)

        # Functional Check 1: Adding .gitignore
        (repo / ".gitignore").write_text("*.log\n", encoding="utf-8")
        (repo / "debug.log").write_text("debug logs\n", encoding="utf-8")
        status_with_ignored = run_cmd(["git", "status", "--porcelain"], cwd=repo, env=env)
        assert "debug.log" not in status_with_ignored, "debug.log should be ignored by .gitignore"

        # Functional Check 2: git rm --cached todo.txt
        run_cmd(["git", "rm", "--cached", "todo.txt"], cwd=repo, env=env)
        status_after_untrack = run_cmd(["git", "status", "--porcelain"], cwd=repo, env=env)
        todo_exists = (repo / "todo.txt").exists()
        todo_content = (repo / "todo.txt").read_text(encoding="utf-8")
        topic_ref = run_cmd(["git", "rev-parse", "refs/heads/topic"], cwd=repo, env=env)

        if os.environ.get("FORCE_FAIL") == "1":
            assert False, "Forced failure for negative test verification"

        # Assertions
        assert is_worktree == "true", "Expected inside work tree"
        assert current_branch == "main", f"Expected branch 'main', got '{current_branch}'"
        assert clean_status == "", "Expected clean working tree before operations"
        assert excludes_cfg == "~/.gitignore_global", f"Expected excludesfile config, got '{excludes_cfg}'"

        # State Assertions
        assert "D  todo.txt" in status_after_untrack, "todo.txt should be staged as deleted in index"
        assert todo_exists, "todo.txt should still exist on disk"
        assert todo_content == "one\n", f"todo.txt content altered: {todo_content}"
        assert topic_ref == commit_b, "topic ref shifted"

        return {
            "iteration": iteration,
            "commit_a": commit_a,
            "commit_b": commit_b,
            "commit_c": commit_c,
            "is_worktree": is_worktree,
            "current_branch": current_branch,
            "excludes_cfg": excludes_cfg,
            "topic_ref": topic_ref,
        }

def main():
    print("Verifying guide syntax and command anchors...")
    verify_guide()
    print("  Guide verification passed.")

    results = []
    print("Running reproducible checks across 2 independent temporary repositories...")
    for i in (1, 2):
        res = run_scenario(i)
        results.append(res)
        print(f"  Run {i} passed: worktree={res['is_worktree']} branch={res['current_branch']} topic={res['topic_ref'][:7]}")

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    inputs_txt = f"""Task: R03-T029
Student: Dheeraj Kumar
Repository: https://github.com/S-AI-Projects/first-contributions
Assigned Branch: student/e26b07f0784/R03-T029
Target Guide: {GUIDE_REL}
Command Anchors:
  - git config --global core.excludesfile ~/.gitignore_global
  - git rm --cached filename
  - git rm -r --cached .
Prerequisites Verified:
  1. Repository state: git rev-parse --is-inside-work-tree == true
  2. Current branch: git branch --show-current == main
  3. Worktree cleanliness: git status --porcelain == clean
  4. Excludes configuration: git config --get core.excludesfile
Base Fixture:
  - Branch: main, Author: Course Student <student@example.invalid>
  - Commits A, B, topic at B, Commit C on main
"""
    (WORK_DIR / "inputs.txt").write_text(inputs_txt, encoding="utf-8")

    expected_txt = """Expected Verification Results:
1. Target Guide:
   - Preserves all 3 command anchors.
   - Contains precondition checklist table and minimal setup example.
2. Preconditions Verified:
   - git rev-parse --is-inside-work-tree returns 'true'.
   - git branch --show-current returns 'main'.
   - git status --porcelain is empty prior to untracking.
   - core.excludesfile configured in isolated environment.
3. State Assertions:
   - *.log rule in .gitignore prevents debug.log from tracking.
   - git rm --cached todo.txt stages deletion ('D  todo.txt') in index while preserving file on disk.
   - refs/heads/topic remains fixed at Commit B.
"""
    (WORK_DIR / "expected.txt").write_text(expected_txt, encoding="utf-8")

    actual_txt = f"""Verification Summary:
Guide Check: PASSED (Found anchors, precondition checklist table, and setup walkthrough)

Run 1:
  - Commit A: {results[0]['commit_a']}
  - Commit B: {results[0]['commit_b']}
  - Commit C: {results[0]['commit_c']}
  - Worktree Check: {results[0]['is_worktree']} (VERIFIED)
  - Current Branch: {results[0]['current_branch']} (VERIFIED)
  - Excludes Config: {results[0]['excludes_cfg']} (VERIFIED)
  - topic Ref: {results[0]['topic_ref']} (UNCHANGED)
  - Result: ALL STATE ASSERTIONS PASSED

Run 2:
  - Commit A: {results[1]['commit_a']}
  - Commit B: {results[1]['commit_b']}
  - Commit C: {results[1]['commit_c']}
  - Worktree Check: {results[1]['is_worktree']} (VERIFIED)
  - Current Branch: {results[1]['current_branch']} (VERIFIED)
  - Excludes Config: {results[1]['excludes_cfg']} (VERIFIED)
  - topic Ref: {results[1]['topic_ref']} (UNCHANGED)
  - Result: ALL STATE ASSERTIONS PASSED
"""
    (WORK_DIR / "actual.txt").write_text(actual_txt, encoding="utf-8")

    git_ver = run_cmd(["git", "--version"], cwd=ROOT)
    py_ver = f"Python {platform.python_version()}"
    versions_txt = f"{git_ver}\n{py_ver}\nOS: {platform.system()} {platform.release()} ({platform.machine()})\n"
    (WORK_DIR / "versions.txt").write_text(versions_txt, encoding="utf-8")

    evidence_md = f"""# Verification Evidence for Task R03-T029

- **Task**: R03-T029 · State the missing setup explicitly: creating a gitignore file
- **Student**: Dheeraj Kumar
- **Guide**: `{GUIDE_REL}`
- **Test Command**: `python3 work/R03-T029/check.py`

## State Assertions Verified
1. **Precondition 1 (Worktree State)**: Confirmed inside active Git repository (`git rev-parse --is-inside-work-tree` returned `true`).
2. **Precondition 2 (Current Branch)**: Confirmed execution on active branch `main` (`git branch --show-current` returned `main`).
3. **Precondition 3 (Worktree Cleanliness)**: Verified staging index was clean prior to untracking.
4. **Precondition 4 (Configuration Isolation)**: Verified `core.excludesfile` in an isolated per-test environment leaving host configuration untouched.
5. **Ignore Functionality**: Confirmed `*.log` rule in `.gitignore` successfully excluded `debug.log`.
6. **File Preservation**: Verified `git rm --cached todo.txt` staged deletion in index while keeping file on disk with `"one\n"` intact.
7. **Unrelated Ref Stability**: `refs/heads/topic` remained fixed at Commit B.

## Tool Versions
- `{git_ver}`
- `{py_ver}`
"""
    (WORK_DIR / "evidence.md").write_text(evidence_md, encoding="utf-8")

    print("\nPASS: All verification checks passed successfully.")

if __name__ == "__main__":
    main()
