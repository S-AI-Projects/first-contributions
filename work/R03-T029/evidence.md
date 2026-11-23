# Verification Evidence for Task R03-T029

- **Task**: R03-T029 · State the missing setup explicitly: creating a gitignore file
- **Student**: Dheeraj Kumar
- **Guide**: `docs/additional-material/git_workflow_scenarios/creating-a-gitignore-file.md`
- **Test Command**: `python3 work/R03-T029/check.py`

## State Assertions Verified
1. **Precondition 1 (Worktree State)**: Confirmed inside active Git repository (`git rev-parse --is-inside-work-tree` returned `true`).
2. **Precondition 2 (Current Branch)**: Confirmed execution on active branch `main` (`git branch --show-current` returned `main`).
3. **Precondition 3 (Worktree Cleanliness)**: Verified staging index was clean prior to untracking.
4. **Precondition 4 (Configuration Isolation)**: Verified `core.excludesfile` in an isolated per-test environment leaving host configuration untouched.
5. **Ignore Functionality**: Confirmed `*.log` rule in `.gitignore` successfully excluded `debug.log`.
6. **File Preservation**: Verified `git rm --cached todo.txt` staged deletion in index while keeping file on disk with `"one
"` intact.
7. **Unrelated Ref Stability**: `refs/heads/topic` remained fixed at Commit B.

## Tool Versions
- `git version 2.54.0 (Apple Git-157)`
- `Python 3.9.6`
