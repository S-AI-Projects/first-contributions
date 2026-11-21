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
