# Undoing a commit with `git reset`

`git reset` changes the current branch and/or the staging area, depending on
the arguments. Choose the form carefully: the default and path-specific forms
keep edits in the working tree, while `--hard` also replaces the working tree.

## Unstage changes without losing edits

After staging changes, running `git reset` with no arguments resets the index
to the current commit. It does not move the branch or discard working-tree
edits, so the changes remain available to edit or stage again:

```shell
git reset
```

To unstage only selected paths, use the path form:

```shell
git reset -- <file>
```

This resets those paths in the index while keeping their working-tree contents.
Other staged paths remain staged.

## Move the branch back and discard local changes

To move the current branch to an earlier commit and also replace the index
and working tree with that commit's contents, use `--hard`:

```shell
git reset --hard HEAD~1
```

This removes the latest commit from the current branch and discards local
changes to tracked files. Use it only when those changes are safe to lose.
It does not delete commits already shared with others; rewriting shared
history can disrupt collaborators, so coordinate before doing so.

In short, plain `git reset` unstages changes but keeps the edits, whereas
`git reset --hard <commit>` moves the branch and overwrites tracked files.
