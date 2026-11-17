#!/usr/bin/env python3
"""R03-T033: Automated verification of Git commit moving and recovery mechanisms.

Verifies:
1. Isolated temporary Git repository setup with commits A, B, and C, and branch topic at B.
2. Demonstration of moving commit C from main to topic using:
   - git reset HEAD~ --soft
   - git stash
   - git checkout topic
   - git stash pop
   - git add / commit
3. Demonstration of reversible mistakes associated with the guide:
   - Mistake A: Accidental git reset --hard HEAD~ (wiping commit and worktree files).
     Recovery: git reset --hard HEAD@{1} (restores commit, tree hash, and files).
   - Mistake B: Main branch unintentionally stripped of commit C after moving.
     Recovery: Switching to main and running git reset --hard main@{1} via reflog.
4. Meaningful Git state assertions:
   - Tree hash match before and after recovery
   - File contents match expected state (notes.txt, todo.txt)
   - Working tree and index cleanliness
   - Reflog and branch reference integrity
5. Exits non-zero on assertion failure.
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
    """Creates initial repository:

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
    tree_c = run_git(repo_dir, "rev-parse", "HEAD^{tree}", check=True).stdout.strip()

    # Create topic branch at Commit B
    run_git(repo_dir, "branch", "topic", sha_b, check=True)

    return {
        "sha_a": sha_a,
        "sha_b": sha_b,
        "sha_c": sha_c,
        "tree_c": tree_c,
    }


def verify_accidental_hard_reset_recovery(tmpdir):
    print("--- Test 1: Recovery from Accidental 'git reset --hard' ---")
    setup = setup_repository(tmpdir)
    sha_c = setup["sha_c"]
    tree_c = setup["tree_c"]

    # Verify initial state on main
    record_result("Init: HEAD is at commit C",
                  run_git(tmpdir, "rev-parse", "HEAD", check=True).stdout.strip() == sha_c)

    # Reversible mistake: user accidentally runs git reset --hard HEAD~ instead of --soft
    run_git(tmpdir, "reset", "--hard", "HEAD~", check=True)
    head_after_mistake = run_git(tmpdir, "rev-parse", "HEAD", check=True).stdout.strip()
    record_result("Mistake: HEAD rolled back to commit B", head_after_mistake == setup["sha_b"])

    todo_path = os.path.join(tmpdir, "todo.txt")
    record_result("Mistake effect: todo.txt missing from working tree", not os.path.exists(todo_path))

    # Recovery: inspect reflog and reset back to HEAD@{1}
    reflog_out = run_git(tmpdir, "reflog", "-n", "2", check=True).stdout
    record_result("Reflog records pre-reset commit in HEAD@{1}", "HEAD@{1}" in reflog_out or sha_c[:7] in reflog_out)

    target_ref = run_git(tmpdir, "rev-parse", "HEAD@{1}", check=True).stdout.strip()
    record_result("HEAD@{1} points to original commit C", target_ref == sha_c)

    # Execute recovery command
    run_git(tmpdir, "reset", "--hard", "HEAD@{1}", check=True)
    recovered_sha = run_git(tmpdir, "rev-parse", "HEAD", check=True).stdout.strip()
    recovered_tree = run_git(tmpdir, "rev-parse", "HEAD^{tree}", check=True).stdout.strip()

    # Assert recovery state facts
    record_result("Recovery Fact 1: Commit hash restored to original commit C", recovered_sha == sha_c)
    record_result("Recovery Fact 2: Tree hash matches original tree_c exactly", recovered_tree == tree_c)

    with open(todo_path) as f:
        todo_content = f.read()
    record_result("Recovery Fact 3: todo.txt restored with original contents ('one\\n')",
                  todo_content == "one\n")

    status_proc = run_git(tmpdir, "status", "--porcelain", check=True)
    record_result("Recovery Fact 4: Working tree is clean after recovery", status_proc.stdout.strip() == "")


def verify_moved_commit_workflow_and_recovery(tmpdir):
    print("--- Test 2: Move Commit to Branch & Reflog Branch Recovery ---")
    setup = setup_repository(tmpdir)
    sha_c = setup["sha_c"]
    sha_b = setup["sha_b"]
    tree_c = setup["tree_c"]

    # 1. Guide workflow: move commit to topic
    run_git(tmpdir, "reset", "HEAD~", "--soft", check=True)
    record_result("Workflow 1: git reset HEAD~ --soft moved main to commit B",
                  run_git(tmpdir, "rev-parse", "HEAD", check=True).stdout.strip() == sha_b)

    status_soft = run_git(tmpdir, "status", "--porcelain", check=True).stdout
    record_result("Workflow 2: todo.txt remains staged in index", "A  todo.txt" in status_soft)

    run_git(tmpdir, "stash", check=True)
    record_result("Workflow 3: git stash recorded directory state",
                  "stash@{0}" in run_git(tmpdir, "stash", "list", check=True).stdout)

    run_git(tmpdir, "checkout", "topic", check=True)
    record_result("Workflow 4: git checkout topic switched to topic branch",
                  run_git(tmpdir, "symbolic-ref", "HEAD", check=True).stdout.strip() == "refs/heads/topic")

    run_git(tmpdir, "stash", "pop", check=True)
    run_git(tmpdir, "add", ".", check=True)
    run_git(tmpdir, "commit", "-m", "Commit C on topic", check=True)
    topic_tree = run_git(tmpdir, "rev-parse", "HEAD^{tree}", check=True).stdout.strip()
    record_result("Workflow 5: Changes committed to topic; tree hash matches tree_c", topic_tree == tree_c)

    # 2. Recovery on main: suppose user wishes to undo the reset on main
    run_git(tmpdir, "checkout", "main", check=True)
    record_result("Recovery Switch: On main branch, currently at commit B",
                  run_git(tmpdir, "rev-parse", "HEAD", check=True).stdout.strip() == sha_b)

    # Identify main's pre-reset commit in branch reflog: main@{1}
    main_reflog_target = run_git(tmpdir, "rev-parse", "main@{1}", check=True).stdout.strip()
    record_result("Branch reflog: main@{1} points to original commit C", main_reflog_target == sha_c)

    # Recover main
    run_git(tmpdir, "reset", "--hard", "main@{1}", check=True)
    main_rec_sha = run_git(tmpdir, "rev-parse", "HEAD", check=True).stdout.strip()
    main_rec_tree = run_git(tmpdir, "rev-parse", "HEAD^{tree}", check=True).stdout.strip()

    record_result("Branch Recovery Fact 1: main restored to commit C", main_rec_sha == sha_c)
    record_result("Branch Recovery Fact 2: main tree hash matches original tree_c", main_rec_tree == tree_c)

    with open(os.path.join(tmpdir, "todo.txt")) as f:
        todo_content = f.read()
    with open(os.path.join(tmpdir, "notes.txt")) as f:
        notes_content = f.read()
    record_result("Branch Recovery Fact 3: Working tree files on main match commit C state",
                  todo_content == "one\n" and notes_content == "alpha\nbeta\n")
    record_result("Branch Recovery Fact 4: Working tree is clean",
                  run_git(tmpdir, "status", "--porcelain", check=True).stdout.strip() == "")


def main():
    if os.environ.get("R03_T033_FORCE_FAIL") == "1":
        print("FORCED FAILURE TEST TRIGGERED (R03_T033_FORCE_FAIL=1)")
        record_result("Simulated failure assertion", False, "Environment variable R03_T033_FORCE_FAIL was set")
        sys.exit(1)

    print("================================================================")
    print("Starting automated verification: check.py (R03-T033)")
    print("================================================================")

    with tempfile.TemporaryDirectory() as tmp1:
        verify_accidental_hard_reset_recovery(tmp1)

    with tempfile.TemporaryDirectory() as tmp2:
        verify_moved_commit_workflow_and_recovery(tmp2)

    print("================================================================")
    print(f"Summary: {PASS_COUNT} passed, {FAIL_COUNT} failed.")
    print("================================================================")

    if FAIL_COUNT > 0:
        sys.exit(1)
    print("ALL CHECKS PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
