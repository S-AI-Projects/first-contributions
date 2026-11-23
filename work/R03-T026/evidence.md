# Verification Evidence for Task R03-T026

- **Task**: R03-T026 · Compare two ways to reach the state: gitflow
- **Student**: Dheeraj Kumar
- **Guide**: `docs/additional-material/git_workflow_scenarios/gitflow.md`
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
- `git version 2.54.0 (Apple Git-157)`
- `Python 3.9.6`
