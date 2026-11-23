#!/usr/bin/env python3
"""
Automated verification script for Task R03-T039.
Validates the explicit prerequisites for resetting a branch:
1. Active Branch Prerequisite: git reset operates on HEAD (must checkout base branch first).
2. Repository State & Staged Changes: Uncommitted changes get wiped by --hard; verify stash safety.
3. Target Branch Availability: Target branch must exist and point to valid commit.
4. Local Config Isolation: Ensure all git configs are strictly --local, leaving global config untouched.

Verifies:
- Repository setup with Course Student <student@example.invalid>:
  - Commit A (notes.txt with "alpha\n")
  - Commit B (notes.txt appended with "beta\n")
  - Branch topic at Commit B
  - Commit C (todo.txt with "one\n") on main
- Precondition checklist and state facts before and after git reset --hard main.
- Cleans temporary directory.
- Exits non-zero if R03_T039_FORCE_FAIL=1 or if assertions fail.
"""

import os
import shutil
import subprocess
import sys
import tempfile


def run_cmd(cmd, cwd, env=None, check=True):
    res = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and res.returncode != 0:
        raise RuntimeError(f"Command {' '.join(cmd)} failed ({res.returncode}):\n{res.stderr}")
    return res


def main():
    if os.environ.get("R03_T039_FORCE_FAIL") == "1":
        print("FORCE_FAIL: Exiting with non-zero code due to R03_T039_FORCE_FAIL=1")
        sys.exit(1)

    temp_base = tempfile.mkdtemp(prefix="r03_t039_reset_")
    passed_assertions = 0

    try:
        # Isolated mock HOME and GIT_CONFIG_GLOBAL to guarantee global config is untouched
        fake_home = os.path.join(temp_base, "fake_home")
        os.makedirs(fake_home, exist_ok=True)
        fake_global_config = os.path.join(fake_home, ".gitconfig")

        test_env = os.environ.copy()
        test_env["HOME"] = fake_home
        test_env["GIT_CONFIG_GLOBAL"] = fake_global_config
        for var in ["GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"]:
            test_env.pop(var, None)

        repo_dir = os.path.join(temp_base, "repo")
        os.makedirs(repo_dir)

        # 1. Initialize local repository
        run_cmd(["git", "init", "-b", "main"], cwd=repo_dir, env=test_env)

        # Prerequisite 4: Local config isolation (strictly --local)
        run_cmd(["git", "config", "--local", "user.name", "Course Student"], cwd=repo_dir, env=test_env)
        run_cmd(["git", "config", "--local", "user.email", "student@example.invalid"], cwd=repo_dir, env=test_env)

        # Assert global config file does not exist or has no user config
        global_check = run_cmd(["git", "config", "--global", "--list"], cwd=repo_dir, env=test_env, check=False)
        assert "user.name" not in global_check.stdout, "Global config must not contain local user.name"
        assert "user.email" not in global_check.stdout, "Global config must not contain local user.email"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: Per-repository config is strictly local; global config untouched.")

        # 2. Base fixture creation
        # Commit A: creates notes.txt with "alpha\n"
        with open(os.path.join(repo_dir, "notes.txt"), "w") as f:
            f.write("alpha\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo_dir, env=test_env)
        run_cmd(["git", "commit", "-m", "Commit A"], cwd=repo_dir, env=test_env)
        commit_a = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=test_env).stdout.strip()

        # Commit B: appends "beta\n"
        with open(os.path.join(repo_dir, "notes.txt"), "a") as f:
            f.write("beta\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo_dir, env=test_env)
        run_cmd(["git", "commit", "-m", "Commit B"], cwd=repo_dir, env=test_env)
        commit_b = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=test_env).stdout.strip()

        # Create branch topic at B
        run_cmd(["git", "branch", "topic", commit_b], cwd=repo_dir, env=test_env)

        # Commit C: adds todo.txt with "one\n" on main
        with open(os.path.join(repo_dir, "todo.txt"), "w") as f:
            f.write("one\n")
        run_cmd(["git", "add", "todo.txt"], cwd=repo_dir, env=test_env)
        run_cmd(["git", "commit", "-m", "Commit C"], cwd=repo_dir, env=test_env)
        commit_c = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=test_env).stdout.strip()

        print(f"Base setup created: Commit A={commit_a[:7]}, B={commit_b[:7]} (topic), C={commit_c[:7]} (main)")

        # -----------------------------------------------------------------
        # Verify Prerequisites Checklist for resetting 'topic' to match 'main'
        # -----------------------------------------------------------------

        # Prerequisite 1: Active branch must be the branch to be reset
        run_cmd(["git", "checkout", "topic"], cwd=repo_dir, env=test_env)
        active_branch = run_cmd(["git", "branch", "--show-current"], cwd=repo_dir, env=test_env).stdout.strip()
        assert active_branch == "topic", f"Expected active branch 'topic', got {active_branch}"
        topic_before = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=test_env).stdout.strip()
        assert topic_before == commit_b, f"topic expected at {commit_b}, got {topic_before}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: Prerequisite 1 verified - Checked out active branch 'topic' at {commit_b[:7]}.")

        # Prerequisite 2: Working directory & Staged changes state
        # Create uncommitted staged changes to demonstrate precondition check
        with open(os.path.join(repo_dir, "draft.txt"), "w") as f:
            f.write("uncommitted work\n")
        run_cmd(["git", "add", "draft.txt"], cwd=repo_dir, env=test_env)

        status_check = run_cmd(["git", "status", "--porcelain"], cwd=repo_dir, env=test_env).stdout.strip()
        assert "A  draft.txt" in status_check, "Expected staged change draft.txt"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: Prerequisite 2 verified - Detected staged changes before reset.")

        # Stash uncommitted changes to protect them from reset --hard
        run_cmd(["git", "stash", "push", "-u", "-m", "pre-reset backup"], cwd=repo_dir, env=test_env)
        clean_status = run_cmd(["git", "status", "--porcelain"], cwd=repo_dir, env=test_env).stdout.strip()
        assert clean_status == "", f"Working tree not clean after stash: {clean_status}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: Working tree and staging area successfully secured and cleaned via stash.")

        # Prerequisite 3: Target branch availability check
        target_check = run_cmd(["git", "rev-parse", "--verify", "main"], cwd=repo_dir, env=test_env).stdout.strip()
        assert target_check == commit_c, f"Target branch 'main' expected at {commit_c}, got {target_check}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: Prerequisite 3 verified - Target branch 'main' resolves to {commit_c[:7]}.")

        # -----------------------------------------------------------------
        # Execute Reset: git reset --hard main
        # -----------------------------------------------------------------
        reset_res = run_cmd(["git", "reset", "--hard", "main"], cwd=repo_dir, env=test_env)
        assert reset_res.returncode == 0, "git reset --hard main failed"

        # Assert meaningful state facts after reset:
        # Fact 1: Active branch 'topic' now points to Commit C
        topic_after = run_cmd(["git", "rev-parse", "topic"], cwd=repo_dir, env=test_env).stdout.strip()
        assert topic_after == commit_c, f"Expected topic at {commit_c}, got {topic_after}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: State Fact 1 - topic branch now points to Commit C ({commit_c[:7]}).")

        # Fact 2: todo.txt from Commit C is present in working tree with content "one\n"
        todo_path = os.path.join(repo_dir, "todo.txt")
        assert os.path.exists(todo_path), "todo.txt should exist after resetting to main"
        with open(todo_path) as f:
            todo_content = f.read()
        assert todo_content == "one\n", f"Expected 'one\\n', got {repr(todo_content)}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: State Fact 2 - Working tree file 'todo.txt' has content from Commit C ('one\\n').")

        # Fact 3: Working tree and index are clean
        final_status = run_cmd(["git", "status", "--porcelain"], cwd=repo_dir, env=test_env).stdout.strip()
        assert final_status == "", f"Expected clean working tree, got: {final_status}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: State Fact 3 - Staging area and working directory are completely clean.")

        # Fact 4: Stashed backup is preserved
        stash_list = run_cmd(["git", "stash", "list"], cwd=repo_dir, env=test_env).stdout.strip()
        assert "pre-reset backup" in stash_list, "Stash backup was lost"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: State Fact 4 - Pre-reset stash backup is safely preserved in stash stack.")

        print(f"\nAll {passed_assertions} assertions passed successfully!")

    finally:
        shutil.rmtree(temp_base, ignore_errors=True)


if __name__ == "__main__":
    main()
