# Deleting a Locally Created Branch

Deleting a local branch is useful when you have finished working on a feature, merged your changes, or accidentally created an unnecessary or misspelled branch.

Git provides both safe deletion and forced deletion options:

```bash
git branch -D <branch_name>
```

```bash
git branch --delete --force <branch_name>  # Same as -D
```

```bash
git branch --delete <branch_name>          # Error on unmerged branch
```

---

## Safe Deletion vs. Forced Deletion

- **Safe deletion (`-d` or `--delete`)**:
  Git performs a safety check before removing the branch reference. If the branch contains commits that are not merged into your current `HEAD` (or into its upstream tracking branch, if configured), Git will abort the deletion with an error. This prevents accidental loss of unmerged work.
- **Forced deletion (`-D` or `--delete --force`)**:
  Bypasses the merge check and immediately removes the local branch reference, even if it contains commits that have not been merged.

---

## Reproducible Example Demonstration

The following self-contained walkthrough demonstrates safe deletion failure on an unmerged branch and successful forced deletion using both `-D` and `--delete --force`.

### 1. Repository Setup

Create an isolated temporary repository with initial branch `main`, author identity `Course Student`, and three commits:

```bash
# Create and enter temporary directory
mkdir -p /tmp/git-branch-demo && cd /tmp/git-branch-demo

# Initialize a local bare repository to serve as remote (self-contained, no network needed)
git init --bare remote.git

# Initialize working repository
git init -b main local
cd local
git remote add origin file://$(pwd)/../remote.git

# Set explicit author identity
git config user.name "Course Student"
git config user.email "student@example.invalid"

# Commit A: create notes.txt
printf "alpha\n" > notes.txt
git add notes.txt
git commit -m "Commit A"
COMMIT_A=$(git rev-parse HEAD)

# Commit B: append to notes.txt
printf "beta\n" >> notes.txt
git add notes.txt
git commit -m "Commit B"
COMMIT_B=$(git rev-parse HEAD)

# Commit C: create todo.txt
printf "one\n" > todo.txt
git add todo.txt
git commit -m "Commit C"
COMMIT_C=$(git rev-parse HEAD)

# Push main to origin
git push -u origin main
```

### 2. View Initial History and Create `topic` at Commit B

View the commit history on `main`:

```bash
$ git log --oneline
<COMMIT_C> (HEAD -> main, origin/main) Commit C
<COMMIT_B> Commit B
<COMMIT_A> Commit A
```

Now, create the `topic` branch pointing to Commit B:

```bash
# Push commit A to origin so origin/topic exists
git push origin ${COMMIT_A}:refs/heads/topic

# Create local topic branch tracking origin/topic and pointing to Commit B
git branch --track topic origin/topic
git branch -f topic ${COMMIT_B}
```

Verify branch references:

```bash
$ git branch -vv
* main  <COMMIT_C> [origin/main] Commit C
  topic <COMMIT_B> [origin/topic: ahead 1] Commit B
```

Here, `topic` contains Commit B, which has not yet been merged/pushed into its upstream tracking branch `origin/topic`.

### 3. Safe Deletion Fails on Unmerged Branch

Attempting to delete `topic` with `--delete` triggers Git's safety check:

```bash
$ git branch --delete topic
warning: not deleting branch 'topic' that is not yet merged to
         'refs/remotes/origin/topic', even though it is merged to HEAD
error: the branch 'topic' is not fully merged
hint: If you are sure you want to delete it, run 'git branch -D topic'
hint: Disable this message with "git config set advice.forceDeleteBranch false"
```

Because `topic` contains changes that are unmerged relative to its tracking branch, Git refuses to delete it with exit code `1`. The branch remains in place:

```bash
$ git branch --list
* main
  topic
```

### 4. Forced Deletion with `git branch -D topic`

When you are certain you want to discard the branch, use `-D`:

```bash
$ git branch -D topic
Deleted branch topic (was <COMMIT_B>).
```

Verify that the branch reference has been removed while `main` and your files remain intact:

```bash
$ git branch --list
* main

$ git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean

$ ls
notes.txt  todo.txt
```

### 5. Equivalent Forced Deletion with `git branch --delete --force`

In an independent repository with the same setup, running `--delete --force` behaves identically:

```bash
$ git branch --delete --force topic
Deleted branch topic (was <COMMIT_B>).
```

Verify branch listing:

```bash
$ git branch --list
* main
```

---

## Why Git Behaves This Way

1. **Branches are lightweight pointers**: In Git, a branch is merely a reference (a file in `.git/refs/heads/`) pointing to a specific commit hash.
2. **Safe deletion prevents accidental loss**: `git branch --delete` verifies that every commit reachable from the branch is also reachable from the target branch (or tracking upstream). If any commit would become orphaned/unreachable, Git halts the operation.
3. **Forced deletion removes the pointer**: `git branch -D` (or `git branch --delete --force`) removes the reference regardless of merge status. The underlying commits remain in the object store until garbage collection (`git gc`), allowing recovery via `git reflog` if needed.
4. **Current branch protection**: Note that Git will never allow you to delete whichever branch is currently checked out (`HEAD`), whether forced or not. You must switch to another branch first.

---

## Related Topics

- [Remove a branch from your repository](removing-branch-from-your-repository.md)
- [Why use branches?](why-using-branches.md)
- [Official Git branch Documentation](https://git-scm.com/docs/git-branch)
