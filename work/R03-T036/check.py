#!/usr/bin/env python3
"""R03-T036: Automated comparison of Git stash commands and flags.

Compares:
1. Workflow 1: git stash apply (default without --index)
   - Staged changes in stash are restored to working tree as UNSTAGED.
   - git diff --cached is empty; git diff shows unstaged modifications.
   - stash@{0} is preserved on the stash stack.
2. Workflow 2: git stash apply --index
   - Staged changes in stash are restored directly to the STAGING AREA (index).
   - git diff --cached contains staged modifications; git diff is empty.
   - stash@{0} is preserved on the stash stack.
3. Workflow 3: git stash pop
   - Restores changes and automatically drops the stash from the stack.
   - stash list is empty afterwards.

Asserts at least three meaningful state facts:
- Staging area (index) state differences (git diff --cached vs git diff)
- Reflog / stash stack reference persistence vs removal
- Branch references remain unchanged
"""

import os
import subprocess
import sys
import tempfile

AUTHOR_NAME = "Course Student"
AUTHOR_EMAIL = "student@example.invalid"

PASS_COUNT = 0
FAIL_COUNT = 0


def record_result(description: str, condition: bool, details: str = ""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"PASS: {description}")
    else:
        FAIL_COUNT += 1
        print(f"FAIL: {description}")
        if details:
            print(f"      Details: {details}")


def get_git_env():
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"] = AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"] = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    return env


def run_git(repo_dir, *args, check=True):
    env = get_git_env()
    cmd = ["git", *args]
    proc = subprocess.run(cmd, cwd=repo_dir, env=env, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)
    return proc


def setup_repository(repo_dir):
    """Sets up repository with:

    Commit A: notes.txt ("alpha\\n")
    Commit B: notes.txt ("beta\\n" appended)
    Commit C: todo.txt ("one\\n")
    Branch topic at Commit B.
    """
    run_git(repo_dir, "init", "-b", "main", check=True)

    # Commit A
    notes_path = os.path.join(repo_dir, "notes.txt")
    with open(notes_path, "w") as f:
        f.write("alpha\n")
    run_git(repo_dir, "add", "notes.txt", check=True)
    run_git(repo_dir, "commit", "-m", "Commit A", check=True)
    sha_a = run_git(repo_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Commit B
    with open(notes_path, "a") as f:
        f.write("beta\n")
    run_git(repo_dir, "add", "notes.txt", check=True)
    run_git(repo_dir, "commit", "-m", "Commit B", check=True)
    sha_b = run_git(repo_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Commit C
    todo_path = os.path.join(repo_dir, "todo.txt")
    with open(todo_path, "w") as f:
        f.write("one\n")
    run_git(repo_dir, "add", "todo.txt", check=True)
    run_git(repo_dir, "commit", "-m", "Commit C", check=True)
    sha_c = run_git(repo_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Branch topic at Commit B
    run_git(repo_dir, "branch", "topic", sha_b, check=True)

    return {
        "sha_a": sha_a,
        "sha_b": sha_b,
        "sha_c": sha_c,
    }


def prepare_fixture_and_stash(repo_dir):
    setup = setup_repository(repo_dir)
    run_git(repo_dir, "switch", "topic", check=True)

    # Create staged change in notes.txt
    notes_path = os.path.join(repo_dir, "notes.txt")
    with open(notes_path, "a") as f:
        f.write("staged WIP line\n")
    run_git(repo_dir, "add", "notes.txt", check=True)

    # Verify staged before stashing
    status_pre = run_git(repo_dir, "status", "--porcelain", check=True).stdout
    assert "M  notes.txt" in status_pre, "notes.txt should be staged"

    # Execute stash
    run_git(repo_dir, "stash", check=True)
    status_after_stash = run_git(repo_dir, "status", "--porcelain", check=True).stdout.strip()
    assert status_after_stash == "", "Working tree should be clean after stash"

    return setup


def test_workflow_apply_default(tmpdir):
    print("--- Testing Workflow 1: git stash apply (Default) ---")
    setup = prepare_fixture_and_stash(tmpdir)
    sha_b = setup["sha_b"]
    sha_c = setup["sha_c"]

    # Execute git stash apply
    run_git(tmpdir, "stash", "apply", check=True)

    # Fact 1: Status reflects unstaged working tree modification (' M ')
    status_out = run_git(tmpdir, "status", "--porcelain", check=True).stdout
    record_result("Workflow 1 Fact 1: File is unstaged in status (' M notes.txt')",
                  " M notes.txt" in status_out)

    # Fact 2: Index (staging area) is clean; unstaged diff has changes
    cached_diff = run_git(tmpdir, "diff", "--cached", check=True).stdout.strip()
    unstaged_diff = run_git(tmpdir, "diff", check=True).stdout.strip()
    record_result("Workflow 1 Fact 2a: git diff --cached is empty (not restaged)",
                  cached_diff == "")
    record_result("Workflow 1 Fact 2b: git diff contains unstaged changes",
                  "staged WIP line" in unstaged_diff)

    # Fact 3: Stash entry remains on stack
    stash_list = run_git(tmpdir, "stash", "list", check=True).stdout
    record_result("Workflow 1 Fact 3: stash@{0} is preserved on stash stack",
                  "stash@{0}" in stash_list)

    # Fact 4: Branch references remain fixed
    topic_ref = run_git(tmpdir, "rev-parse", "refs/heads/topic", check=True).stdout.strip()
    main_ref = run_git(tmpdir, "rev-parse", "refs/heads/main", check=True).stdout.strip()
    record_result("Workflow 1 Fact 4a: topic ref remains at Commit B", topic_ref == sha_b)
    record_result("Workflow 1 Fact 4b: main ref remains at Commit C", main_ref == sha_c)


def test_workflow_apply_index(tmpdir):
    print("--- Testing Workflow 2: git stash apply --index ---")
    setup = prepare_fixture_and_stash(tmpdir)
    sha_b = setup["sha_b"]

    # Execute git stash apply --index
    run_git(tmpdir, "stash", "apply", "--index", check=True)

    # Fact 1: Status reflects staged index modification ('M  ')
    status_out = run_git(tmpdir, "status", "--porcelain", check=True).stdout
    record_result("Workflow 2 Fact 1: File is re-staged in status ('M  notes.txt')",
                  "M  notes.txt" in status_out)

    # Fact 2: Index (staging area) has changes; unstaged diff is clean
    cached_diff = run_git(tmpdir, "diff", "--cached", check=True).stdout.strip()
    unstaged_diff = run_git(tmpdir, "diff", check=True).stdout.strip()
    record_result("Workflow 2 Fact 2a: git diff --cached contains staged changes",
                  "staged WIP line" in cached_diff)
    record_result("Workflow 2 Fact 2b: git diff is empty (no unstaged changes)",
                  unstaged_diff == "")

    # Fact 3: Stash entry remains on stack
    stash_list = run_git(tmpdir, "stash", "list", check=True).stdout
    record_result("Workflow 2 Fact 3: stash@{0} is preserved on stash stack",
                  "stash@{0}" in stash_list)


def test_workflow_pop(tmpdir):
    print("--- Testing Workflow 3: git stash pop (Comparison with apply) ---")
    prepare_fixture_and_stash(tmpdir)

    # Execute git stash pop
    run_git(tmpdir, "stash", "pop", check=True)

    # Fact 1: Stash entry is automatically dropped
    stash_list = run_git(tmpdir, "stash", "list", check=True).stdout.strip()
    record_result("Workflow 3 Fact 1: Stash stack is empty after pop (stash@{0} dropped)",
                  stash_list == "")

    # Fact 2: Working tree has restored changes
    unstaged_diff = run_git(tmpdir, "diff", check=True).stdout.strip()
    record_result("Workflow 3 Fact 2: Working tree contains restored changes",
                  "staged WIP line" in unstaged_diff)


def main():
    if os.environ.get("R03_T036_FORCE_FAIL") == "1":
        print("FORCED FAILURE TEST TRIGGERED (R03_T036_FORCE_FAIL=1)")
        record_result("Simulated failure assertion", False, "Environment variable R03_T036_FORCE_FAIL was set")
        sys.exit(1)

    print("================================================================")
    print("Starting automated verification: check.py (R03-T036)")
    print("================================================================")

    with tempfile.TemporaryDirectory() as tmp1:
        test_workflow_apply_default(tmp1)

    with tempfile.TemporaryDirectory() as tmp2:
        test_workflow_apply_index(tmp2)

    with tempfile.TemporaryDirectory() as tmp3:
        test_workflow_pop(tmp3)

    print("================================================================")
    print(f"Summary: {PASS_COUNT} passed, {FAIL_COUNT} failed.")
    print("================================================================")

    if FAIL_COUNT > 0:
        sys.exit(1)
    print("ALL CHECKS PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
