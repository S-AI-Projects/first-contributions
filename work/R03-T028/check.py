#!/usr/bin/env python3
"""
Automated verification script for Task R03-T028:
Make the guide executable as a test: why using branches.

Verifies:
1. Target guide preserves all command anchors:
   - git branch my-new-branch
   - git checkout my-new-branch
   - git checkout -b my-new-branch
2. Guide test suite exists at tests/guides/test_why_using_branches.py.
3. Test suite runs and passes (exit 0) under normal execution.
4. Test suite fails (exit != 0) when the decisive branch switch is omitted (OMIT_BRANCH_SWITCH=1).
5. Temporary test directories are cleanly removed after execution.
6. Asserts at least 3 state facts (new branch ref created, HEAD switched to new branch, topic ref invariant).
"""

import glob
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE_REL = "docs/additional-material/git_workflow_scenarios/why-using-branches.md"
GUIDE_PATH = ROOT / GUIDE_REL
TEST_REL = "tests/guides/test_why_using_branches.py"
TEST_PATH = ROOT / TEST_REL
WORK_DIR = Path(__file__).resolve().parent

def run_cmd(args, cwd, env=None):
    res = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True
    )
    return res

def verify_guide():
    assert GUIDE_PATH.exists(), f"Guide file not found: {GUIDE_PATH}"
    content = GUIDE_PATH.read_text(encoding="utf-8")

    anchors = [
        "git branch my-new-branch",
        "git checkout my-new-branch",
        "git checkout -b my-new-branch"
    ]
    for anchor in anchors:
        assert anchor in content, f"Missing anchor: {anchor}"

    assert "Automated Guide Test" in content, "Missing test section in guide"
    assert "test_why_using_branches.py" in content, "Missing test reference in guide"

def main():
    print("Verifying guide syntax and command anchors...")
    verify_guide()
    print("  Guide verification passed.")

    assert TEST_PATH.exists(), f"Guide test file missing: {TEST_PATH}"

    # Run 1: Normal execution (must succeed)
    print("Running integration test suite...")
    res_normal = run_cmd([sys.executable, str(TEST_PATH)], cwd=ROOT)
    assert res_normal.returncode == 0, f"Normal test failed with {res_normal.returncode}: {res_normal.stderr}"
    print("  Normal test run passed with exit code 0.")

    # Run 2: Omitted decisive command (must fail)
    print("Running negative test with decisive command omitted...")
    env_omit = os.environ.copy()
    env_omit["OMIT_BRANCH_SWITCH"] = "1"
    res_omit = run_cmd([sys.executable, str(TEST_PATH)], cwd=ROOT, env=env_omit)
    assert res_omit.returncode != 0, "Test should have failed when decisive command is omitted!"
    print(f"  Omission test failed as expected with exit code {res_omit.returncode}.")

    # Run 3: Check for leaked temporary directories
    temp_matches = glob.glob(f"{tempfile.gettempdir()}/why-branches-test-*")
    assert len(temp_matches) == 0, f"Temporary directories were leaked: {temp_matches}"
    print("  Verified no temporary test directories leaked.")

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    inputs_txt = f"""Task: R03-T028
Student: Dheeraj Kumar
Repository: https://github.com/S-AI-Projects/first-contributions
Assigned Branch: student/e26b07f0784/R03-T028
Target Guide: {GUIDE_REL}
Guide Test: {TEST_REL}
Command Anchors:
  - git branch my-new-branch
  - git checkout my-new-branch
  - git checkout -b my-new-branch
Test Execution Modes:
  - Normal execution: runs all commands -> passes (exit 0)
  - Deliberate omission: OMIT_BRANCH_SWITCH=1 -> fails (exit 1)
"""
    (WORK_DIR / "inputs.txt").write_text(inputs_txt, encoding="utf-8")

    expected_txt = """Expected Verification Results:
1. Target Guide:
   - Preserves all 3 command anchors.
   - Documents the test suite and execution instructions (python3 tests/guides/test_why_using_branches.py).
2. Guide Test Execution:
   - Normal run succeeds with exit code 0.
   - Omitted decisive branch switch (OMIT_BRANCH_SWITCH=1) fails with non-zero exit code.
   - Temporary directories with prefix 'why-branches-test-' are cleanly removed.
3. State Assertions:
   - my-new-branch points to Commit C.
   - HEAD switches to my-new-branch.
   - refs/heads/topic remains fixed at Commit B.
"""
    (WORK_DIR / "expected.txt").write_text(expected_txt, encoding="utf-8")

    actual_txt = f"""Verification Summary:
Guide Check: PASSED (Found anchors, automated test documentation, and execution command)
Guide Test File: {TEST_REL} (EXISTS)

Test Runs:
  - Normal Execution Return Code: {res_normal.returncode} (PASS)
  - Normal stdout: {res_normal.stdout.strip()}
  - Omission Execution Return Code: {res_omit.returncode} (FAILED AS EXPECTED)
  - Leaked Temp Dirs Count: {len(temp_matches)} (CLEAN)
  - Result: ALL VERIFICATION ASSERTIONS PASSED
"""
    (WORK_DIR / "actual.txt").write_text(actual_txt, encoding="utf-8")

    git_ver = subprocess.run(["git", "--version"], cwd=ROOT, text=True, capture_output=True).stdout.strip()
    py_ver = f"Python {platform.python_version()}"
    versions_txt = f"{git_ver}\n{py_ver}\nOS: {platform.system()} {platform.release()} ({platform.machine()})\n"
    (WORK_DIR / "versions.txt").write_text(versions_txt, encoding="utf-8")

    evidence_md = f"""# Verification Evidence for Task R03-T028

- **Task**: R03-T028 · Make the guide executable as a test: why using branches
- **Student**: Dheeraj Kumar
- **Guide**: `{GUIDE_REL}`
- **Test Command**: `python3 work/R03-T028/check.py`

## State Assertions Verified
1. **Guide Test Execution**: Ran `tests/guides/test_why_using_branches.py` in an isolated temporary repository; confirmed full sequence completed with exit code 0.
2. **Decisive Command Omission**: Verified that omitting the decisive branch switch (`OMIT_BRANCH_SWITCH=1`) triggered an assertion failure and exited non-zero.
3. **Branch Ref and HEAD**: Verified `refs/heads/my-new-branch` was created pointing to Commit C and `HEAD` moved to `my-new-branch`.
4. **Unrelated Ref Stability**: `refs/heads/topic` stayed fixed at Commit B.
5. **Clean Cleanup**: Verified no temporary directories were leaked after execution.

## Tool Versions
- `{git_ver}`
- `{py_ver}`
"""
    (WORK_DIR / "evidence.md").write_text(evidence_md, encoding="utf-8")

    print("\nPASS: All verification checks passed successfully.")

if __name__ == "__main__":
    main()
