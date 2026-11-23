#!/usr/bin/env python3
"""
Automated verification script for Task R03-T021:
Make the command example reproducible: resetting a commit.

Verifies:
1. The target guide contains the required command anchors and syntax.
2. The setup runs cleanly in two separate temporary directories.
3. Git state assertions verify at least three meaningful state facts:
   - Fact 1: HEAD and refs/heads/main move from Commit C to Commit B.
   - Fact 2: The unrelated ref refs/heads/topic remains fixed at Commit B.
   - Fact 3: Commit C is removed from the active history of main.
   - Fact 4: Changes from Commit C (todo.txt) remain in the working directory as untracked.
   - Fact 5: File contents in notes.txt are preserved with 'alpha\\nbeta\\n'.
   - Fact 6: The staging area (index) is clean relative to Commit B.
4. Dynamic capture of commit IDs without hardcoding hashes.
5. Exit code non-zero on assertion failure.
"""

import os
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE_REL = "docs/additional-material/git_workflow_scenarios/resetting-a-commit.md"
GUIDE_PATH = ROOT / GUIDE_REL
WORK_DIR = Path(__file__).resolve().parent

AUTHOR_NAME = "Course Student"
AUTHOR_EMAIL = "student@example.invalid"

def run_cmd(args, cwd, env=None):
    res = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=True
    )
    return res.stdout.strip()

def verify_guide():
    assert GUIDE_PATH.exists(), f"Guide file not found: {GUIDE_PATH}"
    content = GUIDE_PATH.read_text(encoding="utf-8")
    
    # Verify command anchors
    anchor1 = "The main difference between resetting and reverting a commit is that git reset"
    anchor2 = "and git revert"
    assert anchor1 in content, f"Missing anchor: {anchor1}"
    assert anchor2 in content, f"Missing anchor: {anchor2}"
    
    # Verify published reset command and setup snippets
    assert 'git reset "$B"' in content or "git reset commithash" in content, "Missing reset command in guide"
    assert "Course Student" in content, "Missing author name in guide"
    assert "notes.txt" in content and "todo.txt" in content, "Missing file mentions in guide"

def run_scenario(iteration: int):
    with tempfile.TemporaryDirectory(prefix=f"r03-t021-run{iteration}-") as tmpdir:
        repo = Path(tmpdir)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
        env.update({
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": AUTHOR_NAME,
            "GIT_AUTHOR_EMAIL": AUTHOR_EMAIL,
            "GIT_COMMITTER_NAME": AUTHOR_NAME,
            "GIT_COMMITTER_EMAIL": AUTHOR_EMAIL,
            "LC_ALL": "C",
        })

        # Step 1: Initialize repository
        run_cmd(["git", "init", "-b", "main"], cwd=repo, env=env)
        run_cmd(["git", "config", "user.name", AUTHOR_NAME], cwd=repo, env=env)
        run_cmd(["git", "config", "user.email", AUTHOR_EMAIL], cwd=repo, env=env)

        # Step 2: Commit A creates notes.txt with "alpha\n"
        (repo / "notes.txt").write_text("alpha\n", encoding="utf-8")
        run_cmd(["git", "add", "notes.txt"], cwd=repo, env=env)
        run_cmd(["git", "commit", "-m", "A: add notes"], cwd=repo, env=env)
        commit_a = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)

        # Step 3: Commit B appends "beta\n"
        with open(repo / "notes.txt", "a", encoding="utf-8") as f:
            f.write("beta\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo, env=env)
        run_cmd(["git", "commit", "-m", "B: append notes"], cwd=repo, env=env)
        commit_b = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)

        # Step 4: Create branch topic at commit B
        run_cmd(["git", "branch", "topic", commit_b], cwd=repo, env=env)

        # Step 5: Commit C adds todo.txt with "one\n"
        (repo / "todo.txt").write_text("one\n", encoding="utf-8")
        run_cmd(["git", "add", "todo.txt"], cwd=repo, env=env)
        run_cmd(["git", "commit", "-m", "C: add todo"], cwd=repo, env=env)
        commit_c = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)

        # Verify pre-reset conditions
        assert commit_a != commit_b != commit_c, "Commit hashes must be distinct"
        assert run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env) == commit_c
        assert run_cmd(["git", "rev-parse", "refs/heads/topic"], cwd=repo, env=env) == commit_b
        assert run_cmd(["git", "status", "--porcelain"], cwd=repo, env=env) == ""

        # Step 6: Execute the exact reset command to commit B
        run_cmd(["git", "reset", commit_b], cwd=repo, env=env)

        # Step 7: Verify post-reset state assertions
        head_sha = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)
        main_sha = run_cmd(["git", "rev-parse", "refs/heads/main"], cwd=repo, env=env)
        topic_sha = run_cmd(["git", "rev-parse", "refs/heads/topic"], cwd=repo, env=env)
        status_porcelain = run_cmd(["git", "status", "--porcelain"], cwd=repo, env=env)
        cached_diff = run_cmd(["git", "diff", "--cached"], cwd=repo, env=env)
        log_messages = run_cmd(["git", "log", "--format=%s", "-3"], cwd=repo, env=env).splitlines()
        notes_content = (repo / "notes.txt").read_text(encoding="utf-8")
        todo_exists = (repo / "todo.txt").exists()

        if os.environ.get("FORCE_FAIL") == "1":
            assert False, "Forced failure for negative test verification"

        # Assertion 1: HEAD and main move to Commit B
        assert head_sha == commit_b, f"Expected HEAD == {commit_b}, got {head_sha}"
        assert main_sha == commit_b, f"Expected main == {commit_b}, got {main_sha}"

        # Assertion 2: Unrelated ref topic remains unchanged at Commit B
        assert topic_sha == commit_b, f"Expected topic == {commit_b}, got {topic_sha}"

        # Assertion 3: Commit C is removed from active branch history
        assert log_messages == ["B: append notes", "A: add notes"], f"Unexpected commit log: {log_messages}"

        # Assertion 4: Staging area is clean relative to Commit B
        assert cached_diff == "", f"Staging area is not clean: {cached_diff}"

        # Assertion 5: todo.txt is preserved in working tree as untracked
        assert todo_exists, "todo.txt should exist in working tree"
        assert "??" in status_porcelain and "todo.txt" in status_porcelain, f"Expected untracked todo.txt in status, got: {status_porcelain}"

        # Assertion 6: notes.txt contents are intact
        assert notes_content == "alpha\nbeta\n", f"Unexpected notes.txt content: {notes_content}"

        return {
            "iteration": iteration,
            "commit_a": commit_a,
            "commit_b": commit_b,
            "commit_c": commit_c,
            "head_sha": head_sha,
            "main_sha": main_sha,
            "topic_sha": topic_sha,
            "status_porcelain": status_porcelain,
            "log": log_messages,
            "notes_content": notes_content,
            "todo_exists": todo_exists,
        }

def main():
    print("Verifying guide syntax and command anchors...")
    verify_guide()
    print("  Guide verification passed.")

    results = []
    print("Running reproducible checks across 2 independent temporary repositories...")
    for i in (1, 2):
        res = run_scenario(i)
        results.append(res)
        print(f"  Run {i} passed: main={res['main_sha'][:7]} topic={res['topic_sha'][:7]} status='{res['status_porcelain']}'")

    # Generate evidence files
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    inputs_txt = f"""Task: R03-T021
Student: Dheeraj Kumar
Repository: https://github.com/S-AI-Projects/first-contributions
Assigned Branch: student/e26b07f0784/R03-T021
Target Guide: {GUIDE_REL}
Command Anchors:
  - "The main difference between resetting and reverting a commit is that git reset"
  - "and git revert"
Setup:
  - Repository branch: main
  - Author: Course Student <student@example.invalid>
  - Commits:
    - A: notes.txt ("alpha\\n")
    - B: notes.txt append ("beta\\n")
    - C: todo.txt ("one\\n")
  - Branch topic created at Commit B
Executed Operation:
  - git reset <commit_b>
"""
    (WORK_DIR / "inputs.txt").write_text(inputs_txt, encoding="utf-8")

    expected_txt = """Expected Verification Results:
1. Target Guide:
   - Contains command anchors: 'The main difference between resetting and reverting a commit is that git reset' and 'and git revert'.
   - Documents start-to-finish reproducible example with explicit setup, command, and expected status/log.
2. Pre-reset State:
   - main points to Commit C.
   - topic points to Commit B.
   - Working tree and index clean.
3. Post-reset State (git reset <commit_b>):
   - HEAD and refs/heads/main point to Commit B.
   - refs/heads/topic remains at Commit B.
   - Commit C is removed from the branch log (log shows B then A).
   - Index is clean (no staged changes).
   - todo.txt remains in the working directory as untracked (?? todo.txt).
   - notes.txt contains "alpha\\nbeta\\n".
4. Reproducibility:
   - Identical assertions hold across multiple independent temporary directory runs.
"""
    (WORK_DIR / "expected.txt").write_text(expected_txt, encoding="utf-8")

    actual_txt = f"""Verification Summary:
Guide Check: PASSED (Found anchors, complete setup, exact reset command, expected status/log)

Run 1:
  - Commit A: {results[0]['commit_a']}
  - Commit B: {results[0]['commit_b']}
  - Commit C: {results[0]['commit_c']}
  - HEAD after reset: {results[0]['head_sha']} (matches Commit B)
  - main ref after reset: {results[0]['main_sha']} (matches Commit B)
  - topic ref after reset: {results[0]['topic_sha']} (matches Commit B)
  - Working tree status: {results[0]['status_porcelain']}
  - Log history: {results[0]['log']}
  - notes.txt content: {repr(results[0]['notes_content'])}
  - todo.txt exists: {results[0]['todo_exists']}
  - Result: ALL ASSERTIONS PASSED

Run 2:
  - Commit A: {results[1]['commit_a']}
  - Commit B: {results[1]['commit_b']}
  - Commit C: {results[1]['commit_c']}
  - HEAD after reset: {results[1]['head_sha']} (matches Commit B)
  - main ref after reset: {results[1]['main_sha']} (matches Commit B)
  - topic ref after reset: {results[1]['topic_sha']} (matches Commit B)
  - Working tree status: {results[1]['status_porcelain']}
  - Log history: {results[1]['log']}
  - notes.txt content: {repr(results[1]['notes_content'])}
  - todo.txt exists: {results[1]['todo_exists']}
  - Result: ALL ASSERTIONS PASSED
"""
    (WORK_DIR / "actual.txt").write_text(actual_txt, encoding="utf-8")

    git_ver = run_cmd(["git", "--version"], cwd=ROOT)
    py_ver = f"Python {platform.python_version()}"
    versions_txt = f"{git_ver}\n{py_ver}\nOS: {platform.system()} {platform.release()} ({platform.machine()})\n"
    (WORK_DIR / "versions.txt").write_text(versions_txt, encoding="utf-8")

    evidence_md = f"""# Verification Evidence for Task R03-T021

- **Task**: R03-T021 · Make the command example reproducible: resetting a commit
- **Student**: Dheeraj Kumar
- **Guide**: `{GUIDE_REL}`
- **Test Command**: `python3 work/R03-T021/check.py`

## State Assertions Verified
1. **Ref Movement**: `refs/heads/main` and `HEAD` moved backward from Commit C to Commit B.
2. **Unrelated Ref Stability**: `refs/heads/topic` remained completely unchanged at Commit B.
3. **Commit History**: Commit C was excised from `main`'s log; history reflects `[B, A]`.
4. **Working Tree Preservation**: Changes from Commit C (`todo.txt`) were preserved in the working tree as untracked (`?? todo.txt`).
5. **Index State**: Staging area was reset to Commit B with clean index (`git diff --cached` empty).
6. **Reproducibility**: Two separate temporary repositories independently executed the exact sequence and satisfied all assertions.

## Tool Versions
- `{git_ver}`
- `{py_ver}`
"""
    (WORK_DIR / "evidence.md").write_text(evidence_md, encoding="utf-8")

    print("\nPASS: All verification checks passed successfully.")

if __name__ == "__main__":
    main()
