# Remove a branch from your repository

If you have followed the tutorial up-to-now, our `<add-your-name>` branch has finished its purpose, it is time to delete it from your local machine's repo. This isn't necessary, but the name of this branch shows its rather special purpose. Its life can be made correspondingly short.

First, let's merge your `<add-your-name>` to your main, so to go to your main branch:
```
git checkout main
```

Merge `<add-your-name>` to main:
```
git merge <add-your-name> main
```

Remove `<add-your-name>` on your local machine's repo:
```
git branch -d <add-your-name>
```

You have now deleted your local machine's `<add-your-name>` branch and everything looks neat and tidy.
Though, at this point, you should still have the `<add-your-name>` branch in your GitHub fork. However, before you delete this, remember that you have sent a "Pull request" to my repo from this remote branch. So unless I've already merged it, don't delete this branch.

However, if I have merged your branch and you want to delete the remote branch, use:
```
git push origin --delete <add-your-name>
```

Now, you know how to tidy your branches.
With time, many commits will be added to my public repo. And the main branches of your local machine and of your GitHub fork won't be up-to-date. So in order to keep your repositories synchronized with mine, follow the steps below.

---

## Worked Exercise: Predict, Execute, Verify

This exercise teaches `git checkout main`, `git merge`, and `git branch -d` by asking you to predict what changes before you run the command, then checking your prediction against real Git state.

### Starting State

Consider a repository with the following history:

```
A ── B  ← topic
      \
       C  ← main (HEAD)
```

- Commit A: `notes.txt` with `alpha`
- Commit B: `notes.txt` appended with `beta`
- Commit C: `todo.txt` with `one` (only on `main`)
- You are currently on branch `topic`.

---

### Exercise 1 — `git checkout main`

**Predict:** Before running the command, write down what you think will change:
- Which ref will move? Which refs will stay fixed?
- Will any files appear in or disappear from the working tree?
- Will the index (staging area) change?

**Execute:**
```bash
git checkout main
```

**Verify (explanation):**

| Object | Before | After |
|--------|--------|-------|
| `HEAD` | points to `topic` | points to `main` (Commit C) |
| `main` ref | Commit C | Commit C (unchanged) |
| `topic` ref | Commit B | Commit B (unchanged) |
| Working tree | no `todo.txt` | `todo.txt` appears with `one\n` |
| Index | clean | clean |

`git checkout` only moves `HEAD`; branch refs themselves are never touched. Because `main` contains `todo.txt` (from Commit C) and `topic` does not, Git updates the working tree to add it.

---

### Exercise 2 — `git merge topic main`

**Predict:** `topic` points to Commit B, which is a direct ancestor of `main`'s Commit C. What will the merge do?

**Execute:**
```bash
git merge topic main
```

**Verify (explanation):**

| Object | Before | After |
|--------|--------|-------|
| `main` ref | Commit C | Commit C (unchanged) |
| `topic` ref | Commit B | Commit B (unchanged) |
| Commit graph | A–B–C | A–B–C (no new commit) |
| Working tree | clean | clean |

Because `topic` is already reachable from `main`, Git reports *Already up to date.* No merge commit is created, no ref moves, and the index and working tree are untouched. The source branch ref (`topic`) is **never** moved by a merge.

---

### Exercise 3 — `git branch -d topic`

**Predict:** What is deleted? Do any commit objects disappear?

**Execute:**
```bash
git branch -d topic
```

**Verify (explanation):**

| Object | Before | After |
|--------|--------|-------|
| `topic` ref | Commit B | **deleted** |
| Commit B object | exists | still exists |
| `HEAD` | Commit C | Commit C (unchanged) |
| Working tree | clean | clean |

`git branch -d` deletes only the **ref** (the pointer stored in `.git/refs/heads/topic`). It never removes commit objects — Commit B is still reachable through `main`'s ancestry chain and remains in the object store. Because `topic` was already merged into `main`, the `-d` (safe delete) flag succeeds; `-D` would be needed to force-delete an unmerged branch.

---

#### [Keeping your fork synced with the repository](keeping-your-fork-synced-with-this-repository.md)
