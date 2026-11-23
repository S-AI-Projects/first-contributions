#!/usr/bin/env python3
"""
Automated verification script for Task R03-T023:
Teach recovery from the operation: reverting a commit.

Verifies:
1. Target guide exists and preserves both source command anchors:
   - "Reversion is made easier in git because every commit you push to your remote repository has a unique alphanumeric key known as SHA(Secure Hash Algorithm) tied to it."
   - "You can decide to leave the commit message as the default git message which starts with the word `Revert`"
2. Isolated temporary Git repository setup with:
   - Branch main, author Course Student <student@example.invalid>
   - Commit A: creates notes.txt with 'alpha\\n'
   - Commit B: appends 'beta\\n' to notes.txt
   - Branch topic created at Commit B
   - Commit C: adds todo.txt with 'one\\n'
3. Simulates the reversible mistake:
   - Accidentally reverting Commit C (removing todo.txt).
4. Executes recovery:
   - Method 1: git revert --no-edit HEAD (reverting the revert).
   - Method 2: git reset --hard <commit_c>.
5. Asserts Git state facts:
   - Recovered tree hash matches initial Commit C tree hash.
   - todo.txt content is restored with 'one\\n'.
   - Working tree and index are clean.
   - Unrelated ref refs/heads/topic remains fixed at Commit B.
   - Recovery documentation identifies what cannot be recovered.
6. Runs across 2 independent temporary repositories.
7. Exits non-zero on assertion failure.
"""

import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE_REL = "docs/additional-material/git_workflow_scenarios/reverting-a-commit.md"
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

    anchor1 = "Reversion is made easier in git because every commit you push to your remote repository has a unique alphanumeric key known as SHA(Secure Hash Algorithm) tied to it."
    anchor2 = "You can decide to leave the commit message as the default git message which starts with the word `Revert`"
    assert anchor1 in content, f"Missing anchor 1: {anchor1}"
    assert anchor2 in content, f"Missing anchor 2: {anchor2}"

    assert "Recovery: Undoing an Accidental Revert" in content, "Missing recovery section in guide"
    assert "What cannot be recovered" in content, "Missing note on unrecoverable aspects"

def run_scenario(iteration: int):
    with tempfile.TemporaryDirectory(prefix=f"r03-t023-run{iteration}-") as tmpdir:
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

        # Step 1: Initialize repo
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
        tree_c = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, env=env)

        # Step 6: Simulate the mistake: accidentally revert Commit C
        run_cmd(["git", "revert", "--no-edit", commit_c], cwd=repo, env=env)
        rev_commit = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)
        rev_msg = run_cmd(["git", "log", "-1", "--format=%s"], cwd=repo, env=env)
        assert not (repo / "todo.txt").exists(), "todo.txt should be absent after reverting Commit C"
        assert rev_msg.startswith("Revert"), f"Revert commit message should start with 'Revert': {rev_msg}"

        # Step 7: Execute recovery Method 1: Reverting the revert
        run_cmd(["git", "revert", "--no-edit", rev_commit], cwd=repo, env=env)
        recovered_tree_1 = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, env=env)
        todo_content_1 = (repo / "todo.txt").read_text(encoding="utf-8")
        status_1 = run_cmd(["git", "status", "--porcelain"], cwd=repo, env=env)
        topic_ref = run_cmd(["git", "rev-parse", "refs/heads/topic"], cwd=repo, env=env)

        if os.environ.get("FORCE_FAIL") == "1":
            assert False, "Forced failure for negative test verification"

        # Assertions for Recovery Method 1
        assert recovered_tree_1 == tree_c, f"Recovered tree {recovered_tree_1} != initial tree {tree_c}"
        assert todo_content_1 == "one\n", f"Unexpected todo.txt content: {todo_content_1}"
        assert status_1 == "", f"Working tree not clean: {status_1}"
        assert topic_ref == commit_b, f"topic branch shifted: {topic_ref} != {commit_b}"

        # Step 8: Also verify Method 2: git reset --hard
        run_cmd(["git", "reset", "--hard", commit_c], cwd=repo, env=env)
        recovered_tree_2 = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, env=env)
        head_commit_2 = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)
        assert recovered_tree_2 == tree_c, "Tree after reset does not match initial tree"
        assert head_commit_2 == commit_c, "HEAD after reset does not match Commit C"

        return {
            "iteration": iteration,
            "commit_a": commit_a,
            "commit_b": commit_b,
            "commit_c": commit_c,
            "tree_c": tree_c,
            "rev_commit": rev_commit,
            "recovered_tree": recovered_tree_1,
            "todo_content": todo_content_1,
            "topic_ref": topic_ref,
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
        print(f"  Run {i} passed: tree_c={res['tree_c'][:7]} recovered_tree={res['recovered_tree'][:7]} topic={res['topic_ref'][:7]}")

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    inputs_txt = f"""Task: R03-T023
Student: Dheeraj Kumar
Repository: https://github.com/S-AI-Projects/first-contributions
Assigned Branch: student/e26b07f0784/R03-T023
Target Guide: {GUIDE_REL}
Command Anchors:
  - "Reversion is made easier in git because every commit you push to your remote repository has a unique alphanumeric key known as SHA(Secure Hash Algorithm) tied to it."
  - "You can decide to leave the commit message as the default git message which starts with the word `Revert`"
Setup:
  - Repository branch: main
  - Author: Course Student <student@example.invalid>
  - Commits:
    - A: notes.txt ("alpha\\n")
    - B: notes.txt append ("beta\\n")
    - C: todo.txt ("one\\n")
  - Branch topic created at Commit B
Reversible Mistake:
  - git revert --no-edit <commit_c>
Recovery Mechanisms:
  - Method 1 (Safe for pushed branches): git revert --no-edit HEAD
  - Method 2 (Safe for local branches): git reset --hard <commit_c>
"""
    (WORK_DIR / "inputs.txt").write_text(inputs_txt, encoding="utf-8")

    expected_txt = """Expected Verification Results:
1. Target Guide:
   - Contains both command anchors.
   - Documents mistake scenario and recovery point, commands, and verification.
   - Explicitly identifies what cannot be recovered by each method.
2. Pre-mistake State:
   - Commit C tree contains notes.txt and todo.txt.
   - topic branch at Commit B.
3. Mistake State:
   - git revert <commit_c> creates a revert commit starting with 'Revert'.
   - todo.txt is deleted from the tree.
4. Recovered State (git revert HEAD or git reset --hard <commit_c>):
   - Recovered tree hash matches saved Commit C tree hash.
   - todo.txt content is 'one\\n'.
   - Working tree and index are clean.
   - topic ref remains at Commit B.
"""
    (WORK_DIR / "expected.txt").write_text(expected_txt, encoding="utf-8")

    actual_txt = f"""Verification Summary:
Guide Check: PASSED (Found anchors, recovery section, and unrecoverable notes)

Run 1:
  - Commit A: {results[0]['commit_a']}
  - Commit B: {results[0]['commit_b']}
  - Commit C: {results[0]['commit_c']}
  - Initial Tree (Commit C): {results[0]['tree_c']}
  - Accidental Revert Commit: {results[0]['rev_commit']}
  - Recovered Tree Hash: {results[0]['recovered_tree']} (MATCHES INITIAL TREE)
  - todo.txt Content: {repr(results[0]['todo_content'])} (MATCHES ORIGINAL)
  - topic Ref: {results[0]['topic_ref']} (UNCHANGED)
  - Result: ALL STATE ASSERTIONS PASSED

Run 2:
  - Commit A: {results[1]['commit_a']}
  - Commit B: {results[1]['commit_b']}
  - Commit C: {results[1]['commit_c']}
  - Initial Tree (Commit C): {results[1]['tree_c']}
  - Accidental Revert Commit: {results[1]['rev_commit']}
  - Recovered Tree Hash: {results[1]['recovered_tree']} (MATCHES INITIAL TREE)
  - todo.txt Content: {repr(results[1]['todo_content'])} (MATCHES ORIGINAL)
  - topic Ref: {results[1]['topic_ref']} (UNCHANGED)
  - Result: ALL STATE ASSERTIONS PASSED
"""
    (WORK_DIR / "actual.txt").write_text(actual_txt, encoding="utf-8")

    git_ver = run_cmd(["git", "--version"], cwd=ROOT)
    py_ver = f"Python {platform.python_version()}"
    versions_txt = f"{git_ver}\n{py_ver}\nOS: {platform.system()} {platform.release()} ({platform.machine()})\n"
    (WORK_DIR / "versions.txt").write_text(versions_txt, encoding="utf-8")

    evidence_md = f"""# Verification Evidence for Task R03-T023

- **Task**: R03-T023 · Teach recovery from the operation: reverting a commit
- **Student**: Dheeraj Kumar
- **Guide**: `{GUIDE_REL}`
- **Test Command**: `python3 work/R03-T023/check.py`

## State Assertions Verified
1. **Mistake Simulation**: Accidentally reverting Commit C removed `todo.txt` and generated a revert commit starting with `Revert`.
2. **Tree Recovery**: Executing `git revert --no-edit HEAD` restored the exact tree hash of Commit C.
3. **File Content Integrity**: `todo.txt` was restored with `"one\\n"`.
4. **Working Tree Cleanliness**: Index and working directory are completely clean post-recovery.
5. **Unrelated Ref Invariance**: `refs/heads/topic` stayed fixed at Commit B.
6. **Alternative Local Recovery**: `git reset --hard` successfully restored both commit and tree state.
7. **Documented Limitations**: Documented what cannot be recovered by each method (linear commit history for revert-revert; uncommitted work for reset).

## Tool Versions
- `{git_ver}`
- `{py_ver}`
"""
    (WORK_DIR / "evidence.md").write_text(evidence_md, encoding="utf-8")

    print("\nPASS: All verification checks passed successfully.")

if __name__ == "__main__":
    main()
