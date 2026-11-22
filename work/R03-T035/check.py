#!/usr/bin/env python3
"""R03-T035: Automated verification of path quoting, '--' disambiguation, and branch deletion.

Verifies:
1. Isolated temporary Git repository creation with commits A, B, and C, and branch topic at B.
2. Exercising file 'release notes.txt' and directory 'sample data' with spaces.
3. Unquoted command failure:
   - git add release notes.txt fails with fatal: pathspec 'release' did not match any files.
4. Quoted path success:
   - git add "release notes.txt" "sample data/data.txt" stages both paths.
5. Path versus revision ambiguity resolution using '--':
   - git checkout -- "release notes.txt" safely discards working tree edits.
   - git diff main..topic -- "release notes.txt" "sample data" restricts diff to specified paths.
6. Local branch deletion semantics:
   - git branch --delete topic fails when topic has unmerged commits.
   - git branch -D topic (and git branch --delete --force topic in run 2) forcefully deletes the branch.
7. Meaningful Git state assertions:
   - Branch topic reference removed.
   - Branch main reference remains intact.
   - Working tree and index cleanliness.
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


def verify_run(run_id: int, repo_dir: str, use_force_syntax: bool = False):
    print(f"--- Run {run_id}: Quoting, Disambiguation & Branch Deletion ---")
    setup = setup_repository(repo_dir)
    sha_c = setup["sha_c"]

    # Switch to topic
    run_git(repo_dir, "switch", "topic", check=True)
    record_result(f"Run {run_id}: Switched to branch topic",
                  run_git(repo_dir, "symbolic-ref", "HEAD", check=True).stdout.strip() == "refs/heads/topic")

    # Create files and directories with spaces
    sample_dir = os.path.join(repo_dir, "sample data")
    os.makedirs(sample_dir, exist_ok=True)

    rel_notes = os.path.join(repo_dir, "release notes.txt")
    with open(rel_notes, "w") as f:
        f.write("v1.0 release notes\n")

    sample_file = os.path.join(sample_dir, "data.txt")
    with open(sample_file, "w") as f:
        f.write("sample payload data\n")

    # Fact 1: Unquoted git add fails due to word splitting
    unquoted_res = run_git(repo_dir, "add", "release", "notes.txt", check=False)
    record_result(f"Run {run_id} Fact 1: Unquoted git add fails with non-zero exit",
                  unquoted_res.returncode != 0)
    record_result(f"Run {run_id} Fact 1b: Error specifies pathspec 'release' did not match",
                  "release" in unquoted_res.stderr)

    # Fact 2: Quoted git add succeeds
    run_git(repo_dir, "add", "release notes.txt", "sample data/data.txt", check=True)
    staged = run_git(repo_dir, "diff", "--cached", "--name-only", check=True).stdout.splitlines()
    record_result(f"Run {run_id} Fact 2a: 'release notes.txt' is staged", "release notes.txt" in staged)
    record_result(f"Run {run_id} Fact 2b: 'sample data/data.txt' is staged", "sample data/data.txt" in staged)

    # Commit the changes on topic
    run_git(repo_dir, "commit", "-m", "Add release notes and sample data on topic", check=True)
    topic_head = run_git(repo_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Fact 3: Disambiguation using '--' and path restoration
    with open(rel_notes, "a") as f:
        f.write("accidental uncommitted change\n")

    # Unquoted checkout fails
    unquoted_co = run_git(repo_dir, "checkout", "--", "release", "notes.txt", check=False)
    record_result(f"Run {run_id} Fact 3a: Unquoted checkout fails to match split path",
                  unquoted_co.returncode != 0)

    # Quoted checkout with '--' succeeds
    run_git(repo_dir, "checkout", "--", "release notes.txt", check=True)
    with open(rel_notes) as f:
        restored_content = f.read()
    record_result(f"Run {run_id} Fact 3b: Quoted checkout with '--' restores clean content",
                  restored_content == "v1.0 release notes\n")

    # Fact 4: Revision vs path diff with '--'
    diff_proc = run_git(repo_dir, "diff", "main..topic", "--", "release notes.txt", "sample data", check=True)
    record_result(f"Run {run_id} Fact 4a: Diff correctly identifies release notes.txt across revisions",
                  "release notes.txt" in diff_proc.stdout)
    record_result(f"Run {run_id} Fact 4b: Diff correctly identifies sample data/data.txt across revisions",
                  "sample data/data.txt" in diff_proc.stdout)

    # Switch back to main to test branch deletion
    run_git(repo_dir, "switch", "main", check=True)

    # Fact 5: Safe deletion failure on unmerged branch
    del_proc = run_git(repo_dir, "branch", "--delete", "topic", check=False)
    record_result(f"Run {run_id} Fact 5a: Safe deletion (git branch --delete topic) fails (non-zero)",
                  del_proc.returncode != 0)
    record_result(f"Run {run_id} Fact 5b: Error message specifies branch is not fully merged",
                  "not fully merged" in del_proc.stderr)

    # Fact 6: Forced deletion succeeds
    if use_force_syntax:
        run_git(repo_dir, "branch", "--delete", "--force", "topic", check=True)
        record_result(f"Run {run_id} Fact 6: Forced deletion with --delete --force topic succeeds", True)
    else:
        run_git(repo_dir, "branch", "-D", "topic", check=True)
        record_result(f"Run {run_id} Fact 6: Forced deletion with -D topic succeeds", True)

    # Fact 7: Branch refs and working tree state
    branches = run_git(repo_dir, "branch", "--list", check=True).stdout
    record_result(f"Run {run_id} Fact 7a: Branch 'topic' reference completely removed", "topic" not in branches)

    main_ref = run_git(repo_dir, "rev-parse", "refs/heads/main", check=True).stdout.strip()
    record_result(f"Run {run_id} Fact 7b: Branch 'main' reference remains unchanged at Commit C", main_ref == sha_c)

    status_proc = run_git(repo_dir, "status", "--porcelain", check=True)
    record_result(f"Run {run_id} Fact 7c: Working tree on main is clean", status_proc.stdout.strip() == "")


def main():
    if os.environ.get("R03_T035_FORCE_FAIL") == "1":
        print("FORCED FAILURE TEST TRIGGERED (R03_T035_FORCE_FAIL=1)")
        record_result("Simulated failure assertion", False, "Environment variable R03_T035_FORCE_FAIL was set")
        sys.exit(1)

    print("================================================================")
    print("Starting automated verification: check.py (R03-T035)")
    print("================================================================")

    with tempfile.TemporaryDirectory() as tmp1:
        verify_run(1, tmp1, use_force_syntax=False)

    with tempfile.TemporaryDirectory() as tmp2:
        verify_run(2, tmp2, use_force_syntax=True)

    print("================================================================")
    print(f"Summary: {PASS_COUNT} passed, {FAIL_COUNT} failed.")
    print("================================================================")

    if FAIL_COUNT > 0:
        sys.exit(1)
    print("ALL CHECKS PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
