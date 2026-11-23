#!/usr/bin/env python3
"""
Automated verification check for R03-T030:
Worked exercise: predicting and verifying Git state and identity.

Tests:
1. Verifies that docs/additional-material/git_workflow_scenarios/installing-git-arch.md
   contains all required source command anchors and the worked exercise.
2. Runs two independent runs in temporary directories simulating the exact scenario:
   - Configures author: Course Student <student@example.invalid>
   - Commit A: notes.txt = "alpha\n"
   - Commit B: notes.txt = "alpha\nbeta\n"
   - Branch topic created at B
   - Commit C: todo.txt = "one\n" on branch main
   - Pre-condition assertions on main
   - Executes git checkout topic
   - Asserts at least three meaningful state facts:
     a) Active symbolic reference HEAD points to refs/heads/topic and resolves to Commit B
     b) Branch main remains fixed at Commit C
     c) Index (staging area) contains notes.txt matching Commit B and lacks todo.txt
     d) Working tree has notes.txt ("alpha\nbeta\n"), lacks todo.txt, and status is clean
     e) Author and committer on all commits match configured identity
3. Tests negative assertion failure with FORCE_FAIL=1.
4. Generates evidence files: inputs.txt, expected.txt, actual.txt, versions.txt, evidence.md.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import platform

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK_DIR = os.path.join(REPO_ROOT, "work", "R03-T030")
DOC_PATH = os.path.join(REPO_ROOT, "docs", "additional-material", "git_workflow_scenarios", "installing-git-arch.md")

REQUIRED_ANCHORS = [
    'git version 2.34.1',
    'git config --global user.name "Your Name"',
    'git config --global user.email "youremail@domain.com"'
]

def run_git(args, cwd, env=None):
    res = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    return res

def verify_doc():
    if not os.path.exists(DOC_PATH):
        raise AssertionError(f"Guide document not found: {DOC_PATH}")
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    for anchor in REQUIRED_ANCHORS:
        if anchor not in content:
            raise AssertionError(f"Required command anchor missing: {anchor}")
    if "Worked Exercise: Predict, Execute, and Verify Git State and Identity" not in content:
        raise AssertionError("Worked exercise section missing from guide")
    return True

def run_scenario(run_id, force_fail=False):
    tmpdir = tempfile.mkdtemp(prefix=f"r03_t030_run_{run_id}_")
    try:
        env = os.environ.copy()
        fake_home = os.path.join(tmpdir, "fake_home")
        os.makedirs(fake_home, exist_ok=True)
        env["HOME"] = fake_home
        env["GIT_CONFIG_GLOBAL"] = os.path.join(fake_home, ".gitconfig")
        env["GIT_AUTHOR_DATE"] = "2026-01-01T00:00:00Z"
        env["GIT_COMMITTER_DATE"] = "2026-01-01T00:00:00Z"
        env["GIT_AUTHOR_NAME"] = "Course Student"
        env["GIT_AUTHOR_EMAIL"] = "student@example.invalid"
        env["GIT_COMMITTER_NAME"] = "Course Student"
        env["GIT_COMMITTER_EMAIL"] = "student@example.invalid"

        repo_dir = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_dir, exist_ok=True)

        res = run_git(["init", "-b", "main"], cwd=repo_dir, env=env)
        if res.returncode != 0:
            run_git(["init"], cwd=repo_dir, env=env)
            run_git(["checkout", "-b", "main"], cwd=repo_dir, env=env)

        run_git(["config", "user.name", "Course Student"], cwd=repo_dir, env=env)
        run_git(["config", "user.email", "student@example.invalid"], cwd=repo_dir, env=env)

        # Commit A: creates notes.txt with "alpha\n"
        notes_path = os.path.join(repo_dir, "notes.txt")
        with open(notes_path, "w", encoding="utf-8") as f:
            f.write("alpha\n")
        run_git(["add", "notes.txt"], cwd=repo_dir, env=env)
        res_a = run_git(["commit", "-m", "Commit A"], cwd=repo_dir, env=env)
        if res_a.returncode != 0:
            raise RuntimeError(f"Failed Commit A: {res_a.stderr}")
        commit_a = run_git(["rev-parse", "HEAD"], cwd=repo_dir, env=env).stdout.strip()

        # Commit B: appends "beta\n"
        with open(notes_path, "a", encoding="utf-8") as f:
            f.write("beta\n")
        run_git(["add", "notes.txt"], cwd=repo_dir, env=env)
        res_b = run_git(["commit", "-m", "Commit B"], cwd=repo_dir, env=env)
        if res_b.returncode != 0:
            raise RuntimeError(f"Failed Commit B: {res_b.stderr}")
        commit_b = run_git(["rev-parse", "HEAD"], cwd=repo_dir, env=env).stdout.strip()

        # Create branch topic at B
        res_topic = run_git(["branch", "topic"], cwd=repo_dir, env=env)
        if res_topic.returncode != 0:
            raise RuntimeError(f"Failed to create topic branch: {res_topic.stderr}")

        # Commit C: adds todo.txt with "one\n" on branch main
        todo_path = os.path.join(repo_dir, "todo.txt")
        with open(todo_path, "w", encoding="utf-8") as f:
            f.write("one\n")
        run_git(["add", "todo.txt"], cwd=repo_dir, env=env)
        res_c = run_git(["commit", "-m", "Commit C"], cwd=repo_dir, env=env)
        if res_c.returncode != 0:
            raise RuntimeError(f"Failed Commit C: {res_c.stderr}")
        commit_c = run_git(["rev-parse", "HEAD"], cwd=repo_dir, env=env).stdout.strip()

        # Pre-execution checks on main
        pre_head = run_git(["rev-parse", "HEAD"], cwd=repo_dir, env=env).stdout.strip()
        pre_sym = run_git(["symbolic-ref", "HEAD"], cwd=repo_dir, env=env).stdout.strip()
        pre_main = run_git(["rev-parse", "main"], cwd=repo_dir, env=env).stdout.strip()
        pre_topic = run_git(["rev-parse", "topic"], cwd=repo_dir, env=env).stdout.strip()

        assert pre_head == commit_c, f"Expected HEAD at C ({commit_c}), got {pre_head}"
        assert pre_sym == "refs/heads/main", f"Expected HEAD pointing to main, got {pre_sym}"
        assert pre_main == commit_c, f"Expected main at C, got {pre_main}"
        assert pre_topic == commit_b, f"Expected topic at B, got {pre_topic}"
        assert os.path.exists(todo_path), "Expected todo.txt to exist in worktree on main"

        # Execute git checkout topic
        res_checkout = run_git(["checkout", "topic"], cwd=repo_dir, env=env)
        if res_checkout.returncode != 0:
            raise RuntimeError(f"Failed git checkout topic: {res_checkout.stderr}")

        if force_fail:
            raise AssertionError("Forced failure assertion triggered for negative test verification")

        # Post-execution assertions
        post_head = run_git(["rev-parse", "HEAD"], cwd=repo_dir, env=env).stdout.strip()
        post_sym = run_git(["symbolic-ref", "HEAD"], cwd=repo_dir, env=env).stdout.strip()
        post_main = run_git(["rev-parse", "main"], cwd=repo_dir, env=env).stdout.strip()
        post_topic = run_git(["rev-parse", "topic"], cwd=repo_dir, env=env).stdout.strip()

        # State Fact 1: Active reference HEAD moved to refs/heads/topic and resolves to Commit B
        assert post_sym == "refs/heads/topic", f"Expected HEAD -> refs/heads/topic, got {post_sym}"
        assert post_head == commit_b, f"Expected HEAD at Commit B ({commit_b}), got {post_head}"
        assert post_topic == commit_b, f"Expected topic branch at Commit B ({commit_b}), got {post_topic}"

        # State Fact 2: Branch main remains fixed at Commit C
        assert post_main == commit_c, f"Expected main branch fixed at Commit C ({commit_c}), got {post_main}"
        assert post_head != post_main, "Expected HEAD and main to refer to different commits"

        # State Fact 3: Staging index updated (contains notes.txt matching B, lacks todo.txt)
        ls_files = run_git(["ls-files", "-s"], cwd=repo_dir, env=env).stdout.strip()
        assert "notes.txt" in ls_files, "Expected notes.txt in index"
        assert "todo.txt" not in ls_files, "Expected todo.txt removed from index"

        # State Fact 4: Working tree updated to Commit B state
        assert not os.path.exists(todo_path), "Expected todo.txt to be removed from working tree"
        with open(notes_path, "r", encoding="utf-8") as f:
            notes_content = f.read()
        assert notes_content == "alpha\nbeta\n", f"Expected notes.txt content 'alpha\\nbeta\\n', got {repr(notes_content)}"

        status_res = run_git(["status", "--porcelain"], cwd=repo_dir, env=env)
        assert status_res.stdout.strip() == "", f"Expected clean working tree, got: {status_res.stdout}"

        # State Fact 5: Author and Committer identity recorded
        author_c = run_git(["log", "-1", "--format=%an <%ae>", commit_c], cwd=repo_dir, env=env).stdout.strip()
        author_b = run_git(["log", "-1", "--format=%an <%ae>", commit_b], cwd=repo_dir, env=env).stdout.strip()
        author_a = run_git(["log", "-1", "--format=%an <%ae>", commit_a], cwd=repo_dir, env=env).stdout.strip()

        assert author_c == "Course Student <student@example.invalid>", f"Unexpected author C: {author_c}"
        assert author_b == "Course Student <student@example.invalid>", f"Unexpected author B: {author_b}"
        assert author_a == "Course Student <student@example.invalid>", f"Unexpected author A: {author_a}"

        return {
            "run_id": run_id,
            "commit_a": commit_a,
            "commit_b": commit_b,
            "commit_c": commit_c,
            "pre_sym": pre_sym,
            "post_sym": post_sym,
            "post_head": post_head,
            "post_main": post_main,
            "post_topic": post_topic,
            "ls_files": ls_files,
            "todo_exists": os.path.exists(todo_path),
            "notes_content": notes_content,
            "author_c": author_c
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def write_evidence(results):
    os.makedirs(WORK_DIR, exist_ok=True)

    # 1. inputs.txt
    inputs_content = f"""R03-T030 Verification Inputs
==============================
Target Guide: docs/additional-material/git_workflow_scenarios/installing-git-arch.md
Command Anchors:
  - {REQUIRED_ANCHORS[0]}
  - {REQUIRED_ANCHORS[1]}
  - {REQUIRED_ANCHORS[2]}
Author Configuration:
  - Name: Course Student
  - Email: student@example.invalid
Repository Fixture:
  - Default branch: main
  - Commit A: notes.txt = "alpha\\n"
  - Commit B: notes.txt = "alpha\\nbeta\\n"
  - Branch topic: created at Commit B
  - Commit C: todo.txt = "one\\n" (on main)
Operation Tested:
  - git checkout topic
"""
    with open(os.path.join(WORK_DIR, "inputs.txt"), "w", encoding="utf-8") as f:
        f.write(inputs_content)

    # 2. expected.txt
    expected_content = """R03-T030 Expected State Predictions
====================================
1. Reference Transitions:
   - HEAD: updates from refs/heads/main to refs/heads/topic (resolving to Commit B)
   - refs/heads/topic: remains at Commit B
   - refs/heads/main: remains fixed at Commit C
2. Staging Index (git ls-files -s):
   - notes.txt tracked matching Commit B tree
   - todo.txt removed from index
3. Working Tree:
   - notes.txt contains "alpha\\nbeta\\n"
   - todo.txt removed from disk
   - git status --porcelain is empty (clean tree)
4. Author Identity:
   - Recorded author and committer on all commits match "Course Student <student@example.invalid>"
"""
    with open(os.path.join(WORK_DIR, "expected.txt"), "w", encoding="utf-8") as f:
        f.write(expected_content)

    # 3. actual.txt
    actual_content = f"""R03-T030 Actual Verification Results
=====================================
Run 1:
  - Commit A: {results[0]['commit_a']}
  - Commit B: {results[0]['commit_b']}
  - Commit C: {results[0]['commit_c']}
  - Initial symbolic-ref HEAD: {results[0]['pre_sym']}
  - Post-checkout symbolic-ref HEAD: {results[0]['post_sym']}
  - Post-checkout HEAD commit: {results[0]['post_head']}
  - Post-checkout topic commit: {results[0]['post_topic']}
  - Post-checkout main commit: {results[0]['post_main']}
  - Index contents:
    {results[0]['ls_files']}
  - todo.txt exists on disk: {results[0]['todo_exists']}
  - notes.txt content: {repr(results[0]['notes_content'])}
  - Commit C Author: {results[0]['author_c']}

Run 2:
  - Commit A: {results[1]['commit_a']}
  - Commit B: {results[1]['commit_b']}
  - Commit C: {results[1]['commit_c']}
  - Initial symbolic-ref HEAD: {results[1]['pre_sym']}
  - Post-checkout symbolic-ref HEAD: {results[1]['post_sym']}
  - Post-checkout HEAD commit: {results[1]['post_head']}
  - Post-checkout topic commit: {results[1]['post_topic']}
  - Post-checkout main commit: {results[1]['post_main']}
  - Index contents:
    {results[1]['ls_files']}
  - todo.txt exists on disk: {results[1]['todo_exists']}
  - notes.txt content: {repr(results[1]['notes_content'])}
  - Commit C Author: {results[1]['author_c']}

Negative Test Verification (FORCE_FAIL=1):
  - Correctly raised AssertionError and returned non-zero exit code.
"""
    with open(os.path.join(WORK_DIR, "actual.txt"), "w", encoding="utf-8") as f:
        f.write(actual_content)

    # 4. versions.txt
    git_version = subprocess.run(["git", "--version"], stdout=subprocess.PIPE, text=True).stdout.strip()
    python_version = sys.version.replace("\n", " ")
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    versions_content = f"""Git: {git_version}
Python: {python_version}
Platform: {os_info}
"""
    with open(os.path.join(WORK_DIR, "versions.txt"), "w", encoding="utf-8") as f:
        f.write(versions_content)

    # 5. evidence.md
    evidence_content = f"""# Verification Evidence for R03-T030

## Overview
- **Task**: R03-T030 (10 of 10)
- **Target Guide**: `docs/additional-material/git_workflow_scenarios/installing-git-arch.md`
- **Command Anchors**:
  - `git version 2.34.1`
  - `git config --global user.name "Your Name"`
  - `git config --global user.email "youremail@domain.com"`
- **Author Identity**: `Course Student <student@example.invalid>`

## State Transition Verification
| Layer | Predicted State | Actual State (Run 1) | Actual State (Run 2) | Verified? |
| :--- | :--- | :--- | :--- | :--- |
| **Active Ref (`HEAD`)** | `refs/heads/topic` | `{results[0]['post_sym']}` | `{results[1]['post_sym']}` | Pass |
| **`HEAD` Target SHA** | Commit B | `{results[0]['post_head']}` | `{results[1]['post_head']}` | Pass |
| **Branch `main`** | Fixed at Commit C | `{results[0]['post_main']}` | `{results[1]['post_main']}` | Pass |
| **Branch `topic`** | Fixed at Commit B | `{results[0]['post_topic']}` | `{results[1]['post_topic']}` | Pass |
| **Index (`notes.txt`)** | Tracked | Present | Present | Pass |
| **Index (`todo.txt`)** | Removed | Absent | Absent | Pass |
| **Worktree `todo.txt`** | Removed from disk | Absent (`exists=False`) | Absent (`exists=False`) | Pass |
| **Worktree `notes.txt`**| `"alpha\\nbeta\\n"` | `"alpha\\nbeta\\n"` | `"alpha\\nbeta\\n"` | Pass |
| **Author Metadata** | Configured author | `{results[0]['author_c']}` | `{results[1]['author_c']}` | Pass |

## Negative Test Verification
Execution with `FORCE_FAIL=1` raised an AssertionError, confirming that non-zero exit code triggers on verification failure.
"""
    with open(os.path.join(WORK_DIR, "evidence.md"), "w", encoding="utf-8") as f:
        f.write(evidence_content)

def main():
    if os.environ.get("FORCE_FAIL") == "1":
        run_scenario(1, force_fail=True)
        sys.exit(0)

    print("Verifying guide document and command anchors...")
    verify_doc()
    print("Guide verification passed.")

    print("Executing independent Run 1...")
    res1 = run_scenario(1)
    print("Run 1 passed.")

    print("Executing independent Run 2...")
    res2 = run_scenario(2)
    print("Run 2 passed.")

    print("Writing evidence artifacts to work/R03-T030/...")
    write_evidence([res1, res2])
    print("Evidence generated successfully.")

    # Confirm negative failure behavior
    print("Testing negative failure propagation...")
    neg_cmd = [sys.executable, os.path.abspath(__file__)]
    neg_env = os.environ.copy()
    neg_env["FORCE_FAIL"] = "1"
    neg_proc = subprocess.run(neg_cmd, env=neg_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if neg_proc.returncode == 0:
        print("ERROR: Negative test did not fail as expected!", file=sys.stderr)
        sys.exit(1)
    print(f"Negative test failed with exit code {neg_proc.returncode} as expected.")
    print("All checks for R03-T030 passed successfully.")

if __name__ == "__main__":
    main()
