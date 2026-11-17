# Rebase vs Merge

When contributing to open-source projects, it is essential to understand how to integrate changes cleanly. Two fundamental ways to bring updates from one branch into another are **merge** and **rebase**.

Both commands integrate changes between branches, but they structure history differently:
- **`git merge`**: Combines two branches by creating a new **merge commit** with two parents. It preserves the exact chronological history and records when branches diverged and rejoined.
- **`git rebase`**: Takes the commits from your branch and **replays** them onto the tip of the target branch, producing a strictly linear history without extra merge commits.

---

## Command Syntax: Switching Branches and Rebasing

To rebase your feature branch on top of `main`:

```bash
# Switch to your feature branch
git switch feature_branch

# Rebase your feature branch on top of main
git rebase main
```

Alternatively, you can use the older syntax:

```bash
git checkout <your-branch>
git rebase <branch-you-want-to-copy-changes-from>
```

> **Note on `git switch` vs `git checkout`:**
> `git switch <branch>` and `git checkout <branch>` both switch the current branch. `git switch` was introduced in Git 2.23 as a dedicated, safer command for branch switching, whereas `git checkout` is a multi-purpose command that also restores working-tree files.

---

## State Transition Overview: Before and After Diagrams

Consider a repository where work diverges after common ancestor Commit A:
- `main` has Commit C (adds `todo.txt`).
- `topic` has Commit B (modifies `notes.txt`).

```text
BEFORE INTEGRATION (Common Initial State)
History:
        B (topic) [notes.txt: alpha\nbeta\n]
       /
  A ───
       \
        C (main)  [todo.txt: one\n]

HEAD:         refs/heads/main -> C (or refs/heads/topic -> B)
Branch refs:  main -> C, topic -> B
Index:        Clean
Worktree:     Clean
```

### Scenario A: Rebase (`git switch topic` followed by `git rebase main`)

```text
AFTER REBASE
History:
  A ─── C (main) ─── B' (HEAD -> topic)

HEAD:         refs/heads/topic -> B' (Commit ID changed!)
Branch refs:  main -> C (unchanged), topic -> B' (moved)
Ancestry:     B' has single parent C (rewritten linear history)
Index:        Clean (contains merged notes.txt and todo.txt)
Worktree:     Clean (notes.txt: "alpha\nbeta\n", todo.txt: "one\n")
```

### Scenario B: Merge (`git switch main` followed by `git merge topic`)

```text
AFTER MERGE
History:
        B (topic)
       /         \
  A ───           M (HEAD -> main) [Merge Commit]
       \         /
        C ───────

HEAD:         refs/heads/main -> M (New merge commit)
Branch refs:  main -> M (moved), topic -> B (unchanged)
Ancestry:     M has two parents: Parent 1 = C, Parent 2 = B (original B preserved)
Index:        Clean (contains merged notes.txt and todo.txt)
Worktree:     Clean (notes.txt: "alpha\nbeta\n", todo.txt: "one\n")
```

---

## Reproducible Step-by-Step Demonstration

The following walkthrough sets up two independent temporary repositories with identical histories to demonstrate each operation.

### 1. Common Repository Setup

```bash
# Set author identity
export GIT_AUTHOR_NAME="Course Student"
export GIT_AUTHOR_EMAIL="student@example.invalid"
export GIT_COMMITTER_NAME="Course Student"
export GIT_COMMITTER_EMAIL="student@example.invalid"

# Initialize repository
git init -b main local-repo
cd local-repo

# Commit A on main: create notes.txt
printf "alpha\n" > notes.txt
git add notes.txt
git commit -m "Commit A"
COMMIT_A=$(git rev-parse HEAD)

# Create branch topic at Commit A, switch to it, and create Commit B
git branch topic
git switch topic
printf "beta\n" >> notes.txt
git add notes.txt
git commit -m "Commit B"
COMMIT_B=$(git rev-parse HEAD)

# Switch back to main (demonstrating git checkout) and create Commit C
git checkout main
printf "one\n" > todo.txt
git add todo.txt
git commit -m "Commit C"
COMMIT_C=$(git rev-parse HEAD)
```

At this point:
- `git rev-parse main` prints Commit C.
- `git rev-parse topic` prints Commit B.
- Commit A is the common ancestor of both branches.

---

### 2. Scenario A: Executing `git rebase main`

Switch to `topic` and rebase onto `main`:

```bash
# Switch to topic branch
git switch topic

# Rebase topic onto main
git rebase main
```

Inspect the results:

```bash
# 1. View the linear commit log
$ git log --oneline
<COMMIT_B_PRIME> (HEAD -> topic) Commit B
<COMMIT_C> (main) Commit C
<COMMIT_A> Commit A

# 2. Inspect the rebased commit ID and parent
$ git rev-parse HEAD
<COMMIT_B_PRIME>

$ git rev-parse HEAD^
<COMMIT_C>

# 3. Check reference pointers
$ git show-ref --heads
<COMMIT_C> refs/heads/main
<COMMIT_B_PRIME> refs/heads/topic

# 4. Check status and file contents
$ git status
On branch topic
nothing to commit, working tree clean

$ cat notes.txt
alpha
beta

$ cat todo.txt
one
```

#### Why Rebased Commits Receive New IDs
In Git, a commit's SHA-1/SHA-256 hash is computed cryptographically from its tree object, parent hashes, author/committer data, and commit message. Because `git rebase` changes the parent of Commit B from Commit A to Commit C (and updates the committer timestamp), the commit object is recreated with a completely new hash (`B'`). The original commit `B` remains in the object database until pruned by garbage collection.

---

### 3. Scenario B: Executing `git merge topic`

In an independent repository with the identical initial state, switch to `main` and merge `topic`:

```bash
# Switch to main branch
git switch main

# Merge topic into main
git merge topic -m "Merge branch 'topic' into main"
```

Inspect the results:

```bash
# 1. View graph log showing preserved branch topology
$ git log --graph --oneline
*   <MERGE_COMMIT_M> (HEAD -> main) Merge branch 'topic' into main
|\  
| * <COMMIT_B> (topic) Commit B
* | <COMMIT_C> Commit C
|/  
* <COMMIT_A> Commit A

# 2. Inspect the merge commit parents
$ git rev-parse HEAD^1 HEAD^2
<COMMIT_C>
<COMMIT_B>

# 3. Check reference pointers
$ git show-ref --heads
<MERGE_COMMIT_M> refs/heads/main
<COMMIT_B> refs/heads/topic

# 4. Check status and file contents
$ git status
On branch main
nothing to commit, working tree clean
```

#### Why Merge Preserves History
Unlike rebase, `git merge` does not modify or replay existing commits. Commit B retains its original hash and parent (Commit A). The merge creates an explicit commit `M` with two parents: `HEAD^1` (Commit C) and `HEAD^2` (Commit B).

---

## Detailed Comparison Table

| Attribute | `git rebase` (Scenario A) | `git merge` (Scenario B) |
| :--- | :--- | :--- |
| **Active Branch (`HEAD`)** | `topic` (switched before rebase) | `main` (switched before merge) |
| **`HEAD` Commit** | Points to new rebased commit `B'` | Points to new merge commit `M` |
| **Branch Reference `main`** | Unchanged at Commit C | Moves forward to merge commit `M` |
| **Branch Reference `topic`** | Moves to new commit `B'` | Unchanged at original Commit B |
| **Commit Object IDs** | Replaced: `B` is replaced by `B'` | Preserved: `B` and `C` keep their hashes |
| **Commit Ancestry** | Rewritten linear ancestry: `A <- C <- B'` | Preserved branched ancestry with 2 parents |
| **Staging Area (Index)** | Clean upon successful completion | Clean upon successful completion |
| **Working Tree** | Clean; contains all combined files | Clean; contains all combined files |

---

## Golden Rules for Rebase vs Merge

1. **Never rebase public, shared branches**: Rebasing rewrites commit hashes. If other developers have based work on those commits, rebasing will force them into complex, messy reconciliations.
2. **Rebase local feature branches**: Rebasing your personal feature branch onto upstream `main` keeps history linear and simplifies reviews.
3. **Use merge for integrating features into main**: Merging preserves the full historical context and marks clear integration boundaries.

### Git Pull Configuration

You can configure Git's default integration strategy when running `git pull`:

```bash
# Default behavior: create a merge commit
git config pull.rebase false

# Rebase local commits on top of incoming upstream commits
git config pull.rebase true
```

---

## Related Guides

- [Squashing Commits](squashing-commits.md)
- [Check Commit Log](check-commit-log.md)
- [Official Git Rebase Documentation](https://git-scm.com/docs/git-rebase)
- [Official Git Merge Documentation](https://git-scm.com/docs/git-merge)
