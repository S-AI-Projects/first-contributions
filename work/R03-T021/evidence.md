# Verification Evidence for Task R03-T021

- **Task**: R03-T021 · Make the command example reproducible: resetting a commit
- **Student**: Dheeraj Kumar
- **Guide**: `docs/additional-material/git_workflow_scenarios/resetting-a-commit.md`
- **Test Command**: `python3 work/R03-T021/check.py`

## State Assertions Verified
1. **Ref Movement**: `refs/heads/main` and `HEAD` moved backward from Commit C to Commit B.
2. **Unrelated Ref Stability**: `refs/heads/topic` remained completely unchanged at Commit B.
3. **Commit History**: Commit C was excised from `main`'s log; history reflects `[B, A]`.
4. **Working Tree Preservation**: Changes from Commit C (`todo.txt`) were preserved in the working tree as untracked (`?? todo.txt`).
5. **Index State**: Staging area was reset to Commit B with clean index (`git diff --cached` empty).
6. **Reproducibility**: Two separate temporary repositories independently executed the exact sequence and satisfied all assertions.

## Tool Versions
- `git version 2.54.0 (Apple Git-157)`
- `Python 3.9.6`
