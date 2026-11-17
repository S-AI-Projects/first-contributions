#!/usr/bin/env python3
"""R03-T031: Automated verification of local Git branch deletion.

Verifies:
1. Isolated temporary Git repository creation.
2. Reproduction of commits A, B, and C with branch `topic` at commit B.
3. Safe deletion failure (`git branch --delete`) when unmerged relative to tracking branch.
4. Forced deletion with `git branch -D` (Variant 1).
5. Forced deletion with `git branch --delete --force` (Variant 2 in an independent repository).
6. Meaningful Git state assertions:
   - Branch references (deleted vs preserved)
   - Commit object preservation and ancestry relationships
   - Working tree and staging area (index) cleanliness
   - HEAD symbolic reference stability
7. Inspection of exit codes (non-zero for expected failure, check=True for expected success).
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

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


def setup_repository(base_dir):
    """Sets up a bare remote and a local clone/repo with history A -> B -> C on main,

    and topic branch tracking origin/topic at commit A, but pointing to commit B.
    """
    bare_dir = os.path.join(base_dir, "remote.git")
    local_dir = os.path.join(base_dir, "local")
    os.makedirs(local_dir, exist_ok=True)

    # 1. Bare remote repository
    run_git(base_dir, "init", "--bare", bare_dir, check=True)

    # 2. Local repository
    run_git(local_dir, "init", "-b", "main", check=True)
    run_git(local_dir, "remote", "add", "origin", f"file://{bare_dir}", check=True)

    # Commit A: create notes.txt with "alpha\n"
    notes_path = os.path.join(local_dir, "notes.txt")
    with open(notes_path, "w") as f:
        f.write("alpha\n")
    run_git(local_dir, "add", "notes.txt", check=True)
    run_git(local_dir, "commit", "-m", "Commit A", check=True)
    sha_a = run_git(local_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Commit B: append "beta\n" to notes.txt
    with open(notes_path, "a") as f:
        f.write("beta\n")
    run_git(local_dir, "add", "notes.txt", check=True)
    run_git(local_dir, "commit", "-m", "Commit B", check=True)
    sha_b = run_git(local_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Commit C: create todo.txt with "one\n"
    todo_path = os.path.join(local_dir, "todo.txt")
    with open(todo_path, "w") as f:
        f.write("one\n")
    run_git(local_dir, "add", "todo.txt", check=True)
    run_git(local_dir, "commit", "-m", "Commit C", check=True)
    sha_c = run_git(local_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Push main branch to remote
    run_git(local_dir, "push", "-u", "origin", "main", check=True)

    # Push commit A to origin as topic so origin/topic exists at commit A
    run_git(local_dir, "push", "origin", f"{sha_a}:refs/heads/topic", check=True)

    # Create topic branch tracking origin/topic, but set to commit B
    run_git(local_dir, "branch", "--track", "topic", "origin/topic", check=True)
    run_git(local_dir, "branch", "-f", "topic", sha_b, check=True)

    return {
        "bare_dir": bare_dir,
        "local_dir": local_dir,
        "sha_a": sha_a,
        "sha_b": sha_b,
        "sha_c": sha_c,
    }


def verify_variant_d(tmpdir):
    print("--- Testing Variant 1: Safe deletion failure & forced deletion with -D ---")
    setup = setup_repository(tmpdir)
    local = setup["local_dir"]
    sha_a, sha_b, sha_c = setup["sha_a"], setup["sha_b"], setup["sha_c"]

    # Fact check: setup commits
    record_result("Commit A exists and is ancestor of B",
                  run_git(local, "merge-base", "--is-ancestor", sha_a, sha_b, check=False).returncode == 0)
    record_result("Commit B exists and is ancestor of C",
                  run_git(local, "merge-base", "--is-ancestor", sha_b, sha_c, check=False).returncode == 0)

    # Verify branch 'topic' exists before deletion
    branches_before = run_git(local, "branch", "--list", "topic", check=True).stdout.strip()
    record_result("Branch 'topic' exists prior to deletion", "topic" in branches_before)

    # Verify safe deletion failure: git branch --delete topic
    del_proc = run_git(local, "branch", "--delete", "topic", check=False)
    record_result("Safe deletion (git branch --delete topic) exits non-zero", del_proc.returncode != 0,
                  f"Exit code: {del_proc.returncode}")
    record_result("Safe deletion outputs 'not fully merged' error message",
                  "not fully merged" in del_proc.stderr,
                  f"Stderr: {del_proc.stderr.strip()}")

    # Branch 'topic' must still exist after failed safe deletion
    branches_after_fail = run_git(local, "branch", "--list", "topic", check=True).stdout.strip()
    record_result("Branch 'topic' still exists after safe deletion failure", "topic" in branches_after_fail)

    # Force delete using -D
    force_proc = run_git(local, "branch", "-D", "topic", check=True)
    record_result("Forced deletion (git branch -D topic) succeeds (code 0)", force_proc.returncode == 0)

    # Fact 1: Branch references
    branches_after = run_git(local, "branch", "--list", check=True).stdout
    record_result("Fact 1a: Branch 'topic' reference is completely deleted", "topic" not in branches_after)
    main_ref = run_git(local, "rev-parse", "refs/heads/main", check=True).stdout.strip()
    record_result("Fact 1b: Branch 'main' reference remains intact pointing to commit C", main_ref == sha_c)

    # Fact 2: Commit object preservation and relationships
    cat_b = run_git(local, "cat-file", "-t", sha_b, check=False)
    record_result("Fact 2a: Commit B object remains in Git object database", cat_b.stdout.strip() == "commit")
    head_symref = run_git(local, "symbolic-ref", "HEAD", check=True).stdout.strip()
    record_result("Fact 2b: Symbolic HEAD remains on refs/heads/main", head_symref == "refs/heads/main")

    # Fact 3: Working tree and staging area state
    status_proc = run_git(local, "status", "--porcelain", check=True)
    record_result("Fact 3a: Working tree is clean after branch deletion", status_proc.stdout.strip() == "")

    with open(os.path.join(local, "notes.txt")) as f:
        notes_content = f.read()
    with open(os.path.join(local, "todo.txt")) as f:
        todo_content = f.read()
    record_result("Fact 3b: Working tree files match commit C state ('notes.txt' and 'todo.txt')",
                  notes_content == "alpha\nbeta\n" and todo_content == "one\n")


def verify_variant_force(tmpdir):
    print("--- Testing Variant 2: Forced deletion with --delete --force (independent repo) ---")
    setup = setup_repository(tmpdir)
    local = setup["local_dir"]
    sha_c = setup["sha_c"]

    # Verify branch 'topic' exists before deletion
    branches_before = run_git(local, "branch", "--list", "topic", check=True).stdout.strip()
    record_result("Variant 2: Branch 'topic' exists prior to deletion", "topic" in branches_before)

    # Force delete using --delete --force
    force_proc = run_git(local, "branch", "--delete", "--force", "topic", check=True)
    record_result("Variant 2: Forced deletion (git branch --delete --force topic) succeeds (code 0)",
                  force_proc.returncode == 0)

    # Verify branch reference removal and main branch stability
    branches_after = run_git(local, "branch", "--list", check=True).stdout
    record_result("Variant 2 Fact: Branch 'topic' reference is deleted", "topic" not in branches_after)
    main_ref = run_git(local, "rev-parse", "refs/heads/main", check=True).stdout.strip()
    record_result("Variant 2 Fact: Branch 'main' reference still points to commit C", main_ref == sha_c)


def main():
    if os.environ.get("R03_T031_FORCE_FAIL") == "1":
        print("FORCED FAILURE TEST TRIGGERED (R03_T031_FORCE_FAIL=1)")
        record_result("Simulated failure assertion", False, "Environment variable R03_T031_FORCE_FAIL was set")
        sys.exit(1)

    print("================================================================")
    print("Starting automated verification: check.py (R03-T031)")
    print("================================================================")

    with tempfile.TemporaryDirectory() as tmp1:
        verify_variant_d(tmp1)

    with tempfile.TemporaryDirectory() as tmp2:
        verify_variant_force(tmp2)

    print("================================================================")
    print(f"Summary: {PASS_COUNT} passed, {FAIL_COUNT} failed.")
    print("================================================================")

    if FAIL_COUNT > 0:
        sys.exit(1)
    print("ALL CHECKS PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
