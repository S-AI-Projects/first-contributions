# Reset a branch

```reset``` is the command which can be used when we want to reset the repository with respect to a commit or a branch. A reset, as the name suggests, discards everything on the base(current) branch and makes it exactly same as the branch with which we chose to reset the base branch (calling it as origin branch). This essentially means, that we will have a copy of the origin branch with the name of base branch.<br/>
However, the question is, why don't we just delete the base branch and checkout a new branch with the name of base branch from origin branch. Technically, it will have the same effect as resetting but in some industrial situations we do not have the access to delete a branch, or we can not delete a branch as it will hamper/disrupt a CI/CD pipeline or maybe an ongoing workflow. Hence, to avoid such situations which can lead to downtimes, we suggest using `git reset` whenever we want to reset a particular branch.

## The Command

Its very easy to execute a git reset for branch.
```
git checkout <base_branch>
git reset --hard <origin_branch>
```

An example could be:
```
git checkout stage
git reset --hard master
```
The above commands will reset the `stage` branch with `master` and therefore make `stage` exactly same as `master`.
You must be wondering about why `--hard` flag is used? This is to ignore all the changes which are or will be staged before/after the reset.

### Worked exercise: reset `topic` to `main`

Set up a practice repository in an empty folder:

```
git init -b main demo && cd demo
echo "alpha" > notes.txt && git add notes.txt && git commit -m "A: create notes.txt"
echo "beta" >> notes.txt && git commit -am "B: append beta"
git branch topic
echo "one" > todo.txt && git add todo.txt && git commit -m "C: add todo.txt"
git checkout topic
echo "gamma (uncommitted)" >> notes.txt
echo "scratch" > scratch.txt
```

Now `topic` is at B, `main` is at C, `notes.txt` has one uncommitted edit, and `scratch.txt` is untracked.

**Predict.** Before you run anything, write down your answers:

1. Which branch ref moves, and to which commit?
2. Does `main` change?
3. What happens to the uncommitted edit in `notes.txt`?
4. Does `todo.txt` appear? Does `scratch.txt` survive?
5. What will `git status --short` show?

**Run it.** You are on `topic`, so reset `topic` to `main`:

```
git reset --hard main
```

**Check your prediction:**

```
git rev-parse topic main
git status --short
ls
cat notes.txt
```

You should see the same commit ID twice, `?? scratch.txt`, the files `notes.txt scratch.txt todo.txt`, and `notes.txt` containing only `alpha` and `beta`.

**Answer.** `git reset --hard main` moved the branch you are on (`refs/heads/topic`) from B to C. `main` was only read, so it did not move.

| Item | Before | After | Why |
|---|---|---|---|
| `refs/heads/topic` | B | C | reset moves the branch you are on |
| `refs/heads/main` | C | C | the target is only read, never changed |
| index | B's tree | C's tree | `--hard` resets the index |
| `notes.txt` | alpha, beta, gamma | alpha, beta | `--hard` discards uncommitted edits to tracked files |
| `todo.txt` | missing | present | it comes from C |
| `scratch.txt` | untracked | still untracked | reset never touches untracked files |

The old tip B is not lost yet: `git rev-parse ORIG_HEAD` prints its ID, and it stays in the reflog. The discarded `gamma` line was never committed, so nothing can bring it back.

**Why check out the branch first?** `git reset` always acts on the branch you are on and takes a single target. Typing two branch names, as in `git reset topic main --hard`, fails with `fatal: Cannot do hard reset with paths`, because Git reads `main` as a file path.

## Exercise: predict, run, explain

Try this in a throw-away folder. Your own name and email must be configured (see [configuring git](configuring-git.md)).

```
git init -b main
printf 'alpha\n' > notes.txt
git add notes.txt
git commit -m "A: create notes.txt"
printf 'beta\n' >> notes.txt
git commit -am "B: append beta"
printf 'one\n' > todo.txt
git add todo.txt
git commit -m "C: add todo.txt"
git branch topic HEAD~1
git switch topic
```

`main` has the commits A, B and C. `topic` is checked out and points at B. The goal is to make `topic` exactly like `main`.

**Predict.** For each of these three commands, write down where `topic` will point, what the index will hold, what the working tree will hold, and what `git status --short` will show:

```
git reset --soft main
git reset main
git reset --hard main
```

**Run.** Try one command, look at `git status --short` and `git log --oneline`, then go back to the start with `git reset --hard ORIG_HEAD` (git remembers where `topic` was before the reset in `ORIG_HEAD`) and try the next one.

**Answer.** In all three cases the changed object is the branch `refs/heads/topic`: it moves from B to C. `main` does not move, and `HEAD` stays on `topic`. The commands differ in how much more they change:

| Command | `topic` points at | Index | Working tree | `git status --short` |
|---|---|---|---|---|
| `git reset --soft main` | C | `notes.txt` (unchanged) | `notes.txt` (unchanged) | `D  todo.txt` |
| `git reset main` (same as `--mixed`) | C | `notes.txt`, `todo.txt` (reset to C) | `notes.txt` (unchanged) | ` D todo.txt` |
| `git reset --hard main` | C | `notes.txt`, `todo.txt` (reset to C) | `notes.txt`, `todo.txt` (reset to C) | nothing |

`--soft` only moves the branch, so the index and the working tree still look like B, and `todo.txt` shows up as a staged deletion. `--mixed`, the default, also resets the index, so `todo.txt` is an unstaged deletion. `--hard` also resets the working tree, so `todo.txt` appears and there is nothing left to commit.

`--hard` throws away edits to tracked files, staged or not. If you stage an extra line in `notes.txt` before running `git reset --hard main`, that line is gone afterwards. Untracked files are not touched: an `untracked.txt` that you created stays where it is.

**Compared with deleting the branch.** Switching to `main`, running `git branch -D topic` and then `git switch -c topic main` gives the same result: `topic` at C, with the same index and working tree as after `git reset --hard main`. The difference is that the old position of the branch is lost. After the reset, `git rev-parse topic@{1}` is B. After deleting and recreating the branch, `topic@{1}` does not exist.

**A note on the syntax above.** `git reset` always moves the branch that is checked out, so the base branch is not an argument. The form `git reset <base_branch> <origin_branch>` does not do that. In this example `git reset topic main --hard` stops with an error ("Cannot do hard reset with paths"), and `git reset topic main` moves no branch, because `main` is read as a file name. Switch to the branch you want to reset first (`git switch topic`), then run `git reset --hard main`.
