# Verification Evidence for Task R03-T023

- **Task**: R03-T023 · Teach recovery from the operation: reverting a commit
- **Student**: Dheeraj Kumar
- **Guide**: `docs/additional-material/git_workflow_scenarios/reverting-a-commit.md`
- **Test Command**: `python3 work/R03-T023/check.py`

## State Assertions Verified
1. **Mistake Simulation**: Accidentally reverting Commit C removed `todo.txt` and generated a revert commit starting with `Revert`.
2. **Tree Recovery**: Executing `git revert --no-edit HEAD` restored the exact tree hash of Commit C.
3. **File Content Integrity**: `todo.txt` was restored with `"one\n"`.
4. **Working Tree Cleanliness**: Index and working directory are completely clean post-recovery.
5. **Unrelated Ref Invariance**: `refs/heads/topic` stayed fixed at Commit B.
6. **Alternative Local Recovery**: `git reset --hard` successfully restored both commit and tree state.
7. **Documented Limitations**: Documented what cannot be recovered by each method (linear commit history for revert-revert; uncommitted work for reset).

## Tool Versions
- `git version 2.54.0 (Apple Git-157)`
- `Python 3.9.6`
