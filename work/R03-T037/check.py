#!/usr/bin/env python3
"""
Automated verification script for Task R03-T037.
Diagnoses real command failures for 'keeping your fork synced with this repository':
1. Violated precondition on `git remote add upstream`:
   Failure: Remote 'upstream' already exists in repository configuration.
   Exit code: Nonzero (128).
   Smallest correction: `git remote set-url upstream <url>`
2. Violated precondition on `git checkout main`:
   Failure: Untracked working tree file conflicts with file tracked on 'main'.
   Exit code: Nonzero (1).
   Smallest correction: `git stash -u` before `git checkout main`.

Verifies states dynamically without hard-coding hashes or fragile byte-for-byte strings.
Supports R03_T037_FORCE_FAIL=1 for negative verification.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile


def run_cmd(cmd, cwd, check=True):
    res = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed ({res.returncode}): {' '.join(cmd)}\nStderr: {res.stderr}")
    return res


def main():
    if os.environ.get("R03_T037_FORCE_FAIL") == "1":
        print("FORCE_FAIL: Intentionally exiting with non-zero exit code as requested by R03_T037_FORCE_FAIL=1")
        sys.exit(1)

    temp_base = tempfile.mkdtemp(prefix="r03_t037_sync_")
    passed_assertions = 0

    try:
        # Create bare upstream repository
        upstream_dir = os.path.join(temp_base, "upstream.git")
        run_cmd(["git", "init", "--bare", upstream_dir], cwd=temp_base)

        # Create secondary bare upstream repository for URL reconfiguration
        upstream_v2_dir = os.path.join(temp_base, "upstream_v2.git")
        run_cmd(["git", "init", "--bare", upstream_v2_dir], cwd=temp_base)

        # Setup local working repository
        repo_dir = os.path.join(temp_base, "repo")
        os.makedirs(repo_dir)
        run_cmd(["git", "init", "-b", "main"], cwd=repo_dir)

        # Configure author & committer
        env_vars = {
            "GIT_AUTHOR_NAME": "Course Student",
            "GIT_AUTHOR_EMAIL": "student@example.invalid",
            "GIT_COMMITTER_NAME": "Course Student",
            "GIT_COMMITTER_EMAIL": "student@example.invalid",
        }
        for k, v in env_vars.items():
            os.environ[k] = v
        run_cmd(["git", "config", "user.name", "Course Student"], cwd=repo_dir)
        run_cmd(["git", "config", "user.email", "student@example.invalid"], cwd=repo_dir)

        # Commit A: creates notes.txt with "alpha\n"
        with open(os.path.join(repo_dir, "notes.txt"), "w") as f:
            f.write("alpha\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo_dir)
        run_cmd(["git", "commit", "-m", "Commit A"], cwd=repo_dir)
        commit_a = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir).stdout.strip()

        # Commit B: appends "beta\n"
        with open(os.path.join(repo_dir, "notes.txt"), "a") as f:
            f.write("beta\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo_dir)
        run_cmd(["git", "commit", "-m", "Commit B"], cwd=repo_dir)
        commit_b = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir).stdout.strip()

        # Create branch topic at B
        run_cmd(["git", "branch", "topic", commit_b], cwd=repo_dir)

        # Commit C: adds todo.txt with "one\n"
        with open(os.path.join(repo_dir, "todo.txt"), "w") as f:
            f.write("one\n")
        run_cmd(["git", "add", "todo.txt"], cwd=repo_dir)
        run_cmd(["git", "commit", "-m", "Commit C"], cwd=repo_dir)
        commit_c = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir).stdout.strip()

        # Push main to upstream bare repository to simulate public remote
        upstream_url_v1 = f"file://{upstream_dir}"
        run_cmd(["git", "remote", "add", "upstream", upstream_url_v1], cwd=repo_dir)
        run_cmd(["git", "push", "upstream", "main"], cwd=repo_dir)

        print("=== Base Fixture Initialized ===")
        print(f"Commit A: {commit_a}")
        print(f"Commit B: {commit_b}")
        print(f"Commit C: {commit_c}")

        # -------------------------------------------------------------
        # Scenario 1: Precondition violation on `git remote add upstream`
        # -------------------------------------------------------------
        print("\n--- Testing Scenario 1: Remote upstream already exists ---")
        upstream_url_v2 = f"file://{upstream_v2_dir}"

        # Bad case: attempting to add 'upstream' when it already exists
        bad_add = run_cmd(["git", "remote", "add", "upstream", upstream_url_v2], cwd=repo_dir, check=False)
        assert bad_add.returncode != 0, "Expected non-zero return code when adding existing remote"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: 'git remote add upstream' failed with return code {bad_add.returncode}")

        # Diagnostic message check (case-insensitive regex, version agnostic)
        assert re.search(r"remote\s+upstream\s+already\s+exists", bad_add.stderr, re.IGNORECASE), (
            f"Stderr did not match expected pattern: {bad_add.stderr}"
        )
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: error diagnostic confirms remote 'upstream' already exists")

        # State check: remote URL is unchanged
        current_url = run_cmd(["git", "remote", "get-url", "upstream"], cwd=repo_dir).stdout.strip()
        assert current_url == upstream_url_v1, f"Expected remote URL to remain {upstream_url_v1}, got {current_url}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: upstream remote URL remained unchanged after failed command")

        # Correction: use `git remote set-url upstream <url>`
        repaired_set = run_cmd(["git", "remote", "set-url", "upstream", upstream_url_v2], cwd=repo_dir, check=True)
        assert repaired_set.returncode == 0, "git remote set-url upstream must succeed"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: 'git remote set-url upstream' succeeded with exit code 0")

        # State check: remote URL is now updated
        updated_url = run_cmd(["git", "remote", "get-url", "upstream"], cwd=repo_dir).stdout.strip()
        assert updated_url == upstream_url_v2, f"Expected remote URL to be updated to {upstream_url_v2}, got {updated_url}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: upstream remote URL successfully updated to new target")

        # Restore upstream URL to upstream_url_v1 for sync demonstration
        run_cmd(["git", "remote", "set-url", "upstream", upstream_url_v1], cwd=repo_dir)

        # -------------------------------------------------------------
        # Scenario 2: Precondition violation on `git checkout main`
        # -------------------------------------------------------------
        print("\n--- Testing Scenario 2: Checkout collision from topic to main ---")
        # Switch to branch topic
        run_cmd(["git", "checkout", "topic"], cwd=repo_dir)
        current_branch = run_cmd(["git", "branch", "--show-current"], cwd=repo_dir).stdout.strip()
        assert current_branch == "topic", f"Expected branch 'topic', got {current_branch}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: successfully switched to branch 'topic'")

        # Create conflicting untracked todo.txt in topic
        # (todo.txt was introduced in commit C on main, but does not exist in commit B on topic)
        conflicting_content = "local uncommitted draft notes\n"
        with open(os.path.join(repo_dir, "todo.txt"), "w") as f:
            f.write(conflicting_content)

        # Bad case: attempting checkout main with conflicting untracked file
        bad_checkout = run_cmd(["git", "checkout", "main"], cwd=repo_dir, check=False)
        assert bad_checkout.returncode != 0, "Expected checkout main to fail due to conflicting untracked file"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: 'git checkout main' failed with return code {bad_checkout.returncode}")

        # Diagnostic message check
        assert re.search(r"overwritten by checkout", bad_checkout.stderr, re.IGNORECASE), (
            f"Stderr did not match expected collision message: {bad_checkout.stderr}"
        )
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: error diagnostic confirms untracked file overwrite collision")

        # State check: still on topic, todo.txt content intact
        branch_after_fail = run_cmd(["git", "branch", "--show-current"], cwd=repo_dir).stdout.strip()
        assert branch_after_fail == "topic", f"Expected to remain on topic, got {branch_after_fail}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: branch remained 'topic' after failed checkout")

        with open(os.path.join(repo_dir, "todo.txt")) as f:
            read_draft = f.read()
        assert read_draft == conflicting_content, "Local draft content was altered or lost"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: local untracked file content was preserved untouched")

        # Smallest correction: stash untracked files with `git stash -u`
        stash_res = run_cmd(["git", "stash", "push", "-u", "-m", "wip topic draft"], cwd=repo_dir, check=True)
        assert stash_res.returncode == 0, "git stash push -u failed"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: 'git stash push -u' succeeded")

        # Repaired checkout: now switch to main succeeds
        repaired_checkout = run_cmd(["git", "checkout", "main"], cwd=repo_dir, check=True)
        assert repaired_checkout.returncode == 0, "git checkout main failed after stashing"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: 'git checkout main' succeeded after stashing")

        # State check: on main, todo.txt contains commit C's content
        final_branch = run_cmd(["git", "branch", "--show-current"], cwd=repo_dir).stdout.strip()
        assert final_branch == "main", f"Expected to be on 'main', got {final_branch}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: active branch is now 'main'")

        with open(os.path.join(repo_dir, "todo.txt")) as f:
            main_todo = f.read()
        assert main_todo == "one\n", f"Expected todo.txt to contain 'one\\n', got {repr(main_todo)}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: todo.txt on 'main' reflects commit C ('one\\n')")

        # Verify stash list records the stashed draft
        stash_list = run_cmd(["git", "stash", "list"], cwd=repo_dir).stdout.strip()
        assert "wip topic draft" in stash_list, f"Stash list does not contain saved draft: {stash_list}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: saved changes securely tracked in git stash")

        print(f"\nAll {passed_assertions} assertions passed successfully!")

    finally:
        shutil.rmtree(temp_base, ignore_errors=True)


if __name__ == "__main__":
    main()
