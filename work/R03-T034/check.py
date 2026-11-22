#!/usr/bin/env python3
"""R03-T034: Automated verification of branch and remote semantics for .gitignore and git rm --cached.

Verifies:
1. Building an isolated temporary Git repository with a local bare remote (file://).
2. Explicit author identity configuration.
3. Commits A, B, and C on main; branch topic created at commit B.
4. Execution of git rm --cached and .gitignore commit on branch topic.
5. Assertion of reference isolation:
   - Intended ref (refs/heads/topic) changed to a new commit.
   - Unrelated local ref (refs/heads/main) remained fixed at commit C.
   - Remote refs (refs/remotes/origin/main, refs/remotes/origin/topic) remained fixed.
6. Index and working tree assertions:
   - notes.txt untracked on topic index, but preserved on disk.
   - notes.txt remains fully tracked on main index.
7. Verification of bulk untracking (git rm -r --cached .) in an independent temporary repository.
8. Exits non-zero on assertion failure.
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


def setup_repository(base_dir):
    """Sets up a bare remote and working repository with:

    main: Commit A -> Commit B -> Commit C
    topic at Commit B
    Pushed to origin/main and origin/topic
    """
    bare_dir = os.path.join(base_dir, "remote.git")
    local_dir = os.path.join(base_dir, "local")
    os.makedirs(local_dir, exist_ok=True)

    # 1. Bare remote
    run_git(base_dir, "init", "--bare", bare_dir, check=True)

    # 2. Local repository
    run_git(local_dir, "init", "-b", "main", check=True)
    run_git(local_dir, "remote", "add", "origin", f"file://{bare_dir}", check=True)

    # Commit A
    notes_path = os.path.join(local_dir, "notes.txt")
    with open(notes_path, "w") as f:
        f.write("alpha\n")
    run_git(local_dir, "add", "notes.txt", check=True)
    run_git(local_dir, "commit", "-m", "Commit A", check=True)
    sha_a = run_git(local_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Commit B
    with open(notes_path, "a") as f:
        f.write("beta\n")
    run_git(local_dir, "add", "notes.txt", check=True)
    run_git(local_dir, "commit", "-m", "Commit B", check=True)
    sha_b = run_git(local_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Commit C
    todo_path = os.path.join(local_dir, "todo.txt")
    with open(todo_path, "w") as f:
        f.write("one\n")
    run_git(local_dir, "add", "todo.txt", check=True)
    run_git(local_dir, "commit", "-m", "Commit C", check=True)
    sha_c = run_git(local_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Push main to origin
    run_git(local_dir, "push", "-u", "origin", "main", check=True)

    # Branch topic at B and push
    run_git(local_dir, "branch", "topic", sha_b, check=True)
    run_git(local_dir, "push", "-u", "origin", "topic", check=True)

    return {
        "bare_dir": bare_dir,
        "local_dir": local_dir,
        "sha_a": sha_a,
        "sha_b": sha_b,
        "sha_c": sha_c,
    }


def verify_branch_remote_semantics(tmpdir):
    print("--- Test 1: Branch and Remote Semantics on topic ---")
    setup = setup_repository(tmpdir)
    local = setup["local_dir"]
    sha_b = setup["sha_b"]
    sha_c = setup["sha_c"]

    # Switch to topic
    run_git(local, "switch", "topic", check=True)

    # Record baseline references
    main_ref_before = run_git(local, "rev-parse", "refs/heads/main", check=True).stdout.strip()
    topic_ref_before = run_git(local, "rev-parse", "refs/heads/topic", check=True).stdout.strip()
    orig_main_before = run_git(local, "rev-parse", "refs/remotes/origin/main", check=True).stdout.strip()
    orig_topic_before = run_git(local, "rev-parse", "refs/remotes/origin/topic", check=True).stdout.strip()

    record_result("Baseline: main points to Commit C", main_ref_before == sha_c)
    record_result("Baseline: topic points to Commit B", topic_ref_before == sha_b)
    record_result("Baseline: origin/main points to Commit C", orig_main_before == sha_c)
    record_result("Baseline: origin/topic points to Commit B", orig_topic_before == sha_b)

    # Execute git rm --cached notes.txt on topic
    run_git(local, "rm", "--cached", "notes.txt", check=True)

    # Create and stage .gitignore
    gitignore_path = os.path.join(local, ".gitignore")
    with open(gitignore_path, "w") as f:
        f.write("notes.txt\n")
    run_git(local, "add", ".gitignore", check=True)
    run_git(local, "commit", "-m", "Untrack notes.txt and add .gitignore on topic", check=True)

    # Inspect references after commit
    topic_ref_after = run_git(local, "rev-parse", "refs/heads/topic", check=True).stdout.strip()
    main_ref_after = run_git(local, "rev-parse", "refs/heads/main", check=True).stdout.strip()
    orig_main_after = run_git(local, "rev-parse", "refs/remotes/origin/main", check=True).stdout.strip()
    orig_topic_after = run_git(local, "rev-parse", "refs/remotes/origin/topic", check=True).stdout.strip()

    # Fact 1: Intended ref changed
    record_result("Fact 1: Intended ref (refs/heads/topic) changed to new commit",
                  topic_ref_after != topic_ref_before)

    # Fact 2: Unrelated local ref (refs/heads/main) stayed fixed
    record_result("Fact 2: Unrelated local ref (refs/heads/main) stayed fixed at commit C",
                  main_ref_after == sha_c and main_ref_after == main_ref_before)

    # Fact 3: Unrelated remote ref (origin/main) stayed fixed
    record_result("Fact 3: Remote ref (refs/remotes/origin/main) stayed fixed at commit C",
                  orig_main_after == sha_c and orig_main_after == orig_main_before)

    # Fact 4: Remote tracking ref (origin/topic) stayed fixed prior to push
    record_result("Fact 4: Remote tracking ref (refs/remotes/origin/topic) stayed fixed at commit B",
                  orig_topic_after == sha_b and orig_topic_after == orig_topic_before)

    # Fact 5: Working tree file preservation
    notes_path = os.path.join(local, "notes.txt")
    record_result("Fact 5: notes.txt remains present on filesystem in working tree",
                  os.path.exists(notes_path))
    with open(notes_path) as f:
        notes_content = f.read()
    record_result("Fact 5b: notes.txt content preserved ('alpha\\nbeta\\n')",
                  notes_content == "alpha\nbeta\n")

    # Fact 6: Index isolation between branches
    topic_files = run_git(local, "ls-files", check=True).stdout.split()
    record_result("Fact 6a: notes.txt is removed from index on topic", "notes.txt" not in topic_files)
    record_result("Fact 6b: .gitignore is tracked in index on topic", ".gitignore" in topic_files)

    # Switch to main and verify index is completely unaffected
    run_git(local, "switch", "main", check=True)
    main_files = run_git(local, "ls-files", check=True).stdout.split()
    record_result("Fact 6c: notes.txt remains tracked in index on main", "notes.txt" in main_files)
    record_result("Fact 6d: .gitignore is not present in index on main", ".gitignore" not in main_files)


def verify_bulk_untracking(tmpdir):
    print("--- Test 2: Bulk Untracking with git rm -r --cached . ---")
    setup = setup_repository(tmpdir)
    local = setup["local_dir"]

    run_git(local, "switch", "topic", check=True)

    # Create dummy ignored file
    debug_log = os.path.join(local, "debug.log")
    with open(debug_log, "w") as f:
        f.write("log entry\n")

    # Add .gitignore ignoring *.log and notes.txt
    gitignore_path = os.path.join(local, ".gitignore")
    with open(gitignore_path, "w") as f:
        f.write("*.log\nnotes.txt\n")

    # Bulk untrack
    run_git(local, "rm", "-r", "--cached", ".", check=True)
    run_git(local, "add", ".", check=True)
    run_git(local, "commit", "-m", "Bulk untrack and update .gitignore on topic", check=True)

    tracked = run_git(local, "ls-files", check=True).stdout.split()
    record_result("Bulk untrack: notes.txt removed from topic index", "notes.txt" not in tracked)
    record_result("Bulk untrack: debug.log not added to topic index", "debug.log" not in tracked)
    record_result("Bulk untrack: .gitignore is tracked", ".gitignore" in tracked)
    record_result("Bulk untrack: working tree is clean",
                  run_git(local, "status", "--porcelain", check=True).stdout.strip() == "")


def main():
    if os.environ.get("R03_T034_FORCE_FAIL") == "1":
        print("FORCED FAILURE TEST TRIGGERED (R03_T034_FORCE_FAIL=1)")
        record_result("Simulated failure assertion", False, "Environment variable R03_T034_FORCE_FAIL was set")
        sys.exit(1)

    print("================================================================")
    print("Starting automated verification: check.py (R03-T034)")
    print("================================================================")

    with tempfile.TemporaryDirectory() as tmp1:
        verify_branch_remote_semantics(tmp1)

    with tempfile.TemporaryDirectory() as tmp2:
        verify_bulk_untracking(tmp2)

    print("================================================================")
    print(f"Summary: {PASS_COUNT} passed, {FAIL_COUNT} failed.")
    print("================================================================")

    if FAIL_COUNT > 0:
        sys.exit(1)
    print("ALL CHECKS PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
