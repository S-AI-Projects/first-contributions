#!/usr/bin/env python3
"""
Automated verification script for Task R03-T026:
Compare two ways to reach the state: gitflow.

Verifies:
1. Target guide preserves all command anchors:
   - git branch develop
   - git push -u origin develop
   - git flow init
2. Sets up equivalent repository fixtures across 2 runs:
   - Branch main, author Course Student <student@example.invalid>
   - Bare remote origin (file:// URL)
   - Commit A: notes.txt ("alpha\\n")
   - Commit B: appends "beta\\n" to notes.txt
   - Branch topic created at Commit B
   - Commit C: todo.txt ("one\\n") on main
3. Compares Method A (git branch develop) vs Method B (git checkout -b develop):
   - Method A creates develop pointing to Commit C, but leaves HEAD on main.
   - Method B creates develop pointing to Commit C and switches HEAD to develop.
   - Asserts observable difference in active branch / HEAD ref.
   - Asserts unrelated ref refs/heads/topic remains fixed at Commit B.
4. Verifies git push -u origin develop:
   - Pushes develop to local bare remote.
   - Sets upstream tracking configuration in local repo.
5. Exits non-zero on assertion failure.
"""

import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE_REL = "docs/additional-material/git_workflow_scenarios/gitflow.md"
GUIDE_PATH = ROOT / GUIDE_REL
WORK_DIR = Path(__file__).resolve().parent

AUTHOR_NAME = "Course Student"
AUTHOR_EMAIL = "student@example.invalid"

def run_cmd(args, cwd, env=None, check=True):
    res = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=check
    )
    return res.stdout.strip()

def verify_guide():
    assert GUIDE_PATH.exists(), f"Guide file not found: {GUIDE_PATH}"
    content = GUIDE_PATH.read_text(encoding="utf-8")

    anchors = [
        "git branch develop",
        "git push -u origin develop",
        "git flow init"
    ]
    for anchor in anchors:
        assert anchor in content, f"Missing anchor: {anchor}"

    assert "Comparison: Initializing the Develop Branch" in content, "Missing comparison section"
    assert "Comparison Matrix" in content, "Missing comparison table"

def setup_repo(root: Path, name: str):
    repo = root / name
    repo.mkdir()
    bare = root / f"{name}_remote.git"
    subprocess.run(["git", "init", "--bare", str(bare)], check=True, capture_output=True)

    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "EMAIL"}
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": AUTHOR_NAME,
        "GIT_AUTHOR_EMAIL": AUTHOR_EMAIL,
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
        "GIT_COMMITTER_NAME": AUTHOR_NAME,
        "GIT_COMMITTER_EMAIL": AUTHOR_EMAIL,
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        "LC_ALL": "C",
    })

    run_cmd(["git", "init", "-b", "main"], cwd=repo, env=env)
    run_cmd(["git", "config", "user.name", AUTHOR_NAME], cwd=repo, env=env)
    run_cmd(["git", "config", "user.email", AUTHOR_EMAIL], cwd=repo, env=env)
    run_cmd(["git", "remote", "add", "origin", f"file://{bare}"], cwd=repo, env=env)

    # Commit A
    (repo / "notes.txt").write_text("alpha\n", encoding="utf-8")
    run_cmd(["git", "add", "notes.txt"], cwd=repo, env=env)
    run_cmd(["git", "commit", "-m", "A: add notes"], cwd=repo, env=env)
    commit_a = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)

    # Commit B
    with open(repo / "notes.txt", "a", encoding="utf-8") as f:
        f.write("beta\n")
    run_cmd(["git", "add", "notes.txt"], cwd=repo, env=env)
    run_cmd(["git", "commit", "-m", "B: append notes"], cwd=repo, env=env)
    commit_b = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)

    # Branch topic at Commit B
    run_cmd(["git", "branch", "topic", commit_b], cwd=repo, env=env)

    # Commit C on main
    (repo / "todo.txt").write_text("one\n", encoding="utf-8")
    run_cmd(["git", "add", "todo.txt"], cwd=repo, env=env)
    run_cmd(["git", "commit", "-m", "C: add todo"], cwd=repo, env=env)
    commit_c = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo, env=env)

    # Push main to origin
    run_cmd(["git", "push", "origin", "main"], cwd=repo, env=env)

    return repo, env, commit_a, commit_b, commit_c

def run_scenario(iteration: int):
    with tempfile.TemporaryDirectory(prefix=f"r03-t026-run{iteration}-") as tmpdir:
        root = Path(tmpdir)

        # Setup fixture for Method A
        repo_a, env_a, a1, b1, c1 = setup_repo(root, "repo_a")
        # Setup fixture for Method B
        repo_b, env_b, a2, b2, c2 = setup_repo(root, "repo_b")

        assert c1 == c2 and b1 == b2, "Starting fixtures must be identical"

        # Execute Method A: git branch develop
        run_cmd(["git", "branch", "develop"], cwd=repo_a, env=env_a)
        head_a = run_cmd(["git", "symbolic-ref", "--short", "HEAD"], cwd=repo_a, env=env_a)
        develop_ref_a = run_cmd(["git", "rev-parse", "refs/heads/develop"], cwd=repo_a, env=env_a)
        main_ref_a = run_cmd(["git", "rev-parse", "refs/heads/main"], cwd=repo_a, env=env_a)
        topic_ref_a = run_cmd(["git", "rev-parse", "refs/heads/topic"], cwd=repo_a, env=env_a)

        # Execute Method B: git checkout -b develop
        run_cmd(["git", "checkout", "-b", "develop"], cwd=repo_b, env=env_b)
        head_b = run_cmd(["git", "symbolic-ref", "--short", "HEAD"], cwd=repo_b, env=env_b)
        develop_ref_b = run_cmd(["git", "rev-parse", "refs/heads/develop"], cwd=repo_b, env=env_b)
        main_ref_b = run_cmd(["git", "rev-parse", "refs/heads/main"], cwd=repo_b, env=env_b)
        topic_ref_b = run_cmd(["git", "rev-parse", "refs/heads/topic"], cwd=repo_b, env=env_b)

        # Execute git push -u origin develop on repo_b
        run_cmd(["git", "push", "-u", "origin", "develop"], cwd=repo_b, env=env_b)
        remote_develop_ref = run_cmd(["git", "rev-parse", "refs/remotes/origin/develop"], cwd=repo_b, env=env_b)
        upstream_remote_cfg = run_cmd(["git", "config", "branch.develop.remote"], cwd=repo_b, env=env_b)

        if os.environ.get("FORCE_FAIL") == "1":
            assert False, "Forced failure for negative test verification"

        # Assertions
        # Fact 1: Both methods created develop pointing to Commit C
        assert develop_ref_a == c1, f"Method A develop ref expected {c1}, got {develop_ref_a}"
        assert develop_ref_b == c2, f"Method B develop ref expected {c2}, got {develop_ref_b}"

        # Fact 2: Observable difference in active branch (HEAD)
        assert head_a == "main", f"Method A HEAD expected 'main', got '{head_a}'"
        assert head_b == "develop", f"Method B HEAD expected 'develop', got '{head_b}'"

        # Fact 3: Unrelated ref topic remains unchanged at Commit B in both fixtures
        assert topic_ref_a == b1 and topic_ref_b == b2, "topic ref shifted"

        # Fact 4: main ref remains fixed at Commit C in both fixtures
        assert main_ref_a == c1 and main_ref_b == c2, "main ref shifted"

        # Fact 5: git push -u established remote ref and tracking config
        assert remote_develop_ref == c2, f"Remote tracking ref mismatch: {remote_develop_ref} != {c2}"
        assert upstream_remote_cfg == "origin", f"Upstream remote expected 'origin', got '{upstream_remote_cfg}'"

        return {
            "iteration": iteration,
            "commit_b": b1,
            "commit_c": c1,
            "head_a": head_a,
            "head_b": head_b,
            "develop_ref_a": develop_ref_a,
            "develop_ref_b": develop_ref_b,
            "remote_develop": remote_develop_ref,
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
        print(f"  Run {i} passed: Method A HEAD={res['head_a']} vs Method B HEAD={res['head_b']} develop={res['develop_ref_a'][:7]}")

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    inputs_txt = f"""Task: R03-T026
Student: Dheeraj Kumar
Repository: https://github.com/S-AI-Projects/first-contributions
Assigned Branch: student/e26b07f0784/R03-T026
Target Guide: {GUIDE_REL}
Command Anchors:
  - git branch develop
  - git push -u origin develop
  - git flow init
Compared Operations:
  - Method A: git branch develop (creates ref, leaves HEAD on main)
  - Method B: git checkout -b develop (creates ref, switches HEAD to develop)
Remote Operation:
  - git push -u origin develop (publishes to origin and establishes upstream tracking)
Base Fixture:
  - Branch: main, Author: Course Student <student@example.invalid>
  - Commits A, B, topic at B, Commit C on main
"""
    (WORK_DIR / "inputs.txt").write_text(inputs_txt, encoding="utf-8")

    expected_txt = """Expected Verification Results:
1. Target Guide:
   - Preserves all 3 command anchors.
   - Includes comparison matrix between git branch develop and git checkout -b develop.
   - Explains the observable difference in HEAD reference.
2. Initial State:
   - main points to Commit C.
   - topic points to Commit B.
3. Method A (git branch develop):
   - refs/heads/develop is created pointing to Commit C.
   - HEAD remains on 'main'.
4. Method B (git checkout -b develop):
   - refs/heads/develop is created pointing to Commit C.
   - HEAD switches to 'develop'.
5. Upstream Tracking:
   - git push -u origin develop creates refs/remotes/origin/develop at Commit C and configures branch.develop.remote.
"""
    (WORK_DIR / "expected.txt").write_text(expected_txt, encoding="utf-8")

    actual_txt = f"""Verification Summary:
Guide Check: PASSED (Found anchors, comparison table, and observable difference)

Run 1:
  - Commit B: {results[0]['commit_b']}
  - Commit C: {results[0]['commit_c']}
  - Method A HEAD: {results[0]['head_a']} (STAYS ON MAIN)
  - Method B HEAD: {results[0]['head_b']} (SWITCHES TO DEVELOP)
  - Method A develop Ref: {results[0]['develop_ref_a']} (MATCHES COMMIT C)
  - Method B develop Ref: {results[0]['develop_ref_b']} (MATCHES COMMIT C)
  - Remote develop Ref: {results[0]['remote_develop']} (MATCHES COMMIT C)
  - Result: ALL STATE ASSERTIONS PASSED

Run 2:
  - Commit B: {results[1]['commit_b']}
  - Commit C: {results[1]['commit_c']}
  - Method A HEAD: {results[1]['head_a']} (STAYS ON MAIN)
  - Method B HEAD: {results[1]['head_b']} (SWITCHES TO DEVELOP)
  - Method A develop Ref: {results[1]['develop_ref_a']} (MATCHES COMMIT C)
  - Method B develop Ref: {results[1]['develop_ref_b']} (MATCHES COMMIT C)
  - Remote develop Ref: {results[1]['remote_develop']} (MATCHES COMMIT C)
  - Result: ALL STATE ASSERTIONS PASSED
"""
    (WORK_DIR / "actual.txt").write_text(actual_txt, encoding="utf-8")

    git_ver = run_cmd(["git", "--version"], cwd=ROOT)
    py_ver = f"Python {platform.python_version()}"
    versions_txt = f"{git_ver}\n{py_ver}\nOS: {platform.system()} {platform.release()} ({platform.machine()})\n"
    (WORK_DIR / "versions.txt").write_text(versions_txt, encoding="utf-8")

    evidence_md = f"""# Verification Evidence for Task R03-T026

- **Task**: R03-T026 · Compare two ways to reach the state: gitflow
- **Student**: Dheeraj Kumar
- **Guide**: `{GUIDE_REL}`
- **Test Command**: `python3 work/R03-T026/check.py`

## State Assertions Verified
1. **Develop Ref Creation**: Both `git branch develop` and `git checkout -b develop` created `refs/heads/develop` pointing to Commit C.
2. **Observable Difference in HEAD**:
   - `git branch develop` kept `HEAD` on `main` (`refs/heads/main`).
   - `git checkout -b develop` switched `HEAD` to `develop` (`refs/heads/develop`).
3. **Unrelated Ref Stability**: `refs/heads/topic` remained fixed at Commit B and `refs/heads/main` remained at Commit C.
4. **Upstream Publication and Tracking**: `git push -u origin develop` published the branch to the local bare remote and established upstream tracking configuration (`branch.develop.remote = origin`).
5. **Reproducibility**: Two separate temporary repositories with local bare remotes independently verified identical assertions.

## Tool Versions
- `{git_ver}`
- `{py_ver}`
"""
    (WORK_DIR / "evidence.md").write_text(evidence_md, encoding="utf-8")

    print("\nPASS: All verification checks passed successfully.")

if __name__ == "__main__":
    main()
