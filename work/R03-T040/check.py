#!/usr/bin/env python3
"""
Automated verification script for Task R03-T040.
Implements a prediction-and-verification exercise for 'removing branch from your repository'.

Exercise structure:
  PREDICT: Before executing each command, state what will change (ref/index/worktree).
  EXECUTE: Run the command.
  VERIFY:  Assert the actual Git state matches the prediction.

Commands exercised (from guide anchors):
  - git checkout main
  - git merge <topic> main  (merge topic into main)
  - git branch -d <topic>   (delete merged branch)

Repository fixture:
  - Branch: main, Author: Course Student <student@example.invalid>
  - Commit A: notes.txt with "alpha\\n"
  - Commit B: notes.txt appended with "beta\\n"
  - Branch topic at Commit B
  - Commit C: todo.txt with "one\\n" on main
"""

import os
import shutil
import subprocess
import sys
import tempfile


def run_cmd(cmd, cwd, env=None, check=True):
    res = subprocess.run(
        cmd, cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    if check and res.returncode != 0:
        raise RuntimeError(f"Command {' '.join(cmd)} failed ({res.returncode}):\n{res.stderr}")
    return res


def main():
    if os.environ.get("R03_T040_FORCE_FAIL") == "1":
        print("FORCE_FAIL: Exiting with non-zero code due to R03_T040_FORCE_FAIL=1")
        sys.exit(1)

    temp_base = tempfile.mkdtemp(prefix="r03_t040_rm_branch_")
    passed = 0

    try:
        # Isolated environment
        fake_home = os.path.join(temp_base, "fake_home")
        os.makedirs(fake_home, exist_ok=True)
        env = os.environ.copy()
        env["HOME"] = fake_home
        env["GIT_CONFIG_GLOBAL"] = os.path.join(fake_home, ".gitconfig")
        for v in ["GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"]:
            env.pop(v, None)

        # ── Setup fixture ──────────────────────────────────────────────────────
        repo = os.path.join(temp_base, "repo")
        os.makedirs(repo)
        run_cmd(["git", "init", "-b", "main"], cwd=repo, env=env)
        run_cmd(["git", "config", "--local", "user.name", "Course Student"], cwd=repo, env=env)
        run_cmd(["git", "config", "--local", "user.email", "student@example.invalid"], cwd=repo, env=env)

        # Commit A
        with open(os.path.join(repo, "notes.txt"), "w") as f:
            f.write("alpha\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo, env=env)
        run_cmd(["git", "commit", "-m", "Commit A"], cwd=repo, env=env)
        commit_a = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env).stdout.strip()

        # Commit B
        with open(os.path.join(repo, "notes.txt"), "a") as f:
            f.write("beta\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo, env=env)
        run_cmd(["git", "commit", "-m", "Commit B"], cwd=repo, env=env)
        commit_b = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env).stdout.strip()

        # Create branch topic at B
        run_cmd(["git", "branch", "topic", commit_b], cwd=repo, env=env)

        # Commit C on main
        with open(os.path.join(repo, "todo.txt"), "w") as f:
            f.write("one\n")
        run_cmd(["git", "add", "todo.txt"], cwd=repo, env=env)
        run_cmd(["git", "commit", "-m", "Commit C"], cwd=repo, env=env)
        commit_c = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env).stdout.strip()

        print(f"Fixture: A={commit_a[:7]}  B={commit_b[:7]} [topic]  C={commit_c[:7]} [main]")

        # ── STEP 1: checkout topic to simulate having worked there ─────────────
        run_cmd(["git", "checkout", "topic"], cwd=repo, env=env)

        # ── EXERCISE 1: git checkout main ─────────────────────────────────────
        print("\n=== Exercise 1: git checkout main ===")
        print("PREDICT: HEAD moves from topic to main. Working tree gains todo.txt.")
        print("         Branch ref 'main' unchanged. 'topic' ref unchanged.")

        run_cmd(["git", "checkout", "main"], cwd=repo, env=env)

        # Verify prediction
        active = run_cmd(["git", "branch", "--show-current"], cwd=repo, env=env).stdout.strip()
        assert active == "main", f"Expected HEAD on 'main', got '{active}'"
        passed += 1
        print(f"Assertion {passed} passed: HEAD is now on 'main' (ref changed from topic → main).")

        head_sha = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env).stdout.strip()
        assert head_sha == commit_c, f"Expected HEAD={commit_c[:7]}, got {head_sha[:7]}"
        passed += 1
        print(f"Assertion {passed} passed: HEAD points to Commit C ({commit_c[:7]}) — no commit created.")

        assert os.path.exists(os.path.join(repo, "todo.txt")), "todo.txt must appear in working tree after checkout main"
        with open(os.path.join(repo, "todo.txt")) as f:
            assert f.read() == "one\n"
        passed += 1
        print(f"Assertion {passed} passed: Working tree now contains todo.txt with 'one\\n' (from Commit C).")

        # ── EXERCISE 2: git merge topic main ──────────────────────────────────
        # topic is at commit_b (ancestor of main's commit_c), so this is a no-op fast-forward already done
        print("\n=== Exercise 2: git merge topic main ===")
        print("PREDICT: 'topic' (B) is an ancestor of 'main' (C).")
        print("         Merge is already up-to-date; no new commit, no index change, no worktree change.")
        print("         'topic' ref still points to Commit B.")

        merge_res = run_cmd(["git", "merge", "topic", "main"], cwd=repo, env=env)

        main_after_merge = run_cmd(["git", "rev-parse", "main"], cwd=repo, env=env).stdout.strip()
        assert main_after_merge == commit_c, f"'main' moved unexpectedly after merge: {main_after_merge[:7]}"
        passed += 1
        print(f"Assertion {passed} passed: 'main' ref still at Commit C ({commit_c[:7]}) — already up-to-date, no new commit.")

        topic_after_merge = run_cmd(["git", "rev-parse", "topic"], cwd=repo, env=env).stdout.strip()
        assert topic_after_merge == commit_b, f"'topic' ref should remain at B; got {topic_after_merge[:7]}"
        passed += 1
        print(f"Assertion {passed} passed: 'topic' ref unchanged at Commit B ({commit_b[:7]}) — merge never touches the source branch ref.")

        clean = run_cmd(["git", "status", "--porcelain"], cwd=repo, env=env).stdout.strip()
        assert clean == "", f"Working tree/index not clean after up-to-date merge: '{clean}'"
        passed += 1
        print(f"Assertion {passed} passed: Working tree and index are clean — no changes from already-merged branch.")

        # ── EXERCISE 3: git branch -d topic ───────────────────────────────────
        print("\n=== Exercise 3: git branch -d topic ===")
        print("PREDICT: 'topic' ref is deleted from .git/refs/heads/ (or packed-refs).")
        print("         No commit objects are removed (Commit B is still reachable via main's history).")
        print("         HEAD, working tree, and index are unaffected.")

        run_cmd(["git", "branch", "-d", "topic"], cwd=repo, env=env)

        # Verify prediction: topic ref no longer exists
        topic_check = run_cmd(["git", "rev-parse", "--verify", "topic"], cwd=repo, env=env, check=False)
        assert topic_check.returncode != 0, "'topic' branch ref should no longer exist after -d"
        passed += 1
        print(f"Assertion {passed} passed: 'topic' ref deleted — git rev-parse --verify topic returns non-zero.")

        # Commit B object still reachable via main's ancestry
        reachable = run_cmd(["git", "cat-file", "-e", commit_b], cwd=repo, env=env, check=False)
        assert reachable.returncode == 0, f"Commit B ({commit_b[:7]}) object must still exist in object store"
        passed += 1
        print(f"Assertion {passed} passed: Commit B ({commit_b[:7]}) still exists in object store — deleting a branch never removes commit objects.")

        # HEAD and main still at commit C, working tree unchanged
        head_after_del = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env).stdout.strip()
        assert head_after_del == commit_c, f"HEAD changed unexpectedly after branch delete"
        passed += 1
        print(f"Assertion {passed} passed: HEAD still at Commit C ({commit_c[:7]}) — delete did not affect HEAD or working tree.")

        active_after_del = run_cmd(["git", "branch", "--show-current"], cwd=repo, env=env).stdout.strip()
        assert active_after_del == "main", f"Active branch changed after delete; got '{active_after_del}'"
        passed += 1
        print(f"Assertion {passed} passed: Active branch is still 'main' — branch deletion is ref-only.")

        print(f"\nAll {passed} assertions passed successfully!")

    finally:
        shutil.rmtree(temp_base, ignore_errors=True)


if __name__ == "__main__":
    main()
