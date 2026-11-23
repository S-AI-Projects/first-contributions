# Reset a branch

```reset``` is the command which can be used when we want to reset the repository with respect to a commit or a branch. A reset, as the name suggests, discards everything on the base(current) branch and makes it exactly same as the branch with which we chose to reset the base branch (calling it as origin branch). This essentially means, that we will have a copy of the origin branch with the name of base branch.<br/>
However, the question is, why don't we just delete the base branch and checkout a new branch with the name of base branch from origin branch. Technically, it will have the same effect as resetting but in some industrial situations we do not have the access to delete a branch, or we can not delete a branch as it will hamper/disrupt a CI/CD pipeline or maybe an ongoing workflow. Hence, to avoid such situations which can lead to downtimes, we suggest using `git reset` whenever we want to reset a particular branch.

## Prerequisites Checklist

Before executing a branch reset, ensure the following preconditions are met to avoid accidental data loss or targeting the wrong branch:

1. **Current Working Branch**:
   `git reset` always operates on the currently checked-out branch (`HEAD`). You must switch to the branch you want to reset first:
   ```bash
   git checkout <base_branch>
   # or
   git switch <base_branch>
   ```
   Confirm your active branch using `git branch --show-current`.

2. **Repository State & Staged Changes**:
   Running `git reset --hard` will permanently discard any unstaged modifications and uncommitted staged changes.
   - Check status first:
     ```bash
     git status
     ```
   - If you have uncommitted or staged work you wish to preserve, save it to the stash before resetting:
     ```bash
     git stash push -u -m "backup before reset"
     ```

3. **Target (Origin) Branch Reference**:
   The branch or commit you are resetting to (`<origin_branch>`) must exist in your local repository.
   - If resetting to a remote branch (e.g. `origin/main`), fetch the latest commits first:
     ```bash
     git fetch origin
     ```
   - Verify the target branch exists:
     ```bash
     git rev-parse --verify <origin_branch>
     ```

4. **Local Configuration**:
   Ensure any identity or repository configuration is set locally (`git config --local`) so you do not modify or rely on global settings unintentionally.

---

## Minimal Setup & Step-by-Step Example

Here is a reproducible example demonstrating how to reset a feature branch (`topic`) to match the default branch (`main`):

### 1. Initial State
Consider a repository where `main` has advanced to Commit C (`todo.txt`), while `topic` remains at Commit B:

```
A --- B [topic]
       \
        C [main]
```

### 2. Verify Prerequisites
Switch to the branch to be reset and verify the working directory is clean:
```bash
git checkout topic
git status
```

### 3. Execute the Reset
Reset `topic` to match `main`:
```bash
git reset --hard main
```

### 4. Verify the New State
After the reset:
- `topic` points to Commit C, matching `main`:
  ```bash
  git rev-parse topic
  git rev-parse main
  ```
- The working tree and staging area are updated to reflect Commit C, and `git status` reports a clean working tree.

---

## The Command

Its very easy to execute a git reset for branch.
```
git reset <base_branch> <origin_branch>
```

An example could be:
```
git reset stage master --hard
```
The above command will reset the `stage` branch with `master` and therefore make `stage` exactly same as `master`.
You must be wondering about why `--hard` flag is used? This is to ignore all the changes which are or will be staged before/after the reset.

