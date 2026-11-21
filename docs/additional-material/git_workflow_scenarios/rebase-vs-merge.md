# Rebase vs Merge

When contributing to open-source projects, it’s important to understand how to integrate your changes cleanly.  
Two common ways to bring updates from one branch into another are **merge** and **rebase**.


## What Is Rebase?

**Rebasing** replays your commits from one branch on top of another — effectively moving your work to start from the tip of another branch.  
This creates a **linear and clean commit history** without merge commits.

### Example

```bash
# Switch to your feature branch
git switch feature_branch

# Rebase your feature branch on top of main
git rebase main
```

Alternatively, 
```bash
git checkout <your-branch> 
git rebase <branch-you-want-to-copy-changes-from>
```
> `git switch <branch>` and `git checkout <branch>` both switch branches, but `switch` is newer and more user-friendly.

---
Both merge and rebase are used to integrate changes from one branch into another. 

**Merging** combines the histories of two branches by creating a new **merge commit**. It **preserves the true sequence of events**, showing exactly how and when branches diverged and rejoined. 

```bash
*   b576e33 (HEAD -> main) Merge branch 'feature' into main
|\
| * 22c5476 C4
| * b1a9c33 C3
* | f2a4d33 C2 (branch - 'feature')
|/
* c9f0a10 C1 (main)
```

**Rebasing**, on the other hand, **reapplies your commits** on top of another branch’s latest state. This effectively **keeps the commit history linear and clean**, as if all your work happened sequentially after the commits on the target branch. 

```bash
* e4d2b3c (HEAD -> feature) C4
* 3f68a71 C3 (branch - 'feature')
* f2a4d33 C2
* c9f0a10 C1 (main)
```

``` bash
# This command will display an ASCII-style commit graph directly in your terminal.
# It shows commit history in a tree-like structure.
git log --graph --oneline --all
```

## Merge vs Rebase

| **Feature**     | **Merge**                                      | **Rebase**                                  |
|------------------|------------------------------------------------|---------------------------------------------|
| **History**      | Preserves the true chronological history       | Creates a linear history                    |
| **Extra Commits**| Adds an extra merge commit                     | No extra commits                            |
| **Readability**  | Can become cluttered with merge commits        | Easier to read and follow                   |
| **Use Case**     | Ideal for public branches (e.g., `main`)       | Ideal for personal or feature branches      |


## Important Rule
**Never rebase a public/shared branch (like main).**
Rebasing rewrites commit history, which can cause problems for collaborators who have already based work on those commits.
Always rebase your personal or feature branch **onto main**, not the other way around.

> If the branch is shared — use merge.
> If the branch is personal — use rebase.


## Git Configuration Options
You can tell Git whether to merge or rebase when pulling updates:

```bash
# Always merge (default behavior)
git config pull.rebase false

# Always rebase by default (recommended for linear history)
git config --global pull.rebase true
```

**NOTE: Setting the global option ensures your local branches stay clean and linear without unnecessary merge commits.**

---

## Handling Paths with Spaces and Ambiguity in Rebase Workflows

When working with files and directories that contain spaces—such as `"release notes.txt"` or `"sample data/"`—special care is needed with **shell quoting** and Git's **`--` path separator**.

### Why Path Quoting and `--` Are Required

1. **Shell Word Splitting**: File and folder names with spaces must be enclosed in quotes (e.g., `"release notes.txt"` or `'sample data/data.txt'`). Without quotes, the shell splits the path into separate arguments, causing commands like `git add release notes.txt` to fail with `fatal: pathspec 'release' did not match any files`.
2. **Disambiguating Revisions from Paths (`--`)**: Git commands like `git checkout` can accept either a branch/commit revision or a file path. The `--` syntax explicitly signals that everything following it is a file path, preventing Git from misinterpreting a filename as a branch or revision name.

---

### Reproducible Walkthrough

#### 1. Initial Repository Setup

We create an isolated repository with author `Course Student <student@example.invalid>` on branch `main` with three initial commits:
- **Commit A**: `notes.txt` with `"alpha\n"`
- **Commit B**: appends `"beta\n"` to `notes.txt`
- **Commit C**: `todo.txt` with `"one\n"`
- Branch `topic` created at Commit B.

```bash
# Author identity
export GIT_AUTHOR_NAME="Course Student"
export GIT_AUTHOR_EMAIL="student@example.invalid"
export GIT_COMMITTER_NAME="Course Student"
export GIT_COMMITTER_EMAIL="student@example.invalid"

# Initialize repository
git init -b main repo
cd repo

# Commit A
printf "alpha\n" > notes.txt
git add notes.txt
git commit -m "Commit A: create notes.txt"

# Commit B
printf "beta\n" >> notes.txt
git add notes.txt
git commit -m "Commit B: append beta to notes.txt"
COMMIT_B=$(git rev-parse HEAD)

# Branch topic at Commit B
git branch topic "$COMMIT_B"

# Commit C on main
printf "one\n" > todo.txt
git add todo.txt
git commit -m "Commit C: add todo.txt"
```

#### 2. Add Paths with Spaces on `topic`

Switch to branch `topic`:

```bash
git switch topic
```

Create `"release notes.txt"` and `"sample data/data.txt"`:

```bash
mkdir -p "sample data"
printf "notes for release\n" > "release notes.txt"
printf "sample data payload\n" > "sample data/data.txt"
```

If you attempt to stage them without quotes:
```bash
$ git add release notes.txt
fatal: pathspec 'release' did not match any files
```

You must quote the paths:
```bash
git add "release notes.txt" "sample data/data.txt"
git commit -m "Add release notes and sample data"
```

#### 3. Rebase `topic` on Top of `main`

Now rebase your branch on `main` to incorporate Commit C:

```bash
git rebase main
```

Rebase applies your commit cleanly on top of `main`. Verify the commit history:

```bash
$ git log --oneline
<COMMIT_TOPIC_REBASED> (HEAD -> topic) Add release notes and sample data
<COMMIT_C> (main) Commit C: add todo.txt
<COMMIT_B> Commit B: append beta to notes.txt
<COMMIT_A> Commit A: create notes.txt
```

#### 4. Disambiguating Paths with `git checkout -- <path>`

Suppose you make an accidental change to `"release notes.txt"` and want to discard working tree modifications using `git checkout`:

```bash
printf "accidental change\n" >> "release notes.txt"
```

To restore the file from HEAD safely, use quotes and `--`:

```bash
git checkout -- "release notes.txt"
```

The `--` guarantees Git interprets `"release notes.txt"` as a filepath and not a branch name, safely restoring the file to `"notes for release\n"`.

Similarly, to check out a specific file from another branch (e.g. inspecting `notes.txt` as it was on `main`):

```bash
git checkout main -- "notes.txt"
```
