#!/usr/bin/env python3
"""
Automated verification script for Task R03-T038.
Turns 'installing git arch' into an isolated integration check with explicit
assertions about Git state.

Verifies:
1. Git version output pattern (dynamic version check).
2. Setting global user.name and user.email in an isolated test environment.
3. Verification of git config list and values.
4. Repository setup with Course Student <student@example.invalid>:
   - Commit A (notes.txt with "alpha\n")
   - Commit B (notes.txt appended with "beta\n")
   - Branch topic at Commit B
   - Commit C (todo.txt with "one\n") on main
5. Commit author metadata inheritance from configured user.name and user.email.
6. Decisive command omission test: fails when decisive configuration is omitted.
7. Proper cleanup of temporary directories and propagation of child failures.
"""

import os
import re
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


def run_verification(omit_decisive=False):
    temp_dir = tempfile.mkdtemp(prefix="r03_t038_arch_")
    passed_assertions = 0

    try:
        # Isolated HOME and gitconfig
        fake_home = os.path.join(temp_dir, "fake_home")
        os.makedirs(fake_home, exist_ok=True)
        fake_config = os.path.join(fake_home, ".gitconfig")

        test_env = os.environ.copy()
        test_env["HOME"] = fake_home
        test_env["GIT_CONFIG_GLOBAL"] = fake_config
        for var in ["GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"]:
            test_env.pop(var, None)

        # 1. Verify git version
        ver_res = run_cmd(["git", "--version"], cwd=temp_dir, env=test_env)
        assert ver_res.returncode == 0, "git --version failed"
        assert re.search(r"git version \d+\.\d+", ver_res.stdout), f"Invalid version string: {ver_res.stdout}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: git --version successfully checked ({ver_res.stdout.strip()})")

        # 2. Setup guide repository fixture
        repo_dir = os.path.join(temp_dir, "repo")
        os.makedirs(repo_dir)
        run_cmd(["git", "init", "-b", "main"], cwd=repo_dir, env=test_env)

        author_name = "Course Student"
        author_email = "student@example.invalid"

        if not omit_decisive:
            # Guide's decisive commands: git config --global user.name & user.email
            run_cmd(["git", "config", "--global", "user.name", author_name], cwd=repo_dir, env=test_env)
            run_cmd(["git", "config", "--global", "user.email", author_email], cwd=repo_dir, env=test_env)
        else:
            print("Note: Deliberately omitting decisive commands (git config --global user.name/email)...")

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

        # Commit C: adds todo.txt with "one\n"
        with open(os.path.join(repo_dir, "todo.txt"), "w") as f:
            f.write("one\n")
        run_cmd(["git", "add", "todo.txt"], cwd=repo_dir, env=test_env)
        run_cmd(["git", "commit", "-m", "Commit C"], cwd=repo_dir, env=test_env)
        commit_c = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=test_env).stdout.strip()

        # State check: Verify branches and commit lineage
        topic_commit = run_cmd(["git", "rev-parse", "topic"], cwd=repo_dir, env=test_env).stdout.strip()
        main_commit = run_cmd(["git", "rev-parse", "main"], cwd=repo_dir, env=test_env).stdout.strip()
        assert topic_commit == commit_b, f"Expected topic at {commit_b}, got {topic_commit}"
        assert main_commit == commit_c, f"Expected main at {commit_c}, got {main_commit}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: Commit lineage verified (topic at B={commit_b[:7]}, main at C={commit_c[:7]})")

        # Verify git config list
        list_res = run_cmd(["git", "config", "--list"], cwd=repo_dir, env=test_env)
        assert f"user.name={author_name}" in list_res.stdout, f"Missing user.name in config list: {list_res.stdout}"
        assert f"user.email={author_email}" in list_res.stdout, f"Missing user.email in config list: {list_res.stdout}"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: git config --list contains expected user.name and user.email")

        # Verify git log author attribution embeds the configured identity
        author_res = run_cmd(["git", "log", "-1", "--format=%an <%ae>"], cwd=repo_dir, env=test_env)
        expected_author = f"{author_name} <{author_email}>"
        assert author_res.stdout.strip() == expected_author, f"Expected '{expected_author}', got '{author_res.stdout.strip()}'"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: Commit author attribution matches configured user.name and email")

        # Verify credential helper configuration from guide
        run_cmd(["git", "config", "--global", "credential.helper", "cache"], cwd=repo_dir, env=test_env)
        helper_val = run_cmd(["git", "config", "--global", "credential.helper"], cwd=repo_dir, env=test_env).stdout.strip()
        assert helper_val == "cache", f"Expected credential.helper 'cache', got '{helper_val}'"
        passed_assertions += 1
        print(f"Assertion {passed_assertions} passed: credential.helper successfully configured and verified as 'cache'")

        return passed_assertions
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    if os.environ.get("R03_T038_FORCE_FAIL") == "1":
        print("FORCE_FAIL: Exiting with non-zero code due to R03_T038_FORCE_FAIL=1")
        sys.exit(1)

    if os.environ.get("R03_T038_INTERNAL_OMIT") == "1":
        # Internal worker to test decisive omission failure
        run_verification(omit_decisive=True)
        return

    print("=== Running Integration Check for Guide: installing-git-arch ===")
    total_passed = run_verification(omit_decisive=False)
    print(f"\nIntegration check passed: {total_passed} state assertions verified.")

    # Verify omission test: verify that omitting decisive command fails as required
    print("\n--- Testing Decisive Command Omission ---")
    sub_env = os.environ.copy()
    sub_env["R03_T038_INTERNAL_OMIT"] = "1"
    proc = subprocess.run(
        [sys.executable, __file__],
        env=sub_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.returncode != 0, "Omission test should have failed with non-zero exit code"
    print("Omission test successfully failed when decisive command was omitted (exit code != 0).")
    print("\nAll integration checks and failure propagation tests completed successfully!")


if __name__ == "__main__":
    main()
