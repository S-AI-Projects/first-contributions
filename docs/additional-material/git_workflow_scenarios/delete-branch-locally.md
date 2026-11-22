# Deleting a locally created branch

Deleting a local branch is useful after a branch has served its purpose or was
created by mistake. Git provides a safe deletion and a force deletion:

```shell
git branch -d <branch_name>
git branch -D <branch_name>
```

`-d` is the safe form. Git deletes the branch only when its changes have been
merged into the current branch (or its configured upstream). If the branch
contains unmerged work, Git refuses to delete it. `-D` is shorthand for
`--delete --force` and deletes the branch even if it contains unmerged work.

The long forms are `git branch --delete <branch_name>` for `-d` and
`git branch --delete --force <branch_name>` for `-D`. These commands delete
only the local branch; they do not delete a branch from a remote repository.

For example, if `topic` points to commit B and the current `main` branch
contains A, B, and C, then B is already part of `main`. The safe command
`git branch -d topic` can delete it. Force deletion is unnecessary in this
case.
