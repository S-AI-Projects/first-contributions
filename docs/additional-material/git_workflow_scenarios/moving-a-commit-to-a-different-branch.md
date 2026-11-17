# Moving a commit to a different branch
What if you commit a change, and then realize that you committed to a different branch?
How can you change that? This is what this tutorial covers.

## Moving the latest commits to an existing branch
To do this, type:

```git reset HEAD~ --soft``` - Undoes the last commit, but leaves the changes available.  
```git stash``` - Records the state of the directory.  

```git checkout name-of-the-correct-branch``` - Switches to another branch.
```git stash pop``` - Removes latest stashed state.  
```git add .``` - Or try adding individual files.  
```git commit -m "your message here"``` - Saves and Commits the changes.  

Now your changes are on the correct branch


### Moving the latest commits to a new Branch
To do this, type:  
```git branch newbranch``` -  Creates a new Branch. Saving all the Commits.  
```git reset --hard HEAD~#``` - Move the current branch back by # commits. Remember, these commits will be gone from it  
```git checkout newbranch``` - Goes to the branch you created. It will have all the commits.  

Remember: Any changes not committed will be LOST.

---

## Recovery from Mistakes

When moving commits, mistakes can happen—such as accidentally running a destructive reset or resetting the wrong branch. Git tracks reference changes in the **reflog**, allowing you to recover your original commit and file state.

### 1. Recovering from an Accidental `git reset --hard`

If you accidentally run `git reset --hard HEAD~` instead of `--soft`, Git resets both the commit and your working tree, removing the files introduced in the undone commit.

**Recovery Point:**  
Git records the commit prior to the reset in the reference log. Inspect it using:

```bash
git reflog -n 5
```

The pre-reset commit will be accessible at `HEAD@{1}`.

**Recovery Command:**  
To restore the lost commit and working-tree files immediately:

```bash
git reset --hard HEAD@{1}
```

**Verification:**
1. Check the commit ID:
   ```bash
   git rev-parse HEAD
   ```
   Matches your original pre-reset commit hash.
2. Check the tree hash:
   ```bash
   git rev-parse HEAD^{tree}
   ```
   Matches the saved tree hash of the original commit.
3. Check working-tree files:
   ```bash
   git status
   ```
   Working tree is clean, and all files from the undone commit are restored.

---

### 2. Restoring the Original Branch After Moving a Commit

If you moved a commit from `main` to another branch using `git reset HEAD~ --soft`, but later realize you should not have removed the commit from `main`:

**Recovery Point:**  
Git maintains a branch-specific reflog for `main`. Inspect it using:

```bash
git reflog show main
```

The state before the reset is stored at `main@{1}`.

**Recovery Command:**  
Switch back to `main` and restore it to its pre-reset state:

```bash
git checkout main
git reset --hard main@{1}
```

**Verification:**
- `git rev-parse refs/heads/main` points back to the original commit.
- `git rev-parse HEAD^{tree}` matches the original tree hash.
- `git status` confirms a clean working tree with all restored files intact.

---

### What Cannot Be Recovered

While Git's reflog makes recovering committed states straightforward, be aware of its limitations:

1. **Uncommitted and Unstaged Edits:**  
   If you had uncommitted, unstaged modifications in your working tree when executing `git reset --hard`, Git never recorded them in its object database. These uncommitted changes **cannot** be recovered by the reflog.
2. **Expired Reflog Entries:**  
   Reflog records are local and temporary. By default, Git expires unreachable reflog entries after 30 days and reachable entries after 90 days (or when `git gc --prune=now` is explicitly run).
3. **Dropped Stashes:**  
   If an uncommitted stash entry is dropped with `git stash drop`, it is removed from the stash list and won't appear in standard branch reflogs (though it may temporarily exist as a dangling object recoverable via `git fsck`).

---

## Related Guides

- [Undoing a commit](undoing-a-commit.md)
- [Resetting a commit](resetting-a-commit.md)
- [Official Git Reset Documentation](https://git-scm.com/docs/git-reset)
- [Official Git Reflog Documentation](https://git-scm.com/docs/git-reflog)
