#!/usr/bin/env python3
"""R03-T032: Automated verification of Git rebase vs merge state transitions.

Verifies:
1. Building independent temporary repositories with identical initial histories.
2. Explicit author identity configuration.
3. Scenario A (Rebase):
   - Switch to topic using git switch topic (and git checkout topic demonstration).
   - Rebase topic onto main.
   - Assert rebased commit B' receives a new commit ID and new parent (commit C).
   - Assert main branch ref remains unchanged at commit C.
   - Assert HEAD points to refs/heads/topic and commit B'.
   - Assert file contents and clean index/working tree.
4. Scenario B (Merge):
   - Switch to main using git switch main (and git checkout main demonstration).
   - Merge topic into main.
   - Assert merge commit has both parents: parent 1 = commit C, parent 2 = original commit B.
   - Assert original commit B is preserved in ancestry.
   - Assert topic branch ref remains unchanged at commit B.
   - Assert HEAD points to refs/heads/main and merge commit.
   - Assert file contents and clean index/working tree.
5. Exit non-zero if any assertion fails.
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


def setup_initial_history(repo_dir):
    """Creates the initial repository state:

    Commit A: notes.txt ("alpha\\n")
    Commit B on topic: notes.txt ("beta\\n" appended)
    Commit C on main: todo.txt ("one\\n")
    """
    run_git(repo_dir, "init", "-b", "main", check=True)

    # Commit A on main
    notes_path = os.path.join(repo_dir, "notes.txt")
    with open(notes_path, "w") as f:
        f.write("alpha\n")
    run_git(repo_dir, "add", "notes.txt", check=True)
    run_git(repo_dir, "commit", "-m", "Commit A", check=True)
    sha_a = run_git(repo_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Create branch topic at Commit A, then commit B on topic
    run_git(repo_dir, "branch", "topic", check=True)
    run_git(repo_dir, "switch", "topic", check=True)
    with open(notes_path, "a") as f:
        f.write("beta\n")
    run_git(repo_dir, "add", "notes.txt", check=True)
    run_git(repo_dir, "commit", "-m", "Commit B", check=True)
    sha_b = run_git(repo_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    # Switch back to main and commit C
    run_git(repo_dir, "switch", "main", check=True)
    todo_path = os.path.join(repo_dir, "todo.txt")
    with open(todo_path, "w") as f:
        f.write("one\n")
    run_git(repo_dir, "add", "todo.txt", check=True)
    run_git(repo_dir, "commit", "-m", "Commit C", check=True)
    sha_c = run_git(repo_dir, "rev-parse", "HEAD", check=True).stdout.strip()

    return sha_a, sha_b, sha_c


def verify_scenario_a_rebase(tmpdir):
    print("--- Testing Scenario A: Rebase ---")
    sha_a, sha_b, sha_c = setup_initial_history(tmpdir)

    # Assert initial refs and state
    main_before = run_git(tmpdir, "rev-parse", "refs/heads/main", check=True).stdout.strip()
    topic_before = run_git(tmpdir, "rev-parse", "refs/heads/topic", check=True).stdout.strip()
    record_result("Rebase Init: main points to Commit C", main_before == sha_c)
    record_result("Rebase Init: topic points to Commit B", topic_before == sha_b)

    # Demonstrate branch switching via git checkout and git switch
    run_git(tmpdir, "checkout", "topic", check=True)
    head_after_checkout = run_git(tmpdir, "symbolic-ref", "HEAD", check=True).stdout.strip()
    record_result("Branch switch: git checkout topic switches HEAD to refs/heads/topic",
                  head_after_checkout == "refs/heads/topic")

    run_git(tmpdir, "switch", "main", check=True)
    run_git(tmpdir, "switch", "topic", check=True)
    head_after_switch = run_git(tmpdir, "symbolic-ref", "HEAD", check=True).stdout.strip()
    record_result("Branch switch: git switch topic sets HEAD to refs/heads/topic",
                  head_after_switch == "refs/heads/topic")

    # Execute git rebase main
    run_git(tmpdir, "rebase", "main", check=True)
    rebased_b = run_git(tmpdir, "rev-parse", "HEAD", check=True).stdout.strip()

    # 1. State transition: commit object ID changed
    record_result("Rebase State 1: Rebased commit B' has different object ID from original B",
                  rebased_b != sha_b, f"Original: {sha_b}, Rebased: {rebased_b}")

    # 2. State transition: commit ancestry updated
    parent_of_b_prime = run_git(tmpdir, "rev-parse", "HEAD^", check=True).stdout.strip()
    record_result("Rebase State 2: Parent of rebased commit B' is commit C",
                  parent_of_b_prime == sha_c, f"Expected {sha_c}, got {parent_of_b_prime}")

    # 3. Branch references and HEAD
    main_after = run_git(tmpdir, "rev-parse", "refs/heads/main", check=True).stdout.strip()
    topic_after = run_git(tmpdir, "rev-parse", "refs/heads/topic", check=True).stdout.strip()
    record_result("Rebase State 3a: main branch ref remains unchanged at commit C", main_after == sha_c)
    record_result("Rebase State 3b: topic branch ref moved to rebased commit B'", topic_after == rebased_b)
    head_symref = run_git(tmpdir, "symbolic-ref", "HEAD", check=True).stdout.strip()
    record_result("Rebase State 3c: HEAD symbolic-ref is refs/heads/topic", head_symref == "refs/heads/topic")

    # 4. Working tree and index cleanliness and content
    status_proc = run_git(tmpdir, "status", "--porcelain", check=True)
    record_result("Rebase State 4a: Working tree and index are clean", status_proc.stdout.strip() == "")

    with open(os.path.join(tmpdir, "notes.txt")) as f:
        notes_content = f.read()
    with open(os.path.join(tmpdir, "todo.txt")) as f:
        todo_content = f.read()
    record_result("Rebase State 4b: Working tree files contain combined changes (notes.txt + todo.txt)",
                  notes_content == "alpha\nbeta\n" and todo_content == "one\n")


def verify_scenario_b_merge(tmpdir):
    print("--- Testing Scenario B: Merge ---")
    sha_a, sha_b, sha_c = setup_initial_history(tmpdir)

    # Assert initial refs
    main_before = run_git(tmpdir, "rev-parse", "refs/heads/main", check=True).stdout.strip()
    topic_before = run_git(tmpdir, "rev-parse", "refs/heads/topic", check=True).stdout.strip()
    record_result("Merge Init: main points to Commit C", main_before == sha_c)
    record_result("Merge Init: topic points to Commit B", topic_before == sha_b)

    # Demonstrate branch switching via git checkout and git switch
    run_git(tmpdir, "switch", "topic", check=True)
    run_git(tmpdir, "checkout", "main", check=True)
    head_after_checkout = run_git(tmpdir, "symbolic-ref", "HEAD", check=True).stdout.strip()
    record_result("Merge branch switch: git checkout main switches HEAD to refs/heads/main",
                  head_after_checkout == "refs/heads/main")

    # Execute git merge topic
    run_git(tmpdir, "merge", "topic", "-m", "Merge branch 'topic' into main", check=True)
    merge_sha = run_git(tmpdir, "rev-parse", "HEAD", check=True).stdout.strip()

    # 1. State transition: merge commit has both parents
    parents = run_git(tmpdir, "rev-parse", "HEAD^1", "HEAD^2", check=True).stdout.split()
    record_result("Merge State 1: Merge commit has exactly two parents (Parent 1: C, Parent 2: B)",
                  parents == [sha_c, sha_b], f"Expected {[sha_c, sha_b]}, got {parents}")

    # 2. State transition: original commit B preserved in ancestry
    is_b_ancestor = run_git(tmpdir, "merge-base", "--is-ancestor", sha_b, merge_sha, check=False).returncode == 0
    record_result("Merge State 2: Original commit B is preserved in commit ancestry", is_b_ancestor)

    # 3. Branch references and HEAD
    main_after = run_git(tmpdir, "rev-parse", "refs/heads/main", check=True).stdout.strip()
    topic_after = run_git(tmpdir, "rev-parse", "refs/heads/topic", check=True).stdout.strip()
    record_result("Merge State 3a: main branch ref points to merge commit", main_after == merge_sha)
    record_result("Merge State 3b: topic branch ref remains unchanged at original commit B", topic_after == sha_b)
    head_symref = run_git(tmpdir, "symbolic-ref", "HEAD", check=True).stdout.strip()
    record_result("Merge State 3c: HEAD symbolic-ref is refs/heads/main", head_symref == "refs/heads/main")

    # 4. Working tree and index cleanliness and content
    status_proc = run_git(tmpdir, "status", "--porcelain", check=True)
    record_result("Merge State 4a: Working tree and index are clean", status_proc.stdout.strip() == "")

    with open(os.path.join(tmpdir, "notes.txt")) as f:
        notes_content = f.read()
    with open(os.path.join(tmpdir, "todo.txt")) as f:
        todo_content = f.read()
    record_result("Merge State 4b: Working tree files contain combined changes (notes.txt + todo.txt)",
                  notes_content == "alpha\nbeta\n" and todo_content == "one\n")


def main():
    if os.environ.get("R03_T032_FORCE_FAIL") == "1":
        print("FORCED FAILURE TEST TRIGGERED (R03_T032_FORCE_FAIL=1)")
        record_result("Simulated failure assertion", False, "Environment variable R03_T032_FORCE_FAIL was set")
        sys.exit(1)

    print("================================================================")
    print("Starting automated verification: check.py (R03-T032)")
    print("================================================================")

    with tempfile.TemporaryDirectory() as tmp1:
        verify_scenario_a_rebase(tmp1)

    with tempfile.TemporaryDirectory() as tmp2:
        verify_scenario_b_merge(tmp2)

    print("================================================================")
    print(f"Summary: {PASS_COUNT} passed, {FAIL_COUNT} failed.")
    print("================================================================")

    if FAIL_COUNT > 0:
        sys.exit(1)
    print("ALL CHECKS PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
