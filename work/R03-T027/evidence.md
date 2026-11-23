# Verification Evidence for Task R03-T027

- **Task**: R03-T027 · Explain a real command failure: removing a file
- **Student**: Dheeraj Kumar
- **Guide**: `docs/additional-material/git_workflow_scenarios/removing-a-file.md`
- **Test Command**: `python3 work/R03-T027/check.py`

## State Assertions Verified
1. **Command Failure Capture**: Triggered Git's data-loss protection refusal by creating staged and worktree edits, confirming `git rm --cached notes.txt` exited non-zero with code 1.
2. **Smallest Correction Verification**: Executing `git rm --cached -f notes.txt` cleanly succeeded with exit code 0.
3. **File System Persistence**: Verified that `notes.txt` remained intact on disk with all staged and unstaged content preserved.
4. **Index Untracking**: Verified that `notes.txt` was staged as deleted (`D notes.txt`) in the Git index.
5. **Unrelated Ref Stability**: `refs/heads/topic` remained fixed at Commit B.
6. **Reproducibility**: Two separate temporary repositories independently confirmed the failure and repair dynamics.

## Tool Versions
- `git version 2.54.0 (Apple Git-157)`
- `Python 3.9.6`
