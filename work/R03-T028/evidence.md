# Verification Evidence for Task R03-T028

- **Task**: R03-T028 · Make the guide executable as a test: why using branches
- **Student**: Dheeraj Kumar
- **Guide**: `docs/additional-material/git_workflow_scenarios/why-using-branches.md`
- **Test Command**: `python3 work/R03-T028/check.py`

## State Assertions Verified
1. **Guide Test Execution**: Ran `tests/guides/test_why_using_branches.py` in an isolated temporary repository; confirmed full sequence completed with exit code 0.
2. **Decisive Command Omission**: Verified that omitting the decisive branch switch (`OMIT_BRANCH_SWITCH=1`) triggered an assertion failure and exited non-zero.
3. **Branch Ref and HEAD**: Verified `refs/heads/my-new-branch` was created pointing to Commit C and `HEAD` moved to `my-new-branch`.
4. **Unrelated Ref Stability**: `refs/heads/topic` stayed fixed at Commit B.
5. **Clean Cleanup**: Verified no temporary directories were leaked after execution.

## Tool Versions
- `git version 2.54.0 (Apple Git-157)`
- `Python 3.9.6`
