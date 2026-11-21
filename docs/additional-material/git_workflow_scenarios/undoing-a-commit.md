# Undoing a commit

`git reset` moves the current branch reference and updates the index and working tree according to its mode. Use it only when you understand which state you want to keep. This example uses a disposable repository so the reset cannot affect your project.

## Undo the latest local commit and discard its changes

The following sequence creates three commits on `main`. Commit A creates `notes.txt`, commit B appends to it, and commit C creates `todo.txt`. It also creates `topic` at B. The author is set only in this temporary repository.

```sh
tmp=$(mktemp -d)
git -C "$tmp" init -b main
git -C "$tmp" config user.name 'Course Student'
git -C "$tmp" config user.email 'student@example.invalid'
cd "$tmp"
printf 'alpha\n' > notes.txt
git add notes.txt && git commit -m 'A: add notes'
printf 'beta\n' >> notes.txt
git add notes.txt && git commit -m 'B: append notes'
B=$(git rev-parse HEAD)
git branch topic "$B"
printf 'one\n' > todo.txt
git add todo.txt && git commit -m 'C: add todo'
git reset --hard "$B"
```

The final command moves `main` from C back to B, resets the index and working tree to B, and removes `todo.txt` from this temporary working tree. The `topic` branch still points to B. The commit object C may remain temporarily in Git’s object database, but it is no longer reachable from these branches.

Expected state (the abbreviated object IDs vary):

```text
$ git status --short --branch
## main
$ git log --oneline --decorate -3
<B> (HEAD -> main, topic) B: append notes
<A> A: add notes
```

`notes.txt` contains `alpha` and `beta`, `todo.txt` is absent, and the index and working tree are clean. The branch tip changed from C to B; the `topic` ref stayed at B. `git reset --hard` overwrites tracked working-tree changes, so do not use it to discard work you need. For a shared commit, prefer `git revert`, which adds a new commit instead of moving a published branch backward.

## Keep the changes while undoing the commit

If you want to remove the latest commit but keep its changes staged, use `git reset --soft HEAD~`. The branch moves back one commit; the index and working tree keep the changes from the removed commit. With `--mixed` (the default), the changes remain in the working tree but become unstaged. These modes still rewrite the current branch history, so use them for local commits that have not been shared.

Run the focused state check with `python3 work/R03-T001/check.py` from the repository root.
