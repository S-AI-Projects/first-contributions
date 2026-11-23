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

## Branch and Remote Reference Behavior: Worked Example

To understand exactly which local and remote references are modified when removing a branch, consider a scenario where your current branch is `topic` and the default branch is `main`.

### 1. Minimal Setup with Local and Remote References

In a disposable temporary repository connected to a local bare remote (`file://...`):
- Commits A, B, and C are created on `main` by `Course Student <student@example.invalid>`.
- Commit A creates `notes.txt` (`"alpha\n"`).
- Commit B appends `"beta\n"` to `notes.txt`.
- Branch `topic` is created at Commit B.
- Commit C adds `todo.txt` (`"one\n"`).
- Both `main` and `topic` are published to the remote `origin`.
- The active branch is set to `topic`.

```sh
git checkout topic
```

At this starting point:
- Active branch (`HEAD`): `refs/heads/topic` pointing to Commit B.
- `refs/heads/main`: points to Commit C.
- Working tree: does not contain `todo.txt` (which was introduced on `main` at Commit C).

### 2. Switching to the Default Branch: `git checkout main`

Before deleting a branch, switch away from it:

```sh
git checkout main
```

- **Which ref changes:** Only `HEAD` moves (from `refs/heads/topic` to `refs/heads/main`).
- **Which refs stay fixed:** Both `refs/heads/topic` (at Commit B) and `refs/heads/main` (at Commit C) remain unchanged.
- **Working tree:** `todo.txt` appears in the working directory because it is tracked in Commit C.

### 3. Merging Changes: `git merge topic main` (or `git merge topic`)

Next, merge the topic branch into `main`:

```sh
git merge topic main
```

- **Which ref changes:** Since Commit B is an ancestor of Commit C on `main`, Git reports `Already up to date.` No merge commit is created and `refs/heads/main` remains at Commit C.
- **Which refs stay fixed:** `refs/heads/topic` and `refs/heads/main` both stay at their existing commits.

### 4. Deleting the Local Branch: `git branch -d topic`

Delete the local branch ref:

```sh
git branch -d topic
```

- **Which ref changes:** The local reference `refs/heads/topic` is completely removed.
- **Which refs stay fixed:** `refs/heads/main` and `HEAD` stay at Commit C.
- **Object store:** Commit object B is **not** deleted; it remains in the Git object database as an ancestor of Commit C.
- **Remote refs:** `refs/remotes/origin/topic` remains untouched on the remote repository.

### 5. Deleting the Remote Branch: `git push origin --delete topic`

Finally, delete the remote tracking branch:

```sh
git push origin --delete topic
```

- **Which ref changes:** The remote reference `refs/heads/topic` on `origin` is deleted, and local tracking ref `refs/remotes/origin/topic` is removed.
- **Which refs stay fixed:** Local `refs/heads/main` and remote `refs/remotes/origin/main` remain completely unaffected.

### Reference Summary Matrix

| Step | Executed Command | Affected Reference | Unaffected References |
|---|---|---|---|
| 1. Switch branch | `git checkout main` | `HEAD` (`topic` -> `main`) | `refs/heads/topic`, `refs/heads/main` |
| 2. Merge check | `git merge topic main` | None (`Already up to date`) | `refs/heads/main`, `refs/heads/topic` |
| 3. Local deletion | `git branch -d topic` | `refs/heads/topic` (deleted) | `refs/heads/main`, `HEAD` |
| 4. Remote deletion | `git push origin --delete topic` | `refs/remotes/origin/topic` (deleted) | `refs/heads/main`, `refs/remotes/origin/main` |

#### [Keeping your fork synced with the repository](keeping-your-fork-synced-with-this-repository.md)
