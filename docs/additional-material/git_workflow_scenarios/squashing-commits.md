# What is squashing?

In git, squashing refers to rewriting the history of your commits, so you end up with one commit with a description of the changes done.
It's usually done in open source projects because a lot of the history of a branch in open source projects is only relevant to the developer who created it, and this provides a simpler way to describe the changes made and also revert them if needed.

# How do you squash commits?

First, perform a git log to review the commits you would like to merge in your current branch.

```
git log
```

You should see a series of your commits like so:

```
commit blablabla
Author: omguhh
Date:   10/10/20
    Commit message 1

commit blablabla2
Author: omguhh
Date:   10/10/20
    Commit message 2
```

So now that you see the commits you wish to merge to one, we can move along into doing that with ```git rebase```. Assuming you're already familiar with ```git rebase```, we can starting squashing commits in the interactive mode of git rebase that you can activate like so:

```
git rebase -i
```

Now, with interactive rebasing you can specify the starting and end point of how far back you want to go with commits like so:

```
git rebase -i HEAD~2
```

Running this command will show you something like the following:

```
pick blablabla Changing test01.txt file
pick blablabla2 Adding dummy01.txt file

#
# Commands:
#  p, pick = use commit
#  r, reword = use commit, but edit the commit message
#  e, edit = use commit, but stop for amending
#  s, squash = use commit, but meld into previous commit
#  f, fixup = like "squash", but discard this commit's log message
#  x, exec = run command (the rest of the line) using shell
#
# These lines can be re-ordered; they are executed from top to bottom.
#
# If you remove a line here THAT COMMIT WILL BE LOST.
#
# However, if you remove everything, the rebase will be aborted.
#
# Note that empty commits are commented out
```

So if you want to squash ```blablabla2``` into ```blablablabla```, you would change the following :

```
pick blablabla Changing test01.txt file
squash blablabla2 Adding dummy01.txt file

```

If all goes well, you'd get a result that looks like this:

```
# This is a combination of 2 commits.
# The first commit's message is:
commit message 1

# This is the 2nd commit message:

commit message 2
```

That you can freely change before you decide to exit the editor to save these changes.

Running git log again should show you the commit message you entered before exiting the screen with the commits combined into one.

---

## Recovering from an Accidental or Unwanted Squash

Squashing commits rewrites Git history by replacing multiple individual commits with a single new commit. If you accidentally squash the wrong commits, lose meaningful intermediate commit messages, or squash on the wrong branch, Git provides a built-in safety net: **`git reflog`** and **`git reset --hard`**.

### The Setup and the Mistake

Consider an isolated repository with author `Course Student <student@example.invalid>` on branch `main` with three commits:
- **Commit A**: creates `notes.txt` with `"alpha\n"`
- **Commit B**: appends `"beta\n"` to `notes.txt`
- **Commit C**: creates `todo.txt` with `"one\n"`
- Branch `topic` was created at Commit B.

```bash
# Author identity
export GIT_AUTHOR_NAME="Course Student"
export GIT_AUTHOR_EMAIL="student@example.invalid"
export GIT_COMMITTER_NAME="Course Student"
export GIT_COMMITTER_EMAIL="student@example.invalid"

# Initial repository setup
git init -b main repo
cd repo

printf "alpha\n" > notes.txt
git add notes.txt
git commit -m "Commit A: create notes.txt"

printf "beta\n" >> notes.txt
git add notes.txt
git commit -m "Commit B: append beta to notes.txt"
COMMIT_B=$(git rev-parse HEAD)

git branch topic "$COMMIT_B"

printf "one\n" > todo.txt
git add todo.txt
git commit -m "Commit C: add todo.txt"
```

Viewing the commit history with `git log --oneline`:

```bash
$ git log --oneline
<COMMIT_C> (HEAD -> main) Commit C: add todo.txt
<COMMIT_B> (topic) Commit B: append beta to notes.txt
<COMMIT_A> Commit A: create notes.txt
```

#### The Mistake: Accidentally Squashing Commits B and C

Suppose you accidentally squash the last two commits (`HEAD~2`):

```bash
git rebase -i HEAD~2
```

In the interactive rebase editor, you mark the second commit as `squash`:
```text
pick <COMMIT_B> Commit B: append beta to notes.txt
squash <COMMIT_C> Commit C: add todo.txt
```

After saving and finishing the rebase, Git creates a single combined commit `BC`:

```bash
$ git log --oneline
<COMMIT_BC> (HEAD -> main) Combined commits B and C
<COMMIT_A> Commit A: create notes.txt
```

Your original Commit B and Commit C are no longer in `git log`!

---

### Step-by-Step Recovery

Because Git preserves unreachable commits in its reference log, no commit data is lost immediately.

#### Step 1: Find the Pre-Squash State with `git reflog`

Run `git reflog` to inspect recent reference movements:

```bash
$ git reflog
<COMMIT_BC> HEAD@{0}: rebase (finish): returning to refs/heads/main
<COMMIT_BC> HEAD@{1}: rebase (squash): Combined commits B and C
<COMMIT_B>  HEAD@{2}: rebase (start): checkout HEAD~2
<COMMIT_C>  HEAD@{3}: commit: Commit C: add todo.txt
```

Notice `HEAD@{3}` (or Git's automatic rollback reference `ORIG_HEAD`): it points directly to **Commit C** right before the rebase started.

#### Step 2: Restore the Original History with `git reset --hard`

Reset `main` back to its pre-squash commit:

```bash
git reset --hard ORIG_HEAD
```
*(Alternatively, reset using the specific reflog entry: `git reset --hard HEAD@{3}` or the commit SHA of Commit C).*

Output:
```text
HEAD is now at <COMMIT_C> Commit C: add todo.txt
```

#### Step 3: Verification

1. Verify commit history with `git log`:
   ```bash
   $ git log --oneline
   <COMMIT_C> (HEAD -> main) Commit C: add todo.txt
   <COMMIT_B> (topic) Commit B: append beta to notes.txt
   <COMMIT_A> Commit A: create notes.txt
   ```
2. Verify tree and file contents:
   ```bash
   $ cat notes.txt
   alpha
   beta

   $ cat todo.txt
   one
   ```
   Both the commit hashes and the working tree match the exact pre-squash state.

---

### What Cannot Be Recovered by This Method

While `git reflog` and `git reset --hard` cleanly restore committed history, be aware of what this recovery method **cannot** restore:

1. **Uncommitted Working Tree Changes**: Any uncommitted modifications or unstaged files that were present before running a hard reset are not recorded in Git's object store and cannot be restored. Always ensure `git status` is clean before rebasing or resetting.
2. **Rewritten History on Shared Remote Branches**: If you squashed commits and already force-pushed (`git push --force`) to a shared remote repository where collaborators have pulled the squashed history, resetting locally only fixes your local machine. Undoing the change for team members requires coordinating another force push or manual branch recovery.
3. **Pruned / Expired Commits**: Unreachable commits (such as the pre-squash commits) remain in Git's reflog for 30–90 days by default. If `git gc --prune=now` is explicitly run or the reflog expires, orphaned commits are permanently deleted.
